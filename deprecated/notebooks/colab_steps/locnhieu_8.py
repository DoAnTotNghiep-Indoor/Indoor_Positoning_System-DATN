# THAM KHẢO bước 8, đừng chạy lại: tính toán nay ở ml.preprocess.denoise.hampel_filter(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.
# LỖI ĐÃ SỬA: bản này chạy TRƯỚC khi chia tập nên rò rỉ dữ liệu (trung vị
#   tính trên cả mẫu test). Module mới chỉ lọc trên train, sau bước 9.

# Bước 8: Lọc nhiễu RSSI bằng Hampel filter (MAD). Với mỗi AP trong từng nhóm
# cùng rp_id, giá trị lệch quá k*MAD so với trung vị bị thay bằng chính trung vị
# đó — giảm nhiễu tức thời mà KHÔNG xoá mẫu.

def hampel_smooth(series, k=3.0):
    med = series.median()
    mad = (series - med).abs().median() * 1.4826  # 1.4826: hệ số hiệu chỉnh cho phân phối Gaussian
    if mad == 0:
        return series
    mask = (series - med).abs() > k * mad
    series = series.copy()
    series[mask] = med
    return series

n_outliers_total = 0
for col in ap_cols_selected:
    before_vals = fingerprint[col].copy()
    fingerprint[col] = fingerprint.groupby("rp_id")[col].transform(hampel_smooth)
    n_outliers_total += (before_vals != fingerprint[col]).sum()

print(f"Đã lọc nhiễu Hampel filter cho {len(ap_cols_selected)} cột AP.")
print(f"Tổng số giá trị bị coi là outlier và thay bằng median: {n_outliers_total}")
