# THAM KHẢO bước 9, đừng chạy lại: tính toán nay ở ml.preprocess.split.split_dataset(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.

# Bước 9: Chia train / validation / test 70/15/15, stratify theo rp_id để mỗi RP
# đều có đại diện ở cả ba tập. Chia TRƯỚC khi chuẩn hoá, nếu không là rò rỉ.

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
