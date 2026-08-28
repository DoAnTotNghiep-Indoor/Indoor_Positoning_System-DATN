"""Năm mô hình, cùng một giao diện để so sánh công bằng.

Mỗi module cung cấp `TEN`, `LUOI_THAM_SO` và `build(**tham_so)` trả về estimator
tương thích scikit-learn nhận y hai cột. Nhờ đó `ml/train.py` xử lý mọi mô hình
theo đúng một quy trình — điều kiện để bảng so sánh trong báo cáo có ý nghĩa.
"""

from ml.models import fingerprint_knn, knn, random_forest, wknn, xgboost_model

# Thứ tự chạy: hai mô hình cơ sở trước để có mốc đối chứng.
DANH_SACH = [knn, wknn, random_forest, xgboost_model, fingerprint_knn]

__all__ = [
    "knn", "wknn", "random_forest", "xgboost_model", "fingerprint_knn", "DANH_SACH",
]
