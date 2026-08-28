"""Kiểm thử các bước tiền xử lý.

Mỗi bước test riêng bằng dữ liệu giả nhỏ để chạy nhanh và chỉ ra đúng chỗ hỏng.
Phần cuối chạy trên dữ liệu thật nếu có, để bắt lỗi mà dữ liệu giả không lộ ra.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml import config
from ml import preprocess as pre


@pytest.fixture
def bang_van_tay() -> pd.DataFrame:
    """4 điểm tham chiếu × 5 lần quét, 3 AP với tỉ lệ xuất hiện khác nhau."""
    so_scan = 20
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {
            "scan_id": [f"s{i:03d}" for i in range(so_scan)],
            "rp_id": np.repeat(["RP01", "RP02", "RP03", "RP04"], 5),
            "device_id": ["May-A"] * so_scan,
            "collector_id": [1] * so_scan,
            "total_ap_scanned": 3,
            "azimuth_deg": rng.uniform(-180, 180, so_scan),
            "AP_luon_co": rng.uniform(-70, -50, so_scan),
            "AP_thuong_co": rng.uniform(-85, -65, so_scan),
            "AP_hiem": np.nan,
        }
    )
    df.loc[df.index[:4], "AP_thuong_co"] = np.nan    # xuất hiện 80%
    df.loc[df.index[4:6], "AP_hiem"] = -90.0         # xuất hiện 10%
    return df


AP_COLS = ["AP_luon_co", "AP_thuong_co", "AP_hiem"]


# --- Bước 5: lọc AP ---

def test_loc_ap_theo_nguong(bang_van_tay):
    _, giu, ty_le = pre.filter_access_points(bang_van_tay, AP_COLS, min_appear_rate=0.2)
    assert giu == ["AP_luon_co", "AP_thuong_co"]
    assert ty_le["AP_hiem"] == pytest.approx(0.10)


def test_nguong_khong_loai_ai_khi_bang_khong(bang_van_tay):
    _, giu, _ = pre.filter_access_points(bang_van_tay, AP_COLS, min_appear_rate=0.0)
    assert len(giu) == 3


def test_thu_tu_cot_ap_luon_duoc_sap_xep(bang_van_tay):
    """Thứ tự cột là hợp đồng với backend, không được phụ thuộc thứ tự đầu vào."""
    dao_nguoc = bang_van_tay[[c for c in bang_van_tay.columns if c not in AP_COLS] + AP_COLS[::-1]]
    _, giu, _ = pre.filter_access_points(dao_nguoc, AP_COLS[::-1], min_appear_rate=0.0)
    assert giu == sorted(giu)


# --- Bước 6: lọc mẫu nghèo ---

def test_loai_mau_qua_it_ap(bang_van_tay):
    ket_qua, tk = pre.filter_sparse_scans(bang_van_tay, AP_COLS, min_ap_per_scan=3)
    assert tk["scan_bi_loai"] == 18   # chỉ 2 mẫu đầu có đủ cả 3 AP
    assert len(ket_qua) == 2


# --- Bước 7: điền thiếu ---

def test_gia_tri_dien_thieu_la_min_tru_mot(bang_van_tay):
    gia_tri = pre.compute_missing_value(bang_van_tay, AP_COLS)
    assert gia_tri == pytest.approx(np.nanmin(bang_van_tay[AP_COLS].to_numpy()) - 1)


def test_dien_het_o_trong(bang_van_tay):
    ket_qua, gia_tri, so_o = pre.fill_missing(bang_van_tay, AP_COLS)
    assert ket_qua[AP_COLS].isna().sum().sum() == 0
    assert so_o == 22
    assert (ket_qua[AP_COLS] >= gia_tri).all().all()


# --- Bước 8: Hampel ---

def test_hampel_thay_ngoai_lai_bang_trung_vi():
    df = pd.DataFrame({"rp_id": ["RP01"] * 7, "AP": [-60, -61, -59, -60, -62, -60, 20.0]})
    ket_qua, so_thay = pre.hampel_filter(df, ["AP"])
    assert so_thay == 1
    assert ket_qua["AP"].iloc[-1] == pytest.approx(-60.0)


def test_hampel_giu_nguyen_so_dong():
    df = pd.DataFrame({"rp_id": ["RP01"] * 5, "AP": [-60, -61, -59, -60, 99.0]})
    ket_qua, _ = pre.hampel_filter(df, ["AP"])
    assert len(ket_qua) == len(df)


def test_hampel_bo_qua_nhom_khong_bien_thien():
    """MAD = 0 thì ngưỡng bằng 0, không được đánh dấu nhầm mọi giá trị."""
    df = pd.DataFrame({"rp_id": ["RP01"] * 5, "AP": [-60, -60, -60, -60, -55.0]})
    _, so_thay = pre.hampel_filter(df, ["AP"])
    assert so_thay == 0


# --- Bước 4: ghép toạ độ ---

def test_bo_mau_thieu_toa_do(bang_van_tay):
    rp = pd.DataFrame({"rp_id": ["RP01", "RP02", "RP03"], "x": [0, 7, 14], "y": [0, 0, 0]})
    ket_qua, tk = pre.attach_coordinates(bang_van_tay, rp)
    assert tk["rp_chua_do"] == ["RP04"]
    assert tk["scan_bi_bo"] == 5
    assert ket_qua["x"].notna().all()


# --- Bước 9 + 10: chia tập và chuẩn hoá ---

def test_chia_tap_du_ba_phan(bang_van_tay):
    ket_qua, tk = pre.split_dataset(bang_van_tay)
    assert set(ket_qua["split"]) == {"train", "validation", "test"}
    assert len(ket_qua) == len(bang_van_tay)
    assert tk["chien_luoc"] == "random"


def test_scaler_chi_hoc_tu_train():
    """Đây là quy tắc chống rò rỉ dữ liệu quan trọng nhất của cả pipeline."""
    df = pd.DataFrame(
        {
            "rp_id": ["RP01"] * 6,
            "split": ["train"] * 4 + ["validation", "test"],
            "AP": [0.0, 10.0, 20.0, 30.0, 60.0, -30.0],
        }
    )
    ket_qua, scaler, _ = pre.scale_dataset(df, ["AP"])

    train = ket_qua.loc[ket_qua["split"] == "train", "AP"]
    assert train.min() == pytest.approx(0.0)
    assert train.max() == pytest.approx(1.0)

    # Giá trị ngoài [0, 1] ở val/test là BẰNG CHỨNG scaler chưa thấy hai tập đó.
    assert ket_qua.loc[ket_qua["split"] == "validation", "AP"].iloc[0] > 1.0
    assert ket_qua.loc[ket_qua["split"] == "test", "AP"].iloc[0] < 0.0


# --- Kiểm tra trên dữ liệu thật ---

@pytest.mark.skipif(not config.RAW_CSV.exists(), reason="chưa có dữ liệu thô")
def test_du_lieu_that_du_cot_bat_buoc():
    df = pre.load_raw()
    assert not df.empty
    for cot in config.REQUIRED_RAW_COLS:
        assert cot in df.columns


@pytest.mark.skipif(not config.REFERENCE_POINTS_CSV.exists(), reason="chưa có bảng toạ độ")
def test_bang_toa_do_khong_trung_diem():
    rp = pre.load_reference_points()
    assert rp["rp_id"].is_unique
    assert rp["x"].notna().sum() >= 39
