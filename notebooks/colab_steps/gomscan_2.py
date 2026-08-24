# ==============================================================================
# FILE NÀY CHỈ CÒN GIÁ TRỊ THAM KHẢO — ĐỪNG CHẠY LẠI TRÊN COLAB
#
# Phần tính toán đã chuyển vào kho mã, gọi bằng:
#   ml.preprocess.pivot.build_scan_id() + build_scan_meta()
#
# Chạy toàn bộ pipeline:  python -m ml.pipeline
# Trên Colab:             notebooks/02_preprocessing_colab.ipynb
#
# Giữ lại file này làm tài liệu mô tả bước 2 cho báo cáo.
#
# LỖI ĐÃ SỬA: cột Orientation Azimuth ghi đơn vị độ nhưng giá trị
#   thực là radian. Module mới tự đổi sang độ.
# ==============================================================================

# Bước 2: Gom dữ liệu theo từng lần quét (scan)
# Lý do: "WiFi fingerprint serial number" chỉ lặp lại 1..N theo từng đợt, KHÔNG duy nhất
# toàn cục. Cột "Time" đã kiểm chứng là duy nhất theo từng lần quét thực tế -> dùng làm scan_id.

df["scan_id"] = df["Time"].astype(str)
# Nếu về sau thu từ NHIỀU thiết bị cùng lúc (dễ trùng Time), đổi sang dòng dưới:
# df["scan_id"] = df["Time"].astype(str) + "_" + df["Student ID"].astype(str)

# Kiểm tra không có AP nào bị đo 2 lần trong cùng 1 lần quét (mới pivot được ở bước sau)
dup_check = df.groupby("scan_id")["WiFi BSSID"].apply(lambda s: s.duplicated().any()).sum()
assert dup_check == 0, f"Phát hiện {dup_check} scan có BSSID trùng lặp — cần xử lý trước khi pivot"

scan_meta = (
    df.groupby("scan_id")
      .agg(
          rp_id=("Reference Point ID", "first"),
          device_id=("Phone Model", "first"),
          collector_id=("Student ID", "first"),
          total_ap_scanned=("Total number of AP scanned", "first"),
          azimuth_deg=("Orientation Azimuth (°)", "first"),
      )
      .reset_index()
)

print("Số lần quét (scan):", len(scan_meta))
print("\nSố scan theo từng RP:")
print(scan_meta["rp_id"].value_counts().sort_index())
scan_meta.head()
