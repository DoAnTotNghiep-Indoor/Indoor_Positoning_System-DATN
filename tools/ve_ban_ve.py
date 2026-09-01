"""Bản vẽ thiết kế tầng 1 và các hình đi kèm, xuất ra reports/figures/.

    pip install pillow scipy          # matplotlib đã có trong requirements.txt
    python -m tools.ve_ban_ve

Khác `trich_ban_do.ve_hinh` ở mục đích: hình kia để KIỂM CHỨNG phép dò tường nên
chồng thẳng lên ảnh gốc; bốn hình ở đây để ĐƯA VÀO BÁO CÁO nên vẽ lại nét trên
nền trắng, trục đánh số bằng mét, có thước tỉ lệ.

Toàn bộ hình học lấy từ `Map.png` và `reference_points.csv`, không viết cứng số
đo nào — sửa toạ độ là cả bốn hình đổi theo.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.transforms import Affine2D

from ml import config
from tools.trich_ban_do import ANH, BanDo, _tach_ba_lop

RA = config.REPORTS_DIR / "figures"

# Hai điểm cùng nhóm xa hơn ngưỡng này thì tách cụm, mỗi cụm một nhãn riêng.
#
# Đặt nhãn ở trọng tâm cả nhóm là sai: "Hành lang" có 2 điểm cách nhau 84 m ở
# hai đầu nhà nên trọng tâm rơi vào giữa sảnh, chỗ không có hành lang nào.
NGUONG_CUM_M = 15.0

MAU_VUNG = ["#4C78A8", "#F58518", "#54A24B", "#E45756"]


def _cum(diem: list[tuple[float, float]]) -> list[list[int]]:
    """Gom điểm thành cụm theo liên kết đơn, ngưỡng NGUONG_CUM_M."""
    cha = list(range(len(diem)))

    def goc(i: int) -> int:
        while cha[i] != i:
            cha[i] = cha[cha[i]]
            i = cha[i]
        return i

    for i in range(len(diem)):
        for j in range(i + 1, len(diem)):
            if math.dist(diem[i], diem[j]) <= NGUONG_CUM_M:
                cha[goc(i)] = goc(j)

    gom: dict[int, list[int]] = {}
    for i in range(len(diem)):
        gom.setdefault(goc(i), []).append(i)
    return list(gom.values())


def _go_chong(fig, ax, nhan: list, buoc_px: float = 13.0) -> int:
    """Đẩy nhãn lên cho tới khi hết chồng nhau. Trả về số nhãn phải dịch.

    Đo bằng khung chữ THẬT lấy từ renderer chứ không ước lượng theo số ký tự:
    bề rộng nhãn phụ thuộc phông và cỡ chữ, đoán hụt vài pixel là hai nhãn vẫn
    dính nhau mà vòng lặp đã tưởng xong.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    hop = sorted(((t, t.get_window_extent(renderer=r)) for t in nhan),
                 key=lambda d: (d[1].y0, d[1].x0))

    da_dat, dich = [], 0
    for t, bb in hop:
        dy = 0.0
        while any(bb.translated(0, dy).overlaps(b) for b in da_dat):
            dy += buoc_px
            if dy > 300:
                break
        if dy:
            px, py = ax.transData.transform(t.get_position())
            t.set_position(ax.transData.inverted().transform((px, py + dy)))
            dich += 1
        da_dat.append(bb.translated(0, dy))
    return dich


class Ve:
    def __init__(self) -> None:
        self.bd = BanDo()
        self.net, self.vat_can, _ = _tach_ba_lop(ANH)
        h, w = self.net.shape
        self.khung = [self._mx(0), self._mx(w), self._my(h), self._my(0)]

        rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
        self.rp = rp.dropna(subset=["x", "y"]).reset_index(drop=True)

    def _mx(self, px: float) -> float:
        return (px - self.bd.luoi["x_min"]) / self.bd.px_moi_met_x + self.bd.goc_met_x

    def _my(self, py: float) -> float:
        return (self.bd.luoi["y_max"] - py) / self.bd.px_moi_met_y

    def _nen(self, ax: plt.Axes, vat_can: bool = True) -> None:
        """Nét tường đen, vật cản xám nhạt, nền trắng."""
        if vat_can:
            ax.imshow(
                np.ma.masked_where(~self.vat_can, self.vat_can),
                extent=self.khung, cmap="Greys", vmin=0, vmax=2.6,
                interpolation="nearest", zorder=1,
            )
        ax.imshow(
            np.ma.masked_where(~self.net, self.net),
            extent=self.khung, cmap="Greys", vmin=0, vmax=1.05,
            interpolation="nearest", zorder=2,
        )
        ax.set_facecolor("white")
        ax.set_xlabel("x (mét)")
        ax.set_ylabel("y (mét)")
        ax.set_aspect("equal")
        ax.grid(True, lw=0.4, color="#DDDDDD", zorder=0)
        ax.set_axisbelow(True)

        # Nới khung quanh toà nhà: đường kích thước và chú thích vẽ ở dải này,
        # để mặc định thì chúng tràn ra ngoài trục và bị cắt mất.
        ax.set_xlim(self.khung[0] - 2, self.khung[1] + 10)
        ax.set_ylim(self.khung[2] - 11, self.khung[3] + 8)

    def _thuoc(self, ax: plt.Axes, dai_m: float = 10.0) -> None:
        x0, y0 = self.khung[0] + 4, self.khung[2] + 4
        ax.plot([x0, x0 + dai_m], [y0, y0], lw=3, color="#111111",
                solid_capstyle="butt", zorder=6)
        ax.text(x0 + dai_m / 2, y0 + 1.2, f"{dai_m:.0f} m", ha="center",
                fontsize=9, zorder=6)


def hinh_mat_bang(v: Ve) -> Path:
    """Hình 1 — bản vẽ thiết kế tầng 1, kèm kích thước bao và gốc toạ độ."""
    fig, ax = plt.subplots(figsize=(13.6, 8.6), dpi=130)
    v._nen(ax)

    xs, ys = v.rp["x"], v.rp["y"]
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()

    # Đường kích thước: hộp bao 40 điểm đã đo chính là hệ quy chiếu của cả dự án
    for (ax0, ay0), (ax1, ay1), chu, doi in (
        ((x0, y1 + 3.4), (x1, y1 + 3.4), f"{x1 - x0:.0f} m", (0, 1.2)),
        ((x1 + 5.2, y0), (x1 + 5.2, y1), f"{y1 - y0:.0f} m", (1.8, 0)),
    ):
        ax.annotate("", (ax1, ay1), (ax0, ay0),
                    arrowprops=dict(arrowstyle="<->", lw=1.1, color="#B71C1C"))
        ax.text((ax0 + ax1) / 2 + doi[0], (ay0 + ay1) / 2 + doi[1], chu,
                color="#B71C1C", fontsize=11, fontweight="bold",
                ha="center", va="center",
                rotation=90 if doi[0] else 0)

    ax.plot([x0], [y0], marker="+", ms=16, mew=2, color="#0C447C", zorder=6)
    ax.annotate("gốc (x=-43, y=0)\ncạnh dưới ảnh, phía cửa ra vào",
                (x0, y0), (x0 + 7, y0 - 8), fontsize=9, color="#0C447C",
                arrowprops=dict(arrowstyle="->", color="#0C447C", lw=0.9))

    v._thuoc(ax)
    ax.set_title(
        "Bản vẽ thiết kế tầng 1 — Trung tâm Thông tin – Thư viện, Đại học Đà Lạt\n"
        f"nét đen: tường  ·  xám: kệ sách và vật cản  ·  "
        f"tỉ lệ {v.bd.px_moi_met_x:.2f} px/m",
        fontsize=12.5, pad=14)
    ra = RA / "ban_ve_tang1.png"
    fig.tight_layout()
    fig.savefig(ra, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return ra


def hinh_khu_vuc(v: Ve) -> Path:
    """Hình 2 — 40 điểm khảo sát, nhãn đặt theo CỤM chứ không theo trọng tâm."""
    fig, ax = plt.subplots(figsize=(13.6, 8.6), dpi=130)
    v._nen(ax)

    mau = dict(zip(sorted(v.rp["nhom"].unique()), plt.cm.tab20.colors))
    nhan: list = []
    for nhom, g in v.rp.groupby("nhom"):
        diem = list(zip(g["x"], g["y"]))
        ax.scatter(g["x"], g["y"], s=46, color=mau[nhom], ec="white",
                   lw=1.1, zorder=5)
        for cum in _cum(diem):
            cx = sum(diem[i][0] for i in cum) / len(cum)
            cy = sum(diem[i][1] for i in cum) / len(cum)
            nhan.append(ax.text(
                cx, cy + 2.6, f"{nhom} · {len(cum)}", ha="center",
                    va="bottom", fontsize=8.2, fontweight="bold", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.28", fc="white",
                          ec=mau[nhom], lw=1.1, alpha=0.95)))

    so_nhan = len(nhan)
    da_dich = _go_chong(fig, ax, nhan)
    v._thuoc(ax)
    ax.set_title(
        f"40 điểm khảo sát theo khu vực — {v.rp['nhom'].nunique()} nhóm, "
        f"{so_nhan} nhãn đặt theo cụm\n"
        f"tách cụm khi hai điểm cùng nhóm cách nhau quá {NGUONG_CUM_M:.0f} m"
        f"  ·  {da_dich} nhãn đã đẩy lên cho khỏi chồng",
        fontsize=12.5, pad=14)
    ra = RA / "ban_ve_khu_vuc.png"
    fig.tight_layout()
    fig.savefig(ra, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return ra


def hinh_vung_di_lai(v: Ve) -> Path:
    """Hình 3 — các mảng sàn liên thông. Căn cứ cho phép lọc cạnh xuyên tường."""
    fig, ax = plt.subplots(figsize=(13.6, 8.6), dpi=130)
    v._nen(ax, vat_can=False)

    dt_px = v.bd.px_moi_met_x * v.bd.px_moi_met_y
    chu = []
    for k, i in enumerate(sorted(np.unique(v.bd.vung))[1:]):
        mask = v.bd.vung == i
        ax.imshow(np.ma.masked_where(~mask, mask), extent=v.khung,
                  cmap=matplotlib.colors.ListedColormap([MAU_VUNG[k % 4]]),
                  alpha=0.34, interpolation="nearest", zorder=1)
        ys, xs = np.where(mask)
        ax.text(v._mx(xs.mean()), v._my(ys.mean()), f"Vùng {k + 1}",
                ha="center", fontsize=13, fontweight="bold",
                color=MAU_VUNG[k % 4], zorder=7,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85))
        chu.append(f"Vùng {k + 1}: {mask.sum() / dt_px:,.0f} m²")

    ax.scatter(v.rp["x"], v.rp["y"], s=26, color="#111111", zorder=6)
    v._thuoc(ax)
    ax.set_title(
        "Các mảng sàn liên thông tách được từ nét tường — " + "  ·  ".join(chu) +
        "\ntầng 1 là không gian mở: không có đa giác từng phòng để lấy",
        fontsize=12.5, pad=14)
    ra = RA / "ban_ve_vung_di_lai.png"
    fig.tight_layout()
    fig.savefig(ra, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return ra


def hinh_tuyen(v: Ve, tu: str = "RP01", den: str = "RP39") -> Path:
    """Hình 4 — một tuyến mẫu trên đồ thị đã lọc tường, ghi số mét từng chặng."""
    from backend.services.routing_service import DoThiDiLai

    g = DoThiDiLai()
    duong, tong = g.tim_duong(tu, den)

    fig, ax = plt.subplots(figsize=(13.6, 8.6), dpi=130)
    v._nen(ax)

    for (a, b) in g.canh:
        (xa, ya), (xb, yb) = g.toa_do[a], g.toa_do[b]
        ax.plot([xa, xb], [ya, yb], lw=0.9, color="#B9C6D6", zorder=3)

    px = [g.toa_do[k][0] for k in duong]
    py = [g.toa_do[k][1] for k in duong]
    ax.plot(px, py, lw=3.4, color="#0C447C", zorder=6, solid_capstyle="round")
    ax.scatter(px, py, s=34, color="#0C447C", ec="white", lw=1.1, zorder=7)

    for a, b in zip(duong, duong[1:]):
        (xa, ya), (xb, yb) = g.toa_do[a], g.toa_do[b]
        ax.text((xa + xb) / 2, (ya + yb) / 2, f"{math.dist((xa, ya), (xb, yb)):.1f}",
                fontsize=7.6, ha="center", va="center", zorder=8,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none",
                          alpha=0.9))

    for k, m in ((duong[0], "xuất phát"), (duong[-1], "đích")):
        x, y = g.toa_do[k]
        ax.scatter([x], [y], s=190, marker="o", zorder=8,
                   color="#17A673" if m == "đích" else "#E8590C",
                   ec="white", lw=2)
        ax.text(x, y - 3.4, m, ha="center", va="top", fontsize=9.5,
                fontweight="bold", zorder=8)

    ax.legend(handles=[
        Line2D([], [], color="#B9C6D6", lw=1.4, label=f"{len(g.canh)} cạnh đi được"),
        Line2D([], [], color="#0C447C", lw=3, label=f"tuyến {tu} → {den}"),
    ], loc="lower center", ncol=2, fontsize=9.5, framealpha=0.95)
    v._thuoc(ax)
    ax.set_title(
        f"Tuyến mẫu trên đồ thị đã lọc tường — {tu} → {den}: "
        f"{tong:.1f} m qua {len(duong) - 1} chặng\n"
        "số trên mỗi chặng là mét thật, đo trong hệ toạ độ khảo sát",
        fontsize=12.5, pad=14)
    ra = RA / "ban_ve_tuyen_mau.png"
    fig.tight_layout()
    fig.savefig(ra, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return ra



# Bảng màu đo từ Hình 21–24 của báo cáo CTK45.
MAU_CTK45 = {
    "nen": "#EDEAE2",
    "san": "#C9C9C9",
    "vien": "#A8A8A8",
    "cham": "#E53935",
    "vien_cham": "#B71C1C",
    "nguoi": "#2196F3",
    "quat": "#3B9BE0",
    "the": "#FDFBF0",
}

# Góc nghiêng toà nhà trên bản đồ Mapbox của họ, đo từ ảnh chụp trong báo cáo.
GOC_NGHIENG = -22.0


def hinh_kieu_ctk45(v: Ve) -> Path:
    """Hình 5 — dựng lại Hình 21 của báo cáo CTK45 trên hình học đo thực địa.

    Ba đặc điểm định danh bản đồ của họ đều tái hiện được: toà nhà nghiêng 22°,
    chấm đỏ cho từng điểm, và MỖI ĐIỂM MỘT NHÃN MANG TÊN NHÓM — nên "Cầu thang"
    in ra 12 lần, "Khu vực tự học" 10 lần. Nhãn ở đây KHÔNG gỡ chồng, vì chính
    chỗ chồng nhau mới là thứ cần thấy.

    Không dựng được: đa giác WC và bốn hành lang có nhãn `Hallway1–4`. Chúng chỉ
    tồn tại trong GeoJSON vẽ tay của họ, mà bộ ấy lệch hình học (mục 2.5.1 tài
    liệu thiết kế) nên không đặt vào hệ mét này được.
    """
    xoay = Affine2D().rotate_deg(GOC_NGHIENG)
    q = np.array([xoay.transform((x, y)) for x, y in zip(v.rp["x"], v.rp["y"])])

    fig, ax = plt.subplots(figsize=(9.2, 11.4), dpi=130)
    # `axis("off")` ẩn luôn nền của trục, nên phải tự phủ một lớp: bản đồ của
    # họ có nền be chứ không phải nền trắng, để trắng thì toà nhà mất khung.
    fig.patch.set_facecolor(MAU_CTK45["nen"])
    ax.set_facecolor(MAU_CTK45["nen"])

    tr = xoay + ax.transData
    # Xám vừa chứ không đen: bản đồ Mapbox của họ tô đa giác xám đều, kệ sách
    # không nổi thành khối đen. Vẽ đậm hơn là sai với thứ đang dựng lại.
    ax.imshow(np.ma.masked_where(~(v.net | v.vat_can), np.ones_like(v.net)),
              extent=v.khung, transform=tr, cmap="Greys", vmin=0, vmax=3.1,
              interpolation="nearest", zorder=3)
    ax.imshow(np.ma.masked_where(v.bd.vung == 0, v.bd.vung), extent=v.khung,
              transform=tr, cmap=matplotlib.colors.ListedColormap(
                  [MAU_CTK45["san"]] * 4),
              interpolation="nearest", zorder=2)

    ax.scatter(q[:, 0], q[:, 1], s=54, color=MAU_CTK45["cham"],
               ec=MAU_CTK45["vien_cham"], lw=1, zorder=6)
    for (x, y), nhom in zip(q, v.rp["nhom"]):
        ax.text(x, y + 1.9, nhom, ha="center", va="bottom", fontsize=7.2,
                color="#1A1A1A", zorder=7,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="#BDBDBD",
                          lw=0.5, alpha=0.88))

    # Người dùng: quạt hướng + ghim + nhãn "User", đúng bộ ba trong Hình 21
    ux, uy = xoay.transform((0.0, 18.0))
    ax.scatter([ux], [uy], s=210, marker="o", color=MAU_CTK45["nguoi"],
               ec="white", lw=2.2, zorder=8)
    ax.add_patch(plt.matplotlib.patches.Wedge(
        (ux, uy), 9.5, 52, 128, color=MAU_CTK45["quat"], alpha=0.75, zorder=7))
    ax.text(ux, uy + 11.5, "User", ha="center", va="bottom", fontsize=11,
            fontweight="bold", zorder=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none"))

    ax.set_aspect("equal")
    ax.axis("off")
    xs, ys = q[:, 0], q[:, 1]
    ax.set_xlim(xs.min() - 14, xs.max() + 14)
    ax.set_ylim(ys.min() - 16, ys.max() + 18)

    # Thẻ quãng đường ghim góc trái trên, đúng chỗ và đúng kiểu của Hình 23
    ax.text(0.03, 0.972, "Tổng khoảng cách: 18.43 mét", transform=ax.transAxes,
            fontsize=12, va="top", zorder=10,
            bbox=dict(boxstyle="round,pad=0.45", fc=MAU_CTK45["the"],
                      ec="#D8D2BE"))

    ax.set_title(
        "Dựng lại Hình 21 của báo cáo CTK45 trên hình học đo thực địa\n"
        f"nghiêng {abs(GOC_NGHIENG):.0f}°, {len(v.rp)} chấm đỏ, "
        f"{len(v.rp)} nhãn mang tên nhóm — không gỡ chồng",
        fontsize=12.5, pad=12)
    ra = RA / "ban_ve_kieu_ctk45.png"
    fig.tight_layout()
    fig.savefig(ra, facecolor=MAU_CTK45["nen"], bbox_inches="tight")
    plt.close(fig)
    return ra


def main() -> None:
    RA.mkdir(parents=True, exist_ok=True)
    v = Ve()
    for f in (hinh_mat_bang, hinh_khu_vuc, hinh_vung_di_lai, hinh_tuyen,
              hinh_kieu_ctk45):
        p = f(v)
        print(f"{p.relative_to(config.ROOT_DIR)}  {p.stat().st_size / 1024:,.0f} KB")


if __name__ == "__main__":
    main()
