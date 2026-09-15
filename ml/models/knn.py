"""kNN — mô hình cơ sở đối chứng thứ nhất.

Dự đoán toạ độ bằng trung bình toạ độ của k mẫu có vân tay gần nhất; toàn bộ tập
train chính là mô hình. Dữ liệu chỉ có 39 toạ độ nên bài toán gần phân lớp — lý
do nó thắng XGBoost khi chia ngẫu nhiên, xem `ml/on_dinh.py`.
"""

from __future__ import annotations

from sklearn.neighbors import KNeighborsRegressor

TEN = "kNN"

# Có cả k=1 và k=2: lưới cũ bắt đầu từ 3 và tối ưu rơi đúng vào biên dưới đó.
LUOI_THAM_SO = {
    "n_neighbors": [1, 2, 3, 5, 7, 9, 11],
    "metric": ["euclidean", "manhattan"],
}


def build(n_neighbors: int = 5, metric: str = "euclidean") -> KNeighborsRegressor:
    return KNeighborsRegressor(
        n_neighbors=n_neighbors,
        metric=metric,
        weights="uniform",
    )
