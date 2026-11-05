"""Ngưỡng d1 và k lớn của kNN k động được chọn thế nào, trên đúng dữ liệu học.

    python -m ml.chon_nguong

Tái lập bước tự chọn trong `fit`, in sai số của mọi cặp (ngưỡng, k lớn) và độ ổn định qua
10 lần chia lại. Sinh reports/tables/chon_nguong.csv (sai số theo mét).
"""

from __future__ import annotations

import warnings

import joblib
import numpy as np
import pandas as pd

from ml import config
from ml.danh_gia_cheo import _tham_so, nap_bang_rong
from ml.models import fingerprint_knn_dong as k_dong
from ml.on_dinh import chia_lai
from ml.train import nap_du_lieu

MET_MOI_DON_VI = 0.3508
CAC_K_MO_RONG = (3, 5, 7, 9, 11, 15, 21, 31, 41, 61)


def _sai_so(ca, k, nguong) -> list[float]:
    return [k_dong._loi(y, k_dong.tron(d, pn, pl[k], nguong, nguong)).mean() * MET_MOI_DON_VI
            for d, pn, pl, y in ca]


def run() -> pd.DataFrame:
    tap, ap = nap_du_lieu()
    hoc = pd.concat([tap["train"], tap["validation"]], ignore_index=True)
    X, Y = hoc[ap].to_numpy(float), hoc[config.TARGET_COLS].to_numpy(float)
    mo_hinh = joblib.load(config.ARTIFACTS_DIR / "model_fingerprint_knn_dong.pkl")

    ca = k_dong.tinh_ca_ben_trong(X, Y, mo_hinh.beta, mo_hinh.power, cac_k=CAC_K_MO_RONG)
    moc = np.percentile(np.concatenate([c[0] for c in ca]), k_dong.CAC_PHAN_VI)
    print(f"Giả lập: {len(ca[0][0])} lần quét đã khảo sát, {len(ca[1][0])} chưa khảo sát")
    dong = [dict(k_lon=k, phan_vi=p, nguong=float(t), da_khao_sat=e[0], chua_khao_sat=e[1],
                 trung_binh=float(np.mean(e)))
            for k in CAC_K_MO_RONG for p, t in zip(k_dong.CAC_PHAN_VI, moc)
            for e in [_sai_so(ca, k, t)]]
    bang = pd.DataFrame(dong)
    print(bang.loc[bang.groupby("k_lon")["trung_binh"].idxmin()].round(3).to_string(index=False))
    print(bang[bang["k_lon"] == 15].round(3).to_string(index=False))
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "chon_nguong.csv", index=False)

    X_te = tap["test"][ap].to_numpy(float)
    Y_te = tap["test"][config.TARGET_COLS].to_numpy(float)
    nhanh = mo_hinh.dung_k_nho(X_te)
    loi = k_dong._loi(Y_te, mo_hinh.predict(X_te)) * MET_MOI_DON_VI
    print(f"Test seed 42: {nhanh.mean():.1%} dùng k = 1, sai số nhánh k = 1 {loi[nhanh].mean():.2f} m, "
          f"nhánh k lớn {loi[~nhanh].mean():.2f} m")

    fp, ap_cols = nap_bang_rong()
    tham_so = _tham_so("fingerprint_knn_dong", k_dong)
    for seed in range(10):
        d, a = chia_lai(fp, ap_cols, seed)
        h, t = d[d["split"] != "test"], d[d["split"] == "test"]
        m = k_dong.build(**tham_so).fit(h[a].to_numpy(float), h[config.TARGET_COLS].to_numpy(float))
        print(f"seed {seed}: ngưỡng {m.nguong_:.3f}, k lớn {m.k_lon_}, "
              f"k = 1 trên test {m.dung_k_nho(t[a].to_numpy(float)).mean():.0%}")
    return bang


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    run()
