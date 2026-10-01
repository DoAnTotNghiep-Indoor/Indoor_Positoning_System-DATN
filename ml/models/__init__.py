"""Năm mô hình, cùng một giao diện để so sánh công bằng.

Mỗi module cung cấp `TEN`, `LUOI_THAM_SO` và `build(**tham_so)` trả về estimator
tương thích scikit-learn nhận y hai cột, nhờ đó `ml/train.py` xử lý mọi mô hình
theo đúng một quy trình — điều kiện để bảng so sánh có ý nghĩa.

    cơ sở      kNN, WKNN
    so sánh    Random Forest (mô hình tốt nhất của đồ án gốc CTK45), XGBoost
    đề xuất    kNN k động — Dynamic-k kNN (dựng trên `fingerprint_knn`)
"""

from ml.models import fingerprint_knn_dong, knn, random_forest, wknn, xgboost_model

# Thứ tự chạy: hai mô hình cơ sở trước để có mốc đối chứng.
DANH_SACH = [knn, wknn, random_forest, xgboost_model, fingerprint_knn_dong]

__all__ = ["knn", "wknn", "random_forest", "xgboost_model", "fingerprint_knn_dong", "DANH_SACH"]
