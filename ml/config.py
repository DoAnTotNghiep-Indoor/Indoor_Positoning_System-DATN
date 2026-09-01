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
REFERENCE_POINTS_CSV = REFERENCE_DIR / "reference_points.csv"

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
    "scan_id", "rp_id", "device_id", "collector_id",
    "total_ap_scanned", "azimuth_deg", "x", "y", "split",
]

TARGET_COLS = ["x", "y"]

# LƯU Ý: cột "Orientation Azimuth (°)" trong file thô ghi đơn vị là độ nhưng giá
# trị thực nằm trong khoảng [-pi, pi] — tức là RADIAN. Pipeline tự đổi sang độ ở
# bước pivot để tên cột `azimuth_deg` đúng với nội dung.
AZIMUTH_IS_RADIAN = True

# --- Tham số tiền xử lý ---
# Bước 5: loại AP xuất hiện dưới ngưỡng này. Đổi bằng cờ dòng lệnh để có bảng
# so sánh cho báo cáo: python -m ml.pipeline --min-appear-rate 0.10
MIN_APPEAR_RATE = 0.20

# Bước 6: loại mẫu quét có ít hơn số AP hợp lệ này
MIN_AP_PER_SCAN = 6

# Bước 8: hệ số Hampel filter (k * MAD)
HAMPEL_K = 3.0
MAD_SCALE = 1.4826  # hệ số hiệu chỉnh cho phân phối Gaussian

# Lọc nhiễu CHỈ trên tập train và chạy SAU khi chia tập, vì hai lý do:
#
# - Hampel thay giá trị lệch bằng trung vị của nhóm cùng rp_id; chạy trước khi
#   chia thì trung vị đó tính cả trên mẫu test, tức test tự làm sạch chính nó.
# - Lúc chạy thật backend chỉ nhận MỘT lần quét và không biết nó thuộc rp_id
#   nào, nên không thể lọc Hampel. Test đã lọc nhiễu là test dễ hơn thực tế.
#
# Đặt False để tái lập đúng hành vi bản Colab cũ.
HAMPEL_ON_TRAIN_ONLY = True

# Bước 9: tỉ lệ chia dữ liệu
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15
RANDOM_STATE = 42


# --- Ghi tệp văn bản ---
#
# Trên Windows, `write_text` và `to_csv` tự đổi xuống dòng sang CRLF, nên
# artifact sinh trên Windows khác bản sinh trên Linux ở TỪNG DÒNG. Lúc đó phép
# so "giống hệt từng byte" giữa hai lần chạy pipeline mất sạch ý nghĩa, mà đó
# chính là cách dự án chứng minh pipeline tái lập được. Hai hàm dưới ép LF ở
# đúng một chỗ thay cho mười chỗ gọi rải khắp pipeline.py và train.py.


def ghi_json(duong_dan: Path, du_lieu) -> None:
    duong_dan.write_text(
        json.dumps(du_lieu, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def ghi_csv(bang, duong_dan: Path, **kw) -> None:
    bang.to_csv(duong_dan, lineterminator="\n", **kw)


