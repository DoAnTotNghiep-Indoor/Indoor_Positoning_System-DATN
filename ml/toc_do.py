"""Tốc độ đoán của năm mô hình, cùng điều kiện, cùng tập test seed 42.

    python -m ml.toc_do

Đo từng lần quét một như máy chủ nhận, không đo theo lô. Random Forest đo thêm với một
luồng: mặc định `n_jobs=-1` trả giá dựng luồng cho mỗi lần đoán một mẫu.
Sinh reports/tables/toc_do_du_doan.csv.
"""

from __future__ import annotations

import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml import config, evaluate
from ml import models as goi_mo_hinh
from ml.danh_gia_cheo import _tham_so
from ml.train import nap_du_lieu

SO_VONG = 5


def _do(mo_hinh, X: np.ndarray) -> np.ndarray:
    mo_hinh.predict(X[:1])
    ms = []
    for _ in range(SO_VONG):
        for i in range(len(X)):
            bat_dau = time.perf_counter()
            mo_hinh.predict(X[i: i + 1])
            ms.append((time.perf_counter() - bat_dau) * 1000)
    return np.array(ms)


def _dong(ten: str, mo_hinh, X, **them) -> dict:
    ms = _do(mo_hinh, X)
    return {"mo_hinh": ten, "trung_vi_ms": float(np.median(ms)), "tb_ms": float(ms.mean()),
            "p95_ms": float(np.percentile(ms, 95)), **them}


def run() -> pd.DataFrame:
    tap, ap = nap_du_lieu()
    X_te = tap["test"][ap].to_numpy(float)
    hoc = pd.concat([tap["train"], tap["validation"]], ignore_index=True)
    X, Y = hoc[ap].to_numpy(float), hoc[config.TARGET_COLS].to_numpy(float)

    dong = []
    for m in goi_mo_hinh.DANH_SACH:
        khoa = m.__name__.rsplit(".", 1)[-1]
        tep = Path(config.ARTIFACTS_DIR / f"model_{khoa}.pkl")
        bat_dau = time.perf_counter()
        mo_hinh = joblib.load(tep)
        nap_ms = (time.perf_counter() - bat_dau) * 1000
        bat_dau = time.perf_counter()
        m.build(**_tham_so(khoa, m)).fit(X, Y)
        hoc_s = time.perf_counter() - bat_dau
        dong.append(_dong(m.TEN, mo_hinh, X_te, kich_thuoc_mb=tep.stat().st_size / 1e6,
                          nap_ms=nap_ms, huan_luyen_s=hoc_s))
        if hasattr(mo_hinh, "n_jobs") and mo_hinh.n_jobs == -1:
            mo_hinh.set_params(n_jobs=1)
            dong.append(_dong(f"{m.TEN} (1 luồng)", mo_hinh, X_te))

    bang = pd.DataFrame(dong).sort_values("trung_vi_ms").reset_index(drop=True)
    print(bang.round(3).to_string(index=False))
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "toc_do_du_doan.csv", index=False)
    return bang


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    run()
