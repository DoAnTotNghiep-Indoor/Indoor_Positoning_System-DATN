# THAM KHẢO bước 5, đừng chạy lại: tính toán nay ở ml.preprocess.filter.filter_access_points(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.

# Bước 5: Loại AP xuất hiện dưới MIN_APPEAR_RATE số lần quét. Khảo sát trên
# combined_data.csv: 48/89 AP xuất hiện dưới 10% (nhiễu, hotspot cá nhân, AP xa).
# Nên thử 0.0 / 0.10 / 0.20 rồi so kết quả model ở bước huấn luyện.

MIN_APPEAR_RATE = 0.20

n_scans = fingerprint["scan_id"].nunique()
appear_rate = fingerprint[ap_cols_all].notna().sum() / n_scans

ap_cols_selected = appear_rate[appear_rate >= MIN_APPEAR_RATE].index.tolist()
print(f"Giữ lại {len(ap_cols_selected)}/{len(ap_cols_all)} AP (ngưỡng >= {MIN_APPEAR_RATE:.0%})")

meta_cols = [c for c in fingerprint.columns if c not in ap_cols_all]
fingerprint = fingerprint[meta_cols + ap_cols_selected]

print("\nShape sau khi lọc AP:", fingerprint.shape)
appear_rate.sort_values().head(10)  # xem 10 AP có tỉ lệ xuất hiện thấp nhất
