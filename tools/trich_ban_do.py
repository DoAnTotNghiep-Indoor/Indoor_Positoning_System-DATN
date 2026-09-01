"""Trích hình học toà nhà từ data/reference/Map.png ra ban_do_tang1.json.

Chạy một lần rồi commit kết quả; backend chỉ đọc JSON nên không cần Pillow hay
SciPy lúc chạy thật (hai gói này KHÔNG có trong requirements.txt):

    pip install pillow scipy
    python -m tools.trich_ban_do

Map.png do nhóm CTK45 số hoá, chỉ có hai màu trên nền trong suốt: nét đen là
tường, xám #D9D9D9 vừa là lưới chấm toạ độ vừa là vách ngăn và kệ sách. Phân
biệt hai loại xám bằng kích thước — chấm lưới đều đúng 16 px.

PHÉP BIẾN ĐỔI MÉT ↔ PIXEL. Lưới chấm trải 1000 px ngang và 605 px dọc, hộp bao
40 điểm tham chiếu là 86 m × 52 m, cho 11,628 và 11,635 px/m — khớp tới 4 chữ
số có nghĩa. Đó là căn cứ khẳng định lưới chấm chính là hệ toạ độ mét.

CHIỀU TRỤC, chốt bằng hai bằng chứng độc lập:

* Trục y HƯỚNG LÊN. Toà nhà thắt eo ở giữa (1000 px hai đầu, 775 px đoạn giữa).
  Theo chiều này, đoạn eo ứng với y ∈ [6,4; 21,3] m và cả 8 điểm trong khoảng
  đó đều có |x| ≤ 30 m — vừa lọt. Chiều ngược lại buộc đoạn eo chứa RP22, RP25
  ở |x| = 43 m, rộng hơn cả eo.
* Trục x KHÔNG lật. Khớp 39 điểm với GPS trong POI.geojson bằng phép quay-co-
  tịnh tiến: không lật cho RMS 3,15 m, lật cho 13,84 m. (Tỉ lệ khớp ra 0,39 nên
  bản GeoJSON đó không đúng tỉ lệ thật, chỉ dùng được để xét chiều.)

CỬA GIẢ ĐỊNH. Map.png vẽ tường nhưng không vẽ cửa, chặn hết cạnh cắt tường thì
đồ thị vỡ 7 mảnh. Công cụ nối lại bằng số cạnh ít nhất, mỗi lần chọn cạnh NGẮN
NHẤT giữa hai mảnh — chỗ nhiều khả năng có cửa nhất. Sáu cạnh đó ghi riêng vào
`cua_gia_dinh` để ra thực địa đối chiếu, không trộn vào phần suy ra từ ảnh.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage

from ml import config

ANH = config.REFERENCE_DIR / "Map.png"
RA = config.REFERENCE_DIR / "ban_do_tang1.json"

# Chấm lưới đo được đều 16 px; lấy 17 làm ngưỡng để mọi khối lớn hơn là vật cản.
CHAM_LUOI_PX = 17

# Vùng đi được nhỏ hơn ngần này là khe hở một hai pixel do nét vẽ chồng nhau,
# không phải phòng thật.
VUNG_TOI_THIEU_PX = 500

# Bỏ qua đoạn sát hai đầu cạnh khi dò tường: bảy điểm tham chiếu nằm đúng trên
# nét vẽ cầu thang hoặc kệ sách (xem `_dich_ve_cho_di_duoc`).
BO_QUA_DAU_PX = 3.0

# Chỉ ghi lại cặp bị chặn trong bán kính này. Cạnh dài nhất mà đồ thị k=3 sinh
# ra là 21,0 m nên 25 m đã phủ hết, mà JSON giữ ở 471 dòng thay vì 3.179 dòng
# như khi ghi toàn bộ 780 cặp.
BAN_KINH_GHI_M = 25.0

SO_LANG_GIENG = 3


def _tach_ba_lop(anh: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Trả về (nét tường, vật cản, chấm lưới) — ba lớp tách rời.

    Phép dò chặn coi tường và vật cản như nhau nên `_tach_lop` gộp lại; bản vẽ
    cho báo cáo thì cần vẽ tường đậm còn kệ sách nhạt, nên cần bản chưa gộp.
    """
    a = np.array(Image.open(anh).convert("RGBA"))
    alpha, sang = a[..., 3], a[..., 0]
    net_den = (alpha > 40) & (sang <= 160)
    xam = (alpha > 128) & (sang > 150)

    nhan, _ = ndimage.label(xam, structure=np.ones((3, 3), bool))
    vat_can = np.zeros_like(xam)
    for i, o in enumerate(ndimage.find_objects(nhan), start=1):
        cao, rong = o[0].stop - o[0].start, o[1].stop - o[1].start
        if max(cao, rong) > CHAM_LUOI_PX:
            vat_can |= nhan == i

    return net_den, vat_can, xam & ~vat_can


def _tach_lop(anh: Path) -> tuple[np.ndarray, np.ndarray]:
    """(mặt nạ vật cản gộp, mặt nạ chấm lưới)."""
    net_den, vat_can, cham = _tach_ba_lop(anh)
    return net_den | vat_can, cham


def _luoi_toa_do(cham: np.ndarray) -> dict:
    """Hộp bao tâm các chấm lưới — chính là hộp bao 86 m × 52 m của bộ dữ liệu."""
    nhan, so = ndimage.label(cham, structure=np.ones((3, 3), bool))
    tam = ndimage.center_of_mass(cham, nhan, range(1, so + 1))
    ys = [t[0] for t in tam]
    xs = [t[1] for t in tam]
    return {"so_cham": so, "x_min": min(xs), "x_max": max(xs),
            "y_min": min(ys), "y_max": max(ys)}


def _vung_di_duoc(tuong: np.ndarray) -> np.ndarray:
    """Nhãn các mảng sàn đi được. 0 là tường hoặc bên ngoài toà nhà.

    Đường bao trong Map.png hở vài pixel ở chỗ các nét gặp nhau, nên phải nở
    tường thêm 1 px trước khi loang rồi co lại — không thì "bên ngoài" tràn vào
    khắp nhà. Loang từ ba mầm: góc trên trái và hai điểm trên mép phải, vì mảng
    trời bên phải bị nét vẽ cắt rời khỏi mảng trời bên trái.
    """
    lien_thong = np.ones((3, 3), bool)
    day = ndimage.binary_dilation(tuong, lien_thong)
    nhan, _ = ndimage.label(~day)
    ngoai = np.isin(nhan, [nhan[5, 5], nhan[5, -6], nhan[5, 1047]])
    trong = ndimage.binary_dilation(~ngoai & ~day, lien_thong) & ~tuong

    nhan, so = ndimage.label(trong)
    dien_tich = ndimage.sum(trong, nhan, range(1, so + 1))
    giu = [i + 1 for i in range(so) if dien_tich[i] >= VUNG_TOI_THIEU_PX]
    return np.where(np.isin(nhan, giu), nhan, 0)


class BanDo:
    def __init__(self) -> None:
        self.tuong, cham = _tach_lop(ANH)
        self.luoi = _luoi_toa_do(cham)
        self.vung = _vung_di_duoc(self.tuong)

        rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
        rp = rp.dropna(subset=["x", "y"])
        self.toa_do = {h.rp_id: (float(h.x), float(h.y)) for h in rp.itertuples()}
        self.ten = {h.rp_id: str(h.ten) for h in rp.itertuples()}

        # Hộp bao lấy từ chính bộ điểm chứ không viết cứng 86 x 52: ba con số
        # này phải đi cùng nhau, sửa toạ độ mà quên sửa hằng số là cả sơ đồ lệch
        # mà không có gì báo.
        self.goc_met_x = float(rp["x"].min())
        rong_m = float(rp["x"].max()) - self.goc_met_x
        cao_m = float(rp["y"].max()) - float(rp["y"].min())

        self.px_moi_met_x = (self.luoi["x_max"] - self.luoi["x_min"]) / rong_m
        self.px_moi_met_y = (self.luoi["y_max"] - self.luoi["y_min"]) / cao_m
        self._dich_ve_cho_di_duoc()

    def sang_pixel(self, x: float, y: float) -> tuple[float, float]:
        return (self.luoi["x_min"] + (x - self.goc_met_x) * self.px_moi_met_x,
                self.luoi["y_max"] - y * self.px_moi_met_y)

    def _dich_ve_cho_di_duoc(self) -> None:
        """Kéo điểm rơi trúng nét vẽ về ô đi được gần nhất.

        Bảy điểm rơi trúng vật cản, và đó là XÁC NHẬN chứ không phải lỗi: RP20,
        RP21, RP05, RP06 tên "Cầu thang" rơi đúng các khối cầu thang; RP22, RP25
        tên "Khu vực đọc" rơi trúng kệ sách dọc tường.

        Phải dịch tới ô thuộc vùng ĐỦ LỚN chứ không phải ô trống gần nhất: RP25
        cách mép ngoài kệ sách 2 px, mà khe đó là vùng cụt — dịch vào đấy thì
        điểm mất hết đường nối.
        """
        xa, chi_so = ndimage.distance_transform_edt(self.vung == 0,
                                                    return_indices=True)
        self.px: dict[str, tuple[int, int]] = {}
        self.da_dich: dict[str, float] = {}
        for rp, (x, y) in self.toa_do.items():
            u, w = self.sang_pixel(x, y)
            cot, hang = int(round(u)), int(round(w))
            if self.vung[hang, cot]:
                self.da_dich[rp] = 0.0
            else:
                self.da_dich[rp] = float(xa[hang, cot]) / self.px_moi_met_x
                hang, cot = int(chi_so[0, hang, cot]), int(chi_so[1, hang, cot])
            self.px[rp] = (cot, hang)

    def khoang_cach(self, a: str, b: str) -> float:
        (xa, ya), (xb, yb) = self.toa_do[a], self.toa_do[b]
        return math.hypot(xa - xb, ya - yb)

    def di_duoc(self, a: str, b: str) -> bool:
        """Đoạn thẳng a–b có nằm trọn trong MỘT mảng sàn không.

        Không dùng ngưỡng "dày bao nhiêu mét thì coi là tường": vách mỏng nhất
        trong ảnh chỉ 1 px nên mọi ngưỡng đều hoặc bỏ sót vách mỏng, hoặc cắt
        nhầm cạnh chỉ chạm mép. Xét theo mảng sàn thì không cần ngưỡng nào.
        """
        vung = self.vung[self.px[a][1], self.px[a][0]]
        if vung != self.vung[self.px[b][1], self.px[b][0]]:
            return False

        (x0, y0), (x1, y1) = self.px[a], self.px[b]
        buoc = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(buoc + 1):
            t = i / buoc
            u, w = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if (math.hypot(u - x0, w - y0) < BO_QUA_DAU_PX
                    or math.hypot(u - x1, w - y1) < BO_QUA_DAU_PX):
                continue
            if self.vung[int(round(w)), int(round(u))] != vung:
                return False
        return True


class _MangRoi:
    """Union-find, chỉ để đếm số mảnh và nối chúng lại."""

    def __init__(self, khoa) -> None:
        self._cha = {k: k for k in khoa}

    def goc(self, x: str) -> str:
        while self._cha[x] != x:
            self._cha[x] = self._cha[self._cha[x]]
            x = self._cha[x]
        return x

    def gop(self, a: str, b: str) -> bool:
        ga, gb = self.goc(a), self.goc(b)
        if ga == gb:
            return False
        self._cha[ga] = gb
        return True


def tinh(bd: "BanDo") -> dict:
    ten = list(bd.toa_do)
    cap = [(a, b) for i, a in enumerate(ten) for b in ten[i + 1:]]

    chan = [c for c in cap
            if not bd.di_duoc(*c) and bd.khoang_cach(*c) <= BAN_KINH_GHI_M]
    chan_set = set(chan)

    canh: dict[tuple[str, str], float] = {}
    for a in ten:
        gan = sorted((bd.khoang_cach(a, b), b) for b in ten if b != a)
        for d, b in gan[:SO_LANG_GIENG]:
            khoa = (a, b) if a < b else (b, a)
            if khoa not in chan_set:
                canh[khoa] = d

    roi = _MangRoi(ten)
    for a, b in canh:
        roi.gop(a, b)
    so_manh = len({roi.goc(k) for k in ten})

    cua: list[tuple[str, str]] = []
    while len({roi.goc(k) for k in ten}) > 1:
        khac = [c for c in cap if roi.goc(c[0]) != roi.goc(c[1])]
        a, b = min(khac, key=lambda c: bd.khoang_cach(*c))
        roi.gop(a, b)
        canh[(a, b)] = bd.khoang_cach(a, b)
        cua.append((a, b))

    return {
        "nguon": "Map.png",
        "sinh_boi": "python -m tools.trich_ban_do",
        "anh": {"rong_px": int(bd.tuong.shape[1]), "cao_px": int(bd.tuong.shape[0])},
        "luoi_toa_do": {
            "so_cham": bd.luoi["so_cham"],
            "x_min_px": round(bd.luoi["x_min"], 2),
            "x_max_px": round(bd.luoi["x_max"], 2),
            "y_min_px": round(bd.luoi["y_min"], 2),
            "y_max_px": round(bd.luoi["y_max"], 2),
            "px_moi_met_x": round(bd.px_moi_met_x, 4),
            "px_moi_met_y": round(bd.px_moi_met_y, 4),
            "goc_met_x": bd.goc_met_x,
            "truc_y_huong_len": True,
        },
        "diem_lech_khoi_san": {
            k: round(v, 2) for k, v in sorted(bd.da_dich.items()) if v > 0
        },
        "ban_kinh_ghi_m": BAN_KINH_GHI_M,
        "canh_xuyen_tuong": [list(c) for c in sorted(chan)],
        "so_manh_sau_khi_chan": so_manh,
        "cua_gia_dinh": [list(c) for c in cua],
    }


def ve_hinh(bd: BanDo, kq: dict) -> Path:
    """Hình kiểm chứng: 40 điểm phải nằm gọn trong lòng nhà, cạnh đỏ (bị loại)
    phải cắt qua nét vẽ, cạnh xanh thì không.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chan = {tuple(c) for c in kq["canh_xuyen_tuong"]}
    cua = {tuple(c) for c in kq["cua_gia_dinh"]}
    ten = list(bd.toa_do)

    fig, ax = plt.subplots(figsize=(13.2, 8.4), dpi=110)
    ax.imshow(Image.open(ANH), alpha=0.55)

    def doan(a: str, b: str, **kw) -> None:
        xa, ya = bd.sang_pixel(*bd.toa_do[a])
        xb, yb = bd.sang_pixel(*bd.toa_do[b])
        ax.plot([xa, xb], [ya, yb], **kw)

    da_ghi: set[str] = set()

    def nhan(loai: str, chu: str) -> str | None:
        if loai in da_ghi:
            return None
        da_ghi.add(loai)
        return chu

    for a in ten:
        gan = sorted(ten, key=lambda b: bd.khoang_cach(a, b))
        for b in gan[1:1 + SO_LANG_GIENG]:
            khoa = (a, b) if a < b else (b, a)
            if khoa in cua:
                continue
            if khoa in chan:
                doan(a, b, color="#d64545", lw=1.0, ls=":", zorder=2,
                     label=nhan("chan", "cạnh xuyên tường (đã bỏ)"))
            else:
                doan(a, b, color="#2f6f4f", lw=1.6, zorder=3,
                     label=nhan("giu", "cạnh giữ lại"))
    for a, b in cua:
        doan(a, b, color="#e08a1e", lw=2.0, ls="--", zorder=4,
             label=nhan("cua", "cửa giả định (chưa kiểm chứng thực địa)"))

    for rp, (x, y) in bd.toa_do.items():
        u, w = bd.sang_pixel(x, y)
        ax.plot(u, w, "o", ms=6, color="#1f4e79", zorder=5)
        ax.annotate(rp[2:], (u, w), textcoords="offset points", xytext=(0, 7),
                    ha="center", fontsize=6.5, color="#1f4e79", zorder=6)

    ax.set_title("Đồ thị đi lại dựng trên sơ đồ mặt bằng thật — "
                 f"{len(bd.toa_do)} điểm, {bd.px_moi_met_x:.2f} px/m")
    ax.legend(loc="lower center", ncol=3, fontsize=8, framealpha=0.9)
    ax.set_axis_off()
    fig.tight_layout()

    ra = config.REPORTS_DIR / "figures" / "do_thi_di_lai.png"
    ra.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ra, bbox_inches="tight")
    plt.close(fig)
    return ra


def main() -> None:
    bd = BanDo()
    kq = tinh(bd)
    van = json.dumps(kq, ensure_ascii=False, indent=2) + "\n"
    RA.write_bytes(van.encode("utf-8"))
    hinh = ve_hinh(bd, kq)

    print(f"{RA.name}: {len(kq['canh_xuyen_tuong'])} cặp bị tường chặn "
          f"trong bán kính {BAN_KINH_GHI_M:.0f} m, "
          f"{len(kq['cua_gia_dinh'])} cửa giả định "
          f"(đồ thị vỡ thành {kq['so_manh_sau_khi_chan']} mảnh trước khi nối).")
    print(f"{hinh.relative_to(config.ROOT_DIR)}: hình kiểm chứng")


if __name__ == "__main__":
    main()
