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
REPORTS_DIR = ROOT_DIR / "reports"

RAW_CSV = RAW_DIR / "combined_data.csv"
REFERENCE_POINTS_CSV = REFERENCE_DIR / "reference_points.csv"

# --- Tên file artifact (hợp đồng với backend) ---
FEATURE_LIST_JSON = "feature_list.json"
SCALER_PKL = "scaler.pkl"
MANIFEST_JSON = "pipeline_manifest.json"

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

# Cột bắt buộc phải có trong file thô — thiếu là dừng ngay, không chạy tiếp
REQUIRED_RAW_COLS = [
    COL_TIME, COL_BSSID, COL_RSSI, COL_RP,
    COL_DEVICE, COL_COLLECTOR, COL_TOTAL_AP, COL_AZIMUTH,
]

META_COLS = [
    "scan_id", "rp_id", "device_id", "collector_id",
    "total_ap_scanned", "azimuth_deg", "x", "y", "split",
]

# Cột nhãn cho bài toán hồi quy
TARGET_COLS = ["x", "y"]

# LƯU Ý: cột "Orientation Azimuth (°)" trong file thô ghi đơn vị là độ nhưng giá
# trị thực nằm trong khoảng [-pi, pi] — tức là RADIAN. Pipeline tự đổi sang độ ở
# bước pivot để tên cột `azimuth_deg` đúng với nội dung.
AZIMUTH_IS_RADIAN = True

# --- Tham số tiền xử lý ---
# Bước 5: loại AP xuất hiện dưới ngưỡng này.
# Chạy lại pipeline với 0.0 / 0.10 / 0.20 để có bảng so sánh cho báo cáo:
#     python -m ml.pipeline --min-appear-rate 0.10
MIN_APPEAR_RATE = 0.20

# Bước 6: loại mẫu quét có ít hơn số AP hợp lệ này
MIN_AP_PER_SCAN = 6

# Bước 8: hệ số Hampel filter (k * MAD)
HAMPEL_K = 3.0
MAD_SCALE = 1.4826  # hệ số hiệu chỉnh cho phân phối Gaussian

# Lọc nhiễu CHỈ trên tập train, chạy SAU khi chia tập.
#
# Hampel thay giá trị lệch bằng trung vị của nhóm cùng rp_id. Nếu chạy trước khi
# chia tập thì trung vị đó được tính trên cả mẫu test — tức tập test tự làm sạch
# chính nó, cùng loại lỗi với việc fit scaler trên toàn bộ dữ liệu.
#
# Quan trọng hơn: lúc chạy thật backend chỉ nhận MỘT lần quét và không biết nó
# thuộc rp_id nào, nên không thể lọc Hampel. Test đã lọc nhiễu là test dễ hơn
# thực tế. Đặt False để tái lập đúng hành vi bản Colab cũ.
HAMPEL_ON_TRAIN_ONLY = True

# Bước 9: tỉ lệ chia dữ liệu
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15
RANDOM_STATE = 42

# Cách chia tập:
#   "random"         - ngẫu nhiên, phân tầng theo rp_id (mặc định)
#   "device_holdout" - để riêng 1 thiết bị làm test (cần >= 2 device_id)
#   "time_holdout"   - để riêng khoảng thời gian cuối làm test
SPLIT_STRATEGY = "random"
HOLDOUT_DEVICE = None  # tên thiết bị dùng làm test khi SPLIT_STRATEGY="device_holdout"

# Xử lý điểm tham chiếu chưa có toạ độ đo đạc (hiện tại: RP41):
#   "drop"  - bỏ các mẫu đó, vẫn chạy được (mặc định)
#   "error" - dừng pipeline, dùng khi đã đo đủ và muốn chặn thiếu sót
MISSING_COORD_POLICY = "drop"

# --- Hậu xử lý vị trí (backend dùng lại qua biến môi trường) ---
SMOOTHING_ALPHA = 0.3
MAX_JUMP_DISTANCE_M = 5.0
RESET_AFTER_SECONDS = 30
