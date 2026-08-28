"""12 bước tiền xử lý, xếp theo đúng thứ tự `ml/pipeline.py` gọi.

Thứ tự không tuỳ tiện, ba chỗ bắt buộc:

- Bước 5 trước bước 6: lọc AP xong mới biết mẫu nào còn quá ít AP hợp lệ.
- Bước 9 trước bước 10: chia tập trước khi chuẩn hoá. Đảo lại là rò rỉ dữ liệu —
  scaler học được cả phân bố tập kiểm thử, kết quả đẹp giả tạo và sụp khi chạy thật.
- Bước 9 trước bước 8: Hampel chỉ chạy trên tập train, xem `config.HAMPEL_ON_TRAIN_ONLY`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from ml import config


# ========================= Bước 1 — nạp dữ liệu thô =========================

def load_raw(csv_path: Path | str | None = None) -> pd.DataFrame:
    return pd.read_csv(Path(csv_path) if csv_path else config.RAW_CSV)


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


# ================== Bước 2 + 3 — gom theo lần quét rồi pivot ==================

def build_scan_id(df: pd.DataFrame) -> pd.DataFrame:
    """Gán `scan_id` cho từng lần quét.

    Cột `Time` đã kiểm chứng là duy nhất theo từng lần quét khi thu bằng một máy.
    Thu bằng nhiều máy cùng lúc thì `Time` có thể trùng và pivot sẽ âm thầm lấy
    trung bình — lúc đó phải ghép thêm mã người thu vào khoá.
    """
    df = df.copy()
    df["scan_id"] = df[config.COL_TIME].astype(str)
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
    """Pivot sang bảng vân tay. Trả về (bảng, danh sách cột AP đã sắp xếp).

    Thứ tự cột sắp xếp tường minh bằng `sorted()` chứ không phó mặc hành vi mặc
    định của `pivot_table`: thứ tự này là hợp đồng dữ liệu với backend nên không
    được để nó phụ thuộc phiên bản pandas.
    """
    rong = df.pivot_table(
        index="scan_id",
        columns=config.COL_BSSID,
        values=config.COL_RSSI,
        aggfunc="mean",
    )

    ap_cols = sorted(rong.columns)
    rong = rong[ap_cols]

    fingerprint = scan_meta.merge(rong, left_on="scan_id", right_index=True, how="left")
    return fingerprint, ap_cols


# ===================== Bước 4 — ghép toạ độ thật (x, y) =====================
#
# File thô KHÔNG chứa toạ độ cục bộ (GPS trong nhà gần như không đổi — biên độ
# dao động đo được chỉ khoảng 22 m, vô dụng cho bài toán này). Toạ độ lấy từ
# data/reference/reference_points.csv, nguồn gốc là Bảng 4 trang 46 đồ án CTK45.
# Không có (x, y) thì chỉ phân lớp được điểm tham chiếu chứ không hồi quy được
# toạ độ, tức mất luôn cải tiến chính so với đồ án cũ.

def load_reference_points(csv_path: Path | str | None = None) -> pd.DataFrame:
    path = Path(csv_path) if csv_path else config.REFERENCE_POINTS_CSV

    # utf-8-sig để nuốt luôn BOM nếu file được sửa bằng Excel.
    rp = pd.read_csv(path, encoding="utf-8-sig")[["rp_id", "x", "y"]].copy()
    rp["x"] = pd.to_numeric(rp["x"], errors="coerce")
    rp["y"] = pd.to_numeric(rp["y"], errors="coerce")
    return rp


def attach_coordinates(
    fingerprint: pd.DataFrame,
    reference_points: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Ghép (x, y) vào bảng vân tay, bỏ những mẫu chưa đo toạ độ."""
    rp = reference_points if reference_points is not None else load_reference_points()

    truoc = len(fingerprint)
    ket_qua = fingerprint.merge(rp, on="rp_id", how="left")

    thieu = ket_qua["x"].isna() | ket_qua["y"].isna()
    rp_thieu = sorted(ket_qua.loc[thieu, "rp_id"].unique())
    so_thieu = int(thieu.sum())
    ket_qua = ket_qua.loc[~thieu].reset_index(drop=True)

    thong_ke = {
        "scan_truoc_khi_ghep": truoc,
        "scan_co_toa_do": len(ket_qua),
        "scan_bi_bo": so_thieu,
        "rp_chua_do": rp_thieu,
    }
    return ket_qua, thong_ke


# ============== Bước 5 + 6 — lọc AP hiếm gặp rồi lọc mẫu quá nghèo ==============

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

    ty_le_xuat_hien = (fingerprint[ap_cols].notna().sum() / len(fingerprint)).sort_values()
    giu_lai = sorted(ty_le_xuat_hien[ty_le_xuat_hien >= rate].index)

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


# ======================== Bước 7 — điền RSSI thiếu ========================
#
# Ô trống nghĩa là AP đó không được phát hiện trong lần quét, cần một con số đại
# diện cho "yếu hơn mọi tín hiệu từng đo được": min(RSSI toàn tập) - 1, với bộ
# dữ liệu hiện tại ra -96 dBm. Cách gán động này tốt hơn hằng số cố định -98 (có
# thể trùng tín hiệu yếu thật).
#
# Giá trị PHẢI được ghi vào feature_list.json: backend gặp BSSID không có trong
# lần quét cũng phải điền đúng con số đó, nếu không vector lúc dự đoán sẽ lệch
# phân bố so với lúc huấn luyện.

def compute_missing_value(fingerprint: pd.DataFrame, ap_cols: list[str]) -> float:
    return float(np.nanmin(fingerprint[ap_cols].to_numpy(dtype=float))) - 1.0


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


# ================= Bước 8 — lọc nhiễu bằng Hampel filter (MAD) =================
#
# Với mỗi AP, trong từng nhóm cùng rp_id, giá trị lệch quá k * MAD so với trung
# vị bị thay bằng chính trung vị đó. Giảm nhiễu tức thời (đa đường, che khuất,
# người đi ngang) mà KHÔNG xoá mẫu — quan trọng khi mỗi điểm chỉ có ~20 lần quét.

def hampel_filter(
    df: pd.DataFrame,
    ap_cols: list[str],
    group_col: str = "rp_id",
    k: float | None = None,
) -> tuple[pd.DataFrame, int]:
    """Thay giá trị ngoại lai bằng trung vị nhóm. Trả về (bảng, số ô bị thay)."""
    he_so = k if k is not None else config.HAMPEL_K

    gia_tri = df[ap_cols]
    nhom = df[group_col]

    trung_vi = gia_tri.groupby(nhom).transform("median")
    do_lech = (gia_tri - trung_vi).abs()
    mad = do_lech.groupby(nhom).transform("median") * config.MAD_SCALE

    # mad == 0 nghĩa là quá nửa số mẫu trong nhóm giống hệt nhau; lúc đó ngưỡng
    # bằng 0 sẽ đánh dấu nhầm mọi giá trị khác biệt dù nhỏ, nên bỏ qua nhóm đó.
    ngoai_lai = (mad > 0) & (do_lech > he_so * mad)

    ket_qua = df.copy()
    ket_qua[ap_cols] = gia_tri.where(~ngoai_lai, trung_vi)

    return ket_qua, int(ngoai_lai.to_numpy().sum())


# ============= Bước 9 — chia train / validation / test theo rp_id =============
#
# Tài liệu thiết kế còn yêu cầu hai phép chia nữa — để riêng một thiết bị
# (device_holdout) và để riêng khoảng thời gian cuối (time_holdout). Cả hai KHÔNG
# chạy được với dữ liệu hiện tại: chỉ có một máy, và mỗi điểm tham chiếu chỉ được
# đo đúng một buổi nên tách theo thời gian cũng là tách theo vị trí. Viết lại sau
# khi đo bổ sung.

def split_random(fingerprint: pd.DataFrame) -> pd.DataFrame:
    # Phân tầng cần mỗi lớp có ít nhất 2 mẫu ở mỗi lần cắt.
    dem = fingerprint["rp_id"].value_counts()
    phan_tang = fingerprint["rp_id"] if dem.min() >= 3 else None

    ty_le_tam = config.TEST_SIZE + config.VALIDATION_SIZE
    train, tam = train_test_split(
        fingerprint,
        test_size=ty_le_tam,
        stratify=phan_tang,
        random_state=config.RANDOM_STATE,
    )

    # Phải kiểm tra lại trên tập tạm: nó nhỏ hơn nhiều nên một điểm có thể rơi
    # xuống còn 1 mẫu, lúc đó sklearn ném lỗi thay vì phân tầng.
    dem_tam = tam["rp_id"].value_counts()
    phan_tang_tam = tam["rp_id"] if (phan_tang is not None and dem_tam.min() >= 2) else None

    val, test = train_test_split(
        tam,
        test_size=config.TEST_SIZE / ty_le_tam,
        stratify=phan_tang_tam,
        random_state=config.RANDOM_STATE,
    )

    return pd.concat(
        [
            train.assign(split="train"),
            val.assign(split="validation"),
            test.assign(split="test"),
        ],
        ignore_index=True,
    )


def split_dataset(fingerprint: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    ket_qua = split_random(fingerprint)

    thong_ke = {
        "chien_luoc": "random",
        "so_mau": ket_qua["split"].value_counts().to_dict(),
        "so_rp_moi_tap": ket_qua.groupby("split")["rp_id"].nunique().to_dict(),
    }

    # Điểm tham chiếu chỉ có trong test mà không có trong train là không học được.
    rp_train = set(ket_qua.loc[ket_qua["split"] == "train", "rp_id"])
    rp_test = set(ket_qua.loc[ket_qua["split"] == "test", "rp_id"])
    thieu = sorted(rp_test - rp_train)
    if thieu:
        thong_ke["canh_bao"] = f"{len(thieu)} điểm chỉ có trong test, không có trong train: {thieu}"

    return ket_qua, thong_ke


# ============ Bước 10 — chuẩn hoá min-max, fit CHỈ trên tập train ============
#
#     fit scaler trên train  ->  transform train, validation, test bằng scaler đó.
#
# Giá trị của validation và test được phép nằm ngoài [0, 1]. Đó không phải lỗi mà
# là bằng chứng scaler chưa từng nhìn thấy hai tập đó — bộ dữ liệu hiện tại cho
# giá trị lớn nhất 1,147, nghĩa là tập test có tín hiệu mạnh hơn mọi mẫu train.
#
# scaler.pkl phải đi kèm feature_list.json: backend nạp lại đúng scaler này để
# tiền xử lý lúc dự đoán khớp với lúc huấn luyện.

def fit_scaler(fingerprint: pd.DataFrame, ap_cols: list[str]) -> MinMaxScaler:
    train = fingerprint[fingerprint["split"] == "train"]

    # Fit trên mảng numpy chứ không phải DataFrame, để scaler KHÔNG ghi nhớ tên
    # cột: backend dựng vector số thuần từ feature_list.json, mang theo tên cột
    # chỉ tạo cảm giác an toàn giả — thứ tự cột mới là thứ phải kiểm soát.
    scaler = MinMaxScaler()
    scaler.fit(train[ap_cols].to_numpy(dtype=float))
    return scaler


def apply_scaler(
    fingerprint: pd.DataFrame,
    ap_cols: list[str],
    scaler: MinMaxScaler,
) -> pd.DataFrame:
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

    gia_tri = ket_qua[ap_cols].to_numpy()
    thong_ke = {
        "nho_nhat": float(gia_tri.min()),
        "lon_nhat": float(gia_tri.max()),
        "so_dac_trung": len(ap_cols),
    }
    return ket_qua, scaler, thong_ke
