"""12 bước tiền xử lý. Hàm xếp theo số bước, `ml/pipeline.py` gọi theo thứ tự
1-2-3-4-**9**-5-6-7-8-10.

Bước 9 chạy sớm vì bốn bước sau nó đều học một tham số từ dữ liệu — bộ cột giữ
lại (5), giá trị điền thiếu (7), trung vị nhóm (8), min/max của scaler (10) — và
cả bốn chỉ được nhìn tập train. Bước 5 vẫn phải trước 6: lọc AP xong mới biết
mẫu nào còn quá ít AP hợp lệ.
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
    """Gán `scan_id` cho từng lần quét. `Time` duy nhất theo lần quét khi thu bằng
    MỘT máy; thu nhiều máy cùng lúc thì `Time` có thể trùng và pivot âm thầm lấy
    trung bình.
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

    Thứ tự cột sắp bằng `sorted()` tường minh vì đây là hợp đồng dữ liệu với
    backend, không được phụ thuộc phiên bản pandas.
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
# File thô KHÔNG có toạ độ cục bộ (GPS trong nhà chỉ dao động ~22 m). Lấy từ
# reference_points.csv, nguồn là Bảng 4 trang 46 đồ án CTK45. Không có (x, y)
# thì chỉ phân lớp được điểm chứ không hồi quy được toạ độ.

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
    tinh_tren: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, list[str], pd.Series]:
    """Giữ lại AP xuất hiện đủ thường xuyên. Trả về (bảng đã lọc, danh sách AP giữ
    lại, tỉ lệ xuất hiện của mọi AP) — tỉ lệ trả kèm để vẽ biểu đồ biện minh cho
    ngưỡng đã chọn trong báo cáo.

    `tinh_tren` giới hạn phần dữ liệu dùng để TÍNH tỉ lệ; bộ cột chọn ra vẫn áp
    cho toàn bảng. Truyền tập train vào để việc chọn đặc trưng không nhìn val/test.
    """
    rate = min_appear_rate if min_appear_rate is not None else config.MIN_APPEAR_RATE
    nguon = fingerprint if tinh_tren is None else tinh_tren

    ty_le_xuat_hien = (nguon[ap_cols].notna().sum() / len(nguon)).sort_values()
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
# Ô trống = AP không được phát hiện, cần số đại diện cho "yếu hơn mọi tín hiệu
# từng đo": min(RSSI) - 1, ra -96 dBm; hơn hằng số -98 vốn có thể trùng tín
# hiệu yếu thật. PHẢI ghi vào feature_list.json, nếu không vector lúc dự đoán
# lệch phân bố so với lúc huấn luyện.

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
# Với mỗi AP, trong từng nhóm cùng rp_id, giá trị lệch quá k * MAD so với trung
# vị bị thay bằng chính trung vị đó — giảm nhiễu tức thời mà KHÔNG xoá mẫu,
# quan trọng khi mỗi điểm chỉ có ~20 lần quét.

def hampel_filter(
    df: pd.DataFrame,
    ap_cols: list[str],
    group_col: str = "rp_id",
    k: float | None = None,
    gia_tri_dien: float | None = None,
) -> tuple[pd.DataFrame, int]:
    """Thay giá trị ngoại lai bằng trung vị nhóm. Trả về (bảng, số ô bị thay).

    `gia_tri_dien` là giá trị bước 7 điền vào ô trống. Ô mang giá trị ấy được
    MIỄN: với AP bắt được ở hơn nửa số lần quét, trung vị nhóm là số đo thật nên
    ô điền thiếu lệch xa và bị coi là ngoại lai — lọc nhiễu hoá thành điền khuyết,
    biến "không bắt được AP" thành "bắt được ở mức trung bình". Lúc suy luận
    `FeatureMapper` giữ nguyên giá trị điền, nên train và inference sẽ lệch nhau.
    """
    he_so = k if k is not None else config.HAMPEL_K

    gia_tri = df[ap_cols]
    nhom = df[group_col]

    trung_vi = gia_tri.groupby(nhom).transform("median")
    do_lech = (gia_tri - trung_vi).abs()
    mad = do_lech.groupby(nhom).transform("median") * config.MAD_SCALE

    # mad == 0 nghĩa là quá nửa số mẫu trong nhóm giống hệt nhau; lúc đó ngưỡng
    # bằng 0 sẽ đánh dấu nhầm mọi giá trị khác biệt dù nhỏ, nên bỏ qua nhóm đó.
    ngoai_lai = (mad > 0) & (do_lech > he_so * mad)
    if gia_tri_dien is not None:
        ngoai_lai &= gia_tri != gia_tri_dien

    ket_qua = df.copy()
    ket_qua[ap_cols] = gia_tri.where(~ngoai_lai, trung_vi)

    return ket_qua, int(ngoai_lai.to_numpy().sum())


# ============= Bước 9 — chia train / validation / test theo rp_id =============
# Tài liệu còn yêu cầu device_holdout và time_holdout, cả hai KHÔNG chạy được:
# chỉ có một máy, và mỗi điểm chỉ đo một buổi nên tách thời gian là tách vị trí.

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
# Validation và test được phép nằm ngoài [0, 1] — bằng chứng scaler chưa từng
# nhìn thấy chúng (lớn nhất 1,147). scaler.pkl phải đi kèm feature_list.json để
# backend tiền xử lý khớp lúc huấn luyện.

def fit_scaler(fingerprint: pd.DataFrame, ap_cols: list[str]) -> MinMaxScaler:
    train = fingerprint[fingerprint["split"] == "train"]

    # Fit trên mảng numpy chứ không phải DataFrame để scaler KHÔNG ghi nhớ tên cột:
    # backend dựng vector số thuần từ feature_list.json, thứ tự cột mới là thứ
    # phải kiểm soát.
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
