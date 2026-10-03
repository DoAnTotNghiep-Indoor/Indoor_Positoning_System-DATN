"""XGBoost Regression — mô hình so sánh (gradient boosting); mô hình đề xuất là kNN k động.

XGBoost không nhận nhãn hai cột nên bọc trong `MultiOutputRegressor`. Lớp bọc
này huấn luyện HAI mô hình riêng biệt, một cho trục x một cho trục y.

Lưới 648 tổ hợp, mỗi tổ hợp một tiến trình (`ml.train`);
dùng `--nhanh` của `ml/train.py` khi thử. Vài tham số tối ưu nằm ở biên lưới,
nhưng nới thêm một nấc chỉ đổi sai số validation dưới 0,1 m.
"""

from __future__ import annotations

from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor

from ml import config

TEN = "XGBoost"

LUOI_THAM_SO = {
    "n_estimators": [100, 300, 500],
    "max_depth": [3, 5, 7],
    "learning_rate": [0.03, 0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.6, 0.8, 1.0],
    "reg_lambda": [0.5, 1, 5, 10],
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
        # Một luồng: cùng tham số và seed mà khác số luồng thì kết quả khác (đo được một
        # dự đoán lệch hơn 10 đơn vị lưới giữa 1 và 16 luồng). `ml.train` chạy song song
        # các tổ hợp lưới nên vẫn dùng hết lõi.
        n_jobs=1,
        verbosity=0,
    )
    return MultiOutputRegressor(nen)


def do_quan_trong_dac_trung(model: MultiOutputRegressor, ten_dac_trung: list[str]) -> dict:
    """Độ quan trọng đặc trưng, tách riêng cho trục x và trục y.

    Trả lời câu hỏi hội đồng hay hỏi: AP nào thực sự đóng góp vào việc định vị. AP
    có độ quan trọng gần 0 ở cả hai trục thì ngưỡng lọc bước 5 nên siết chặt hơn.
    """
    return {
        truc: dict(zip(ten_dac_trung, uoc_luong.feature_importances_.tolist()))
        for truc, uoc_luong in zip(("x", "y"), model.estimators_)
    }
