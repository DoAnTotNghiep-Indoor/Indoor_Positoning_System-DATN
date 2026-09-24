"""So sánh các thuật toán tìm đường trên đúng đồ thị đi lại mà máy chủ dùng.

    python -m tools.so_sanh_tim_duong

Đồ thị là `LuoiDiLai` của `backend/services/routing_service.py`: nút là góc lồi
vật cản cộng điểm tham chiếu, cạnh nối hai nút nhìn thấy nhau, trọng số là mét.
Truy vấn là mọi cặp điểm tham chiếu (có hướng). Mọi thuật toán viết lại bằng
Python thuần trên cùng danh sách kề để so công bằng — không lấy bản C của scipy
cho một thuật toán này mà bản Python cho thuật toán kia.

Chỉ số: quãng đường so với đường ngắn nhất (Dijkstra làm mốc), số nút đã mở,
thời gian mỗi truy vấn, và thời gian tiền xử lý với thuật toán tính trước mọi cặp.
"""

from __future__ import annotations

import heapq
import json
import math
import time
from collections import deque

import numpy as np
import pandas as pd

from backend.services.routing_service import BAN_DO_JSON, LuoiDiLai
from ml import config

RA = config.REPORTS_DIR / "tables" / "so_sanh_tim_duong.csv"
SO_LAN_LAP = 3


def _duong(truoc: dict, dich: int) -> list[int]:
    nut = [dich]
    while nut[-1] in truoc:
        nut.append(truoc[nut[-1]])
    return nut[::-1]


def dijkstra(ke, nguon, dich, h=None):
    g, truoc, xong, hang = {nguon: 0.0}, {}, set(), [(0.0, nguon)]
    while hang:
        _, u = heapq.heappop(hang)
        if u in xong:
            continue
        xong.add(u)
        if u == dich:
            return g[u], _duong(truoc, dich), len(xong)
        for v, w in ke[u]:
            moi = g[u] + w
            if moi < g.get(v, math.inf):
                g[v], truoc[v] = moi, u
                heapq.heappush(hang, (moi + (h[v] if h is not None else 0.0), v))
    return math.inf, [], len(xong)


def a_sao(ke, nguon, dich, xy):
    return dijkstra(ke, nguon, dich, h=np.hypot(*(xy - xy[dich]).T))


def tham_lam(ke, nguon, dich, xy):
    """Greedy best-first: chỉ nhìn khoảng cách thẳng còn lại, không nhìn quãng đã đi."""
    h = np.hypot(*(xy - xy[dich]).T)
    truoc, xong, hang = {}, {nguon}, [(h[nguon], nguon)]
    mo = 0
    while hang:
        _, u = heapq.heappop(hang)
        mo += 1
        if u == dich:
            duong = _duong(truoc, dich)
            return sum(_w(ke, a, b) for a, b in zip(duong, duong[1:])), duong, mo
        for v, _ in ke[u]:
            if v not in xong:
                xong.add(v)
                truoc[v] = u
                heapq.heappush(hang, (h[v], v))
    return math.inf, [], mo


def bfs(ke, nguon, dich):
    """Ít cạnh nhất, bỏ qua độ dài cạnh."""
    truoc, thay, hang = {}, {nguon}, deque([nguon])
    mo = 0
    while hang:
        u = hang.popleft()
        mo += 1
        if u == dich:
            duong = _duong(truoc, dich)
            return sum(_w(ke, a, b) for a, b in zip(duong, duong[1:])), duong, mo
        for v, _ in ke[u]:
            if v not in thay:
                thay.add(v)
                truoc[v] = u
                hang.append(v)
    return math.inf, [], mo


def bellman_ford(ke, nguon, dich):
    n = len(ke)
    g = [math.inf] * n
    g[nguon] = 0.0
    truoc = {}
    luot = 0
    for _ in range(n - 1):
        luot += 1
        doi = False
        for u in range(n):
            if g[u] == math.inf:
                continue
            for v, w in ke[u]:
                if g[u] + w < g[v]:
                    g[v], truoc[v], doi = g[u] + w, u, True
        if not doi:
            break
    return g[dich], _duong(truoc, dich), luot * n


def floyd_warshall(ke):
    n = len(ke)
    D = np.full((n, n), np.inf)
    ke_tiep = np.full((n, n), -1, dtype=int)
    np.fill_diagonal(D, 0.0)
    for u in range(n):
        ke_tiep[u, u] = u
        for v, w in ke[u]:
            D[u, v] = w
            ke_tiep[u, v] = v
    # Vòng k viết bằng numpy theo hàng: Floyd thuần Python ở ~700 nút mất cỡ
    # 3,4·10^8 phép so sánh, không chạy nổi trong thời gian hợp lý.
    for k in range(n):
        moi = D[:, k:k + 1] + D[k:k + 1, :]
        tot_hon = moi < D
        D = np.where(tot_hon, moi, D)
        ke_tiep = np.where(tot_hon, ke_tiep[:, k:k + 1], ke_tiep)
    return D, ke_tiep


def truy_floyd(D, ke_tiep, nguon, dich):
    if ke_tiep[nguon, dich] < 0:
        return math.inf, [], 0
    duong = [nguon]
    while duong[-1] != dich:
        duong.append(int(ke_tiep[duong[-1], dich]))
    return float(D[nguon, dich]), duong, len(duong)


def _w(ke, a, b):
    return next(w for v, w in ke[a] if v == b)


def run() -> pd.DataFrame:
    luoi = LuoiDiLai(json.loads(BAN_DO_JSON.read_text(encoding="utf-8")))
    ke, xy = luoi.ke, luoi.xy * luoi.met_moi_don_vi
    so_canh = sum(len(k) for k in ke) // 2
    rp = [luoi.chi_so[k] for k in luoi.rp]
    cap = [(a, b) for a in rp for b in rp if a != b]
    print(f"Đồ thị: {len(ke)} nút ({luoi.so_goc} góc vật cản + {len(rp)} điểm tham chiếu), "
          f"{so_canh} cạnh · {len(cap)} truy vấn")

    moc = {c: dijkstra(ke, *c)[0] for c in cap}

    t = time.perf_counter()
    D, ke_tiep = floyd_warshall(ke)
    tien_xu_ly_floyd = (time.perf_counter() - t) * 1000

    cach = {
        "Dijkstra": lambda a, b: dijkstra(ke, a, b),
        "A* (Euclid)": lambda a, b: a_sao(ke, a, b, xy),
        "Bellman-Ford": lambda a, b: bellman_ford(ke, a, b),
        "Floyd-Warshall (tra bảng)": lambda a, b: truy_floyd(D, ke_tiep, a, b),
        "BFS (ít cạnh nhất)": lambda a, b: bfs(ke, a, b),
        "Tham lam (Greedy best-first)": lambda a, b: tham_lam(ke, a, b, xy),
    }
    dong = []
    for ten, f in cach.items():
        tot = math.inf
        for _ in range(SO_LAN_LAP):
            t = time.perf_counter()
            kq = [f(a, b) for a, b in cap]
            tot = min(tot, time.perf_counter() - t)
        dai = np.array([k[0] for k in kq])
        chuan = np.array([moc[c] for c in cap])
        lech = dai / chuan - 1
        dong.append({
            "thuat_toan": ten,
            "toi_uu": bool(np.all(lech < 1e-9)),
            "ti_le_truy_van_toi_uu": float((lech < 1e-9).mean()),
            "dai_hon_trung_binh_pt": float(lech.mean() * 100),
            "dai_hon_lon_nhat_pt": float(lech.max() * 100),
            "nut_mo_trung_binh": float(np.mean([k[2] for k in kq])),
            "ms_moi_truy_van": tot / len(cap) * 1000,
            "tien_xu_ly_ms": tien_xu_ly_floyd if ten.startswith("Floyd") else 0.0,
        })
    bang = pd.DataFrame(dong)
    config.ghi_csv(bang, RA, index=False)
    print(bang.to_string(index=False, float_format=lambda v: f"{v:9.3f}"))
    return bang


if __name__ == "__main__":
    run()
