"""kNN vân tay với k động: chọn k theo độ giống của lần quét với dữ liệu đã thu.

`ml.quet_k` cho thấy k = 1 tốt nhất khi người dùng đứng đúng điểm đã khảo sát,
còn k lớn tốt nhất khi đứng ở chỗ chưa khảo sát (trung bình nhiều láng giềng
nội suy được vị trí ở giữa). Máy chủ không biết người dùng đứng đâu, nhưng biết
lần quét giống vân tay đã có tới mức nào: khoảng cách Bray-Curtis tới láng giềng
gần nhất, d1.

    d1 < nguong  ->  k = k_nho  (trả đúng toạ độ điểm đã khảo sát)
    ngược lại    ->  k = k_lon  (nội suy giữa các điểm)

`nguong` và `k_lon` để None thì `fit` tự chọn chỉ trên dữ liệu được đưa vào,
bằng hai tình huống giả lập bên trong, nặng như nhau:

    đã khảo sát    ->  chia ngẫu nhiên 80/20 theo lần quét
    chưa khảo sát  ->  bỏ trọn từng điểm tham chiếu (mỗi toạ độ là một điểm)

Nhờ vậy dùng được nguyên trong `ml.train`, `ml.on_dinh`, `ml.danh_gia_cheo`
mà không rò phần thử. Đánh giá đầy đủ: `python -m ml.ket_hop`.
"""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin

from ml.models.fingerprint_knn import DinhViPhanLop, bieu_dien_powed

TEN = "kNN vân tay (Bray-Curtis), k động"

CAC_K_LON = (15, 21, 31, 41)
CAC_PHAN_VI = tuple(range(5, 100, 5))

# beta quanh giá trị kNN vân tay thường chọn; ngưỡng và k lớn tự chọn trong fit.
LUOI_THAM_SO = {"beta": [3.0, 3.5, 4.0]}
LUOI_NHANH = {"beta": [4.0]}


def _loi(Y, P) -> np.ndarray:
    Y, P = np.asarray(Y, float), np.asarray(P, float)
    return np.hypot(Y[:, 0] - P[:, 0], Y[:, 1] - P[:, 1])


def _knn(beta, power, k, X, Y) -> DinhViPhanLop:
    return DinhViPhanLop(beta=beta, n_neighbors=k, power=power).fit(X, Y)


def khoang_cach_gan_nhat(mo_k1: DinhViPhanLop, X) -> np.ndarray:
    """d1 của từng lần quét, đo trên đúng biểu diễn mà mô hình dùng."""
    Xp = bieu_dien_powed(X, mo_k1.beta)
    return mo_k1.clf_.kneighbors(Xp, n_neighbors=1)[0][:, 0]


def _mot_ca(beta, power, k_nho, cac_k, X_hoc, Y_hoc, X_thu):
    nho = _knn(beta, power, k_nho, X_hoc, Y_hoc)
    lon = {k: _knn(beta, power, k, X_hoc, Y_hoc).predict(X_thu) for k in cac_k}
    return khoang_cach_gan_nhat(nho, X_thu), nho.predict(X_thu), lon


def tinh_ca_ben_trong(X, Y, beta, power, k_nho=1, cac_k=CAC_K_LON):
    """[(d1, dự đoán k nhỏ, {k lớn: dự đoán}, toạ độ thật)] cho hai tình huống."""
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    chon = np.random.default_rng(0).random(len(X)) < 0.8
    ca = [(*_mot_ca(beta, power, k_nho, cac_k, X[chon], Y[chon], X[~chon]), Y[~chon])]

    nhom = np.unique(Y, axis=0, return_inverse=True)[1].ravel()
    d, p, q, y = [], [], {k: [] for k in cac_k}, []
    for g in np.unique(nhom):
        bo = nhom == g
        dd, pp, qq = _mot_ca(beta, power, k_nho, cac_k, X[~bo], Y[~bo], X[bo])
        d.append(dd); p.append(pp); y.append(Y[bo])
        for k in cac_k:
            q[k].append(qq[k])
    ca.append((np.concatenate(d), np.vstack(p), {k: np.vstack(v) for k, v in q.items()}, np.vstack(y)))
    return ca


def tron(d1, p_nho, p_lon, t1, t2):
    """t1 == t2: chọn cứng. t1 < t2: trọng số k nhỏ giảm tuyến tính từ t1 tới t2."""
    if t2 > t1:
        w = np.clip((t2 - d1) / (t2 - t1), 0.0, 1.0)
    else:
        w = (d1 < t1).astype(float)
    return w[:, None] * p_nho + (1 - w[:, None]) * p_lon


def chon_tham_so(ca, mem: bool = False) -> tuple[float, float, int]:
    """(t1, t2, k lớn) cho trung bình sai số hai tình huống nhỏ nhất."""
    moc = np.percentile(np.concatenate([c[0] for c in ca]), CAC_PHAN_VI)
    tot, tot_loi = None, np.inf
    for k in ca[0][2]:
        for i, t1 in enumerate(moc):
            for t2 in (moc[i:] if mem else [t1]):
                loi = np.mean([_loi(y, tron(d, pn, pl[k], t1, t2)).mean() for d, pn, pl, y in ca])
                if loi < tot_loi:
                    tot, tot_loi = (float(t1), float(t2), int(k)), loi
    return tot


class DinhViKDong(BaseEstimator, RegressorMixin):
    def __init__(self, beta: float = 4.0, power: float = 1.0, k_nho: int = 1,
                 nguong: float | None = None, k_lon: int | None = None):
        self.beta = beta
        self.power = power
        self.k_nho = k_nho
        self.nguong = nguong
        self.k_lon = k_lon

    def fit(self, X, y):
        if self.nguong is None or self.k_lon is None:
            t1, _, k = chon_tham_so(tinh_ca_ben_trong(X, y, self.beta, self.power, self.k_nho))
            self.nguong_ = t1 if self.nguong is None else self.nguong
            self.k_lon_ = k if self.k_lon is None else self.k_lon
        else:
            self.nguong_, self.k_lon_ = self.nguong, self.k_lon
        self.nho_ = _knn(self.beta, self.power, self.k_nho, X, y)
        self.lon_ = _knn(self.beta, self.power, self.k_lon_, X, y)
        return self

    def dung_k_nho(self, X) -> np.ndarray:
        return khoang_cach_gan_nhat(self.nho_, X) < self.nguong_

    def predict(self, X):
        X = np.asarray(X, float)
        return np.where(self.dung_k_nho(X)[:, None], self.nho_.predict(X), self.lon_.predict(X))


def build(beta: float = 4.0, power: float = 1.0) -> DinhViKDong:
    return DinhViKDong(beta=beta, power=power)
