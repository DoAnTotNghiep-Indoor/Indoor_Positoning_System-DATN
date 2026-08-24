# Bước 8: Lọc nhiễu RSSI bằng Hampel filter (dựa trên Median Absolute Deviation - MAD)
# Với mỗi AP, trong từng nhóm cùng rp_id, thay các giá trị lệch quá k*MAD so với median
# bằng chính median đó -> giảm nhiễu tức thời (đa đường, che khuất, người đi qua)
# mà KHÔNG xóa mất mẫu (khác với cách xóa outlier trực tiếp gây mất thông tin).

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
