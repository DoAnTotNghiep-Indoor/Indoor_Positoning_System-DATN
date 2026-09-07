# THAM KHẢO bước 6, đừng chạy lại: tính toán nay ở ml.preprocess.filter.filter_sparse_scans(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.

# Bước 6: Loại mẫu quét bắt được dưới 6 AP. Chạy SAU bước 5 vì bỏ AP yếu xong
# mới biết mẫu nào còn quá ít AP hợp lệ.

MIN_AP_PER_SCAN = 6

detected_count = fingerprint[ap_cols_selected].notna().sum(axis=1)
before = len(fingerprint)
fingerprint = fingerprint[detected_count >= MIN_AP_PER_SCAN].reset_index(drop=True)

print(f"Loại {before - len(fingerprint)} scan có < {MIN_AP_PER_SCAN} AP hợp lệ.")
print("Số scan còn lại:", len(fingerprint))
print("\nSố AP phát hiện được trên mỗi scan (thống kê):")
detected_count.describe()
