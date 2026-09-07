# THAM KHẢO bước 2, đừng chạy lại: tính toán nay ở ml.preprocess.pivot.build_scan_id() + build_scan_meta(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.
# LỖI ĐÃ SỬA: cột Orientation Azimuth ghi đơn vị độ nhưng giá trị thực là
#   radian. Module mới tự đổi sang độ.

# Bước 2: Gom dữ liệu theo từng lần quét. "WiFi fingerprint serial number" chỉ
# lặp 1..N theo từng đợt nên không duy nhất toàn cục; "Time" đã kiểm chứng là
# duy nhất theo lần quét nên dùng làm scan_id.

df["scan_id"] = df["Time"].astype(str)
# Thu từ NHIỀU thiết bị cùng lúc (dễ trùng Time) thì đổi sang dòng dưới:
# df["scan_id"] = df["Time"].astype(str) + "_" + df["Student ID"].astype(str)

# Không AP nào được đo hai lần trong cùng một lần quét thì bước sau mới pivot được
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
