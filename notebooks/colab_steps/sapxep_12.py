# Bước 12: Sắp xếp lại thứ tự cột đặc trưng (AP) và thứ tự dòng theo rp_id, tăng dần
# Chạy sau khi đã có fingerprint_dataset.csv (kết quả bước 11 - xuatketqua_11.py)

import pandas as pd
import os

# Nếu đang chạy tiếp session cũ (đã có sẵn fingerprint_dataset.csv trong /content) thì đọc luôn.
# Nếu chạy session Colab MỚI (file chưa tồn tại), sẽ hiện nút Choose Files để bạn upload lại.
if not os.path.exists("fingerprint_dataset.csv"):
    print("Chưa thấy fingerprint_dataset.csv trong session này — hãy chọn file để upload:")
    from google.colab import files
    uploaded = files.upload()

fingerprint_full = pd.read_csv("fingerprint_dataset.csv")

meta_cols = ["scan_id", "rp_id", "device_id", "collector_id", "total_ap_scanned", "azimuth_deg", "split"]
ap_cols = [c for c in fingerprint_full.columns if c not in meta_cols]

print("Tổng số cột đặc trưng AP (dùng để huấn luyện model):", len(ap_cols))
print("Tổng số giá trị rp_id duy nhất:", fingerprint_full["rp_id"].nunique())

# Sắp xếp cột AP tăng dần theo tên (BSSID)
ap_cols_sorted = sorted(ap_cols)

# Sắp xếp dòng dữ liệu theo rp_id tăng dần (RP01 -> RP41)
fingerprint_sorted = fingerprint_full.sort_values("rp_id", kind="stable").reset_index(drop=True)
fingerprint_sorted = fingerprint_sorted[meta_cols + ap_cols_sorted]

OUT_NAME = "fingerprint_dataset_sorted.csv"
fingerprint_sorted.to_csv(OUT_NAME, index=False)
print(f"\nĐã lưu {OUT_NAME} trong Colab. Đang tải về máy...")

# Tải file về máy — nếu không thấy hộp thoại tải xuống, kiểm tra trình duyệt có chặn popup không
from google.colab import files
files.download(OUT_NAME)

fingerprint_sorted.head()
