# THAM KHẢO bước 7, đừng chạy lại: tính toán nay ở ml.preprocess.missing.fill_missing(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.

# Bước 7: Điền RSSI thiếu bằng hằng số ĐỘNG min(RSSI) - 1, thay vì cố định -98
# vốn có thể trùng tín hiệu yếu thật. Cách gán động này theo nghiên cứu trên bộ
# UJIIndoorLoc cho độ chính xác tốt hơn rõ rệt.

missing_value = float(np.nanmin(fingerprint[ap_cols_selected].values)) - 1
print("missing_value (RSSI gán cho AP không phát hiện):", missing_value)

n_missing_before = fingerprint[ap_cols_selected].isna().sum().sum()
fingerprint[ap_cols_selected] = fingerprint[ap_cols_selected].fillna(missing_value)

print(f"Đã điền {n_missing_before} ô RSSI bị thiếu bằng giá trị {missing_value}")
fingerprint[ap_cols_selected].describe().T[["min", "max", "mean"]].head(10)
