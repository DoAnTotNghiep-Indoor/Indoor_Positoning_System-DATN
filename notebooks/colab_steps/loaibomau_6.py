# Bước 6: Loại bỏ mẫu quét (scan) có quá ít AP phát hiện được
# Ngưỡng tối thiểu 6 AP/mẫu (theo tài liệu tham khảo và kế hoạch phân tích của nhóm).
# Thực hiện SAU bước lọc AP (locAP_5) vì sau khi bỏ AP yếu, một số scan có thể
# còn lại rất ít AP hợp lệ và cần bị loại.

MIN_AP_PER_SCAN = 6

detected_count = fingerprint[ap_cols_selected].notna().sum(axis=1)
before = len(fingerprint)
fingerprint = fingerprint[detected_count >= MIN_AP_PER_SCAN].reset_index(drop=True)

print(f"Loại {before - len(fingerprint)} scan có < {MIN_AP_PER_SCAN} AP hợp lệ.")
print("Số scan còn lại:", len(fingerprint))
print("\nSố AP phát hiện được trên mỗi scan (thống kê):")
detected_count.describe()
