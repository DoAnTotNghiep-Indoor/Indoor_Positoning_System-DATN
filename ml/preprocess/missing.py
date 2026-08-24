"""Bước 7 — Điền giá trị RSSI thiếu bằng hằng số động.

Ô trống nghĩa là AP đó không được phát hiện trong lần quét, cần một con số đại
diện cho "yếu hơn mọi tín hiệu từng đo được".

Thay vì gán cố định -98 (cách phổ biến nhưng có thể trùng hoặc gần tín hiệu yếu
thật), tính `min(RSSI toàn tập) - 1`. Với bộ dữ liệu hiện tại ra -96 dBm. Theo
nghiên cứu tham khảo trên UJIIndoorLoc, cách gán động cải thiện độ chính xác rõ
rệt so với hằng số tuỳ chọn.

Giá trị này PHẢI được ghi vào feature_list.json: backend gặp BSSID không có
trong lần quét cũng phải điền đúng con số đó, nếu không vector lúc dự đoán sẽ
lệch phân bố so với lúc huấn luyện.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_missing_value(fingerprint: pd.DataFrame, ap_cols: list[str]) -> float:
    """Giá trị đại diện cho AP không phát hiện được."""
    nho_nhat = np.nanmin(fingerprint[ap_cols].to_numpy(dtype=float))
    if not np.isfinite(nho_nhat):
        raise ValueError("Không tính được RSSI nhỏ nhất — toàn bộ cột AP đều rỗng.")
    return float(nho_nhat) - 1.0


def fill_missing(
    fingerprint: pd.DataFrame,
    ap_cols: list[str],
    missing_value: float | None = None,
) -> tuple[pd.DataFrame, float, int]:
    """Điền ô trống. Trả về (bảng, giá trị đã dùng, số ô đã điền)."""
    gia_tri = missing_value if missing_value is not None else compute_missing_value(fingerprint, ap_cols)

    so_o_trong = int(fingerprint[ap_cols].isna().sum().sum())
    ket_qua = fingerprint.copy()
    ket_qua[ap_cols] = ket_qua[ap_cols].fillna(gia_tri)

    return ket_qua, gia_tri, so_o_trong
