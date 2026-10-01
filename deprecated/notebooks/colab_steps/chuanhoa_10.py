# THAM KHẢO bước 10, đừng chạy lại: tính toán nay ở ml.preprocess.scale.scale_dataset(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.

# Bước 10: Chuẩn hoá min-max, fit CHỈ trên train rồi transform cả ba tập bằng
# scaler đó. Fit trên toàn bộ dataset rồi mới chia là rò rỉ dữ liệu.

from sklearn.preprocessing import MinMaxScaler
import joblib

scaler = MinMaxScaler()
train_df = train_df.copy()
val_df = val_df.copy()
test_df = test_df.copy()

train_df[ap_cols_selected] = scaler.fit_transform(train_df[ap_cols_selected])
val_df[ap_cols_selected] = scaler.transform(val_df[ap_cols_selected])
test_df[ap_cols_selected] = scaler.transform(test_df[ap_cols_selected])

joblib.dump(scaler, "scaler.pkl")

print("Đã fit scaler trên train, transform val/test. Đã lưu scaler.pkl")
print("\nKiểm tra khoảng giá trị sau chuẩn hóa (phải nằm trong [0, 1]):")
print(train_df[ap_cols_selected].min().min(), "->", train_df[ap_cols_selected].max().max())
