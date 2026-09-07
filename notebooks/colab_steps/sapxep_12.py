# THAM KHẢO bước 12, đừng chạy lại: tính toán nay ở ml.pipeline.run(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.

# Bước 12: Sắp lại thứ tự cột đặc trưng (AP) và thứ tự dòng theo rp_id, tăng dần.
# Chạy sau bước 11 (xuatketqua_11.py) vì cần fingerprint_dataset.csv.

import pandas as pd
import os

# Session cũ đã có sẵn tệp thì đọc luôn; session mới sẽ hiện nút Choose Files.
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

# Sắp xếp dòng theo rp_id tăng dần (RP01 -> RP41)
fingerprint_sorted = fingerprint_full.sort_values("rp_id", kind="stable").reset_index(drop=True)
fingerprint_sorted = fingerprint_sorted[meta_cols + ap_cols_sorted]

OUT_NAME = "fingerprint_dataset_sorted.csv"
fingerprint_sorted.to_csv(OUT_NAME, index=False)
print(f"\nĐã lưu {OUT_NAME} trong Colab. Đang tải về máy...")

# Tải về máy — không thấy hộp thoại thì kiểm tra trình duyệt có chặn popup không
from google.colab import files
files.download(OUT_NAME)

fingerprint_sorted.head()
