"""GET /map, GET /graph, POST /route — dữ liệu không gian và chỉ đường.

Một response cho cả bản đồ (CTK45 cần 6). Toạ độ theo đơn vị lưới Bảng 4, cùng hệ
với /predict; khoảng cách là mét, đổi bằng `met_moi_don_vi`.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend import schemas
from backend.config import settings
from backend.dependencies import lay_do_thi

router = APIRouter(tags=["map"])

# Phục vụ thẳng từ data/reference/ để Dashboard khỏi giữ thêm một bản sao.
SO_DO_PNG = settings.reference_dir / "Map.png"


@lru_cache(maxsize=1)
def _du_lieu_ban_do() -> dict:
    """Dữ liệu bản đồ gần như không đổi nên dựng một lần rồi giữ trong bộ nhớ."""
    do_thi = lay_do_thi()
    xs = [x for x, _ in do_thi.toa_do.values()]
    ys = [y for _, y in do_thi.toa_do.values()]

    return {
        "don_vi": "don_vi_luoi",
        "met_moi_don_vi": do_thi.met_moi_don_vi,
        "pham_vi": {
            "x_min": min(xs), "x_max": max(xs),
            "y_min": min(ys), "y_max": max(ys),
        },
        "diem_tham_chieu": [
            do_thi.mo_ta_diem(k, day_du=True) for k in sorted(do_thi.toa_do)
        ],
        "do_thi": do_thi.thong_ke(),
    }


@router.get("/map", response_model=schemas.BanDo)
async def ban_do() -> schemas.BanDo:
    return schemas.BanDo(**_du_lieu_ban_do())


@router.get("/map/so-do.png", include_in_schema=False)
async def so_do_png() -> FileResponse:
    return FileResponse(SO_DO_PNG, media_type="image/png")


@router.get("/graph", response_model=schemas.DoThi)
async def do_thi() -> schemas.DoThi:
    g = lay_do_thi()
    return schemas.DoThi(
        **g.thong_ke(),
        canh=[
            {"tu": a, "den": b, "khoang_cach_m": round(d, 2),
             "cua_gia_dinh": (a, b) in g.cua_gia_dinh}
            for (a, b), d in sorted(g.canh.items())
        ],
    )


@router.post("/route", response_model=schemas.KetQuaChiDuong, responses={
    404: {"description": "Không có điểm tham chiếu hoặc khu vực"},
    409: {"description": "Không có đường đi"}})
async def chi_duong(yeu_cau: schemas.YeuCauChiDuong) -> schemas.KetQuaChiDuong:
    g = lay_do_thi()

    if yeu_cau.tu_rp is not None:
        if yeu_cau.tu_rp not in g.toa_do:
            raise HTTPException(404, f"Không có điểm tham chiếu '{yeu_cau.tu_rp}'")
        x, y = g.toa_do[yeu_cau.tu_rp]
    else:
        x, y = yeu_cau.tu_x, yeu_cau.tu_y

    if yeu_cau.den_nhom is not None:
        dich = g.diem_cua_nhom(yeu_cau.den_nhom)
        if not dich:
            raise HTTPException(404, f"Không có khu vực '{yeu_cau.den_nhom}'")
    else:
        if yeu_cau.den_rp not in g.toa_do:
            raise HTTPException(404, f"Không có điểm tham chiếu '{yeu_cau.den_rp}'")
        dich = {yeu_cau.den_rp}

    kq = g.chi_duong(x, y, dich, yeu_cau.thuat_toan)
    if kq is None:
        raise HTTPException(409, f"Không tìm được đường tới '{yeu_cau.den_nhom or yeu_cau.den_rp}'")

    return schemas.KetQuaChiDuong(
        **{**kq, "quang_duong_m": round(kq["quang_duong_m"], 2)},
        so_chang=len(kq["duong_di"]) - 1,
        thuat_toan=yeu_cau.thuat_toan,
    )
