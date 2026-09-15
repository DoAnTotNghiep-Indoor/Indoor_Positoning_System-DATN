"""POST /predict và WS /ws/location — nhận một lần quét, trả toạ độ.

WS chỉ đăng ký khi `WEBSOCKET=true`; mặc định tắt, client dùng REST."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import (APIRouter, Depends, HTTPException, Query, WebSocket,
                     WebSocketDisconnect)
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from backend import database, repository, schemas
from backend.config import settings
from backend.database import lay_session
from backend.dependencies import lay_bo_gop, lay_predictor
from backend.services.prediction_service import KhongDuAp
from backend.services.websocket_service import manager

router = APIRouter(tags=["predict"])
log = logging.getLogger(__name__)


async def _mot_lan_quet(device_id: str, scan: list[dict]) -> dict:
    """Đường xử lý chung của REST và WebSocket, để hai lối không trôi khỏi nhau."""
    predictor = lay_predictor()
    bo_gop = lay_bo_gop()

    # Threadpool: gọi thẳng thì chặn vòng lặp sự kiện, đuôi 1.243 ms với 40 request.
    x, y, so_ap, do_tre = await run_in_threadpool(predictor.du_doan, scan)

    # Chặn TRƯỚC khi gộp và ghi CSDL: toạ độ vô căn cứ kéo lệch cửa sổ gộp.
    if so_ap < predictor.so_ap_toi_thieu:
        raise KhongDuAp(so_ap, predictor.so_ap_toi_thieu)

    x_gop, y_gop = bo_gop.them(device_id, x, y)

    # Tra `database.TaoSession` lúc gọi để test trỏ được sang CSDL tạm.
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
        # Dạng Z như pydantic tuần tự hoá, để REST và WS trả cùng một chuỗi.
        "timestamp": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"),
        "matched_ap": so_ap,
        "scan_count": bo_gop.so_mau_dang_giu(device_id),
        "latency_ms": round(do_tre, 3),
    }


@router.post("/predict", response_model=schemas.KetQuaDuDoan, responses={
    422: {"description": "Không đủ AP khớp (`khong_du_ap`) hoặc sai schema"}})
async def predict(yeu_cau: schemas.YeuCauDuDoan) -> schemas.KetQuaDuDoan:
    try:
        ket_qua = await _mot_lan_quet(
            yeu_cau.device_id,
            [{"bssid": m.bssid, "rssi": m.rssi} for m in yeu_cau.scan],
        )
    except KhongDuAp as e:
        # Kèm hai con số để client nói "khớp 2, cần ít nhất 6".
        raise HTTPException(
            422,
            {"loi": "khong_du_ap", "so_ap": e.so_ap, "toi_thieu": e.toi_thieu},
        ) from e
    if settings.websocket:
        await manager.phat(ket_qua)
    return schemas.KetQuaDuDoan(**ket_qua)


@router.get("/predictions", response_model=list[schemas.MucLichSu])
async def predictions(
    device_id: str | None = None,
    # SQLite hiểu `LIMIT -1` là không giới hạn.
    gioi_han: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(lay_session),
) -> list[schemas.MucLichSu]:
    return await repository.lich_su(session, device_id, gioi_han)


async def ws_location(ws: WebSocket) -> None:
    """Gửi {"device_id", "scan"} thì nhận toạ độ của mình, toạ độ ấy được phát cho
    mọi kênh đang mở. Không gửi gì là chế độ xem."""
    await manager.ket_noi(ws)
    try:
        while True:
            # Gói sai nào cũng trả lỗi rồi nghe tiếp. Không dùng `receive_json()`: nó
            # vỡ KeyError với khung nhị phân.
            tin = await ws.receive()
            if tin["type"] == "websocket.disconnect":
                raise WebSocketDisconnect(tin.get("code", 1000))
            try:
                goi = json.loads(tin.get("text") or tin.get("bytes") or b"")
            except ValueError:
                await ws.send_json({"loi": "khong_phai_json"})
                continue
            try:
                yeu_cau = schemas.YeuCauDuDoan.model_validate(goi)
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
            except Exception:
                # Một lần CSDL bận không được làm đứt kênh thời gian thực.
                log.exception("lỗi xử lý lần quét qua WebSocket")
                await ws.send_json({"loi": "may_chu_loi"})
                continue

            await ws.send_json(ket_qua)
            await manager.phat(ket_qua, tru=ws)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.ngat(ws)


async def ws_tam_tat(ws: WebSocket) -> None:
    # Đóng trước khi bắt tay: không có route thì yêu cầu rơi xuống StaticFiles và vỡ 500.
    await ws.close(code=1008)


router.add_api_websocket_route("/ws/location", ws_location if settings.websocket else ws_tam_tat)
