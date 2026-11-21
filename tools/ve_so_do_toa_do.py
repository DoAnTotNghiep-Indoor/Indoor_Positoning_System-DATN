"""Sơ đồ tầng 1 có trục toạ độ (mét), điểm tham chiếu và chỗ đo tại chỗ, để tra vị trí trong báo cáo.

    python -m tools.ve_so_do_toa_do

Ghi reports/figures/so_do_toa_do.png. Gốc toạ độ ở giữa cửa chính, x sang ngang, y vào trong nhà.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backend.services.routing_service import DoThiDiLai
from ml import config
from tools.mat_bang import doc_mat_bang, tam

PHIEU = config.ROOT_DIR / "data/raw/nhom15_2026/2026-11-18/phieu.csv"
XANH, CAM, CHU = "#2C5BD8", "#E08A2E", "#0D1A30"


def main():
    l = DoThiDiLai().luoi
    m = l.met_moi_don_vi
    (x0, y1), (x1, y0) = l.sang_don_vi(np.array([[0, 0], [l.o.shape[1], l.o.shape[0]]])) * m

    fig, ax = plt.subplots(figsize=(11, 9.2))
    ax.imshow(np.where(l.o, 1.0, 0.8), cmap="gray", vmin=0, vmax=1, extent=(x0, x1, y0, y1), zorder=0)
    ax.set_xticks(np.arange(-16, 17, 2)); ax.set_yticks(np.arange(-2, 29, 2))
    ax.set_xticks(np.arange(-16, 17, 1), minor=True); ax.set_yticks(np.arange(-2, 29, 1), minor=True)
    ax.grid(which="major", color="#9DB8EE", lw=0.7, alpha=0.8, zorder=1)
    ax.grid(which="minor", color="#9DB8EE", lw=0.3, alpha=0.4, zorder=1)
    ax.set_xlim(-16.5, 16.5); ax.set_ylim(-1.5, 28.7)
    ax.set_xlabel("x (m)", color=CHU); ax.set_ylabel("y (m)", color=CHU)
    ax.tick_params(colors=CHU, labelsize=9)

    for e in doc_mat_bang():
        x, y = e["tai"] if e.get("loai") == "nhan" else tam(e.get("diem") or [(999, 999)])
        if e.get("ten") and e["loai"] in ("nhan", "phong", "quay") and abs(x * m) < 15 and y * m < 28 and "icon" not in e:
            ax.text(x * m, y * m, e["ten"], ha="center", va="center",
                    fontsize=8.5, color="#5A6478", style="italic", zorder=2)

    ten = {i: k for k, i in l.chi_so.items()}
    for i in range(l.so_goc, len(l.xy)):
        x, y = l.xy[i] * m
        rp = int(ten[i][2:]) <= 40
        ax.scatter(x, y, s=46, c=CAM if rp else "white", edgecolors=CAM, lw=1.2, zorder=3)
        ax.annotate(ten[i][2:], (x, y), xytext=(0, 6), textcoords="offset points", ha="center",
                    fontsize=7.5, color=CHU, zorder=4)

    for _, r in pd.read_csv(PHIEU).iterrows():
        ax.scatter(r.x * m, r.y * m, s=70, marker="D", c=XANH, edgecolors="white", lw=0.8, zorder=5)
        trai = -15 < r.x * m < 0
        ax.annotate(r.ma, (r.x * m, r.y * m), xytext=(-7 if trai else 7, -10), textcoords="offset points",
                    ha="right" if trai else "left",
                    fontsize=8.5, color=XANH, fontweight="bold", zorder=6)

    ax.scatter([], [], s=46, c=CAM, label="Điểm tham chiếu (số là mã RP)")
    ax.scatter([], [], s=46, c="white", edgecolors=CAM, label="Điểm chức năng, không có vân tay")
    ax.scatter([], [], s=70, marker="D", c=XANH, label="Chỗ đo tại chỗ ngày 18/11/2026")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False, fontsize=9)
    ax.set_aspect("equal")
    fig.tight_layout()
    ra = config.REPORTS_DIR / "figures/so_do_toa_do.png"
    fig.savefig(ra, dpi=200)
    print(ra)


if __name__ == "__main__":
    main()
