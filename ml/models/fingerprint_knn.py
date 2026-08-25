"""kNN vân tay dùng khoảng cách Bray-Curtis — mô hình tối ưu cho dữ liệu hiện có.

Xuất phát từ một quan sát về chính bộ dữ liệu: 782 mẫu nhưng chỉ có 39 toạ độ
khác nhau, vì dữ liệu được thu ĐÚNG TẠI các điểm tham chiếu chứ không có mẫu nào
ở giữa. Nhãn (x, y) vì thế bị lượng tử hoá theo lưới khoảng 7 mét.

Với cấu trúc đó, hồi quy liên tục làm việc thừa: nó cố đoán những toạ độ không
hề tồn tại trong dữ liệu. Bài toán thực chất gần với phân lớp 39 điểm hơn. Mô
hình này làm đúng thế — chọn điểm tham chiếu, rồi trả về toạ độ của điểm đó.

Hai lựa chọn kỹ thuật đem lại phần lớn cải thiện:

**Bray-Curtis thay cho Euclid.** Khoảng cách Bray-Curtis là L1 đã chuẩn hoá theo
tổng cường độ: `sum|a-b| / sum(a+b)`. Nó so sánh *hình dạng* của vân tay chứ
không so sánh độ mạnh tuyệt đối, nên bớt nhạy với việc cùng một vị trí nhưng
thiết bị khác hoặc hướng cầm máy khác cho ra mức tín hiệu chung cao thấp khác
nhau. Đo trên validation: đúng điểm 82,9% so với 70,1% của Euclid.

**Biểu diễn powed.** Nâng giá trị đã chuẩn hoá lên luỹ thừa beta làm giãn khoảng
cách giữa các AP mạnh và nén phần AP yếu. AP yếu chủ yếu là nhiễu, nên giảm ảnh
hưởng của chúng giúp ích. Cách biểu diễn này lấy từ tài liệu về UJIIndoorLoc.

Trọng số `1/d^power` với `top` lớp có xác suất cao nhất cho phép chuyển mượt giữa
hai thái cực: `n_neighbors=1` là chọn cứng một điểm, `n_neighbors` lớn với
`power` nhỏ là trung bình mềm nhiều điểm.
"""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.neighbors import KNeighborsClassifier

TEN = "kNN vân tay (Bray-Curtis)"

LUOI_THAM_SO = {
    "beta": [1.25, 1.5, 1.75, 2.0],
    "n_neighbors": [1, 3, 5],
    "power": [1, 4, 8],
}

LUOI_NHANH = {
    "beta": [1.5, 1.75],
    "n_neighbors": [1, 3],
    "power": [1, 8],
}


def bieu_dien_powed(X: np.ndarray, beta: float) -> np.ndarray:
    """Nâng đặc trưng đã chuẩn hoá lên luỹ thừa beta.

    Phải cắt ngưỡng dưới ở 0 trước khi nâng luỹ thừa: scaler fit trên tập train
    nên mẫu validation/test có thể mang giá trị âm (đo được thấp nhất -0,333), mà
    số âm mũ 1,75 cho ra NaN. Cắt ở 0 nghĩa là "yếu hơn mọi mẫu từng thấy lúc
    huấn luyện" — đúng ý nghĩa cần biểu đạt.
    """
    return np.clip(np.asarray(X, dtype=float), 0.0, None) ** beta


class DinhViPhanLop(BaseEstimator, RegressorMixin):
    """Phân lớp điểm tham chiếu rồi trả về toạ độ, nhưng vẫn nhận y hai cột.

    Giữ nguyên giao diện `fit(X, y_2_cot)` như ba mô hình hồi quy còn lại, để
    `ml/train.py` đối xử với mọi mô hình theo cùng một quy trình. Nhãn lớp được
    suy ra từ chính các dòng toạ độ duy nhất trong y.
    """

    def __init__(
        self,
        beta: float = 1.75,
        n_neighbors: int = 1,
        power: float = 1.0,
        top: int | None = None,
        metric: str = "braycurtis",
    ):
        self.beta = beta
        self.n_neighbors = n_neighbors
        self.power = power
        self.top = top
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

        if self.top:
            xac_suat = xac_suat.copy()
            nguong = np.sort(xac_suat, axis=1)[:, -self.top][:, None]
            xac_suat[xac_suat < nguong] = 0.0
            xac_suat /= xac_suat.sum(axis=1, keepdims=True)

        # Lớp mà classifier biết, theo đúng thứ tự của predict_proba
        return xac_suat @ self.toa_do_[self.clf_.classes_]

    def du_doan_diem(self, X) -> np.ndarray:
        """Chỉ số điểm tham chiếu được chọn — dùng để đo độ chính xác phân lớp."""
        return self.clf_.predict(bieu_dien_powed(X, self.beta))


def build(
    beta: float = 1.75,
    n_neighbors: int = 1,
    power: float = 1.0,
    top: int | None = None,
) -> DinhViPhanLop:
    return DinhViPhanLop(beta=beta, n_neighbors=n_neighbors, power=power, top=top)
