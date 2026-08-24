"""Bốn mô hình hồi quy toạ độ, cùng một giao diện để so sánh công bằng.

Mỗi module trong gói này cung cấp đúng hai thứ:

    TEN         tên hiển thị trong bảng so sánh
    LUOI_THAM_SO  dict {tên tham số: [các giá trị thử]}
    build(**tham_so) -> estimator tương thích scikit-learn, nhận y hai cột

Nhờ giao diện chung, `ml/train.py` không cần biết mô hình nào là gì — nó quét
lưới, chọn cấu hình tốt nhất trên tập validation, rồi đánh giá trên tập test
theo đúng một quy trình cho cả bốn. Đây là điều kiện để bảng so sánh trong báo
cáo có ý nghĩa.

kNN, WKNN và Random Forest nhận thẳng y hai cột. XGBoost thì không, nên
`xgboost_model` bọc trong MultiOutputRegressor để huấn luyện riêng model_x và
model_y đúng như thiết kế ở mục 2.4.
"""

from ml.models import knn, random_forest, wknn, xgboost_model

# Thứ tự này là thứ tự chạy: hai mô hình cơ sở trước để có mốc đối chứng,
# rồi mới tới các mô hình mạnh hơn.
DANH_SACH = [knn, wknn, random_forest, xgboost_model]

__all__ = ["knn", "wknn", "random_forest", "xgboost_model", "DANH_SACH"]
