"""Hình và bảng minh hoạ chỉ đường cho báo cáo: các bước dựng đồ thị và một lần chạy A* có ghi từng bước.

    python -m tools.minh_hoa_chi_duong [TU] [DEN]      # mặc định RP02 (cửa chính) tới RP39 (phòng tạp chí)

Ghi reports/figures/chi_duong_dung_do_thi.png, reports/figures/chi_duong_a_sao.png,
reports/tables/chi_duong_a_sao_buoc.csv và reports/tables/chi_duong_chi_dan.csv.
"""
from __future__ import annotations

import heapq
import math
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backend.services.routing_service import DoThiDiLai
from ml import config

HINH = config.REPORTS_DIR / "figures"
BANG = config.REPORTS_DIR / "tables"
XANH, CAM, XAM = "#2C5BD8", "#E08A2E", "#C9D1DE"


def a_sao_ghi_buoc(l, tu: str, den: str):
    """Như LuoiDiLai.tim (xuất phát và đích đều là điểm tham chiếu), nhưng ghi thứ tự mở đỉnh."""
    s, t = l.chi_so[tu], l.chi_so[den]
    h = np.hypot(*(l.xy - l.xy[t]).T) * l.met_moi_don_vi
    g, truoc, mo, hang, xong = {s: 0.0}, {}, [], [(h[s], 0.0, s)], set()
    while hang:
        f, _, u = heapq.heappop(hang)
        if u in xong:
            continue
        xong.add(u)
        mo.append((u, g[u], h[u], g[u] + h[u]))
        if u == t:
            break
        for v, w in l.ke[u]:
            if g[u] + w < g.get(v, math.inf) - 1e-12:
                g[v], truoc[v] = g[u] + w, u
                heapq.heappush(hang, (g[v] + h[v], -g[v], v))
    tuyen = [t]
    while tuyen[-1] != s:
        tuyen.append(truoc[tuyen[-1]])
    return mo, tuyen[::-1], g[t]


def ten_nut(l, i, ten_rp):
    return ten_rp.get(i, f"góc {i}")


def ve_nen(ax, l):
    x0, x1 = l.sang_don_vi(np.array([[0, 0]]))[0][0], l.sang_don_vi(np.array([[l.o.shape[1], 0]]))[0][0]
    y1, y0 = l.sang_don_vi(np.array([[0, 0]]))[0][1], l.sang_don_vi(np.array([[0, l.o.shape[0]]]))[0][1]
    ax.imshow(np.where(l.o, 1.0, 0.82), cmap="gray", vmin=0, vmax=1, extent=(x0, x1, y0, y1))
    ax.set_xlim(-47, 47); ax.set_ylim(-4, 76)
    ax.set_xticks([]); ax.set_yticks([])


def main():
    tu, den = (sys.argv[1:3] if len(sys.argv) >= 3 else ("RP02", "RP39"))
    d = DoThiDiLai()
    l = d.luoi
    ten_rp = {v: k for k, v in l.chi_so.items()}
    m = l.met_moi_don_vi

    # Hình 1: ba bước dựng đồ thị.
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.2))
    for ax, tieu_de in zip(axs, ["(a) Vùng đi được từ mặt bằng", "(b) Góc lồi của vật cản và điểm tham chiếu",
                                 "(c) Nối các cặp nhìn thấy nhau"]):
        ve_nen(ax, l)
        ax.set_title(tieu_de, fontsize=12)
    for ax in axs[1:]:
        ax.scatter(*l.xy[:l.so_goc].T, s=6, c=XANH)
        ax.scatter(*l.xy[l.so_goc:].T, s=14, c=CAM)
    for i, ke in enumerate(l.ke):
        for j, _ in ke:
            if j > i:
                axs[2].plot(*l.xy[[i, j]].T, c=XANH, lw=0.25, alpha=0.35)
    fig.tight_layout()
    fig.savefig(HINH / "chi_duong_dung_do_thi.png", dpi=160)
    plt.close(fig)

    # Hình 2: A* từ TU tới DEN.
    mo, tuyen, dai = a_sao_ghi_buoc(l, tu, den)
    fig, ax = plt.subplots(figsize=(8, 6.6))
    ve_nen(ax, l)
    for i, ke in enumerate(l.ke):
        for j, _ in ke:
            if j > i:
                ax.plot(*l.xy[[i, j]].T, c=XAM, lw=0.15, alpha=0.3)
    da_mo = [u for u, *_ in mo]
    ax.scatter(*l.xy[da_mo].T, s=28, c=XANH, zorder=3)
    for k, u in enumerate(da_mo, 1):
        ax.annotate(str(k), l.xy[u], xytext=(-9 if k % 2 else 5, 0), textcoords="offset points", fontsize=8,
                    ha="center", va="center", color=XANH, weight="bold", zorder=4)
    ax.plot(*l.xy[tuyen].T, c=XANH, lw=3, zorder=2)
    for k, c, nhan in [(tu, "black", "xuất phát"), (den, CAM, "đích")]:
        x, y = l.xy[l.chi_so[k]]
        ax.scatter([x], [y], s=120, c=c, zorder=5)
        ax.annotate(f"{k} ({nhan})", (x, y), xytext=(6, -12), textcoords="offset points", fontsize=10,
                    weight="bold", zorder=5)
    ax.set_title(f"A* từ {tu} tới {den}: mở {len(mo)} đỉnh, đường dài {dai:.1f} m".replace(".", ","), fontsize=12)
    fig.tight_layout()
    fig.savefig(HINH / "chi_duong_a_sao.png", dpi=160)
    plt.close(fig)

    bang = pd.DataFrame([{"buoc": k, "dinh": ten_nut(l, u, ten_rp), "x": round(l.xy[u][0], 1),
                          "y": round(l.xy[u][1], 1), "g_m": round(gu, 2), "h_m": round(hu, 2), "f_m": round(fu, 2),
                          "tren_tuyen": u in tuyen} for k, (u, gu, hu, fu) in enumerate(mo, 1)])
    bang.to_csv(BANG / "chi_duong_a_sao_buoc.csv", index=False, encoding="utf-8")

    # Dijkstra trên cùng truy vấn để so số đỉnh mở.
    _, _, _, mo_dij = l.tim(*d.toa_do[tu], {den}, thuat_toan="dijkstra")

    kq = d.chi_duong(*d.toa_do[tu], {den})
    cd = pd.DataFrame(kq["chi_dan"])
    cd.to_csv(BANG / "chi_duong_chi_dan.csv", index=False, encoding="utf-8")
    print(bang.to_string(index=False))
    print(f"\nA*: {len(mo)} đỉnh mở, Dijkstra: {mo_dij}; quãng đường {kq['quang_duong_m']:.2f} m")
    print(cd.to_string(index=False))


if __name__ == "__main__":
    main()
