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
MAC_CUC_BO = frozenset("2367abef")
log = logging.getLogger(__name__)


@router.post("/predict", response_model=schemas.KetQuaDuDoan, responses={
    422: {"description": "Không đủ AP khớp (`khong_du_ap`) hoặc sai schema"}})
async def predict(yeu_cau: schemas.YeuCauDuDoan) -> schemas.KetQuaDuDoan:
    predictor, bo_gop = lay_predictor(), lay_bo_gop()
    device_id = yeu_cau.device_id
    scan = [m.model_dump() for m in yeu_cau.scan]

    # AP lạ lấy từ lần quét điện thoại gửi, trước khi DEMO thay.
    ap_la = predictor.mapper.ap_la(scan)

    phat_lai = lay_phat_lai()
    if phat_lai is not None:
        rp_demo, scan = phat_lai.quet_tiep(device_id)
        log.info("DEMO %s: phát lại lần quét ở %s", device_id, rp_demo)

    # Threadpool: gọi thẳng thì chặn vòng lặp sự kiện, đuôi 1.243 ms với 40 request.
    x, y, so_ap, do_tre = await run_in_threadpool(predictor.du_doan, scan)

    # Tra `database.TaoSession` lúc gọi để test trỏ được sang CSDL tạm. AP lạ và vị trí chung
    # một giao dịch: mỗi request một lần commit.
    async with database.TaoSession() as session:
        await repository.ghi_ap_la(session, ap_la)
        # Chặn TRƯỚC khi gộp và ghi vị trí: toạ độ vô căn cứ kéo lệch cửa sổ gộp. AP lạ vẫn
        # ghi: thư viện thay nhiều AP thì chính các lần quét bị chặn mới chứa AP mới.
        if so_ap < predictor.so_ap_toi_thieu:
            await session.commit()
            raise HTTPException(422, {"loi": "khong_du_ap", "so_ap": so_ap,
                                      "toi_thieu": predictor.so_ap_toi_thieu})
        x_gop, y_gop = bo_gop.them(device_id, x, y)
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


@router.get("/ap-la", response_model=schemas.ThongKeApLa)
async def ap_la(
    gioi_han: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(lay_session),
) -> schemas.ThongKeApLa:
    """BSSID điện thoại bắt được nhưng mô hình không dùng, gặp nhiều nhất trước."""
    mapper = lay_predictor().mapper
    tong, ds = await repository.ds_ap_la(session, gioi_han)
    return schemas.ThongKeApLa(
        so_lan_quet=tong,
        nguong_thuong_xuyen=mapper.min_appear_rate * 100,
        ap=[schemas.MucApLa(
            bssid=a.bssid,
            trong_du_lieu=a.bssid in mapper.bssid_du_lieu,
            # Bit quản trị cục bộ (bit 1 của octet đầu) bật khi chữ số hex thứ hai là một trong
            # 2 3 6 7 a b e f. So ký tự để một BSSID sai định dạng không làm hỏng cả bảng.
            mac_ngau_nhien=a.bssid[1:2] in MAC_CUC_BO,
            so_lan=a.so_lan,
            ti_le=a.so_lan / tong * 100,
            rssi_tb=a.tong_rssi / a.so_lan,
            rssi_manh_nhat=a.rssi_manh_nhat,
            lan_dau=a.lan_dau,
            lan_cuoi=a.lan_cuoi,
        ) for a in ds])
