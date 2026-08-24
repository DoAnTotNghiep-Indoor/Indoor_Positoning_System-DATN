# ==============================================================================
# FILE NÀY CHỈ CÒN GIÁ TRỊ THAM KHẢO — ĐỪNG CHẠY LẠI TRÊN COLAB
#
# Phần tính toán đã chuyển vào kho mã, gọi bằng:
#   ml.preprocess.pivot.to_wide()
#
# Chạy toàn bộ pipeline:  python -m ml.pipeline
# Trên Colab:             notebooks/02_preprocessing_colab.ipynb
#
# Giữ lại file này làm tài liệu mô tả bước 3 cho báo cáo.
# ==============================================================================

# Bước 3: Chuyển dữ liệu từ dạng dài (long) sang dạng bảng fingerprint (wide)
# Mỗi dòng = 1 lần quét, mỗi cột = 1 BSSID, giá trị = RSSI (dBm).
# Ô trống (AP không phát hiện trong lần quét đó) sẽ là NaN -> xử lý ở bước missRSSI_7.

rssi_wide = df.pivot_table(
    index="scan_id", columns="WiFi BSSID", values="WiFi RSSI (dBm)", aggfunc="mean"
)
ap_cols_all = list(rssi_wide.columns)

print("Số scan:", rssi_wide.shape[0], "| Số AP (cột) ban đầu:", rssi_wide.shape[1])

fingerprint = scan_meta.merge(rssi_wide, left_on="scan_id", right_index=True, how="left")

print("\nShape bảng fingerprint:", fingerprint.shape)
fingerprint.head()
