"""Bước 2 + 3 — Gom theo lần quét rồi chuyển từ dạng dài sang bảng vân tay.

Bước 2: mỗi lần quét thành một `scan_id`, kèm thông tin mô tả (rp_id, thiết bị,
người thu, hướng đặt máy).
Bước 3: pivot thành bảng rộng — mỗi dòng một lần quét, mỗi cột một BSSID.

Khác bản Colab: thứ tự cột BSSID được sắp xếp tường minh bằng `sorted()` thay vì
phụ thuộc vào hành vi mặc định của `pivot_table`. Thứ tự này chính là hợp đồng
dữ liệu với backend nên không được để nó phụ thuộc phiên bản pandas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml import config


def build_scan_id(df: pd.DataFrame, multi_device: bool | None = None) -> pd.DataFrame:
    """Gán `scan_id` cho từng lần quét.

    Cột `Time` đã kiểm chứng là duy nhất theo từng lần quét khi thu bằng một máy.
    Khi thu bằng nhiều máy cùng lúc thì `Time` có thể trùng, lúc đó ghép thêm mã
    người thu. Tham số `multi_device=None` nghĩa là tự phát hiện.
    """
    df = df.copy()

    if multi_device is None:
        multi_device = df[config.COL_DEVICE].nunique() > 1

    if multi_device:
        df["scan_id"] = (
            df[config.COL_TIME].astype(str)
            + "_"
            + df[config.COL_COLLECTOR].astype(str)
            + "_"
            + df[config.COL_DEVICE].astype(str)
        )
    else:
        df["scan_id"] = df[config.COL_TIME].astype(str)

    # Một AP không được đo hai lần trong cùng một lần quét, nếu không pivot sẽ
    # âm thầm lấy trung bình và làm sai dữ liệu.
    trung = df.duplicated(subset=["scan_id", config.COL_BSSID]).sum()
    if trung:
        raise ValueError(
            f"Phát hiện {trung} cặp (scan_id, BSSID) trùng lặp. "
            f"Nếu dữ liệu thu từ nhiều máy, gọi lại với multi_device=True."
        )

    return df


def build_scan_meta(df: pd.DataFrame) -> pd.DataFrame:
    """Bảng mô tả mỗi lần quét — một dòng một `scan_id`."""
    meta = (
        df.groupby("scan_id")
        .agg(
            rp_id=(config.COL_RP, "first"),
            device_id=(config.COL_DEVICE, "first"),
            collector_id=(config.COL_COLLECTOR, "first"),
            total_ap_scanned=(config.COL_TOTAL_AP, "first"),
            azimuth_deg=(config.COL_AZIMUTH, "first"),
        )
        .reset_index()
    )

    # Cột gốc ghi đơn vị độ nhưng giá trị thực là radian trong [-pi, pi].
    if config.AZIMUTH_IS_RADIAN:
        meta["azimuth_deg"] = np.degrees(meta["azimuth_deg"])

    return meta


def to_wide(df: pd.DataFrame, scan_meta: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Pivot sang bảng vân tay. Trả về (bảng, danh sách cột AP đã sắp xếp)."""
    rong = df.pivot_table(
        index="scan_id",
        columns=config.COL_BSSID,
        values=config.COL_RSSI,
        aggfunc="mean",
    )

    # Thứ tự cột là hợp đồng dữ liệu — cố định tường minh, không phó mặc pandas.
    ap_cols = sorted(rong.columns)
    rong = rong[ap_cols]

    fingerprint = scan_meta.merge(rong, left_on="scan_id", right_index=True, how="left")
    return fingerprint, ap_cols
