"""Hằng số dùng chung cho toàn bộ pipeline ML.

Mọi tham số tiền xử lý tập trung ở đây để notebook, pipeline và test dùng chung
một nguồn. Giá trị thực tế được ghi vào artifacts/feature_list.json sau khi chạy
pipeline — backend đọc lại từ đó, KHÔNG đọc trực tiếp file này.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SPLITS_DIR = DATA_DIR / "splits"
REFERENCE_DIR = DATA_DIR / "reference"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
REPORTS_DIR = ROOT_DIR / "reports"

RAW_CSV = RAW_DIR / "combined_data.csv"

# Đợt B: phần dữ liệu CTK45 của ba máy còn lại, chỉ có ở dạng bảng rộng đã xử lý.
# Nguồn và cách tách ghi trong data/raw/ctk45_xu_ly/README.md. Đặt False để chỉ
# dùng đợt A (dữ liệu thô của một máy).
CTK45_XU_LY_CSV = RAW_DIR / "ctk45_xu_ly" / "combined_data_sorted.csv"
GOP_DOT_B = True
GIA_TRI_KHONG_BAT_CTK45 = -100.0
REFERENCE_POINTS_CSV = REFERENCE_DIR / "reference_points.csv"

# Nhãn điểm sai trong dữ liệu thô CTK45, sửa lúc nạp chứ không đụng tệp thô:
# 20 lần quét "RP41" (13/01/2025, 14:28–14:42, giữa phiên RP27 và RP28) trùng khít
# 20 dòng RP26 trong combined_data_sorted.csv của CTK45; báo cáo cũng chỉ có RP01–RP40.
NHAN_RP_SUA = {"RP41": "RP26"}

# --- Tên file artifact (hợp đồng với backend) ---
FEATURE_LIST_JSON = "feature_list.json"
SCALER_PKL = "scaler.pkl"
MANIFEST_JSON = "pipeline_manifest.json"

COL_TIME = "Time"
COL_BSSID = "WiFi BSSID"
COL_RSSI = "WiFi RSSI (dBm)"
COL_RP = "Reference Point ID"
COL_DEVICE = "Phone Model"
COL_COLLECTOR = "Student ID"
COL_TOTAL_AP = "Total number of AP scanned"
COL_AZIMUTH = "Orientation Azimuth (°)"

REQUIRED_RAW_COLS = [
    COL_TIME, COL_BSSID, COL_RSSI, COL_RP,
    COL_DEVICE, COL_COLLECTOR, COL_TOTAL_AP, COL_AZIMUTH,
]

META_COLS = [
    "scan_id", "rp_id", "dot", "device_id", "collector_id",
    "total_ap_scanned", "azimuth_deg", "x", "y", "split",
]

TARGET_COLS = ["x", "y"]

# --- Tham số tiền xử lý ---
# Bước 5: loại AP xuất hiện dưới ngưỡng này. Đổi bằng cờ dòng lệnh để có bảng
# so sánh cho báo cáo: python -m ml.pipeline --min-appear-rate 0.10
MIN_APPEAR_RATE = 0.20

# Bước 6: loại mẫu quét có ít hơn số AP hợp lệ này
MIN_AP_PER_SCAN = 6

# Khoảng RSSI có thể có thật, cận trên KHÔNG gồm 0: trình điều khiển WiFi Android
# thỉnh thoảng trả 0 cho AP quá gần, mà 0 dBm (1 mW thu được) không phải số đo
# thật. Backend và pipeline lọc cùng một khoảng này.
RSSI_NHO_NHAT = -100.0
RSSI_LON_NHAT = 0.0

# Bước 8: hệ số Hampel filter (k * MAD)
HAMPEL_K = 3.0
MAD_SCALE = 1.4826  # hệ số hiệu chỉnh cho phân phối Gaussian

# Bước 9: tỉ lệ chia dữ liệu
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15
RANDOM_STATE = 42

# Mô hình triển khai, chỉ định thay vì lấy mô hình có sai số validation thấp
# nhất: validation chia ngẫu nhiên theo lần quét nên luôn ưu tiên mô hình nhớ
# đúng điểm đã khảo sát (k = 1), trong khi người dùng thật còn đứng ở chỗ chưa
# khảo sát. k động cân bằng hai trường hợp, đánh giá trên 10 lần chia lại, bỏ trọn
# từng điểm và khác đợt đo, không dùng tập test seed 42.
# Đặt None để quay về chọn theo validation.
MO_HINH_TRIEN_KHAI = "fingerprint_knn_dong"


# --- Ghi tệp văn bản ---
# Trên Windows, `write_text` và `to_csv` tự đổi xuống dòng sang CRLF nên artifact
# sinh trên Windows khác bản sinh trên Linux ở TỪNG DÒNG, làm phép so "giống hệt
# từng byte" giữa hai lần chạy mất ý nghĩa — mà đó là cách dự án chứng minh
# pipeline tái lập được. Hai hàm dưới ép LF ở đúng một chỗ.


def ghi_json(duong_dan: Path, du_lieu) -> None:
    duong_dan.write_text(
        json.dumps(du_lieu, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def ghi_csv(bang, duong_dan: Path, **kw) -> None:
    bang.to_csv(duong_dan, lineterminator="\n", **kw)




def song_song(ham, cac_doi_so: list[tuple]) -> list:
    """ham(*đối số) cho từng bộ, mỗi bộ một tiến trình trên mọi lõi; kết quả giữ thứ tự."""
    from joblib import Parallel, delayed

    return Parallel(n_jobs=-1)(delayed(ham)(*a) for a in cac_doi_so)
