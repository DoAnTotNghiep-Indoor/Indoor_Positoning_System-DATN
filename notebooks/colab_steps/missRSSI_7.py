# Bước 7: Xử lý giá trị RSSI thiếu (missing value) bằng hằng số ĐỘNG
# Thay vì gán cố định -98 (cách phổ biến nhưng có thể trùng/gần tín hiệu yếu thật),
# tính missing_value = min(RSSI toàn bộ dữ liệu) - 1.
# Theo nghiên cứu tham khảo trên bộ dữ liệu UJIIndoorLoc, cách gán động này cải thiện
# độ chính xác định vị rõ rệt so với hằng số cố định tùy chọn.

missing_value = float(np.nanmin(fingerprint[ap_cols_selected].values)) - 1
print("missing_value (RSSI gán cho AP không phát hiện):", missing_value)

n_missing_before = fingerprint[ap_cols_selected].isna().sum().sum()
fingerprint[ap_cols_selected] = fingerprint[ap_cols_selected].fillna(missing_value)

print(f"Đã điền {n_missing_before} ô RSSI bị thiếu bằng giá trị {missing_value}")
fingerprint[ap_cols_selected].describe().T[["min", "max", "mean"]].head(10)
