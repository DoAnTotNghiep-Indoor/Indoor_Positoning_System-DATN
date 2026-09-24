"""Thử các cách kết hợp mô hình, độ phức tạp thấp và trung bình.

    python -m ml.ket_hop

Xuất phát từ `ml.quet_k`: kNN vân tay với k = 1 tốt nhất khi điểm cần đoán đã
được khảo sát, k lớn tốt nhất khi chưa.

    Trung bình k nhỏ, k lớn     -> cộng đôi hai dự đoán, không tham số
    Trung bình kNN + XGBoost    -> cộng đôi hai mô hình khác họ, không tham số
    k động (chọn cứng)          -> `ml.models.fingerprint_knn_dong`, mô hình triển khai
    k động (trộn mềm)           -> trọng số k nhỏ giảm tuyến tính giữa hai ngưỡng

Ngưỡng và k lớn chọn LỒNG NHAU, chỉ trên phần học của từng lần chia (xem
`fingerprint_knn_dong`). Phần thử không bao giờ góp vào việc chọn.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from ml import config, evaluate
from ml.danh_gia_cheo import _tham_so, chuan_bi_lan_gap, nap_bang_rong
from ml.models import fingerprint_knn, fingerprint_knn_dong as kd, xgboost_model
from ml.on_dinh import chia_lai

SO_SEED = 10
MET_MOI_DON_VI = 0.3508
K_SO_SANH = 41

THAM_SO_FK = _tham_so("fingerprint_knn", fingerprint_knn)
THAM_SO_XGB = _tham_so("xgboost_model", xgboost_model)


def _loi(Y, P) -> np.ndarray:
    return evaluate.khoang_cach_loi(Y, P)


def danh_gia_mot_lan(X_hoc, Y_hoc, X_thu, Y_thu) -> dict[str, np.ndarray]:
    beta, power = THAM_SO_FK["beta"], THAM_SO_FK["power"]
    d1, p1, lon = kd._mot_ca(beta, power, 1, (K_SO_SANH,), X_hoc, Y_hoc, X_thu)
    p_xgb = xgboost_model.build(**THAM_SO_XGB).fit(X_hoc, Y_hoc).predict(X_thu)
    ra = {
        "kNN vân tay, k = 1": _loi(Y_thu, p1),
        f"kNN vân tay, k = {K_SO_SANH}": _loi(Y_thu, lon[K_SO_SANH]),
        "XGBoost": _loi(Y_thu, p_xgb),
        f"Trung bình k = 1 và k = {K_SO_SANH}": _loi(Y_thu, (p1 + lon[K_SO_SANH]) / 2),
        "Trung bình kNN vân tay và XGBoost": _loi(Y_thu, (p1 + p_xgb) / 2),
    }
    ca = kd.tinh_ca_ben_trong(X_hoc, Y_hoc, beta, power)
    for ten, mem in (("k động, chọn cứng", False), ("k động, trộn mềm", True)):
        t1, t2, k = kd.chon_tham_so(ca, mem)
        pl = kd._knn(beta, power, k, X_hoc, Y_hoc).predict(X_thu)
        ra[ten] = _loi(Y_thu, kd.tron(d1, p1, pl, t1, t2))
    return ra


def run() -> pd.DataFrame:
    fp, ap_cols = nap_bang_rong()
    theo_seed: dict[str, list[float]] = {}
    for s in range(SO_SEED):
        d, a = chia_lai(fp, ap_cols, s)
        hoc, thu = d[d["split"] != "test"], d[d["split"] == "test"]
        kq = danh_gia_mot_lan(hoc[a].to_numpy(float), hoc[config.TARGET_COLS].to_numpy(float),
                              thu[a].to_numpy(float), thu[config.TARGET_COLS].to_numpy(float))
        for ten, loi in kq.items():
            theo_seed.setdefault(ten, []).append(loi.mean())
        print(f"seed {s} xong", flush=True)

    bo_diem: dict[str, list[np.ndarray]] = {}
    for i, (_, Xh, Yh, Xt, Yt) in enumerate(chuan_bi_lan_gap(fp, ap_cols)):
        for ten, loi in danh_gia_mot_lan(Xh, Yh, Xt, Yt).items():
            bo_diem.setdefault(ten, []).append(loi)
        print(f"gấp {i + 1} xong", flush=True)

    dong = []
    for ten in theo_seed:
        s = np.array(theo_seed[ten]) * MET_MOI_DON_VI
        b = np.concatenate(bo_diem[ten]) * MET_MOI_DON_VI
        dong.append({"mo_hinh": ten, "ngau_nhien_10_seed_m": s.mean(), "lech_chuan_m": s.std(ddof=1),
                     "bo_diem_m": b.mean(), "bo_diem_trung_vi_m": float(np.median(b)),
                     "trung_binh_hai_giao_thuc_m": (s.mean() + b.mean()) / 2})
    bang = pd.DataFrame(dong)
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "ket_hop.csv", index=False)
    print(bang.to_string(index=False, float_format=lambda v: f"{v:6.2f}"))
    return bang


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    run()
