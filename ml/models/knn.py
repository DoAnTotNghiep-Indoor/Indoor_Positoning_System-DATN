"""kNN — mô hình cơ sở đối chứng thứ nhất.

Dự đoán toạ độ bằng trung bình cộng toạ độ của k mẫu huấn luyện có vân tay RSSI
gần nhất. Không có tham số nào được học; toàn bộ tập train chính là mô hình.

Đây là baseline bắt buộc, và nó đã bác bỏ giả thiết ban đầu của đồ án: XGBoost
KHÔNG thắng được kNN (6,48 m so với 5,15 m), trong khi tài liệu thiết kế đặt
mục tiêu thấp hơn baseline 10-20%. Nguyên nhân nằm ở dữ liệu chứ không ở việc
chỉnh tham số — chỉ có 39 toạ độ khác nhau vì mẫu thu đúng tại các điểm tham
chiếu, nên bài toán gần với phân lớp hơn là hồi quy liên tục, mà đó lại là chỗ
hồi quy cây quyết định yếu nhất. Kết quả này là một phần nội dung của đồ án,
không phải lỗi cần giấu: xem mục 2.4.1 của `docs/Phan_Tich_Thiet_Ke_He_Thong.md`.
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
