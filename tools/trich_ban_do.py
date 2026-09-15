"""Trích hình học toà nhà từ data/reference/Map.png ra ban_do_tang1.json.

Chạy một lần rồi commit kết quả; backend chỉ đọc JSON nên không cần Pillow hay
SciPy lúc chạy thật (hai gói này KHÔNG có trong requirements.txt)::

    pip install pillow scipy
    python -m tools.trich_ban_do

Map.png chỉ hai màu trên nền trong suốt: nét đen là tường, xám #D9D9D9 vừa là
lưới chấm toạ độ vừa là vách ngăn và kệ sách — phân biệt bằng kích thước, chấm
lưới đều đúng 16 px.

ĐƠN VỊ LƯỚI ↔ PIXEL: lưới chấm trải 1000 × 605 px, hộp bao điểm tham chiếu
86 × 52 đơn vị, cho 11,628 và 11,635 px/đơn vị — lưới chấm chính là hệ toạ độ
Bảng 4. Khoá JSON vẫn tên `px_moi_met_*` để client cũ đọc được. Trục y HƯỚNG LÊN
và trục x KHÔNG lật: đoạn thắt eo chỉ lọt theo chiều y đó, và khớp 39 điểm với
GPS trong POI.geojson cho RMS 3,15 so với 13,84 khi lật.

ĐƠN VỊ LƯỚI ↔ MÉT: một đơn vị KHÔNG phải một mét. Hình 7 báo cáo CTK45 ghi bốn
đoạn dọc toà nhà 4 + 5,2 + 8,8 + 1,6 = 19,6 m, trên đường bao cao 55,87 đơn vị,
nên 0,3508 m/đơn vị. Đối chứng ngoài: đa giác toà thư viện trên OpenStreetMap
chỉ chứa trọn mặt bằng khi tỉ lệ ≤ 0,35 (đặt đúng phương vị đo từ Google Maps);
ở 1 m/đơn vị chỉ 74% mặt bằng lọt vào trong nhà.

LƯỚI ĐI LẠI: mặt nạ sàn đi được, góc lồi của vật cản, cặp nút nhìn thấy nhau và
cạnh cửa giả định — backend tìm đường ngắn nhất trên đó.

ĐỒ THỊ TẦM NHÌN: mọi cặp điểm có đoạn thẳng nằm trọn trong một mảng sàn ghi vào
`canh_nhin_thay`; backend nối thẳng các cặp đó, nên tuyến chỉ rẽ qua điểm mốc
khi thật sự có vật cản.

CỬA GIẢ ĐỊNH: Map.png vẽ tường nhưng không vẽ cửa, chặn hết cạnh cắt tường thì
đồ thị vỡ thành mảnh rời. `CUA_CU` là các cửa vòng nối tự động (mỗi lần chọn cạnh
ngắn nhất giữa hai mảnh) đã chọn trước đây, `CUA_NHOM_CHI_DINH` là cạnh nhóm nối
thêm; tất cả ghi riêng vào `cua_gia_dinh` để ra thực địa đối chiếu.
"""

from __future__ import annotations

import base64
import json
import math
import zlib
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

# Hình 7 báo cáo CTK45 (trang 44): bốn kích thước dọc, từ cạnh dưới lên.
CHIEU_DOC_HINH7_M = (4.0, 5.2, 8.8, 1.6)

# Cửa do vòng nối tự động chọn ở các bản trước, nay cố định để luật nối bên dưới
# không làm vòng đó chọn lại khác đi. Bỏ RP18-RP20 theo nhóm.
CUA_CU = [("RP19", "RP28"), ("RP16", "RP22"), ("RP17", "RP25"), ("RP10", "RP12"),
          ("RP02", "RP05"), ("RP20", "RP23")]

# Luật nối nhóm chỉ định: cạnh mở thêm như cửa giả định, cạnh cấm, và điểm chỉ
# được nối với đúng các điểm liệt kê.
CUA_NHOM_CHI_DINH = [("RP26", "RP19"), ("RP27", "RP19"), ("RP29", "RP20"),
                     ("RP32", "RP21"), ("RP06", "RP02"), ("RP20", "RP26"),
                     ("RP21", "RP27"), ("RP05", "RP45"), ("RP06", "RP44")]
CAM_NOI = [("RP18", "RP20"), ("RP45", "RP13"), ("RP45", "RP12"), ("RP45", "RP20"),
           ("RP44", "RP14"), ("RP44", "RP15"), ("RP44", "RP21")]
CHI_NOI = {"RP01": ("RP45", "RP02"), "RP03": ("RP44", "RP02")}
# Chỉ là đích: không nối điểm tham chiếu nào, tới được qua góc lối đi.
KHONG_NOI = {"RP42", "RP43"}


def duoc_noi(a: str, b: str) -> bool:
    if a in KHONG_NOI or b in KHONG_NOI or {a, b} in [set(c) for c in CAM_NOI]:
        return False
    return (a not in CHI_NOI or b in CHI_NOI[a]) and (b not in CHI_NOI or a in CHI_NOI[b])


# Hai cầu thang đầu hành lang nam, nhóm 2025 bổ sung: (x tâm, y tâm, rộng, cao)
# tính bằng đơn vị lưới. Map.png của CTK45 không vẽ chúng nên RP44/RP45 chỉ có chấm.
#
# LỚP HÌNH thuần, không ghi vào mặt nạ vật cản nên đồ thị và khoảng cách không
# đổi. Cỡ 5 × 5 theo hộp vẽ tay, không theo lõi 7,5 × 8,4 của RP20/RP21 vì dải
# hành lang nam chỉ cao chừng 6 đơn vị.
KHOI_CAU_THANG_BO_SUNG = [(28.0, 2.5, 5.0, 5.0), (-28.0, 2.5, 5.0, 5.0)]

# Vật cản trong Map.png tô sắc xám này; hai nơi vẽ lại khối bổ sung đều lấy từ
# đây để không lệch tông với 12 cầu thang có sẵn.
SAC_VAT_CAN_PNG = (217 / 255, 217 / 255, 217 / 255)
ALPHA_NEN_ANH = 0.55


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
    """Hộp bao tâm các chấm lưới — chính là hộp bao 86 × 52 đơn vị của bộ dữ liệu."""
    nhan, so = ndimage.label(cham, structure=np.ones((3, 3), bool))
    tam = ndimage.center_of_mass(cham, nhan, range(1, so + 1))
    ys = [t[0] for t in tam]
    xs = [t[1] for t in tam]
    return {"so_cham": so, "x_min": min(xs), "x_max": max(xs),
            "y_min": min(ys), "y_max": max(ys)}


def _vung_di_duoc(tuong: np.ndarray) -> np.ndarray:
    """Nhãn các mảng sàn đi được. 0 là tường hoặc bên ngoài toà nhà.

    Đường bao Map.png hở vài pixel chỗ các nét gặp nhau nên phải nở tường 1 px
    trước khi loang rồi co lại. Loang từ ba mầm vì mảng trời bên phải bị nét vẽ
    cắt rời khỏi mảng bên trái.
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

        Bảy điểm rơi trúng vật cản, và đó là XÁC NHẬN chứ không phải lỗi: RP20, RP21,
        RP05, RP06 tên "Cầu thang" rơi đúng khối cầu thang; RP22, RP25 "Khu vực đọc"
        rơi trúng kệ sách. Phải dịch tới ô thuộc vùng ĐỦ LỚN chứ không phải ô trống
        gần nhất: khe 2 px cạnh kệ sách là vùng cụt, vào đấy thì điểm mất đường nối.
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

        Không dùng ngưỡng "dày bao nhiêu mét thì là tường": vách mỏng nhất chỉ 1 px
        nên mọi ngưỡng đều hoặc bỏ sót vách mỏng, hoặc cắt nhầm cạnh chỉ chạm mép.
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

    cap = [c for c in cap if duoc_noi(*c)]
    thong = {c: bd.di_duoc(*c) for c in cap}
    chan = [c for c in cap if not thong[c] and bd.khoang_cach(*c) <= BAN_KINH_GHI_M]
    chan_set = set(chan)
    nhin_thay = sorted(tuple(sorted(c)) for c in cap if thong[c])

    canh: dict[tuple[str, str], float] = {}
    for a in ten:
        gan = sorted((bd.khoang_cach(a, b), b) for b in ten if b != a and duoc_noi(a, b))
        for d, b in gan[:SO_LANG_GIENG]:
            khoa = (a, b) if a < b else (b, a)
            if khoa not in chan_set:
                canh[khoa] = d

    roi = _MangRoi(ten)
    for a, b in canh:
        roi.gop(a, b)
    ten_noi = [k for k in ten if k not in KHONG_NOI]
    so_manh = len({roi.goc(k) for k in ten_noi})

    cua: list[tuple[str, str]] = []
    for a, b in CUA_CU + CUA_NHOM_CHI_DINH:
        roi.gop(a, b)
        canh[(a, b)] = bd.khoang_cach(a, b)
        cua.append((a, b))
    # Cố định danh sách trên thì vòng này không thêm gì; còn thêm là đồ thị vẫn đứt.
    while len({roi.goc(k) for k in ten_noi}) > 1:
        khac = [c for c in cap if roi.goc(c[0]) != roi.goc(c[1])]
        a, b = min(khac, key=lambda c: bd.khoang_cach(*c))
        roi.gop(a, b)
        canh[(a, b)] = bd.khoang_cach(a, b)
        cua.append((a, b))

    for a, ke in CHI_NOI.items():
        for b in ke:
            assert thong.get((a, b), thong.get((b, a))), f"{a}-{b} không nhìn thấy nhau"

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
        "chi_noi": {k: list(v) for k, v in CHI_NOI.items()},
        "cam_noi": [list(c) for c in CAM_NOI],
        "canh_nhin_thay": [list(c) for c in nhin_thay],
        "ty_le_quy_doi": ty_le_quy_doi(bd),
        "luoi_di_lai": luoi_di_lai(bd, cua),
    }


def ty_le_quy_doi(bd: "BanDo") -> dict:
    net_den, _, _ = _tach_ba_lop(ANH)
    hang = np.nonzero(net_den.any(axis=1))[0]
    cao = float(hang.max() - hang.min()) / bd.px_moi_met_y
    return {"met_moi_don_vi": round(sum(CHIEU_DOC_HINH7_M) / cao, 4),
            "chieu_doc_hinh7_m": list(CHIEU_DOC_HINH7_M),
            "chieu_doc_duong_bao_don_vi": round(cao, 2),
            "nguon": "Hình 7, báo cáo CTK45 trang 44"}


def luoi_di_lai(bd: "BanDo", cua: list[tuple[str, str]]) -> dict:
    """Mặt nạ đi được, góc lồi vật cản và cặp nút nhìn thấy nhau.

    Góc là ô trống kề chéo một ô vật cản mà hai ô kề cạnh đều trống. Giữ từng góc
    riêng, không gom: hai phía đầu một vách 1 px nằm sát nhau, gom lại thì nút rơi
    nhầm sang bên kia vách.
    """
    from backend.services.routing_service import nhin_thay

    trong = bd.vung > 0
    nha = ndimage.binary_fill_holes(ndimage.binary_dilation(trong, iterations=3))
    o = trong & nha

    cao, rong = o.shape
    p = np.pad(o, 1)
    goc = np.zeros_like(o)
    for dy in (-1, 1):
        for dx in (-1, 1):
            goc |= (o & p[1 + dy:cao + 1 + dy, 1:-1] & p[1:-1, 1 + dx:rong + 1 + dx]
                    & ~p[1 + dy:cao + 1 + dy, 1 + dx:rong + 1 + dx])
    goc_px = [[int(c), int(r)] for r, c in np.argwhere(goc)]

    nut = np.array(goc_px + [list(bd.px[k]) for k in bd.toa_do], float)
    ten = [None] * len(goc_px) + list(bd.toa_do)
    canh = []
    for i in range(len(nut) - 1):
        j = np.arange(i + 1, len(nut))
        canh += [[i, int(k)] for k in j[nhin_thay(o, nut[i], nut[j])]
                 if _noi_nut(ten[i], ten[k])]
    # Cửa chỉ nối đúng hai đầu mút, không mở lối cho nút khác đi tắt vào giữa.
    so = {k: len(goc_px) + i for i, k in enumerate(bd.toa_do)}
    canh += [[so[a], so[b]] for a, b in cua]

    return {"rong": rong, "cao": cao,
            "mat_na": _nen(np.packbits(o)),
            "rp_px": {k: list(bd.px[k]) for k in bd.toa_do},
            "goc_px": _nen(np.array(goc_px, np.uint16)),
            "canh": _nen(np.array(canh, np.uint16))}


def _noi_nut(a: str | None, b: str | None) -> bool:
    """Nút góc không mang tên; điểm trong CHI_NOI không nối với góc nào."""
    if a is None or b is None:
        return (a or b) not in CHI_NOI
    return duoc_noi(a, b)


def _nen(a: np.ndarray) -> str:
    return base64.b64encode(zlib.compress(a.tobytes(), 9)).decode()


def _ve_khoi_bo_sung(ax, bd: "BanDo") -> None:
    """Khối cầu thang bổ sung, vẽ trong hệ PIXEL của Map.png."""
    from matplotlib.patches import Rectangle

    for x, y, rong, cao in KHOI_CAU_THANG_BO_SUNG:
        u, w = bd.sang_pixel(x - rong / 2, y + cao / 2)
        ax.add_patch(Rectangle((u, w), rong * bd.px_moi_met_x, cao * bd.px_moi_met_y,
                               facecolor=SAC_VAT_CAN_PNG, alpha=ALPHA_NEN_ANH,
                               edgecolor="none", zorder=1))


def ve_hinh(bd: BanDo, kq: dict) -> Path:
    """Hình kiểm chứng: mọi điểm nằm gọn trong lòng nhà, cạnh xanh (nhìn thấy
    nhau) không được cắt qua nét vẽ nào.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cua = {tuple(c) for c in kq["cua_gia_dinh"]}
    chi_dinh = set(CUA_NHOM_CHI_DINH)

    fig, ax = plt.subplots(figsize=(13.2, 8.4), dpi=110)
    ax.imshow(Image.open(ANH), alpha=ALPHA_NEN_ANH)
    _ve_khoi_bo_sung(ax, bd)

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

    for a, b in kq["canh_nhin_thay"]:
        doan(a, b, color="#2f6f4f", lw=0.6, alpha=0.45, zorder=3,
             label=nhan("thay", "cặp nhìn thấy nhau — nối thẳng"))
    for a, b in cua - chi_dinh:
        doan(a, b, color="#e08a1e", lw=2.0, ls="--", zorder=4,
             label=nhan("cua", "cửa giả định (chưa kiểm chứng thực địa)"))
    for a, b in cua & chi_dinh:
        doan(a, b, color="#c0392b", lw=2.0, ls="--", zorder=4,
             label=nhan("chi_dinh", "nối thêm theo nhóm chỉ định"))

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

    print(f"{RA.name}: {len(kq['canh_nhin_thay'])} cặp nhìn thấy nhau, "
          f"{len(kq['canh_xuyen_tuong'])} cặp bị tường chặn "
          f"trong bán kính {BAN_KINH_GHI_M:.0f} m, "
          f"{len(kq['cua_gia_dinh'])} cửa giả định "
          f"(đồ thị vỡ thành {kq['so_manh_sau_khi_chan']} mảnh trước khi nối).")
    print(f"{hinh.relative_to(config.ROOT_DIR)}: hình kiểm chứng")


if __name__ == "__main__":
    main()
