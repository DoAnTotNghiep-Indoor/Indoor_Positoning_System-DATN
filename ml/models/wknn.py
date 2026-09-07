"""WKNN — mô hình cơ sở đối chứng thứ hai.

Giống kNN nhưng láng giềng gần được tính trọng số lớn hơn theo `1/(d + eps)`:
vân tay RSSI càng giống thì vị trí càng gần, không có lý do gì để mẫu thứ 11 có
tiếng nói ngang mẫu thứ nhất. `eps = 1e-6` chặn chia cho 0 khi vân tay trùng khít.
"""

from __future__ import annotations

import numpy as np
from sklearn.neighbors import KNeighborsRegressor

TEN = "WKNN"

EPS = 1e-6

# KHÔNG có k=1, khác lưới của kNN: một láng giềng thì trọng số không có gì để
# cân, nên WKNN ở k=1 chính là kNN ở k=1. Để k=1 thì cả hai cùng chọn nó và
# bảng so sánh có hai dòng trùng khít, mất một mô hình cơ sở mà không ai thấy.
LUOI_THAM_SO = {
    "n_neighbors": [2, 3, 5, 7, 9, 11],
    "metric": ["euclidean", "manhattan"],
}


def trong_so_nghich_dao(khoang_cach: np.ndarray) -> np.ndarray:
    # Phải là hàm đặt tên ở cấp module, KHÔNG dùng lambda: joblib không pickle
    # được lambda, mà backend cần nạp lại mô hình từ .pkl lúc khởi động.
    return 1.0 / (np.asarray(khoang_cach, dtype=float) + EPS)


def build(n_neighbors: int = 5, metric: str = "euclidean") -> KNeighborsRegressor:
    return KNeighborsRegressor(
        n_neighbors=n_neighbors,
        metric=metric,
        weights=trong_so_nghich_dao,
    )
