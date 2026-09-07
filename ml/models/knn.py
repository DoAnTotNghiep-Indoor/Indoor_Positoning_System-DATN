"""kNN — mô hình cơ sở đối chứng thứ nhất.

Dự đoán toạ độ bằng trung bình toạ độ của k mẫu có vân tay gần nhất; không học
tham số nào, toàn bộ tập train chính là mô hình.

Baseline bắt buộc, và nó đã bác bỏ giả thiết ban đầu: XGBoost KHÔNG thắng được
kNN (7,16 m so với 5,22 m). Nguyên nhân ở dữ liệu chứ không ở chỉnh tham số —
chỉ có 39 toạ độ khác nhau nên bài toán gần với phân lớp, đúng chỗ hồi quy cây
yếu nhất. Xem mục 2.4.1 của `docs/Phan_Tich_Thiet_Ke_He_Thong.md`.
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
