"""kNN vân tay dùng khoảng cách Bray-Curtis — mô hình tối ưu cho dữ liệu hiện có.

782 mẫu nhưng chỉ 39 toạ độ khác nhau vì dữ liệu thu ĐÚNG TẠI các điểm tham
chiếu, không có mẫu nào ở giữa. Nhãn (x, y) bị lượng tử hoá theo lưới ~7 m nên
bài toán gần với phân lớp 39 điểm hơn là hồi quy liên tục.

Bray-Curtis (`sum|a-b| / sum(a+b)`) là L1 chuẩn hoá theo tổng cường độ: so hình
dạng vân tay chứ không so độ mạnh tuyệt đối nên bớt nhạy với thiết bị hay hướng
cầm máy khác — trên validation đúng điểm 84,6% so với 73,5% của Euclid. Biểu
diễn powed nâng giá trị lên luỹ thừa beta, giãn các AP mạnh và nén AP yếu vốn
chủ yếu là nhiễu (theo UJIIndoorLoc).
"""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.neighbors import KNeighborsClassifier

TEN = "kNN vân tay (Bray-Curtis)"

# beta quét tới 3,5. Lưới cũ dừng ở 2,0 và tối ưu rơi đúng vào biên trên đó —
# dấu hiệu điểm tốt hơn nằm ngoài lưới. Cực trị thật ở 2,75-3,0, sai số tăng
# trở lại từ 3,5 nên lưới này đã bao trọn.
LUOI_THAM_SO = {
    "beta": [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5],
    "n_neighbors": [1, 3, 5],
    "power": [1, 4, 8],
}

LUOI_NHANH = {
    "beta": [2.0, 2.75],
    "n_neighbors": [1, 3],
    "power": [1, 8],
}


def to_hop_trung(tham_so: dict) -> bool:
    """Với k=1 chỉ có một láng giềng nên trọng số không tác dụng: mọi power cho
    ra cùng kết quả. Giữ lại đúng một bộ thay vì huấn luyện lại ba lần."""
    return tham_so["n_neighbors"] == 1 and tham_so["power"] != 1


def bieu_dien_powed(X: np.ndarray, beta: float) -> np.ndarray:
    """Nâng đặc trưng đã chuẩn hoá lên luỹ thừa beta.

    Phải cắt ngưỡng dưới ở 0 trước: scaler fit trên train nên mẫu validation/test
    có thể âm (thấp nhất -0,333), mà số âm mũ 1,75 cho ra NaN. Cắt ở 0 nghĩa là
    "yếu hơn mọi mẫu từng thấy lúc huấn luyện".
    """
    return np.clip(np.asarray(X, dtype=float), 0.0, None) ** beta


class DinhViPhanLop(BaseEstimator, RegressorMixin):
    """Phân lớp điểm tham chiếu rồi trả về toạ độ, nhưng vẫn nhận y hai cột — giữ
    nguyên giao diện `fit(X, y_2_cot)` như ba mô hình hồi quy còn lại, để
    `ml/train.py` đối xử với mọi mô hình theo cùng một quy trình.
    """

    def __init__(
        self,
        beta: float = 1.75,
        n_neighbors: int = 1,
        power: float = 1.0,
        metric: str = "braycurtis",
    ):
        self.beta = beta
        self.n_neighbors = n_neighbors
        self.power = power
        self.metric = metric

    def _trong_so(self, khoang_cach):
        return 1.0 / (np.asarray(khoang_cach, dtype=float) ** self.power + 1e-12)

    def fit(self, X, y):
        y = np.asarray(y, dtype=float)

        # Mỗi toạ độ duy nhất thành một lớp
        self.toa_do_, nhan = np.unique(y, axis=0, return_inverse=True)

        self.clf_ = KNeighborsClassifier(
            n_neighbors=min(self.n_neighbors, len(nhan)),
            metric=self.metric,
            weights="uniform" if self.n_neighbors == 1 else self._trong_so,
        )
        self.clf_.fit(bieu_dien_powed(X, self.beta), nhan)
        return self

    def predict(self, X):
        xac_suat = self.clf_.predict_proba(bieu_dien_powed(X, self.beta))
        # Lớp mà classifier biết, theo đúng thứ tự của predict_proba
        return xac_suat @ self.toa_do_[self.clf_.classes_]


def build(
    beta: float = 1.75,
    n_neighbors: int = 1,
    power: float = 1.0,
) -> DinhViPhanLop:
    return DinhViPhanLop(beta=beta, n_neighbors=n_neighbors, power=power)
