"""Bước 5 + 6 — Lọc AP kém chất lượng rồi lọc mẫu quét quá nghèo.

Thứ tự này bắt buộc: lọc AP xong mới biết mẫu nào còn quá ít AP hợp lệ. Đảo lại
sẽ giữ nhầm những mẫu chỉ toàn AP nhiễu.

Bước 5 loại AP xuất hiện dưới ngưỡng số lần quét — thường là điểm phát cá nhân
hoặc AP ở toà nhà khác, chỉ làm nhiễu mô hình.
Bước 6 loại mẫu bắt được quá ít AP để định vị tin cậy.
"""

from __future__ import annotations

import pandas as pd

from ml import config


def filter_access_points(
    fingerprint: pd.DataFrame,
    ap_cols: list[str],
    min_appear_rate: float | None = None,
) -> tuple[pd.DataFrame, list[str], pd.Series]:
    """Giữ lại AP xuất hiện đủ thường xuyên.

    Trả về (bảng đã lọc, danh sách AP giữ lại, tỉ lệ xuất hiện của mọi AP).
    Tỉ lệ trả kèm để vẽ biểu đồ biện minh cho ngưỡng đã chọn trong báo cáo.
    """
    rate = min_appear_rate if min_appear_rate is not None else config.MIN_APPEAR_RATE

    so_scan = len(fingerprint)
    ty_le_xuat_hien = (fingerprint[ap_cols].notna().sum() / so_scan).sort_values()

    giu_lai = sorted(ty_le_xuat_hien[ty_le_xuat_hien >= rate].index)
    if not giu_lai:
        raise ValueError(
            f"Ngưỡng {rate:.0%} loại sạch cả {len(ap_cols)} AP. "
            f"Tỉ lệ cao nhất đo được chỉ {ty_le_xuat_hien.max():.1%}."
        )

    cot_meta = [c for c in fingerprint.columns if c not in ap_cols]
    return fingerprint[cot_meta + giu_lai].copy(), giu_lai, ty_le_xuat_hien


def filter_sparse_scans(
    fingerprint: pd.DataFrame,
    ap_cols: list[str],
    min_ap_per_scan: int | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Loại mẫu quét bắt được ít hơn ngưỡng AP hợp lệ."""
    nguong = min_ap_per_scan if min_ap_per_scan is not None else config.MIN_AP_PER_SCAN

    so_ap = fingerprint[ap_cols].notna().sum(axis=1)
    giu = so_ap >= nguong
    ket_qua = fingerprint.loc[giu].reset_index(drop=True)

    thong_ke = {
        "nguong_ap_toi_thieu": nguong,
        "scan_truoc": len(fingerprint),
        "scan_sau": len(ket_qua),
        "scan_bi_loai": int((~giu).sum()),
        "ap_moi_scan_min": int(so_ap.min()),
        "ap_moi_scan_trung_vi": float(so_ap.median()),
        "ap_moi_scan_max": int(so_ap.max()),
    }
    return ket_qua, thong_ke
