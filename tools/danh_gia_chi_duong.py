"""Sai số quãng đường chỉ đường so với đường ngắn nhất thật trên mặt bằng.

    pip install scipy
    python -m tools.danh_gia_chi_duong

Mốc đo độc lập với cách tìm đường đang đánh giá: Dijkstra trên lưới điểm ảnh nửa
độ phân giải của mặt nạ đi được, mỗi ô nối 80 hướng trong bán kính 5 ô, cộng
cạnh cửa giả định. Mốc không biết luật `chi_noi` nên lệch có chủ ý ở RP01, RP03. Rời rạc
hoá làm mốc dài hơn đường thật tối đa khoảng 0,5%, cộng nửa ô (6 cm).

Hai phép đo:

- `thuat_toan`: vị trí xuất phát ngẫu nhiên trong vùng đi được, tới mọi khu vực.
  Cả hai cách cùng đổi mét bằng một tỉ lệ, nên chỉ còn sai số của thuật toán.
- `dau_cuoi`: tập test của mô hình đang triển khai. Quãng đường ứng dụng hiển thị
  khi đứng ở vị trí DỰ ĐOÁN so với quãng đường thật từ vị trí THẬT — con số người
  dùng thực sự nhìn thấy. `cu_1m` là cách cũ đúng như ứng dụng từng hiển thị,
  coi mỗi đơn vị lưới là một mét.
"""

from __future__ import annotations

import json
import math

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

from backend.services.routing_service import DoThiDiLai
from ml import config, evaluate, postprocess

RA = config.REPORTS_DIR / "tables" / "routing_error.csv"
SO_VI_TRI_NGAU_NHIEN = 400
BAN_KINH_O = 5


class MocDo:
    def __init__(self, g: DoThiDiLai):
        l = g.luoi
        cao, rong = l.o.shape
        o = l.o[: cao // 2 * 2, : rong // 2 * 2].reshape(cao // 2, 2, rong // 2, 2).all(axis=(1, 3))
        self.o, self.l = o, l
        h, w = o.shape
        self.o_trong = np.argwhere(o)
        self.chi_so = -np.ones(o.shape, int)
        self.chi_so[o] = np.arange(len(self.o_trong))

        huong = [(dx, dy) for dx in range(-BAN_KINH_O, BAN_KINH_O + 1)
                 for dy in range(-BAN_KINH_O, BAN_KINH_O + 1)
                 if (dx or dy) and math.gcd(abs(dx), abs(dy)) == 1]
        hang, cot, trong_so = [], [], []
        f = self.o_trong
        for dx, dy in huong:
            n = max(abs(dx), abs(dy))
            ok = np.ones(len(f), bool)
            for s in range(1, 2 * n + 1):
                r = np.rint(f[:, 0] + dy * s / (2 * n)).astype(int)
                c = np.rint(f[:, 1] + dx * s / (2 * n)).astype(int)
                trong = (r >= 0) & (r < h) & (c >= 0) & (c < w)
                ok &= trong
                ok[trong] &= o[r[trong], c[trong]]
            nguon = np.nonzero(ok)[0]
            hang.append(nguon)
            cot.append(self.chi_so[f[nguon, 0] + dy, f[nguon, 1] + dx])
            trong_so.append(np.full(len(nguon), math.hypot(2 * dx / l._kx, 2 * dy / l._ky)))
        for a, b in g.cua_gia_dinh:
            pa, pb = l.xy[l.chi_so[a]], l.xy[l.chi_so[b]]
            i, j = self.o_gan(*pa), self.o_gan(*pb)
            w = math.hypot(*(pa - pb))
            hang += [np.array([i]), np.array([j])]
            cot += [np.array([j]), np.array([i])]
            trong_so += [np.array([w]), np.array([w])]
        self.G = coo_matrix((np.concatenate(trong_so), (np.concatenate(hang), np.concatenate(cot))),
                            shape=(len(f),) * 2).tocsr()
        self.met = l.met_moi_don_vi

    def o_gan(self, x: float, y: float) -> int:
        c, r = self.l.chieu_vao(x, y)
        r, c = r // 2, c // 2
        if self.chi_so[r, c] >= 0:
            return int(self.chi_so[r, c])
        return int((np.abs(self.o_trong[:, 0] - r) + np.abs(self.o_trong[:, 1] - c)).argmin())

    def truong(self, rp: set[str]) -> np.ndarray:
        """Quãng đường mét từ mọi ô tới điểm gần nhất trong [rp]."""
        nguon = [self.o_gan(*self.l.xy[self.l.chi_so[k]]) for k in rp]
        return dijkstra(self.G, indices=nguon, min_only=True) * self.met


def _nhom(g: DoThiDiLai) -> dict[str, set[str]]:
    ra: dict[str, set[str]] = {}
    for rp, n in g.nhan.items():
        if n["nhom"]:
            ra.setdefault(n["nhom"], set()).add(rp)
    return ra


def thuat_toan(g: DoThiDiLai, moc: MocDo, nhom: dict, truong: dict,
               so: int = SO_VI_TRI_NGAU_NHIEN, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    o = moc.l.o
    trong = np.argwhere(o)
    dong = []
    for r, c in trong[rng.choice(len(trong), so, replace=False)]:
        x, y = moc.l.sang_don_vi(np.array([c, r], float))[0]
        tu = g.gan_nhat(x, y)
        o_moc = moc.o_gan(x, y)
        for ten, rp in nhom.items():
            if tu in rp:
                continue
            a = g.chi_duong(x, y, rp, "a_sao")
            d = g.chi_duong(x, y, rp, "dijkstra")
            dong.append({"phep_do": "thuat_toan", "x": x, "y": y, "khu_vuc": ten,
                         "moc_m": truong[ten][o_moc],
                         "cu_m": g.tim_duong_toi_nhom(tu, ten)[1],
                         "moi_m": a["quang_duong_m"], "dijkstra_m": d["quang_duong_m"],
                         "mo_a_sao": a["so_nut_mo"], "mo_dijkstra": d["so_nut_mo"]})
    return pd.DataFrame(dong)


def dau_cuoi(g: DoThiDiLai, moc: MocDo, nhom: dict, truong: dict) -> pd.DataFrame:
    meta = json.loads((config.ARTIFACTS_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    ap = json.loads((config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON)
                    .read_text(encoding="utf-8"))["ap_columns"]
    te = pd.read_csv(config.SPLITS_DIR / "test.csv")
    p = joblib.load(config.ARTIFACTS_DIR / meta["file_active"]).predict(te[ap].to_numpy(float))
    y = te[["x", "y"]].to_numpy(float)

    vi_tri = [("mot_lan_quet", i, p[i]) for i in range(len(te))]
    for chuoi in evaluate.nhom_theo_thoi_gian(te):
        for k in range(len(chuoi)):
            cua_so = p[chuoi[max(0, k - postprocess.CUA_SO_MAC_DINH + 1): k + 1]]
            vi_tri.append(("cua_so_truot", chuoi[k], postprocess.dong_thuan_khong_gian(cua_so)))

    dong = []
    for kieu, i, (px, py) in vi_tri:
        rp_that = te["rp_id"].iloc[i]
        o_that = moc.o_gan(*y[i])
        tu = g.gan_nhat(px, py)
        for ten, rp in nhom.items():
            if rp_that in rp:
                continue
            cu = g.tim_duong_toi_nhom(tu, ten)[1]
            dong.append({"phep_do": kieu, "x": px, "y": py, "khu_vuc": ten,
                         "moc_m": truong[ten][o_that],
                         "cu_m": cu, "cu_1m": cu / g.met_moi_don_vi,
                         "moi_m": g.chi_duong(px, py, rp)["quang_duong_m"]})
    return pd.DataFrame(dong)


def tom_tat(df: pd.DataFrame) -> pd.DataFrame:
    ra = []
    for kieu, n in df.groupby("phep_do"):
        for cot in ("cu_1m", "cu_m", "moi_m", "dijkstra_m"):
            if cot not in n or n[cot].isna().all():
                continue
            e = (n[cot] - n["moc_m"]).abs()
            ra.append({"phep_do": kieu, "cach": cot, "so_cap": len(n),
                       "tb_m": e.mean(), "trung_vi_m": e.median(), "p90_m": e.quantile(0.9),
                       "max_m": e.max(), "tuong_doi_tb": (e / n["moc_m"]).mean(),
                       "ty_le_tren_1m": (e > 1).mean()})
    return pd.DataFrame(ra).round(4)


def main() -> None:
    g = DoThiDiLai()
    moc = MocDo(g)
    nhom = _nhom(g)
    truong = {ten: moc.truong(rp) for ten, rp in nhom.items()}

    df_tt = thuat_toan(g, moc, nhom, truong)
    df_dc = dau_cuoi(g, moc, nhom, truong)
    bang = tom_tat(pd.concat([df_tt, df_dc], ignore_index=True))
    RA.parent.mkdir(parents=True, exist_ok=True)
    bang.to_csv(RA, index=False)

    print(f"tỉ lệ {g.met_moi_don_vi} m/đơn vị lưới; mốc: {len(moc.o_trong)} ô, {moc.G.nnz} cạnh")
    print(bang.to_string(index=False))
    print(f"A* mở trung bình {df_tt['mo_a_sao'].mean():.1f} nút, Dijkstra "
          f"{df_tt['mo_dijkstra'].mean():.1f}; lệch quãng đường lớn nhất "
          f"{(df_tt['moi_m'] - df_tt['dijkstra_m']).abs().max():.2e} m")
    print(f"{RA.relative_to(config.ROOT_DIR)}")


if __name__ == "__main__":
    main()
