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

# Buổi thu bổ sung. ĐANG TẮT: đã thử gộp và đo, mô hình xấu đi trên chính
# những điểm cũ (2,30 → 4,08 m) vì bộ mới thu bằng Redmi K40 Pro còn bộ cũ
# bằng Samsung SM-S908E. Bật lại sau khi đo được độ lệch hai máy — cách đo
# ghi trong data/raw/nhom15_2026/README.md.
GOP_BUOI_BO_SUNG = False
RAW_BO_SUNG = (sorted((RAW_DIR / "nhom15_2026").glob("*/RP*.csv"))
               if GOP_BUOI_BO_SUNG else [])
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
    "scan_id", "rp_id", "device_id", "collector_id",
    "total_ap_scanned", "azimuth_deg", "x", "y", "split",
]

TARGET_COLS = ["x", "y"]

# LƯU Ý: cột "Orientation Azimuth (°)" ghi đơn vị độ nhưng giá trị thực nằm
# trong [-pi, pi], tức RADIAN. Pipeline đổi sang độ ở bước pivot để tên cột
# `azimuth_deg` đúng với nội dung.
AZIMUTH_IS_RADIAN = True

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

# Lọc nhiễu CHỈ trên tập train và chạy SAU khi chia tập, vì hai lý do:
#
# - Hampel thay giá trị lệch bằng trung vị của nhóm cùng rp_id; chạy trước khi
#   chia thì trung vị tính cả trên mẫu test, tức test tự làm sạch chính nó.
# - Lúc chạy thật backend chỉ nhận MỘT lần quét và không biết nó thuộc rp_id
#   nào nên không lọc Hampel được; test đã lọc nhiễu là test dễ hơn thực tế.
#
# Đặt False để tái lập đúng hành vi bản Colab cũ.
HAMPEL_ON_TRAIN_ONLY = True

# Bước 9: tỉ lệ chia dữ liệu
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15
RANDOM_STATE = 42

# Mô hình triển khai, chỉ định thay vì lấy mô hình có sai số validation thấp
# nhất: validation chia ngẫu nhiên theo lần quét nên luôn ưu tiên mô hình nhớ
# đúng điểm đã khảo sát (k = 1), trong khi người dùng thật còn đứng ở chỗ chưa
# khảo sát. k động cân bằng hai trường hợp — xem `python -m ml.ket_hop`, đánh giá
# trên 10 lần chia lại và bỏ trọn từng điểm, không dùng tập test seed 42.
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


