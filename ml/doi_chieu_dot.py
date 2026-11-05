"""Đối chiếu điểm đo giữa đợt A và đợt B.

    python -m ml.doi_chieu_dot

Kiểm mã điểm, toạ độ trong tệp CTK45 so với bảng điểm tham chiếu, vân tay trung bình cùng
mã có gần nhau hơn khác mã không, và mỗi đợt tự định vị từng điểm từ 39 điểm còn lại của
chính nó tới đâu. Cuối cùng chạy lại ba giao thức với ba toạ độ của tệp để đo độ nhạy.
Sinh reports/tables/doi_chieu_dot.csv.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from ml import config, evaluate
from ml.danh_gia_cheo import _tham_so, chuan_bi_lan_gap, nap_bang_rong
from ml.khac_dot import HAI_CHIEU, chuan_bi_chieu
from ml.models import fingerprint_knn_dong as k_dong
from ml.on_dinh import chia_lai

MET_MOI_DON_VI = 0.3508
SO_LAN_XAO = 20_000


def _van_tay(fp: pd.DataFrame, ap: list[str], dot: str) -> pd.DataFrame:
    d = fp[fp["dot"] == dot]
    return (d.set_index("rp_id")[ap].fillna(config.GIA_TRI_KHONG_BAT_CTK45) + 100) / 100


def _bray_curtis(P: np.ndarray, Q: np.ndarray) -> np.ndarray:
    return np.abs(P[:, None] - Q[None]).sum(2) / (P[:, None] + Q[None]).sum(2)


def _vi_tri_noi_bo(X: pd.DataFrame, toa_do: pd.DataFrame, beta: float) -> pd.DataFrame:
    """Toạ độ mỗi điểm suy từ các điểm còn lại của cùng đợt, trung bình các lần quét."""
    Y = toa_do.loc[X.index].to_numpy(float)
    nhan = X.index.to_numpy()
    ra = {}
    for rp in sorted(set(nhan)):
        bo = nhan == rp
        mo = k_dong._knn(beta, 1.0, 7, X.to_numpy(float)[~bo], Y[~bo])
        ra[rp] = mo.predict(X.to_numpy(float)[bo]).mean(0)
    return pd.DataFrame(ra, index=["x", "y"]).T


def _ba_giao_thuc(fp: pd.DataFrame, ap: list[str], tham_so: dict) -> tuple[float, float, float]:
    seed = []
    for s in range(10):
        d, a = chia_lai(fp, ap, s)
        h, t = d[d["split"] != "test"], d[d["split"] == "test"]
        m = k_dong.build(**tham_so).fit(h[a].to_numpy(float), h[config.TARGET_COLS].to_numpy(float))
        seed.append(evaluate.khoang_cach_loi(t[config.TARGET_COLS].to_numpy(float),
                                             m.predict(t[a].to_numpy(float))).mean())
    bo = np.concatenate([evaluate.khoang_cach_loi(Yt, k_dong.build(**tham_so).fit(Xh, Yh).predict(Xt))
                         for _, Xh, Yh, Xt, Yt in chuan_bi_lan_gap(fp, ap)])
    khac = []
    for h, t in HAI_CHIEU:
        Xh, Yh, Xt, Yt = chuan_bi_chieu(fp, ap, h, t)
        khac.append(evaluate.khoang_cach_loi(Yt, k_dong.build(**tham_so).fit(Xh, Yh).predict(Xt)).mean())
    return (float(np.mean(seed)) * MET_MOI_DON_VI, float(bo.mean()) * MET_MOI_DON_VI,
            float(np.mean(khac)) * MET_MOI_DON_VI)


def run() -> pd.DataFrame:
    fp, ap = nap_bang_rong()
    tham_so = _tham_so("fingerprint_knn_dong", k_dong)
    ref = pd.read_csv(config.REFERENCE_POINTS_CSV).set_index("rp_id")[config.TARGET_COLS]

    tep = pd.read_csv(config.CTK45_XU_LY_CSV).groupby("ID_RP")[["X", "Y"]].first()
    lech = pd.DataFrame({"x_bang": ref["x"], "y_bang": ref["y"],
                         "x_tep": tep["X"], "y_tep": tep["Y"]}).dropna()
    lech["lech_m"] = np.hypot(lech.x_bang - lech.x_tep, lech.y_bang - lech.y_tep) * MET_MOI_DON_VI
    print(f"{len(lech)} mã có trong cả hai nguồn, {(lech.lech_m > 0).sum()} mã lệch toạ độ:")
    print(lech[lech.lech_m > 0].round(2).to_string())

    a, b = _van_tay(fp, ap, "A"), _van_tay(fp, ap, "B")
    so_b = b.index.value_counts()
    print(f"Mã điểm: A {a.index.nunique()}, B {b.index.nunique()}, trùng {set(a.index) == set(b.index)}; "
          f"đợt B {so_b.min()}–{so_b.max()} lần quét mỗi điểm")
    rps = sorted(set(a.index))
    Ca, Cb = a.groupby(level=0).mean().loc[rps], b.groupby(level=0).mean().loc[rps]
    D = _bray_curtis(Cb.to_numpy(), Ca.to_numpy())
    rng = np.random.default_rng(0)
    xao = [D[np.arange(len(rps)), rng.permutation(len(rps))].mean() for _ in range(SO_LAN_XAO)]
    print(f"Bray-Curtis vân tay trung bình: cùng mã {np.diag(D).mean():.3f}, "
          f"khác mã {D[~np.eye(len(rps), dtype=bool)].mean():.3f}, xáo nhãn thấp nhất {min(xao):.3f}")

    hang = (D < np.diag(D)[:, None]).sum(1) + 1
    truoc = (ref.loc[rps, "y"] < 41).to_numpy()
    print(f"Gần nhất đúng mã: {(hang == 1).sum()}/40 (y < 41: {(hang[truoc] == 1).sum()}/{truoc.sum()}, "
          f"y ≥ 41: {(hang[~truoc] == 1).sum()}/{(~truoc).sum()})")
    nua = rng.random(len(b)) < 0.5
    D_b = _bray_curtis(b[nua].groupby(level=0).mean().loc[rps].to_numpy(),
                       b[~nua].groupby(level=0).mean().loc[rps].to_numpy())
    print(f"Đối chứng, hai nửa đợt B: {(D_b.argmin(1) == np.arange(len(rps))).sum()}/40")
    manh_b = np.argsort(-Cb.to_numpy(), axis=1)[:, :4]
    print("AP mạnh nhất đợt A nằm trong 4 AP mạnh nhất đợt B: "
          f"{sum(m in t for m, t in zip(Ca.to_numpy().argmax(1), manh_b))}/40 điểm")

    va, vb = _vi_tri_noi_bo(a, ref, tham_so["beta"]), _vi_tri_noi_bo(b, ref, tham_so["beta"])
    kq = pd.DataFrame({"hang_van_tay": hang, "bc_cung_ma": np.diag(D)}, index=rps)
    kq["lech_vi_tri_m"] = np.hypot(va.x - vb.x, va.y - vb.y) * MET_MOI_DON_VI
    v = kq.lech_vi_tri_m
    print(f"Vị trí suy từ tín hiệu, A so với B: TB {v.mean():.2f} m, trung vị {v.median():.2f} m, "
          f"y < 41 {v[truoc].mean():.2f} m, y ≥ 41 {v[~truoc].mean():.2f} m")
    print(kq.sort_values("lech_vi_tri_m", ascending=False).head(6).round(2).to_string())
    config.ghi_csv(kq, config.REPORTS_DIR / "tables" / "doi_chieu_dot.csv", index_label="rp_id")

    print("Ba giao thức, toạ độ bảng:", np.round(_ba_giao_thuc(fp, ap, tham_so), 2))
    fp2 = fp.copy()
    for rp, dong in lech[lech.lech_m > 0].iterrows():
        fp2.loc[fp2["rp_id"] == rp, config.TARGET_COLS] = (dong.x_tep, dong.y_tep)
    print("Ba giao thức, toạ độ của tệp:", np.round(_ba_giao_thuc(fp2, ap, tham_so), 2))
    return kq


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    run()
