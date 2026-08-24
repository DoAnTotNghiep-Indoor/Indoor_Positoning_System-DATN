"""Random Forest — mốc so sánh trung gian.

Có lý do cụ thể để đưa mô hình này vào: đồ án CTK45 báo cáo Random Forest đạt
97,16% với sai số 6,02 m ở bài toán phân lớp điểm tham chiếu. Giữ nó lại cho
phép so sánh trực tiếp với số liệu đã công bố của nhóm trước, dù bài toán đã
chuyển từ phân lớp sang hồi quy.

`n_jobs=-1` dùng hết lõi CPU. Trên Colab thường là 2 lõi, trên máy để bàn nhiều
hơn — đây là chỗ hiếm hoi trong đồ án mà phần cứng thực sự tạo khác biệt.
"""

from __future__ import annotations

from sklearn.ensemble import RandomForestRegressor

from ml import config

TEN = "Random Forest"

LUOI_THAM_SO = {
    "n_estimators": [100, 200, 500],
    "max_depth": [None, 10, 20],
}


def build(n_estimators: int = 200, max_depth: int | None = None) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
    )
