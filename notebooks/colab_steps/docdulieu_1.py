# ==============================================================================
# FILE NÀY CHỈ CÒN GIÁ TRỊ THAM KHẢO — ĐỪNG CHẠY LẠI TRÊN COLAB
#
# Phần tính toán đã chuyển vào kho mã, gọi bằng:
#   ml.preprocess.load.load_raw()
#
# Chạy toàn bộ pipeline:  python -m ml.pipeline
# Trên Colab:             notebooks/02_preprocessing_colab.ipynb
#
# Giữ lại file này làm tài liệu mô tả bước 1 cho báo cáo.
# ==============================================================================

# Bước 1: Nạp dữ liệu thô vào Colab và kiểm tra nhanh

# ---- CÁCH 1: Upload trực tiếp mỗi lần chạy ----
from google.colab import files
uploaded = files.upload()  # chọn combined_data.csv
RAW_PATH = "combined_data.csv"

# ---- CÁCH 2 (khuyên dùng, đỡ upload lại): Mount Google Drive ----
# from google.colab import drive
# drive.mount('/content/drive')
# RAW_PATH = "/content/drive/MyDrive/DATN/combined_data.csv"

import pandas as pd
import numpy as np

pd.set_option("display.max_columns", None)

df = pd.read_csv(RAW_PATH)

print("Shape:", df.shape)
print("\nCột dữ liệu:", list(df.columns))
print("\nSố giá trị thiếu theo cột:\n", df.isnull().sum())
print("\nSố dòng trùng lặp:", df.duplicated().sum())
print("\nSố Reference Point (RP):", df["Reference Point ID"].nunique())
print("Số BSSID (AP) duy nhất:", df["WiFi BSSID"].nunique())
print("Khoảng RSSI:", df["WiFi RSSI (dBm)"].min(), "->", df["WiFi RSSI (dBm)"].max())

df.head()
