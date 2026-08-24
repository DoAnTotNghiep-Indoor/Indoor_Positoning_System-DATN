"""Đo chất lượng định vị.

Chỉ số chính là **sai số khoảng cách** tính bằng mét:

    error = sqrt((x_du_doan - x_that)^2 + (y_du_doan - y_that)^2)

Đây là con số duy nhất hội đồng quan tâm — "sai số trung bình 3,2 mét" nói lên
điều gì đó, còn "R² = 0,94" thì không.

Ngoài ra ghi thêm MAE/RMSE tách theo từng trục để biết mô hình lệch nhiều hơn
theo chiều dài hay chiều ngang toà nhà, và thời gian dự đoán một mẫu vì yêu cầu
phi chức năng đặt mốc dưới 200 ms cho cả đường đi từ lúc nhận RSSI tới lúc trả
toạ độ.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

# Các mốc phần trăm dùng cho đường CDF trong báo cáo
CDF_PERCENTILES = (50, 75, 90)


def khoang_cach_loi(y_that: np.ndarray, y_du_doan: np.ndarray) -> np.ndarray:
    """Sai số khoảng cách Euclid của từng mẫu, đơn vị mét."""
    y_that = np.asarray(y_that, dtype=float)
    y_du_doan = np.asarray(y_du_doan, dtype=float)
    return np.sqrt(((y_du_doan - y_that) ** 2).sum(axis=1))


def do_thoi_gian_du_doan(model, X: np.ndarray, so_lan: int = 50) -> float:
    """Thời gian dự đoán trung bình cho MỘT mẫu, tính bằng mili giây.

    Đo từng mẫu một chứ không đo cả lô: lúc chạy thật backend nhận từng lần quét
    rời rạc, dự đoán theo lô sẽ cho con số đẹp hơn thực tế nhiều lần.
    """
    X = np.asarray(X, dtype=float)
    mau = X[: min(so_lan, len(X))]

    model.predict(mau[:1])  # chạy nóng, bỏ lần đầu vì có chi phí khởi tạo

    bat_dau = time.perf_counter()
    for i in range(len(mau)):
        model.predict(mau[i : i + 1])
    tong = time.perf_counter() - bat_dau

    return tong / len(mau) * 1000


def danh_gia(
    y_that: np.ndarray,
    y_du_doan: np.ndarray,
    ten_mo_hinh: str = "",
    thoi_gian_ms: float | None = None,
) -> dict:
    """Toàn bộ chỉ số cho một mô hình trên một tập dữ liệu."""
    loi = khoang_cach_loi(y_that, y_du_doan)
    y_that = np.asarray(y_that, dtype=float)
    y_du_doan = np.asarray(y_du_doan, dtype=float)
    lech = y_du_doan - y_that

    ket_qua = {
        "mo_hinh": ten_mo_hinh,
        "so_mau": int(len(loi)),
        # Sai số khoảng cách (mét) — chỉ số chính
        "loi_trung_binh": float(loi.mean()),
        "loi_trung_vi": float(np.median(loi)),
        "loi_nho_nhat": float(loi.min()),
        "loi_lon_nhat": float(loi.max()),
        "loi_do_lech_chuan": float(loi.std()),
        # MAE / RMSE theo từng trục
        "mae_x": float(np.abs(lech[:, 0]).mean()),
        "mae_y": float(np.abs(lech[:, 1]).mean()),
        "rmse_x": float(np.sqrt((lech[:, 0] ** 2).mean())),
        "rmse_y": float(np.sqrt((lech[:, 1] ** 2).mean())),
    }

    # CDF: p% số mẫu có sai số dưới ngưỡng này
    for p in CDF_PERCENTILES:
        ket_qua[f"cdf_{p}"] = float(np.percentile(loi, p))

    if thoi_gian_ms is not None:
        ket_qua["thoi_gian_du_doan_ms"] = float(thoi_gian_ms)

    return ket_qua


def bang_so_sanh(ket_qua: list[dict]) -> pd.DataFrame:
    """Gộp kết quả nhiều mô hình thành bảng, xếp theo sai số trung bình."""
    df = pd.DataFrame(ket_qua)
    if "loi_trung_binh" in df.columns:
        df = df.sort_values("loi_trung_binh").reset_index(drop=True)
    return df


def loi_theo_diem(
    rp_id: pd.Series,
    y_that: np.ndarray,
    y_du_doan: np.ndarray,
) -> pd.DataFrame:
    """Sai số trung bình tại từng điểm tham chiếu.

    Dùng vẽ bản đồ nhiệt lỗi — chỗ nào sai nhiều thường là chỗ ít AP phủ tới
    hoặc bị che khuất, và đó là thông tin cụ thể để cải thiện, khác hẳn một con
    số trung bình chung chung.
    """
    loi = khoang_cach_loi(y_that, y_du_doan)
    return (
        pd.DataFrame(
            {
                "rp_id": np.asarray(rp_id),
                "loi": loi,
                "x_that": np.asarray(y_that)[:, 0],
                "y_that": np.asarray(y_that)[:, 1],
            }
        )
        .groupby("rp_id")
        .agg(
            so_mau=("loi", "size"),
            loi_trung_binh=("loi", "mean"),
            loi_lon_nhat=("loi", "max"),
            x=("x_that", "first"),
            y=("y_that", "first"),
        )
        .reset_index()
        .sort_values("loi_trung_binh", ascending=False)
    )


def duong_cdf(loi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Toạ độ để vẽ đường CDF: (sai số đã sắp xếp, tỉ lệ tích luỹ %)."""
    da_sap = np.sort(np.asarray(loi, dtype=float))
    ty_le = np.arange(1, len(da_sap) + 1) / len(da_sap) * 100
    return da_sap, ty_le
