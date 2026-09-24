"""Thử nghiệm mạng nơ-ron nhiều lớp (MLP) — hướng học sâu, trên cùng ba cách đánh giá.

    python -m ml.mlp

Hai cách phát biểu, giống hai hướng mà các đồ án trước đã dùng:

    MLP hồi quy     -> đầu ra (x, y) trực tiếp, hàm mất mát bình phương sai số
    MLP phân lớp    -> softmax trên 40 điểm tham chiếu, toạ độ = trung bình các
                       điểm theo xác suất (cùng ý tưởng với kNN vân tay)

Tham số chọn trên validation seed 42 như `ml.train`, rồi giữ nguyên khi chia lại
10 seed và khi bỏ trọn một điểm. Không đưa vào `ml.models.DANH_SACH` để không
đổi mô hình đang triển khai; đây là thí nghiệm đối chứng.
"""

from __future__ import annotations

import warnings
from itertools import product

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import TransformedTargetRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler

from ml import config, evaluate
from ml.danh_gia_cheo import chuan_bi_lan_gap, nap_bang_rong
from ml.on_dinh import chia_lai
from ml.train import nap_du_lieu

SO_SEED = 10
MET_MOI_DON_VI = 0.3508

LUOI = {
    "an": [(64, 64), (128, 64), (256, 128, 64)],
    "alpha": [1e-4, 1e-3, 1e-2],
}


def mlp_hoi_quy(an=(128, 64), alpha=1e-3, seed=0):
    # Chuẩn hoá cả đầu ra: toạ độ trải từ -41 tới 41 mà adam khởi tạo quanh 0.
    return TransformedTargetRegressor(
        regressor=MLPRegressor(hidden_layer_sizes=an, alpha=alpha, max_iter=3000,
                               early_stopping=True, validation_fraction=0.15,
                               n_iter_no_change=50, random_state=seed),
        transformer=StandardScaler())


class MlpPhanLop(BaseEstimator, RegressorMixin):
    def __init__(self, an=(128, 64), alpha=1e-3, seed=0):
        self.an, self.alpha, self.seed = an, alpha, seed

    def fit(self, X, y):
        self.toa_do_, nhan = np.unique(np.asarray(y, dtype=float), axis=0, return_inverse=True)
        self.clf_ = MLPClassifier(hidden_layer_sizes=self.an, alpha=self.alpha, max_iter=3000,
                                  early_stopping=True, validation_fraction=0.15,
                                  n_iter_no_change=50, random_state=self.seed).fit(X, nhan)
        return self

    def predict(self, X):
        return self.clf_.predict_proba(X) @ self.toa_do_[self.clf_.classes_]


BIEN_THE = {"MLP hồi quy": mlp_hoi_quy, "MLP phân lớp": MlpPhanLop}


def _loi(tao, tham_so, Xh, Yh, Xt, Yt) -> np.ndarray:
    return evaluate.khoang_cach_loi(Yt, tao(**tham_so).fit(Xh, Yh).predict(Xt))


def run() -> pd.DataFrame:
    tap, ap = nap_du_lieu()
    tr, va = tap["train"], tap["validation"]
    lay = lambda d, a: (d[a].to_numpy(float), d[config.TARGET_COLS].to_numpy(float))
    fp, ap_cols = nap_bang_rong()
    cac_seed = [chia_lai(fp, ap_cols, s) for s in range(SO_SEED)]
    cac_gap = chuan_bi_lan_gap(fp, ap_cols)

    dong = []
    for ten, tao in BIEN_THE.items():
        tot, tot_loi = None, np.inf
        for an, alpha in product(LUOI["an"], LUOI["alpha"]):
            loi = _loi(tao, {"an": an, "alpha": alpha}, *lay(tr, ap), *lay(va, ap)).mean()
            if loi < tot_loi:
                tot, tot_loi = {"an": an, "alpha": alpha}, loi
        theo_seed = []
        for d, a in cac_seed:
            hoc, thu = d[d["split"] != "test"], d[d["split"] == "test"]
            theo_seed.append(_loi(tao, tot, *lay(hoc, a), *lay(thu, a)).mean())
        bo_diem = np.concatenate([_loi(tao, tot, Xh, Yh, Xt, Yt) for _, Xh, Yh, Xt, Yt in cac_gap])
        dong.append({"mo_hinh": ten, "tham_so": str(tot), "validation": tot_loi,
                     "test_10_seed": float(np.mean(theo_seed)),
                     "test_10_seed_lech_chuan": float(np.std(theo_seed, ddof=1)),
                     "bo_diem": float(bo_diem.mean()), "bo_diem_trung_vi": float(np.median(bo_diem))})
        print(f"{ten:14s} {tot}  val {tot_loi:6.2f}  10 seed {np.mean(theo_seed):6.2f} "
              f"± {np.std(theo_seed, ddof=1):4.2f}  bỏ điểm {bo_diem.mean():6.2f}  (đơn vị lưới)")

    bang = pd.DataFrame(dong)
    for cot in ("validation", "test_10_seed", "test_10_seed_lech_chuan", "bo_diem", "bo_diem_trung_vi"):
        bang[cot + "_m"] = bang[cot] * MET_MOI_DON_VI
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "mlp.csv", index=False)
    return bang


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    run()
