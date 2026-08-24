"""XGBoost Regression — mô hình chính của đồ án.

XGBoost không nhận nhãn hai cột, nên bọc trong `MultiOutputRegressor`. Lớp bọc
này huấn luyện **hai mô hình riêng biệt**, một cho trục x một cho trục y — đúng
thiết kế `model_x`, `model_y` ở mục 2.4, chỉ là không phải tự viết vòng lặp.

Lưới tham số dưới đây chép đúng tài liệu thiết kế: 3 x 3 x 3 x 2 x 2 x 3 = 324
tổ hợp. Với 547 mẫu huấn luyện thì quét hết mất vài phút; dùng `--nhanh` trong
`ml/train.py` để chạy lưới rút gọn khi đang thử nghiệm.
"""

from __future__ import annotations

from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor

from ml import config

TEN = "XGBoost"

# Lưới đầy đủ theo mục 2.4 tài liệu thiết kế
LUOI_THAM_SO = {
    "n_estimators": [100, 300, 500],
    "max_depth": [3, 5, 7],
    "learning_rate": [0.03, 0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
    "reg_lambda": [1, 5, 10],
}

# Lưới rút gọn cho lúc thử nghiệm nhanh — 2 x 2 x 2 = 8 tổ hợp
LUOI_NHANH = {
    "n_estimators": [300, 500],
    "max_depth": [3, 5],
    "learning_rate": [0.05, 0.1],
}


def build(
    n_estimators: int = 300,
    max_depth: int = 5,
    learning_rate: float = 0.05,
    subsample: float = 1.0,
    colsample_bytree: float = 1.0,
    reg_lambda: float = 1.0,
) -> MultiOutputRegressor:
    nen = XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        reg_lambda=reg_lambda,
        random_state=config.RANDOM_STATE,
        objective="reg:squarederror",
        n_jobs=-1,
        verbosity=0,
    )
    return MultiOutputRegressor(nen)


def do_quan_trong_dac_trung(model: MultiOutputRegressor, ten_dac_trung: list[str]) -> dict:
    """Độ quan trọng đặc trưng, tách riêng cho trục x và trục y.

    Biểu đồ này trả lời được câu hỏi hội đồng hay hỏi: AP nào thực sự đóng góp
    vào việc định vị. Nếu một AP có độ quan trọng gần 0 ở cả hai trục thì ngưỡng
    lọc ở bước 5 nên siết chặt hơn.
    """
    return {
        truc: dict(zip(ten_dac_trung, uoc_luong.feature_importances_.tolist()))
        for truc, uoc_luong in zip(("x", "y"), model.estimators_)
    }
