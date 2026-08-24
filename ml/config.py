"""Hằng số dùng chung cho toàn bộ pipeline ML.

Mọi tham số tiền xử lý tập trung ở đây để notebook, pipeline và test dùng chung
một nguồn. Giá trị thực tế được ghi vào artifacts/feature_list.json sau khi chạy
pipeline — backend đọc lại từ đó, KHÔNG đọc trực tiếp file này.
"""

from pathlib import Path

# --- Đường dẫn ---
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SPLITS_DIR = DATA_DIR / "splits"
REFERENCE_DIR = DATA_DIR / "reference"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"

RAW_CSV = RAW_DIR / "combined_data.csv"
REFERENCE_POINTS_CSV = REFERENCE_DIR / "reference_points.csv"

# --- Cột trong dữ liệu thô ---
COL_TIME = "Time"
COL_BSSID = "WiFi BSSID"
COL_SSID = "WiFi SSID"
COL_RSSI = "WiFi RSSI (dBm)"
COL_RP = "Reference Point ID"
COL_DEVICE = "Phone Model"
COL_COLLECTOR = "Student ID"
COL_TOTAL_AP = "Total number of AP scanned"
COL_AZIMUTH = "Orientation Azimuth (°)"

META_COLS = [
    "scan_id", "rp_id", "device_id", "collector_id",
    "total_ap_scanned", "azimuth_deg", "split",
]

# --- Tham số tiền xử lý ---
# Bước 5: loại AP xuất hiện dưới ngưỡng này (thử thêm 0.0 và 0.10 để so sánh)
MIN_APPEAR_RATE = 0.20

# Bước 6: loại mẫu quét có ít hơn số AP hợp lệ này
MIN_AP_PER_SCAN = 6

# Bước 8: hệ số Hampel filter (k * MAD)
HAMPEL_K = 3.0
MAD_SCALE = 1.4826  # hệ số hiệu chỉnh cho phân phối Gaussian

# Bước 9: tỉ lệ chia dữ liệu
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15
RANDOM_STATE = 42

# --- Hậu xử lý vị trí (backend dùng lại qua biến môi trường) ---
SMOOTHING_ALPHA = 0.3
MAX_JUMP_DISTANCE_M = 5.0
RESET_AFTER_SECONDS = 30
