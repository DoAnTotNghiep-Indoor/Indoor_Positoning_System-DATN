"""Bước 10 — Chuẩn hoá min-max, fit CHỈ trên tập train.

Quy tắc bắt buộc chống rò rỉ dữ liệu:
    fit scaler trên train  ->  transform train, validation, test bằng scaler đó.
TUYỆT ĐỐI không fit trên toàn bộ dataset rồi mới chia.

Giá trị của validation và test được phép nằm ngoài khoảng [0, 1]. Đó không phải
lỗi mà là bằng chứng scaler chưa từng nhìn thấy hai tập đó — bộ dữ liệu hiện tại
cho giá trị lớn nhất 1,147, nghĩa là tập test có tín hiệu mạnh hơn mọi mẫu train.

`scaler.pkl` phải đi kèm `feature_list.json`: backend nạp lại đúng scaler này để
tiền xử lý lúc dự đoán khớp với lúc huấn luyện.
"""

from __future__ import annotations

import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def fit_scaler(fingerprint: pd.DataFrame, ap_cols: list[str]) -> MinMaxScaler:
    """Học tham số chuẩn hoá từ tập train."""
    train = fingerprint[fingerprint["split"] == "train"]
    if train.empty:
        raise ValueError("Không có mẫu nào thuộc tập train để fit scaler.")

    # Fit trên mảng numpy chứ không phải DataFrame, để scaler KHÔNG ghi nhớ tên
    # cột. Backend lúc dự đoán dựng vector số thuần từ feature_list.json; nếu
    # scaler mang theo tên cột thì sklearn sẽ cảnh báo mỗi lần transform, và tệ
    # hơn là tạo cảm giác an toàn giả — thứ tự cột mới là thứ phải kiểm soát,
    # và nó đã được feature_list.json giữ.
    scaler = MinMaxScaler()
    scaler.fit(train[ap_cols].to_numpy(dtype=float))
    return scaler


def apply_scaler(
    fingerprint: pd.DataFrame,
    ap_cols: list[str],
    scaler: MinMaxScaler,
) -> pd.DataFrame:
    """Áp scaler cho cả ba tập."""
    ket_qua = fingerprint.copy()
    ket_qua[ap_cols] = scaler.transform(ket_qua[ap_cols].to_numpy(dtype=float))
    return ket_qua


def scale_dataset(
    fingerprint: pd.DataFrame,
    ap_cols: list[str],
) -> tuple[pd.DataFrame, MinMaxScaler, dict]:
    """Fit trên train rồi transform toàn bộ. Trả về (bảng, scaler, thống kê)."""
    scaler = fit_scaler(fingerprint, ap_cols)
    ket_qua = apply_scaler(fingerprint, ap_cols, scaler)

    gia_tri = ket_qua[ap_cols]
    thong_ke = {
        "nho_nhat": float(gia_tri.to_numpy().min()),
        "lon_nhat": float(gia_tri.to_numpy().max()),
        "so_dac_trung": len(ap_cols),
    }
    return ket_qua, scaler, thong_ke
