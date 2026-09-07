"""GET /map, GET /graph, POST /route — dữ liệu không gian và chỉ đường.

Gộp toàn bộ dữ liệu bản đồ vào MỘT response; CTK45 tách thành 6 endpoint GeoJSON
nên mở bản đồ một lần là 6 round-trip tới MongoDB Atlas.

Mọi toạ độ đơn vị MÉT, cùng hệ với thứ /predict trả về; client tự đổi sang khung
vẽ. Trả pixel thì client có hai phép đổi sẽ trôi khỏi nhau, marker nằm sai phòng
dù mô hình đúng tuyệt đối.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend import schemas
from backend.config import settings
from backend.dependencies import lay_do_thi

router = APIRouter(tags=["map"])

# Sơ đồ mặt bằng đã số hoá, phục vụ thẳng từ data/reference/ thay vì chép vào
# frontend/: Flutter buộc phải giữ bản sao riêng (chỉ đóng gói được asset trong
# mobile/), nhưng Dashboard thì không — thêm bản thứ ba là thêm chỗ quên đồng bộ.
SO_DO_PNG = settings.reference_dir / "Map.png"


@lru_cache(maxsize=1)
def _du_lieu_ban_do() -> dict:
    """Dữ liệu bản đồ gần như không đổi nên dựng một lần rồi giữ trong bộ nhớ."""
    do_thi = lay_do_thi()
    xs = [x for x, _ in do_thi.toa_do.values()]
    ys = [y for _, y in do_thi.toa_do.values()]

    return {
        "don_vi": "met",
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
    if not SO_DO_PNG.exists():
        raise HTTPException(404, "Chưa có data/reference/Map.png")
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


# Toạ độ được phép nằm ngoài hộp bao điểm tham chiếu ngần này mét. Hộp bao ấy
# CHÍNH LÀ toà nhà; nới ra một chút cho phần rìa mà khảo sát chưa đặt điểm.
LE_NGOAI_M = 10.0


def _kiem_trong_nha(x: float, y: float) -> None:
    """Chặn toạ độ không thể là vị trí trong thư viện.

    Không chặn thì (9999, 9999) vẫn được neo im lặng vào góc gần nhất rồi trả về
    một tuyến đường trông rất hợp lý — lại đúng họ lỗi "nhận dữ liệu vô nghĩa mà
    vẫn trả kết quả tự tin".
    """
    pv = _du_lieu_ban_do()["pham_vi"]
    if not (pv["x_min"] - LE_NGOAI_M <= x <= pv["x_max"] + LE_NGOAI_M
            and pv["y_min"] - LE_NGOAI_M <= y <= pv["y_max"] + LE_NGOAI_M):
        raise HTTPException(
            422,
            {"loi": "ngoai_pham_vi", "tu_x": x, "tu_y": y,
             "pham_vi": pv, "le_ngoai_m": LE_NGOAI_M},
        )


@router.post("/route", response_model=schemas.KetQuaChiDuong)
async def chi_duong(yeu_cau: schemas.YeuCauChiDuong) -> schemas.KetQuaChiDuong:
    g = lay_do_thi()

    # Neo điểm đầu vào điểm tham chiếu gần nhất khi client gửi toạ độ. Vị trí do
    # /predict trả về vốn đã luôn rơi đúng một điểm nên bước này gần như không
    # dịch chuyển gì — nó tồn tại để nhận được cả toạ độ tuỳ ý.
    if yeu_cau.tu_rp is not None:
        tu = yeu_cau.tu_rp
    else:
        _kiem_trong_nha(yeu_cau.tu_x, yeu_cau.tu_y)
        tu = g.gan_nhat(yeu_cau.tu_x, yeu_cau.tu_y)
    den = yeu_cau.den_rp

    # Kiểm CẢ HAI đầu. Bản trước chỉ kiểm đầu đến, nên tu_rp lạ lọt xuống
    # Dijkstra và vỡ bằng KeyError — client nhận 500 thay vì 404.
    for k in (tu, den):
        if k not in g.toa_do:
            raise HTTPException(404, f"Không có điểm tham chiếu '{k}'")

    duong, quang_duong = g.tim_duong(tu, den)
    if not duong:
        raise HTTPException(409, f"Không tìm được đường từ '{tu}' tới '{den}'")

    return schemas.KetQuaChiDuong(
        tu=tu,
        den=den,
        quang_duong_m=round(quang_duong, 2),
        so_chang=len(duong) - 1,
        duong_di=g.toa_do_duong(duong),
        chi_dan=g.chi_dan(duong),
    )
