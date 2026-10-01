# THAM KHẢO bước 4, đừng chạy lại: tính toán nay ở ml.preprocess.coords.attach_coordinates(),
# chạy bằng `python -m ml.pipeline`. Giữ lại để mô tả bước này cho báo cáo.
# LỖI ĐÃ SỬA: bản này im lặng bỏ qua khi thiếu toạ độ, và thực tế chưa chạy
#   lần nào — dataset cũ không có cột x, y.

# Bước 4: Ghép toạ độ thật (x, y) theo rp_id. combined_data.csv KHÔNG có toạ độ
# cục bộ (GPS thô trong nhà gần như không đổi). Cần reference_points.csv gồm
# rp_id,x,y tính bằng mét. KHÔNG tự đoán toạ độ — chỉ dùng số đã đo thật.

RP_COORD_PATH = "reference_points.csv"

try:
    rp_coords = pd.read_csv(RP_COORD_PATH)
    fingerprint = fingerprint.merge(rp_coords, on="rp_id", how="left")
    missing_coords = fingerprint["x"].isna().sum()
    if missing_coords:
        print(f"CẢNH BÁO: {missing_coords} scan không tìm thấy tọa độ RP tương ứng "
              f"— kiểm tra lại rp_id trong {RP_COORD_PATH}")
    else:
        print("Đã ghép tọa độ đầy đủ cho toàn bộ scan.")
    display(fingerprint[["scan_id", "rp_id", "x", "y"]].head())
except FileNotFoundError:
    print(f"CHƯA có {RP_COORD_PATH} trong session Colab.")
    print("-> Upload file này (google.colab.files.upload()) rồi chạy lại cell này.")
    print("-> Nếu chưa đo đạc, tạm thời có thể bỏ qua bước này và dùng rp_id làm nhãn phân lớp,")
    print("   nhưng KHÔNG thể huấn luyện mô hình hồi quy (x, y) nếu thiếu tọa độ thật.")
