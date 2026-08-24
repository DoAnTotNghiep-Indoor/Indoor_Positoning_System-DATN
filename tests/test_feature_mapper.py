"""Kiểm thử hợp đồng dữ liệu giữa ML và Backend — bài test BẮT BUỘC.

Đây là bài test tồn tại để chặn đúng lỗi mà đồ án CTK45 mắc phải: backend nhận
`rssi: list[float]` — mảng số trần không kèm BSSID — rồi chỉ kiểm tra số lượng
phần tử. Client gửi đủ 36 giá trị nhưng sai thứ tự thì mô hình vẫn chạy trơn tru
và trả về toạ độ sai hoàn toàn, không một cảnh báo nào.

Cách chặn: `artifacts/feature_list.json` là nguồn sự thật duy nhất về thứ tự cột.
Mọi phía đều phải ánh xạ theo BSSID, không bao giờ theo vị trí trong mảng.

`map_scan_to_vector` dưới đây là bản tham chiếu của phép ánh xạ. Khi
`backend/services/preprocessing_service.py` được viết, nó phải cho ra kết quả
y hệt — lúc đó thay lời gọi trong test này bằng lời gọi vào service thật.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from ml import config

pytestmark = pytest.mark.skipif(
    not (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).exists(),
    reason="chưa có artifacts/feature_list.json — chạy `python -m ml.pipeline` trước",
)


@pytest.fixture(scope="module")
def hop_dong() -> dict:
    duong_dan = config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON
    return json.loads(duong_dan.read_text(encoding="utf-8"))


def map_scan_to_vector(scan: list[dict], hop_dong: dict) -> np.ndarray:
    """Dựng vector đặc trưng từ một lần quét, ánh xạ THEO BSSID.

    scan: [{"bssid": "88:dc:...", "rssi": -67}, ...]

    BSSID lạ (AP mới lắp, hotspot điện thoại) bị bỏ qua.
    BSSID có trong hợp đồng nhưng không bắt được lần này thì điền giá trị thiếu.
    """
    thu_tu = hop_dong["ap_columns"]
    gia_tri_thieu = hop_dong["missing_rssi_value"]

    do_manh = {muc["bssid"]: float(muc["rssi"]) for muc in scan}
    return np.array([do_manh.get(bssid, gia_tri_thieu) for bssid in thu_tu], dtype=float)


# --- Tính toàn vẹn của chính bản hợp đồng ---

def test_hop_dong_du_truong(hop_dong):
    for truong in ("ap_columns", "feature_count", "missing_rssi_value", "target_columns"):
        assert truong in hop_dong, f"feature_list.json thiếu trường '{truong}'"


def test_so_dac_trung_khop_danh_sach(hop_dong):
    assert hop_dong["feature_count"] == len(hop_dong["ap_columns"])


def test_bssid_khong_trung_lap(hop_dong):
    cot = hop_dong["ap_columns"]
    assert len(cot) == len(set(cot)), "feature_list.json có BSSID trùng lặp"


def test_thu_tu_cot_on_dinh(hop_dong):
    """Thứ tự phải xác định được, không phụ thuộc phiên bản pandas hay thứ tự đọc."""
    assert hop_dong["ap_columns"] == sorted(hop_dong["ap_columns"])


def test_thu_tu_khop_voi_dataset(hop_dong):
    """Cột trong CSV huấn luyện phải trùng khít thứ tự trong hợp đồng."""
    import pandas as pd

    duong_dan = config.PROCESSED_DIR / "fingerprint_dataset_sorted.csv"
    if not duong_dan.exists():
        pytest.skip("chưa có dataset đã xử lý")

    cot_csv = list(pd.read_csv(duong_dan, nrows=1).columns)
    ap_trong_csv = [c for c in cot_csv if c not in config.META_COLS]
    assert ap_trong_csv == hop_dong["ap_columns"]


# --- Phép ánh xạ ---

def test_quet_du_ap_cho_dung_gia_tri(hop_dong):
    thu_tu = hop_dong["ap_columns"]
    scan = [{"bssid": b, "rssi": -50 - i} for i, b in enumerate(thu_tu)]

    vector = map_scan_to_vector(scan, hop_dong)
    assert vector.shape == (hop_dong["feature_count"],)
    np.testing.assert_allclose(vector, [-50 - i for i in range(len(thu_tu))])


def test_dao_thu_tu_van_ra_ket_qua_giong_het(hop_dong):
    """ĐÂY LÀ BÀI TEST QUAN TRỌNG NHẤT.

    Cùng một lần quét, gửi lên theo thứ tự đảo ngược, phải cho ra đúng cùng một
    vector. Nếu test này hỏng nghĩa là hệ thống đã tụt về đúng lỗi của đồ án cũ.
    """
    thu_tu = hop_dong["ap_columns"]
    scan = [{"bssid": b, "rssi": -50 - i} for i, b in enumerate(thu_tu)]

    xuoi = map_scan_to_vector(scan, hop_dong)
    nguoc = map_scan_to_vector(list(reversed(scan)), hop_dong)
    np.testing.assert_array_equal(xuoi, nguoc)


def test_ap_khong_bat_duoc_thi_dien_gia_tri_thieu(hop_dong):
    thu_tu = hop_dong["ap_columns"]
    scan = [{"bssid": thu_tu[0], "rssi": -55}]

    vector = map_scan_to_vector(scan, hop_dong)
    assert vector[0] == pytest.approx(-55)
    assert np.all(vector[1:] == hop_dong["missing_rssi_value"])


def test_bssid_la_bi_bo_qua(hop_dong):
    """AP mới lắp hoặc hotspot điện thoại không được làm lệch vector."""
    thu_tu = hop_dong["ap_columns"]
    chi_ap_quen = [{"bssid": thu_tu[0], "rssi": -55}]
    them_ap_la = chi_ap_quen + [
        {"bssid": "00:11:22:33:44:55", "rssi": -40},
        {"bssid": "aa:bb:cc:dd:ee:ff", "rssi": -30},
    ]

    np.testing.assert_array_equal(
        map_scan_to_vector(chi_ap_quen, hop_dong),
        map_scan_to_vector(them_ap_la, hop_dong),
    )


def test_quet_rong_van_ra_dung_so_chieu(hop_dong):
    vector = map_scan_to_vector([], hop_dong)
    assert vector.shape == (hop_dong["feature_count"],)
    assert np.all(vector == hop_dong["missing_rssi_value"])


# --- Scaler đi kèm hợp đồng ---

def test_scaler_khop_so_dac_trung(hop_dong):
    import joblib

    duong_dan = config.ARTIFACTS_DIR / config.SCALER_PKL
    if not duong_dan.exists():
        pytest.skip("chưa có scaler.pkl")

    scaler = joblib.load(duong_dan)
    assert scaler.n_features_in_ == hop_dong["feature_count"], (
        "scaler.pkl và feature_list.json lệch số đặc trưng — "
        "hai file phải sinh ra từ cùng một lần chạy pipeline"
    )


def test_vector_qua_scaler_khong_loi(hop_dong):
    """Đường đi thật của backend: quét -> vector -> scaler -> sẵn sàng dự đoán."""
    import joblib

    duong_dan = config.ARTIFACTS_DIR / config.SCALER_PKL
    if not duong_dan.exists():
        pytest.skip("chưa có scaler.pkl")

    scaler = joblib.load(duong_dan)
    scan = [{"bssid": hop_dong["ap_columns"][0], "rssi": -55}]
    vector = map_scan_to_vector(scan, hop_dong).reshape(1, -1)

    da_chuan_hoa = scaler.transform(vector)
    assert da_chuan_hoa.shape == (1, hop_dong["feature_count"])
    assert np.isfinite(da_chuan_hoa).all()
