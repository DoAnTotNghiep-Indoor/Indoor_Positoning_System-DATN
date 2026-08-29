"""POST /predict và WS /ws/location — nhận một lần quét, trả toạ độ."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from backend import database, repository, schemas
from backend.database import lay_session
from backend.dependencies import lay_bo_gop, lay_predictor
from backend.services.websocket_service import manager

router = APIRouter(tags=["predict"])


async def _mot_lan_quet(device_id: str, scan: list[dict]) -> dict:
    """Đường đi chung của REST và WebSocket, để hai lối không trôi khỏi nhau.

    Trước đây /predict tự viết lại đoạn này và quên bước phát, nên toạ độ gửi
    lên bằng REST không bao giờ tới được dashboard nào đang mở.
    """
    predictor = lay_predictor()
    bo_gop = lay_bo_gop()

    x, y, so_ap, do_tre = predictor.du_doan(scan)
    x_gop, y_gop = bo_gop.them(device_id, x, y)

    # database.TaoSession chứ không phải TaoSession import sẵn: `from ...
    # import TaoSession` khoá luôn giá trị lúc import, nên khi kiểm thử
    # trỏ CSDL sang tệp tạm thì module này vẫn ghi vào data/ips.db thật.
    async with database.TaoSession() as session:
        await repository.ghi_du_doan(
            session,
            device_id=device_id,
            x=x, y=y, x_gop=x_gop, y_gop=y_gop,
            so_ap=so_ap,
            mo_hinh=predictor.ten_mo_hinh,
            do_tre_ms=do_tre,
        )

    return {
        "device_id": device_id,
        "x": x, "y": y,
        "x_smooth": x_gop, "y_smooth": y_gop,
        "model": predictor.ten_mo_hinh,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "matched_ap": so_ap,
        "scan_count": bo_gop.so_mau_dang_giu(device_id),
        "latency_ms": round(do_tre, 3),
    }


@router.post("/predict", response_model=schemas.KetQuaDuDoan)
async def predict(yeu_cau: schemas.YeuCauDuDoan) -> schemas.KetQuaDuDoan:
    ket_qua = await _mot_lan_quet(
        yeu_cau.device_id,
        [{"bssid": m.bssid, "rssi": m.rssi} for m in yeu_cau.scan],
    )
    await manager.phat(ket_qua)
    return schemas.KetQuaDuDoan(**ket_qua)


@router.get("/predictions", response_model=list[schemas.MucLichSu])
async def predictions(
    device_id: str | None = None,
    gioi_han: int = 100,
    session: AsyncSession = Depends(lay_session),
) -> list[schemas.MucLichSu]:
    return await repository.lich_su(session, device_id, gioi_han)


@router.websocket("/ws/location")
async def ws_location(ws: WebSocket) -> None:
    """Kênh thời gian thực.

    Gửi lên {"device_id": ..., "scan": [{"bssid", "rssi"}, ...]} thì nhận lại
    toạ độ của chính mình, và toạ độ đó được phát cho mọi dashboard đang mở.
    Không gửi gì thì chỉ ở chế độ xem.

    Đồ án CTK45 chỉ có REST nên client phải polling — tốn pin, độ trễ cao.
    """
    await manager.ket_noi(ws)
    try:
        while True:
            goi = await ws.receive_json()
            device_id = goi.get("device_id")
            if not device_id:
                await ws.send_json({"loi": "thiếu device_id"})
                continue

            ket_qua = await _mot_lan_quet(device_id, goi.get("scan", []))
            await ws.send_json(ket_qua)
            await manager.phat(ket_qua, tru=ws)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.ngat(ws)
