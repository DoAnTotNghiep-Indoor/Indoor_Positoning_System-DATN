"""POST /predict và WS /ws/location — nhận một lần quét, trả toạ độ."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import (APIRouter, Depends, HTTPException, Query, WebSocket,
                     WebSocketDisconnect)
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from backend import database, repository, schemas
from backend.database import lay_session
from backend.dependencies import lay_bo_gop, lay_predictor
from backend.services.prediction_service import KhongDuAp
from backend.services.websocket_service import manager

router = APIRouter(tags=["predict"])


async def _mot_lan_quet(device_id: str, scan: list[dict]) -> dict:
    """Đường đi chung của REST và WebSocket, để hai lối không trôi khỏi nhau.

    Trước đây /predict tự viết lại đoạn này và quên bước phát, nên toạ độ gửi lên
    bằng REST không bao giờ tới được dashboard nào đang mở.
    """
    predictor = lay_predictor()
    bo_gop = lay_bo_gop()

    # Đẩy sang threadpool: `du_doan` là việc nặng CPU và đồng bộ, gọi thẳng trong
    # hàm async thì nó chặn vòng lặp sự kiện. Đo với 40 request song song: chặn
    # vòng lặp cho đuôi 1.243 ms, vượt ngưỡng 200 ms của yêu cầu phi chức năng.
    x, y, so_ap, do_tre = await run_in_threadpool(predictor.du_doan, scan)

    # Chặn TRƯỚC khi gộp và trước khi ghi CSDL: một toạ độ không dựa trên dữ liệu
    # nào thì không đáng nằm trong lịch sử, và nó còn kéo lệch cửa sổ gộp.
    if so_ap < predictor.so_ap_toi_thieu:
        raise KhongDuAp(so_ap, predictor.so_ap_toi_thieu)

    x_gop, y_gop = bo_gop.them(device_id, x, y)

    # database.TaoSession chứ không phải TaoSession import sẵn: `from ... import`
    # khoá luôn giá trị lúc import, nên khi test trỏ CSDL sang tệp tạm thì module
    # này vẫn ghi vào data/ips.db thật.
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
    try:
        ket_qua = await _mot_lan_quet(
            yeu_cau.device_id,
            [{"bssid": m.bssid, "rssi": m.rssi} for m in yeu_cau.scan],
        )
    except KhongDuAp as e:
        # 422 chứ không 400: yêu cầu đúng cú pháp, chỉ là nội dung không đủ để xử lý.
        # Trả kèm cả hai con số để client nói rõ "khớp 2, cần ít nhất 6". `toi_thieu`
        # là NGƯỠNG chứ không phải tổng số AP của thư viện.
        raise HTTPException(
            422,
            {"loi": "khong_du_ap", "so_ap": e.so_ap, "toi_thieu": e.toi_thieu},
        ) from e
    await manager.phat(ket_qua)
    return schemas.KetQuaDuDoan(**ket_qua)


@router.get("/predictions", response_model=list[schemas.MucLichSu])
async def predictions(
    device_id: str | None = None,
    # Có chặn trên và chặn dưới: SQLite hiểu `LIMIT -1` là KHÔNG giới hạn, nên
    # `?gioi_han=-1` trả nguyên bảng lịch sử cho một request không cần xác thực.
    gioi_han: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(lay_session),
) -> list[schemas.MucLichSu]:
    return await repository.lich_su(session, device_id, gioi_han)


@router.websocket("/ws/location")
async def ws_location(ws: WebSocket) -> None:
    """Kênh thời gian thực.

    Gửi lên {"device_id": ..., "scan": [{"bssid", "rssi"}, ...]} thì nhận lại toạ
    độ của chính mình, và toạ độ đó được phát cho mọi dashboard đang mở. Không gửi
    gì thì chỉ ở chế độ xem. CTK45 chỉ có REST nên client phải polling.
    """
    await manager.ket_noi(ws)
    try:
        while True:
            # Kiểm bằng chính schema của REST. Bản trước bóc tay bằng
            # `goi.get(...)` nên năm loại gói sai — không phải JSON, JSON là số
            # hay mảng, `scan` sai kiểu, phần tử thiếu `bssid` — đều bật ngoại
            # lệ ra khỏi vòng lặp và làm ĐỨT kênh (code 1006). Ứng dụng khi ấy
            # lặng lẽ rơi về REST, mất phần thời gian thực mà không ai biết.
            try:
                yeu_cau = schemas.YeuCauDuDoan.model_validate(await ws.receive_json())
            except json.JSONDecodeError:
                await ws.send_json({"loi": "khong_phai_json"})
                continue
            except ValidationError as e:
                await ws.send_json({
                    "loi": "goi_sai_dinh_dang",
                    "chi_tiet": [{"truong": ".".join(str(p) for p in m["loc"]),
                                  "vi_sao": m["msg"]}
                                 for m in e.errors(include_url=False,
                                                   include_context=False)][:5],
                })
                continue

            try:
                ket_qua = await _mot_lan_quet(
                    yeu_cau.device_id,
                    [{"bssid": m.bssid, "rssi": m.rssi} for m in yeu_cau.scan],
                )
            except KhongDuAp as e:
                await ws.send_json(
                    {"loi": "khong_du_ap", "so_ap": e.so_ap,
                     "toi_thieu": e.toi_thieu}
                )
                continue

            await ws.send_json(ket_qua)
            await manager.phat(ket_qua, tru=ws)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.ngat(ws)
