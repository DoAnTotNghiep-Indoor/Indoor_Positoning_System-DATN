# Bước 4: Ghép tọa độ thật (x, y) theo rp_id
# combined_data.csv KHÔNG có tọa độ cục bộ (GPS thô trong nhà gần như không đổi, không dùng được).
# Cần file reference_points.csv với 2 cột: rp_id,x,y (đơn vị mét), ví dụ:
#   rp_id,x,y
#   RP01,-16,0
#   RP02,0,0
# KHÔNG tự đoán tọa độ nếu chưa có số đo thực tế — chỉ dùng số liệu đã khảo sát/đo đạc thật.

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
