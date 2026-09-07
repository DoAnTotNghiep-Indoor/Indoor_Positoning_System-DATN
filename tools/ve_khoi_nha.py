"""Sơ đồ hình khối toà nhà thư viện nhìn từ trên cao, xuất ra reports/figures/.

    python -m tools.ve_khoi_nha

Khác mọi hình còn lại trong `tools/`: chúng dựng từ `Map.png` (mặt bằng BÊN
TRONG một tầng), hình này dựng từ ảnh vệ tinh Google Maps (khối tích BÊN NGOÀI
cả cụm công trình). Ảnh KHÔNG chép vào kho mã vì có bản quyền; chỉ chép số đo
kèm cách đo, để dựng lại được mà không cần ảnh gốc:

  * tách mái theo hiệu R-B (mái xám, sân đất đỏ), lấp lỗ, mở/đóng hình thái;
  * cắt riêng từng khối bằng đĩa tròn rồi mở 15 px cho đứt cổ nối, quét góc
    0-90° bước 0,25° tìm khung chữ nhật đặc nhất;
  * khe hở đo bằng biến đổi khoảng cách nên là khe HẸP NHẤT, không phải
    khoảng cách tâm;
  * tỉ lệ px→mét chốt bằng cạnh dài khối thư viện = 86 m.

Năm khối nằm trên HAI họ góc, không phải một: B-C-D theo lưới nhà (68-69°,
khớp `PHUONG_VI_TRUC_DAI`), A và E xoay 23-26°, lệch 44,5°. Chính chỗ lệch này
tạo thế chong chóng của cụm nhà.

PHÁC HOẠ khối tích, không phải bản vẽ đo đạc: kích thước là đường bao mái nên
lớn hơn chân tường 1-2 m mỗi phía; toạ độ vẫn lấy từ `reference_points.csv`.
Tỉ lệ còn một chỗ chưa chốt (hộp bao mái 2,37 · đa giác Google 1,76 · dữ liệu
86/52 = 1,65) nên hình KHÔNG vẽ hộp 86 × 52 m chồng lên.
"""

from __future__ import annotations

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow, Polygon

from ml import config

RA = config.REPORTS_DIR / "figures"

# Phương vị trục dài cụm nhà, độ theo chiều kim đồng hồ từ bắc. Xem
# `LaBan.gocBacSoDo` — cùng một phép đo, ba đường độc lập khớp trong 3,5°.
PHUONG_VI_TRUC_DAI = 338.5

# Lưới nhà nghiêng bao nhiêu so với trục bắc-nam.
NGHIENG = 360.0 - PHUONG_VI_TRUC_DAI

# Cùng góc ấy đọc trên ảnh (trục y hướng XUỐNG), tức góc dùng để khớp khung.
GOC_LUOI_ANH = 90.0 - NGHIENG

# A và E lệch ngần này so với lưới nhà — trung bình của 22,5-25,75° đo được.
LECH_CANH = 44.5

TY_LE_PX_MOI_MET = 6.602

# Gốc toạ độ mét: tâm khối Tây Nam.
GOC_PX = (277.0, 569.0)

# Tâm và cạnh mái theo pixel ảnh, kèm góc khung đo được trên ảnh.
KHOI = {
    "A": {"tam": (405.5, 121.9), "canh": (175.0, 172.0), "goc": 23.75,
          "ten": "Khối Bắc", "thu_vien": False},
    "B": {"tam": (149.5, 217.5), "canh": (188.0, 178.0), "goc": 69.00,
          "ten": "Khối Tây Bắc", "thu_vien": True},
    "C": {"tam": (265.0, 380.0), "canh": (176.0, 190.0), "goc": 68.50,
          "ten": "Khối Giữa", "thu_vien": True},
    "D": {"tam": (277.0, 569.0), "canh": (184.0, 182.0), "goc": 69.00,
          "ten": "Khối Tây Nam", "thu_vien": True},
    "E": {"tam": (542.2, 496.4), "canh": (172.0, 176.0), "goc": 24.25,
          "ten": "Trung tâm CNTT", "thu_vien": False},
}

# Phần thấp giữa cụm: sảnh nối dính liền cạnh đông khối Giữa, và một khối phụ
# trợ nhỏ nhô tiếp về phía đông. Ghim "Trung tâm Thông tin - Thư viện" của
# Google rơi đúng lên sảnh này chứ không lên khối mái nào.
LOI = {
    "sanh": {"tam": (392.0, 334.0), "canh": (104.0, 92.0), "goc": GOC_LUOI_ANH,
             "ten": "Sảnh nối"},
    "phu": {"tam": (470.0, 318.0), "canh": (62.0, 60.0), "goc": GOC_LUOI_ANH,
            "ten": "Khối phụ trợ"},
}

# Hai mảng đất đỏ, không phải một: ảnh cũ nhìn thành một sân nên bản trước vẽ
# một vòng tròn nằm giữa hai mảng, tức nằm đúng chỗ đang có mái.
SAN = {
    "tren": [(334, 303), (316, 251), (333, 184), (371, 192),
             (407, 211), (425, 230), (408, 300), (388, 307)],
    "duoi": [(381, 368), (435, 360), (482, 408), (469, 463),
             (455, 492), (435, 493), (373, 431), (373, 384)],
}

# Cặp khối chạm nhau trên ảnh (khe hở đo được bằng 0 px).
DINH_LIEN = [("B", "C"), ("C", "D"), ("C", "sanh"), ("sanh", "phu")]

# (khối, khối, khe hở mét, phía đặt nhãn: +1 hoặc -1).
KHE_HO = [("sanh", "A", 7.7, +1), ("sanh", "E", 6.5, +1), ("D", "E", 10.5, -1)]

MAU = {
    "thu_vien": "#C8D8E8", "vien_thu_vien": "#31536E",
    "khac": "#E4E0D8", "vien_khac": "#8A8578",
    "loi": "#DCE6EE", "vien_loi": "#5C7A94",
    "song": "#8FA9BF", "san": "#E3B9A2", "chu": "#22303C",
}


def _met(px: tuple[float, float]) -> tuple[float, float]:
    """Pixel ảnh → mét, gốc ở khối Tây Nam, trục y hướng LÊN như bản đồ."""
    return ((px[0] - GOC_PX[0]) / TY_LE_PX_MOI_MET,
            (GOC_PX[1] - px[1]) / TY_LE_PX_MOI_MET)


def _hinh_chu_nhat(tam: tuple[float, float], canh: tuple[float, float],
                   goc_anh: float, co: float = 1.0) -> np.ndarray:
    """Khung chữ nhật trong hệ mét. `goc_anh` đọc ở hệ ảnh (y xuống) nên phải
    đảo dấu; quên chỗ này thì cả cụm nhà lật gương qua trục bắc-nam."""
    a, b = canh[0] * co / 2, canh[1] * co / 2
    t = np.radians(-goc_anh)
    xoay = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    return np.array([(-a, -b), (a, -b), (a, b), (-a, b)]) @ xoay.T + np.array(tam)


def _khung(v: dict, co: float = 1.0) -> np.ndarray:
    canh_m = (v["canh"][0] / TY_LE_PX_MOI_MET, v["canh"][1] / TY_LE_PX_MOI_MET)
    return _hinh_chu_nhat(_met(v["tam"]), canh_m, v["goc"], co)


def _ve_mai_chop(ax, v: dict, mau_net: str) -> None:
    """Bốn sống mái chạy từ góc vào ô trũng giữa — nét nhận ra ngay cụm nhà này
    trên ảnh vệ tinh, và là thứ phân biệt khối mái với phần sảnh mái bằng."""
    ngoai, trong = _khung(v), _khung(v, 0.42)
    ax.add_patch(Polygon(trong, closed=True, facecolor="none",
                         edgecolor=mau_net, lw=0.9, alpha=0.6, zorder=5))
    for p, q in zip(ngoai, trong):
        ax.plot(*zip(p, q), color=mau_net, lw=0.9, alpha=0.6, zorder=5)


def ve() -> "config.Path":
    fig, ax = plt.subplots(figsize=(9.6, 9.8), dpi=140)
    ax.set_facecolor("white")

    for dinh in SAN.values():
        ax.add_patch(Polygon([_met(p) for p in dinh], closed=True,
                             facecolor=MAU["san"], alpha=0.7, edgecolor="none",
                             zorder=1))
    # Hai mảng sân đều là khe hẹp giữa các khối, không đủ chỗ đặt chữ vào
    # trong, nên nhãn ra ngoài rồi kéo đường chỉ vào.
    for nhan, dat, chi in (("Sân trong\n(bắc)", (128, 96), (398, 258)),
                           ("Sân trong\n(nam)", (632, 636), (424, 448))):
        ax.annotate(nhan, xy=_met(chi), xytext=_met(dat), ha="center",
                    va="center", fontsize=9.5, style="italic", color="#8E5F45",
                    zorder=6,
                    arrowprops=dict(arrowstyle="-", lw=0.8, color="#B58B72"))

    tam = {k: _met(v["tam"]) for k, v in list(KHOI.items()) + list(LOI.items())}
    for a, b in DINH_LIEN:
        ax.plot(*zip(tam[a], tam[b]), color=MAU["song"], lw=13, alpha=0.45,
                solid_capstyle="round", zorder=2)

    for v in LOI.values():
        ax.add_patch(Polygon(_khung(v), closed=True, facecolor=MAU["loi"],
                             edgecolor=MAU["vien_loi"], lw=1.6, ls=(0, (5, 2)),
                             zorder=4))
    ax.annotate("Sảnh nối + khối phụ trợ\n(mái bằng, thấp)", xy=tam["phu"],
                xytext=(tam["phu"][0] + 21, tam["phu"][1] + 19),
                ha="center", va="center", fontsize=9.5, color=MAU["vien_loi"],
                zorder=6,
                arrowprops=dict(arrowstyle="-", lw=0.8, color=MAU["vien_loi"]))

    for k, v in KHOI.items():
        tv = v["thu_vien"]
        vien = MAU["vien_thu_vien"] if tv else MAU["vien_khac"]
        ax.add_patch(Polygon(_khung(v), closed=True,
                             facecolor=MAU["thu_vien"] if tv else MAU["khac"],
                             edgecolor=vien, lw=2.4 if tv else 1.6, zorder=4))
        _ve_mai_chop(ax, v, vien)
        x, y = tam[k]
        ax.text(x, y + 2.6, v["ten"], ha="center", va="center", fontsize=11.5,
                fontweight="bold" if tv else "normal", color=MAU["chu"], zorder=6)
        ax.text(x, y - 2.0,
                f"≈ {v['canh'][0] / TY_LE_PX_MOI_MET:.0f} × "
                f"{v['canh'][1] / TY_LE_PX_MOI_MET:.0f} m",
                ha="center", va="center", fontsize=9.5, color="#5A6A78", zorder=6)
        ax.text(x, y - 6.0, f"mái xoay {v['goc']:.0f}°", ha="center", va="center",
                fontsize=8.5, color=vien, zorder=6)

    for a, b, ho, phia in KHE_HO:
        p, q = np.array(tam[a]), np.array(tam[b])
        ax.plot(*zip(p, q), color=MAU["vien_khac"], lw=2.2, ls=(0, (6, 4)),
                zorder=3)
        # Đẩy nhãn ra vuông góc với đường nối: đặt ngay trên đường thì nó rơi
        # vào chỗ hai khối gần nhau nhất và bị nét viền cắt ngang.
        n = np.array([-(q - p)[1], (q - p)[0]])
        ax.annotate(f"hở ≈ {ho:.1f} m", xy=(p + q) / 2,
                    xytext=(p + q) / 2 + n / np.linalg.norm(n) * 11.0 * phia,
                    ha="center", va="center", fontsize=9.5,
                    color=MAU["vien_khac"], zorder=6,
                    arrowprops=dict(arrowstyle="-", lw=0.8,
                                    color=MAU["vien_khac"]),
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec=MAU["vien_khac"], lw=0.6, alpha=0.95))

    _kim_chi_nam(ax)
    _thuoc(ax)

    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.margins(0.15)
    ax.axis("off")
    ax.set_title(
        "Sơ đồ khối Trung tâm Thông tin - Thư viện, Đại học Đà Lạt\n"
        f"nhìn từ trên cao · lưới nhà nghiêng {NGHIENG:.1f}° so với trục bắc-nam",
        fontsize=13.5, pad=16, color=MAU["chu"])
    ax.text(0.5, -0.03,
            "Nét liền đậm: ba khối mái của thư viện.  Nét đứt mảnh: sảnh nối và "
            "khối phụ trợ, mái bằng nên thấp hơn hẳn.\n"
            "Góc ghi dưới mỗi khối là góc mái đo trên ảnh: B-C-D theo lưới nhà, "
            f"A và E xoay thêm {LECH_CANH:.1f}° — thế chong chóng của cụm.\n"
            "Phác hoạ từ ảnh Google Maps; kích thước là đường bao mái, sai số ±2-3 m.",
            transform=ax.transAxes, ha="center", va="top", fontsize=9.5,
            color="#66707A")

    RA.mkdir(parents=True, exist_ok=True)
    ra = RA / "so_do_khoi_nha.png"
    fig.savefig(ra, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ra


def _kim_chi_nam(ax) -> None:
    """Mũi tên chỉ bắc THẬT, không phải chỉ lên đỉnh hình."""
    x0, y0 = 74, 76
    ax.add_patch(FancyArrow(x0, y0, 0, 11, width=0.9, head_width=3.6,
                            head_length=4.2, color=MAU["chu"], zorder=7))
    ax.text(x0, y0 + 17.5, "B", ha="center", va="center", fontsize=13,
            fontweight="bold", color=MAU["chu"], zorder=7)
    t = np.radians(NGHIENG)
    ax.add_patch(FancyArrow(x0, y0, -11 * np.sin(t), 11 * np.cos(t), width=0.5,
                            head_width=2.4, head_length=3.0,
                            color=MAU["vien_thu_vien"], alpha=0.75, zorder=7))
    ax.text(x0 - 15, y0 + 7, f"trục nhà\n{NGHIENG:.1f}°", ha="center", va="center",
            fontsize=8.5, color=MAU["vien_thu_vien"], zorder=7)


def _thuoc(ax, dai_m: float = 20.0) -> None:
    x0, y0 = -24, -26
    ax.plot([x0, x0 + dai_m], [y0, y0], color=MAU["chu"], lw=2.6, zorder=7)
    for x in (x0, x0 + dai_m):
        ax.plot([x, x], [y0 - 1.4, y0 + 1.4], color=MAU["chu"], lw=2.6, zorder=7)
    ax.text(x0 + dai_m / 2, y0 + 2.6, f"{dai_m:.0f} m", ha="center", va="bottom",
            fontsize=10, color=MAU["chu"], zorder=7)


def main() -> None:
    p = ve()
    print(f"{p.relative_to(config.ROOT_DIR)}  {p.stat().st_size / 1024:,.0f} KB")


if __name__ == "__main__":
    main()
