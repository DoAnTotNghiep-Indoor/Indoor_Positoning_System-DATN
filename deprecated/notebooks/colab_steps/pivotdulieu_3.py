# THAM KHẢO bước 3, đừng chạy lại: tính toán nay ở ml.preprocess.pivot.to_wide(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.

# Bước 3: Chuyển từ dạng dài (long) sang bảng fingerprint (wide) — mỗi dòng một
# lần quét, mỗi cột một BSSID, giá trị là RSSI (dBm). Ô trống thành NaN, xử lý
# ở bước 7.

rssi_wide = df.pivot_table(
    index="scan_id", columns="WiFi BSSID", values="WiFi RSSI (dBm)", aggfunc="mean"
)
ap_cols_all = list(rssi_wide.columns)

print("Số scan:", rssi_wide.shape[0], "| Số AP (cột) ban đầu:", rssi_wide.shape[1])

fingerprint = scan_meta.merge(rssi_wide, left_on="scan_id", right_index=True, how="left")

print("\nShape bảng fingerprint:", fingerprint.shape)
fingerprint.head()
