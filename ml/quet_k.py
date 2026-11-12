"""Quét số láng giềng k: k cố định và k động cho ba mô hình họ kNN, trên ba giao thức.

    python -m ml.quet_k

Mỗi họ giữ metric và trọng số `ml.train` đã chọn (họ Bray-Curtis lấy beta của kNN k
động), chỉ đổi cách chọn k:

    k cố định   mọi lần quét dùng cùng một k, k = 1 .. 61
    k động      d1 < ngưỡng -> k nhỏ, ngược lại -> k lớn. d1 đo bằng metric của chính họ;
                ngưỡng (và k lớn khi "tự chọn") chọn lúc học bằng hai tình huống giả lập
                của `fingerprint_knn_dong`, không nhìn phần thử

Dòng "kNN Bray-Curtis, k động 1 / tự chọn" chính là mô hình triển khai. Giao thức:

    validation seed 42     -> tiêu chí chọn tham số của `ml.train`
    test seed 42           -> bảng chính của `ml.train`: học train + validation, kiểm test một lần
    test, 10 seed          -> chia ngẫu nhiên lại, chặn lạc quan
    bỏ trọn một điểm       -> toạ độ chưa từng thấy, chặn bi quan
    khác đợt               -> học một đợt đo, kiểm đợt kia, trung bình hai chiều

Sai số ghi theo đơn vị lưới, cột đuôi `_m` quy ra mét.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from ml import config, evaluate
from ml.danh_gia_cheo import _tham_so, chuan_bi_lan_gap, nap_bang_rong
from ml.khac_dot import HAI_CHIEU, chuan_bi_chieu
from ml.models import fingerprint_knn_dong as k_dong
from ml.models import knn, wknn
from ml.models.fingerprint_knn import DinhViPhanLop
from ml.on_dinh import chia_lai
from ml.train import nap_du_lieu

CAC_K = (1, 2, 3, 4, 5, 7, 9, 11, 15, 21, 31, 41, 61)
K_NHO = (1, 2, 3)
K_LON = (7, 11, 15, 21, 31, 41, 61)
TU_CHON = "tự chọn"
SO_SEED = 10
BC = "kNN Bray-Curtis"
HO = ("kNN", "WKNN", BC)


def _tao(ho: str, ts: dict, k: int):
    if ho == BC:
        return DinhViPhanLop(beta=ts["beta"], n_neighbors=k, power=ts["power"])
    return {"kNN": knn, "WKNN": wknn}[ho].build(**{**ts, "n_neighbors": k})


def _d1(mo, X) -> np.ndarray:
    if isinstance(mo, DinhViPhanLop):
        return k_dong.khoang_cach_gan_nhat(mo, X)
    return mo.kneighbors(X, n_neighbors=1)[0][:, 0]


def _ca_ben_trong(ho, ts, X, Y) -> list[tuple]:
    """Hai tình huống của `k_dong.tinh_ca_ben_trong` cho họ bất kỳ: [(d1, {k: dự đoán}, toạ độ)]."""
    cac_k = sorted(set(K_NHO) | set(K_LON))
    chon = np.random.default_rng(0).random(len(X)) < 0.8
    nhom = np.unique(Y, axis=0, return_inverse=True)[1].ravel()
    ra = []
    for phan in ([(chon, ~chon)], [(nhom != g, nhom == g) for g in np.unique(nhom)]):
        d, p, y = [], {k: [] for k in cac_k}, []
        for hoc, thu in phan:
            mo = {k: _tao(ho, ts, k).fit(X[hoc], Y[hoc]) for k in cac_k}
            d.append(_d1(mo[1], X[thu]))
            y.append(Y[thu])
            for k in cac_k:
                p[k].append(mo[k].predict(X[thu]))
        ra.append((np.concatenate(d), {k: np.vstack(v) for k, v in p.items()}, np.vstack(y)))
    return ra


def _mot_gap(ho, ts, Xh, Yh, Xt, Yt) -> dict:
    """{(kiểu, k, k lớn): (sai số từng lần quét, lần quét nào dùng k nhỏ)} cho một lần chia."""
    mo = {k: _tao(ho, ts, k).fit(Xh, Yh) for k in CAC_K}
    P = {k: m.predict(Xt) for k, m in mo.items()}
    ra = {("cố định", k, None): (evaluate.khoang_cach_loi(Yt, P[k]), None) for k in CAC_K}
    d1 = _d1(mo[1], Xt)
    ca = _ca_ben_trong(ho, ts, Xh, Yh)
    for kn in K_NHO:
        for kl in K_LON + (TU_CHON,):
            cac = k_dong.CAC_K_LON if kl == TU_CHON else (kl,)
            t, _, k = k_dong.chon_tham_so([(d, p[kn], {c: p[c] for c in cac}, y) for d, p, y in ca])
            nho = d1 < t
            ra[("động", kn, kl)] = (evaluate.khoang_cach_loi(Yt, np.where(nho[:, None], P[kn], P[k])), nho)
    return ra


def _dong(khoa: tuple, theo: dict) -> dict:
    ho, kieu, k, kl = khoa
    va = theo["validation"][0][0]
    te = theo["test_42"][0][0]
    seed = [l.mean() for l, _ in theo["10_seed"]]
    bd = np.concatenate([l for l, _ in theo["bo_diem"]])
    r = {"mo_hinh": ho, "kieu_k": kieu, "k": k, "k_lon": kl,
         "validation": float(va.mean()), "validation_dung_diem": float((va < 1e-9).mean()),
         "test_42": float(te.mean()), "test_42_trung_vi": float(np.median(te)),
         "test_10_seed": float(np.mean(seed)), "test_10_seed_lech_chuan": float(np.std(seed, ddof=1)),
         "bo_diem": float(bd.mean()), "bo_diem_trung_vi": float(np.median(bd))}
    chieu = [f"{h}→{t}" for h, t in HAI_CHIEU]
    for c in chieu:
        r[f"khac_dot_{c}"] = float(theo[c][0][0].mean())
    r["khac_dot"] = float(np.mean([r[f"khac_dot_{c}"] for c in chieu]))
    if kieu == "động":
        for ten, cac in (("10_seed", ["10_seed"]), ("bo_diem", ["bo_diem"]), ("khac_dot", chieu)):
            r[f"ty_le_k_nho_{ten}"] = float(np.concatenate([n for c in cac for _, n in theo[c]]).mean())
    return r


def _hoc_thu(d: pd.DataFrame, a: list[str]) -> tuple:
    hoc, thu = d[d["split"] != "test"], d[d["split"] == "test"]
    return (hoc[a].to_numpy(float), hoc[config.TARGET_COLS].to_numpy(float),
            thu[a].to_numpy(float), thu[config.TARGET_COLS].to_numpy(float))


def run() -> pd.DataFrame:
    tap, ap = nap_du_lieu()
    tr, va, te = tap["train"], tap["validation"], tap["test"]
    hoc = pd.concat([tr, va])
    fp, ap_cols = nap_bang_rong()
    gap = {
        "validation": [(tr[ap].to_numpy(float), tr[config.TARGET_COLS].to_numpy(float),
                        va[ap].to_numpy(float), va[config.TARGET_COLS].to_numpy(float))],
        "test_42": [(hoc[ap].to_numpy(float), hoc[config.TARGET_COLS].to_numpy(float),
                     te[ap].to_numpy(float), te[config.TARGET_COLS].to_numpy(float))],
        "10_seed": [_hoc_thu(*chia_lai(fp, ap_cols, s)) for s in range(SO_SEED)],
        "bo_diem": [g[1:] for g in chuan_bi_lan_gap(fp, ap_cols)],
        **{f"{h}→{t}": [chuan_bi_chieu(fp, ap_cols, h, t)] for h, t in HAI_CHIEU},
    }
    dong = k_dong.build(**_tham_so("fingerprint_knn_dong", k_dong))
    ts = {"kNN": _tham_so("knn", knn), "WKNN": _tham_so("wknn", wknn),
          BC: {"beta": dong.beta, "power": dong.power}}

    viec = [(ho, ten, g) for ho in HO for ten, ds in gap.items() for g in ds]
    kq = config.song_song(_mot_gap, [(ho, ts[ho], *g) for ho, _, g in viec])
    gom = {}
    for (ho, ten, _), r in zip(viec, kq):
        for nhan, v in r.items():
            gom.setdefault((ho, *nhan), {}).setdefault(ten, []).append(v)
    bang = pd.DataFrame([_dong(khoa, theo) for khoa, theo in gom.items()])
    for cot in ("validation", "test_42", "test_42_trung_vi", "test_10_seed", "test_10_seed_lech_chuan", "bo_diem", "bo_diem_trung_vi",
                "khac_dot_A→B", "khac_dot_B→A", "khac_dot"):
        bang[cot + "_m"] = bang[cot] * config.MET_MOI_DON_VI

    nhan = bang.apply(lambda r: f"k = {r['k']}" if r["kieu_k"] == "cố định"
                      else f"k động {r['k']} / {r['k_lon']}", axis=1)
    hien = bang[["mo_hinh", "test_42_m", "test_10_seed_m", "bo_diem_m", "khac_dot_m",
                 "ty_le_k_nho_10_seed", "ty_le_k_nho_bo_diem"]].assign(cach_chon_k=nhan)
    print(hien.to_string(index=False, float_format=lambda v: f"{v:5.2f}"))

    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "quet_k.csv", index=False)
    _ve(bang)
    return bang


def _ve(bang: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mau = {"kNN": "#2c5bd8", "WKNN": "#e07b39", BC: "#2a9d8f"}
    cot = [("test_10_seed_m", "Chia ngẫu nhiên, trung bình 10 seed"),
           ("bo_diem_m", "Bỏ trọn một điểm tham chiếu"),
           ("khac_dot_m", "Khác đợt đo, trung bình hai chiều")]
    hinh, truc = plt.subplots(1, 3, figsize=(18, 4.8), sharex=True)
    for ho in HO:
        cua = bang[bang["mo_hinh"] == ho]
        co_dinh = cua[cua["kieu_k"] == "cố định"]
        dong = cua[(cua["kieu_k"] == "động") & (cua["k"] == 1) & (cua["k_lon"] != TU_CHON)]
        for t, (c, _) in zip(truc, cot):
            t.plot(co_dinh["k"], co_dinh[c], "o-", color=mau[ho], label=f"{ho}, k cố định")
            t.plot(dong["k_lon"].astype(int), dong[c], "s--", color=mau[ho], label=f"{ho}, k động 1 / k lớn")
    for t, (_, ten) in zip(truc, cot):
        t.set_title(ten)
        t.set_xlabel("k cố định, hoặc k lớn của k động")
        t.set_ylabel("sai số trung bình (m)")
        t.set_xscale("log")
        t.set_xticks(CAC_K)
        t.set_xticklabels(CAC_K)
        t.grid(alpha=0.3)
    truc[0].legend(fontsize=8)
    hinh.tight_layout()
    (config.REPORTS_DIR / "figures").mkdir(parents=True, exist_ok=True)
    hinh.savefig(config.REPORTS_DIR / "figures" / "quet_k.png", dpi=150)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    run()
