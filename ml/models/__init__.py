"""Sáu mô hình, cùng một giao diện để so sánh công bằng.

Mỗi module cung cấp `TEN`, `LUOI_THAM_SO` và `build(**tham_so)` trả về estimator
tương thích scikit-learn nhận y hai cột, nhờ đó `ml/train.py` xử lý mọi mô hình
theo đúng một quy trình — điều kiện để bảng so sánh có ý nghĩa.

    cơ sở      kNN, WKNN
    so sánh    Random Forest (mô hình tốt nhất của đồ án gốc CTK45), XGBoost,
               kNN k động — Dynamic-k kNN (dựng trên `fingerprint_knn`)
    triển khai Bộ 3: HistGB + KAN + Transformer (`bo_ba`)

`DANH_SACH` là năm mô hình mà các script đánh giá (`danh_gia_cheo`, `khac_dot`,
`on_dinh`, `toc_do`, `ujiindoorloc`) học lại hàng chục lần. Bộ 3 học mỗi lần vài
phút trên GPU nên chỉ `ml.train` học nó (`HUAN_LUYEN`).
"""

from ml.models import bo_ba, fingerprint_knn_dong, knn, random_forest, wknn, xgboost_model

# Thứ tự chạy: hai mô hình cơ sở trước để có mốc đối chứng.
DANH_SACH = [knn, wknn, random_forest, xgboost_model, fingerprint_knn_dong]
HUAN_LUYEN = [*DANH_SACH, bo_ba]

__all__ = ["knn", "wknn", "random_forest", "xgboost_model", "fingerprint_knn_dong", "bo_ba",
           "DANH_SACH", "HUAN_LUYEN"]
