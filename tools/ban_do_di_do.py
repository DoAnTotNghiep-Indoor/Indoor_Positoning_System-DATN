"""Bản đồ đi đo thực địa: điểm cần đo, thứ tự đi, và điểm đã đo xong.

    python -m tools.ban_do_di_do

Đọc `data/reference/diem_can_do.csv` (danh sách và thứ tự đi) rồi soi
`data/raw/nhom15_2026/` xem điểm nào đã có tệp — điểm ấy tự chuyển sang dấu tích.
Không có ô đánh dấu tay: chạy `tools.thu_van_tay` xong là bản đồ tự cập nhật,
nên không bao giờ lệch giữa "đã tích" và "đã có dữ liệu thật".

Chạy lại sau mỗi vài điểm để biết còn phải đi đâu.
"""

from __future__ import annotations

import math

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ml import config  # noqa: E402
from tools.ve_ban_ve import RA, Ve  # noqa: E402

DANH_SACH = config.REFERENCE_DIR / "diem_can_do.csv"
THU_MOI = config.RAW_DIR / "nhom15_2026"

# Số lần quét mỗi điểm và giãn cách, khớp `tools.thu_van_tay` — dùng để ước
# lượng thời gian còn lại.
SO_LAN, GIAY = 20, 45


def da_do() -> dict[str, int]:
    """Điểm nào đã có tệp, và trong đó bao nhiêu lần quét."""
    if not THU_MOI.is_dir():
        return {}
    xong = {}
    # rglob: mỗi buổi một thư mục con theo ngày, điểm đã đo nằm rải khắp chúng.
    for tep in THU_MOI.rglob("RP*.csv"):
        try:
            d = pd.read_csv(tep)
            xong[tep.stem] = int(d["WiFi fingerprint serial number"].nunique())
        except (OSError, KeyError, ValueError):
            xong[tep.stem] = 0
    return xong


def ve() -> "config.Path":
    can = pd.read_csv(DANH_SACH).sort_values("thu_tu").reset_index(drop=True)
    xong = da_do()
    can["xong"] = can.rp_id.map(lambda k: xong.get(k, 0))

    v = Ve()
    fig, ax = plt.subplots(figsize=(13.6, 8.6), dpi=130)
    v._nen(ax)

    ax.scatter(v.rp["x"], v.rp["y"], s=44, color="#B4BCC4", ec="white", lw=0.8,
               zorder=4, label=f"{len(v.rp)} điểm đã có dữ liệu")

    # Đường đi nối theo thứ tự, vẽ mờ dưới các chấm để không che số.
    ax.plot(can.x, can.y, color="#4C78A8", lw=1.4, alpha=0.45, ls=(0, (5, 3)),
            zorder=3, label=f"thứ tự đi ({_quang_duong(can):.0f} m)")

    r = can[can.xong == 0]
    x_ = can[can.xong > 0]
    ax.scatter(r.x, r.y, s=150, color="#D64545", marker="o", ec="white", lw=1.4,
               zorder=6, label=f"{len(r)} điểm CÒN PHẢI ĐO")
    if len(x_):
        ax.scatter(x_.x, x_.y, s=170, color="#2E9E5B", marker="o", ec="white",
                   lw=1.4, zorder=6, label=f"{len(x_)} điểm ĐÃ ĐO XONG")

    for h in can.itertuples():
        ax.annotate("✓" if h.xong else str(h.thu_tu), (h.x, h.y),
                    ha="center", va="center", fontsize=8.5, color="white",
                    fontweight="bold", zorder=7)
        ax.annotate(h.rp_id[2:], (h.x, h.y), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=6.5, zorder=7,
                    color="#2E9E5B" if h.xong else "#8A1C1C", fontweight="bold")

    v._thuoc(ax)
    ax.legend(loc="upper right", fontsize=9.5, framealpha=0.95)
    con = len(r) * SO_LAN * GIAY / 3600
    ax.set_title(
        f"Bản đồ đi đo — {len(x_)}/{len(can)} điểm xong, còn {len(r)} điểm "
        f"(≈ {con:.1f} giờ đứng đo)\n"
        "số trong chấm đỏ là thứ tự đi · số nhỏ phía trên là mã RP",
        fontsize=12.5, pad=14)

    fig.tight_layout()
    ra = RA / "ban_do_di_do.png"
    fig.savefig(ra, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return ra


def _quang_duong(can: pd.DataFrame) -> float:
    return sum(math.dist((can.x[i], can.y[i]), (can.x[i + 1], can.y[i + 1]))
               for i in range(len(can) - 1))


def main() -> None:
    can = pd.read_csv(DANH_SACH).sort_values("thu_tu")
    xong = da_do()

    print(f"{'':>3} {'mã':<6}{'x':>7}{'y':>7}   trạng thái")
    for h in can.itertuples():
        n = xong.get(h.rp_id, 0)
        dau = f"✓ đã đo ({n} lần quét)" if n else "· chưa đo"
        print(f"{h.thu_tu:>3} {h.rp_id:<6}{h.x:>7.1f}{h.y:>7.1f}   {dau}")

    r = len(can) - sum(1 for h in can.itertuples() if xong.get(h.rp_id))
    print(f"\nXong {len(can) - r}/{len(can)} · còn {r} điểm "
          f"≈ {r * SO_LAN * GIAY / 3600:.1f} giờ đứng đo")
    p = ve()
    print(f"{p.relative_to(config.ROOT_DIR)}")


if __name__ == "__main__":
    main()
