"""POST /predict và GET /predictions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from backend import database, repository, schemas
from backend.database import lay_session
from backend.dependencies import lay_bo_gop, lay_phat_lai, lay_predictor

router = APIRouter(tags=["predict"])
log = logging.getLogger(__name__)


@router.post("/predict", response_model=schemas.KetQuaDuDoan, responses={
    422: {"description": "Không đủ AP khớp (`khong_du_ap`) hoặc sai schema"}})
async def predict(yeu_cau: schemas.YeuCauDuDoan) -> schemas.KetQuaDuDoan:
    predictor, bo_gop = lay_predictor(), lay_bo_gop()
    device_id = yeu_cau.device_id
    scan = [m.model_dump() for m in yeu_cau.scan]

    phat_lai = lay_phat_lai()
    if phat_lai is not None:
        rp_demo, scan = phat_lai.quet_tiep(device_id)
        log.info("DEMO %s: phát lại lần quét ở %s", device_id, rp_demo)

    # Threadpool: gọi thẳng thì chặn vòng lặp sự kiện, đuôi 1.243 ms với 40 request.
    x, y, so_ap, do_tre = await run_in_threadpool(predictor.du_doan, scan)

    # Chặn TRƯỚC khi gộp và ghi CSDL: toạ độ vô căn cứ kéo lệch cửa sổ gộp.
    if so_ap < predictor.so_ap_toi_thieu:
        raise HTTPException(422, {"loi": "khong_du_ap", "so_ap": so_ap,
                                  "toi_thieu": predictor.so_ap_toi_thieu})

    x_gop, y_gop = bo_gop.them(device_id, x, y)

    # Tra `database.TaoSession` lúc gọi để test trỏ được sang CSDL tạm.
    async with database.TaoSession() as session:
        await repository.ghi_du_doan(
            session, device_id=device_id, x=x, y=y, x_gop=x_gop, y_gop=y_gop,
            so_ap=so_ap, mo_hinh=predictor.ten_mo_hinh, do_tre_ms=do_tre)

    return schemas.KetQuaDuDoan(
        device_id=device_id, x=x, y=y, x_smooth=x_gop, y_smooth=y_gop,
        model=predictor.ten_mo_hinh, timestamp=datetime.now(timezone.utc),
        matched_ap=so_ap, scan_count=bo_gop.so_mau_dang_giu(device_id),
        latency_ms=round(do_tre, 3))


@router.get("/predictions", response_model=list[schemas.MucLichSu])
async def predictions(
    device_id: str | None = None,
    # SQLite hiểu `LIMIT -1` là không giới hạn.
    gioi_han: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(lay_session),
) -> list[schemas.MucLichSu]:
    return await repository.lich_su(session, device_id, gioi_han)
