"""kNN — mô hình cơ sở đối chứng thứ nhất.

Dự đoán toạ độ bằng trung bình cộng toạ độ của k mẫu huấn luyện có vân tay RSSI
gần nhất. Không có tham số nào được học; toàn bộ tập train chính là mô hình.

Đây là baseline bắt buộc: nếu XGBoost không thắng được kNN thì mọi lập luận về
"cải tiến bằng học máy" đều rỗng. Tài liệu thiết kế đặt mục tiêu XGBoost phải
thấp hơn baseline ít nhất 10-20% sai số trung bình.
"""

from __future__ import annotations

from sklearn.neighbors import KNeighborsRegressor

TEN = "kNN"

LUOI_THAM_SO = {
    "n_neighbors": [3, 5, 7, 9, 11],
    "metric": ["euclidean", "manhattan"],
}


def build(n_neighbors: int = 5, metric: str = "euclidean") -> KNeighborsRegressor:
    return KNeighborsRegressor(
        n_neighbors=n_neighbors,
        metric=metric,
        weights="uniform",
    )
