"""WKNN — mô hình cơ sở đối chứng thứ hai.

Giống kNN nhưng láng giềng gần được tính trọng số lớn hơn, theo `1/(d + eps)`.
Hợp lý về mặt vật lý: vân tay RSSI càng giống thì vị trí càng gần, nên không có
lý do gì để mẫu thứ 11 có tiếng nói ngang mẫu thứ nhất.

`eps = 1e-6` chặn chia cho 0 khi gặp mẫu trùng khít vân tay.
"""

from __future__ import annotations

import numpy as np
from sklearn.neighbors import KNeighborsRegressor

TEN = "WKNN"

EPS = 1e-6

LUOI_THAM_SO = {
    "n_neighbors": [3, 5, 7, 9, 11],
    "metric": ["euclidean", "manhattan"],
}


def trong_so_nghich_dao(khoang_cach: np.ndarray) -> np.ndarray:
    """Trọng số 1/(d + eps).

    Phải là hàm đặt tên ở cấp module, KHÔNG được dùng lambda: joblib không
    pickle được lambda, mà backend cần nạp lại mô hình từ file .pkl lúc khởi
    động. Dùng lambda thì train xong không triển khai được.
    """
    return 1.0 / (np.asarray(khoang_cach, dtype=float) + EPS)


def build(n_neighbors: int = 5, metric: str = "euclidean") -> KNeighborsRegressor:
    return KNeighborsRegressor(
        n_neighbors=n_neighbors,
        metric=metric,
        weights=trong_so_nghich_dao,
    )
