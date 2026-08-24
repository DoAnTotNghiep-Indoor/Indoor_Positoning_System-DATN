# ==============================================================================
# FILE NÀY CHỈ CÒN GIÁ TRỊ THAM KHẢO — ĐỪNG CHẠY LẠI TRÊN COLAB
#
# Phần tính toán đã chuyển vào kho mã, gọi bằng:
#   ml.preprocess.filter.filter_access_points()
#
# Chạy toàn bộ pipeline:  python -m ml.pipeline
# Trên Colab:             notebooks/02_preprocessing_colab.ipynb
#
# Giữ lại file này làm tài liệu mô tả bước 5 cho báo cáo.
# ==============================================================================

# Bước 5: Lọc AP kém chất lượng (appearance rate thấp)
# Loại AP xuất hiện trong dưới MIN_APPEAR_RATE số lần quét.
# Khảo sát thực tế trên combined_data.csv: 48/89 AP xuất hiện dưới 10% số lần quét
# (nhiễu / hotspot cá nhân / AP ở xa) -> nên loại để tránh làm nhiễu mô hình.
# Nên thử nhiều cấu hình (0.0 = giữ hết, 0.10, 0.20) rồi so sánh kết quả model ở bước huấn luyện.

MIN_APPEAR_RATE = 0.20

n_scans = fingerprint["scan_id"].nunique()
appear_rate = fingerprint[ap_cols_all].notna().sum() / n_scans

ap_cols_selected = appear_rate[appear_rate >= MIN_APPEAR_RATE].index.tolist()
print(f"Giữ lại {len(ap_cols_selected)}/{len(ap_cols_all)} AP (ngưỡng >= {MIN_APPEAR_RATE:.0%})")

meta_cols = [c for c in fingerprint.columns if c not in ap_cols_all]
fingerprint = fingerprint[meta_cols + ap_cols_selected]

print("\nShape sau khi lọc AP:", fingerprint.shape)
appear_rate.sort_values().head(10)  # xem 10 AP có tỉ lệ xuất hiện thấp nhất
