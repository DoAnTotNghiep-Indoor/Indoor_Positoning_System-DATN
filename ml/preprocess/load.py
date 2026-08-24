"""Bước 1 — Nạp dữ liệu thô và kiểm tra tính hợp lệ.

Khác bản Colab: không in ra rồi thôi, mà kiểm tra bằng assert. Dữ liệu sai định
dạng phải dừng ngay tại đây, đừng để lỗi lan xuống tận bước chuẩn hoá rồi mới
phát hiện.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml import config


def load_raw(csv_path: Path | str | None = None) -> pd.DataFrame:
    """Đọc file RSSI thô, kiểm tra đủ cột và không rỗng."""
    path = Path(csv_path) if csv_path else config.RAW_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy dữ liệu thô: {path}\n"
            f"Đặt file combined_data.csv vào {config.RAW_DIR}"
        )

    df = pd.read_csv(path)

    thieu = [c for c in config.REQUIRED_RAW_COLS if c not in df.columns]
    if thieu:
        raise ValueError(
            f"File thô thiếu {len(thieu)} cột bắt buộc: {thieu}\n"
            f"Cột đang có: {list(df.columns)}"
        )

    if df.empty:
        raise ValueError(f"File thô rỗng: {path}")

    return df


def describe_raw(df: pd.DataFrame) -> dict:
    """Thống kê nhanh dùng cho log pipeline và cho chương mô tả dữ liệu."""
    rssi = df[config.COL_RSSI]
    return {
        "so_dong": len(df),
        "so_lan_quet": df[config.COL_TIME].nunique(),
        "so_rp": df[config.COL_RP].nunique(),
        "so_bssid": df[config.COL_BSSID].nunique(),
        "so_thiet_bi": df[config.COL_DEVICE].nunique(),
        "so_nguoi_thu": df[config.COL_COLLECTOR].nunique(),
        "rssi_min": float(rssi.min()),
        "rssi_max": float(rssi.max()),
        "so_dong_trung_lap": int(df.duplicated().sum()),
    }
