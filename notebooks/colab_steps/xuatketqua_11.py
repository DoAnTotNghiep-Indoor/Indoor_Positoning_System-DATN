# ==============================================================================
# FILE NÀY CHỈ CÒN GIÁ TRỊ THAM KHẢO — ĐỪNG CHẠY LẠI TRÊN COLAB
#
# Phần tính toán đã chuyển vào kho mã, gọi bằng:
#   ml.pipeline.run()
#
# Chạy toàn bộ pipeline:  python -m ml.pipeline
# Trên Colab:             notebooks/02_preprocessing_colab.ipynb
#
# Giữ lại file này làm tài liệu mô tả bước 11 cho báo cáo.
#
# LỖI ĐÃ SỬA: tải từng file rời nên lần chạy trước chỉ lấy được CSV,
#   mất scaler.pkl và feature_list.json. Pipeline mới ghi thẳng vào artifacts/.
# ==============================================================================

# Bước 11: Xuất artifact cuối cùng (dataset + feature_list + train/val/test) và tải về

import json

fingerprint_full = pd.concat([
    train_df.assign(split="train"),
    val_df.assign(split="validation"),
    test_df.assign(split="test"),
], ignore_index=True)

fingerprint_full.to_csv("fingerprint_dataset.csv", index=False)
train_df.to_csv("train.csv", index=False)
val_df.to_csv("validation.csv", index=False)
test_df.to_csv("test.csv", index=False)

feature_list = {
    "ap_columns": ap_cols_selected,
    "feature_count": len(ap_cols_selected),
    "missing_rssi_value": missing_value,
    "min_ap_per_scan": MIN_AP_PER_SCAN,
    "min_appear_rate": MIN_APPEAR_RATE,
}
with open("feature_list.json", "w", encoding="utf-8") as f:
    json.dump(feature_list, f, ensure_ascii=False, indent=2)

print("Đã lưu: fingerprint_dataset.csv, train.csv, validation.csv, test.csv, feature_list.json, scaler.pkl")
print("\nTóm tắt:")
print("- Số scan sau làm sạch:", len(fingerprint_full))
print("- Số AP dùng làm feature:", len(ap_cols_selected))
print("- missing_value:", missing_value)
print(fingerprint_full["split"].value_counts())

# Tải file về máy (bỏ qua nếu đang lưu trực tiếp vào Google Drive)
from google.colab import files
for fn in ["fingerprint_dataset.csv", "train.csv", "validation.csv", "test.csv", "feature_list.json", "scaler.pkl"]:
    files.download(fn)
