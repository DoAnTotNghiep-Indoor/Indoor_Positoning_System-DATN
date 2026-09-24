"""Quét số láng giềng k cho ba mô hình họ kNN, trên cả ba cách đánh giá.

    python -m ml.quet_k

`ml.train` chọn k = 1 cho kNN và kNN vân tay, tức thực chất là láng giềng gần
nhất (NN). Bảng này cho thấy k = 1 thắng ở đâu và thua ở đâu, thay vì chỉ báo
mỗi giá trị được chọn:

    validation seed 42     -> tiêu chí chọn tham số của `ml.train`
    test, 10 seed          -> chia ngẫu nhiên lại, chặn LẠC QUAN
    bỏ trọn một điểm       -> toạ độ chưa từng thấy, chặn BI QUAN

Các tham số khác (metric, beta, power) giữ đúng như `ml.train` đã chọn; chỉ k
thay đổi. Sai số ghi theo đơn vị lưới của Bảng 4 và quy ra mét.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from ml import config, evaluate
from ml.danh_gia_cheo import _tham_so, chuan_bi_lan_gap, nap_bang_rong
from ml.models import fingerprint_knn, knn, wknn
from ml.on_dinh import chia_lai
from ml.train import nap_du_lieu

CAC_K = [1, 2, 3, 4, 5, 7, 9, 11, 15, 21, 31, 41, 61]
SO_SEED = 10
MET_MOI_DON_VI = 0.3508

MO_HINH = [knn, wknn, fingerprint_knn]


def _tham_so_voi_k(mo_dun, k: int) -> dict:
    tham_so = dict(_tham_so(mo_dun.__name__.rsplit(".", 1)[-1], mo_dun))
    tham_so["n_neighbors"] = k
    return tham_so


def _loi(mo_dun, k, X_hoc, Y_hoc, X_thu, Y_thu) -> np.ndarray:
    mo = mo_dun.build(**_tham_so_voi_k(mo_dun, k)).fit(X_hoc, Y_hoc)
    return evaluate.khoang_cach_loi(Y_thu, mo.predict(X_thu))


def run() -> pd.DataFrame:
    tap, ap = nap_du_lieu()
    tr, va = tap["train"], tap["validation"]
    fp, ap_cols = nap_bang_rong()
    cac_seed = [chia_lai(fp, ap_cols, s) for s in range(SO_SEED)]
    cac_gap = chuan_bi_lan_gap(fp, ap_cols)

    dong = []
    for mo_dun in MO_HINH:
        for k in CAC_K:
            loi_va = _loi(mo_dun, k, tr[ap].to_numpy(float), tr[config.TARGET_COLS].to_numpy(float),
                          va[ap].to_numpy(float), va[config.TARGET_COLS].to_numpy(float))
            theo_seed = []
            for d, a in cac_seed:
                hoc, thu = d[d["split"] != "test"], d[d["split"] == "test"]
                theo_seed.append(_loi(mo_dun, k, hoc[a].to_numpy(float), hoc[config.TARGET_COLS].to_numpy(float),
                                      thu[a].to_numpy(float), thu[config.TARGET_COLS].to_numpy(float)).mean())
            bo_diem = np.concatenate([_loi(mo_dun, k, Xh, Yh, Xt, Yt) for _, Xh, Yh, Xt, Yt in cac_gap])
            dong.append({
                "mo_hinh": mo_dun.TEN, "k": k,
                "validation": loi_va.mean(),
                "validation_dung_diem": float((loi_va < 1e-9).mean()),
                "test_10_seed": float(np.mean(theo_seed)),
                "test_10_seed_lech_chuan": float(np.std(theo_seed, ddof=1)),
                "bo_diem": float(bo_diem.mean()),
                "bo_diem_trung_vi": float(np.median(bo_diem)),
            })
            print(f"{mo_dun.TEN:28s} k={k:2d}  val {loi_va.mean():6.2f}  "
                  f"10 seed {np.mean(theo_seed):6.2f}  bỏ điểm {bo_diem.mean():6.2f}  (đơn vị lưới)")

    bang = pd.DataFrame(dong)
    for cot in ("validation", "test_10_seed", "test_10_seed_lech_chuan", "bo_diem", "bo_diem_trung_vi"):
        bang[cot + "_m"] = bang[cot] * MET_MOI_DON_VI
    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "quet_k.csv", index=False)
    _ve(bang)
    return bang


def _ve(bang: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mau = {"kNN": "#2c5bd8", "WKNN": "#e07b39", "kNN vân tay (Bray-Curtis)": "#2a9d8f"}
    hinh, truc = plt.subplots(1, 2, figsize=(13, 4.8), sharex=True)
    for ten, nhom in bang.groupby("mo_hinh", sort=False):
        truc[0].plot(nhom["k"], nhom["test_10_seed_m"], "o-", color=mau[ten], label=ten)
        truc[1].plot(nhom["k"], nhom["bo_diem_m"], "o-", color=mau[ten], label=ten)
    truc[0].set_title("Chia ngẫu nhiên, trung bình 10 seed")
    truc[1].set_title("Bỏ trọn một điểm tham chiếu")
    for t in truc:
        t.set_xlabel("số láng giềng k")
        t.set_ylabel("sai số trung bình (m)")
        t.set_xscale("log")
        t.set_xticks(CAC_K)
        t.set_xticklabels(CAC_K)
        t.grid(alpha=0.3)
    truc[0].legend()
    hinh.tight_layout()
    (config.REPORTS_DIR / "figures").mkdir(parents=True, exist_ok=True)
    hinh.savefig(config.REPORTS_DIR / "figures" / "quet_k.png", dpi=150)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    run()
