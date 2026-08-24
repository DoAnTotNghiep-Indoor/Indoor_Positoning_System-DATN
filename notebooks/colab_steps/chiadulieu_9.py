# ==============================================================================
# FILE NÀY CHỈ CÒN GIÁ TRỊ THAM KHẢO — ĐỪNG CHẠY LẠI TRÊN COLAB
#
# Phần tính toán đã chuyển vào kho mã, gọi bằng:
#   ml.preprocess.split.split_dataset()
#
# Chạy toàn bộ pipeline:  python -m ml.pipeline
# Trên Colab:             notebooks/02_preprocessing_colab.ipynb
#
# Giữ lại file này làm tài liệu mô tả bước 9 cho báo cáo.
# ==============================================================================

# Bước 9: Chia train / validation / test theo tỉ lệ 70/15/15
# Stratify theo rp_id để mỗi RP đều có đại diện đều ở cả 3 tập (tránh lệch phân bố).
# QUAN TRỌNG: chia tập TRƯỚC khi chuẩn hóa (bước sau) để tránh rò rỉ dữ liệu (data leakage).

from sklearn.model_selection import train_test_split

train_df, temp_df = train_test_split(
    fingerprint, test_size=0.30, stratify=fingerprint["rp_id"], random_state=42
)
val_df, test_df = train_test_split(
    temp_df, test_size=0.50, stratify=temp_df["rp_id"], random_state=42
)

print("Train:", len(train_df), "| Validation:", len(val_df), "| Test:", len(test_df))
print("\nPhân bố RP trong tập train (5 dòng đầu):")
train_df["rp_id"].value_counts().sort_index().head()
