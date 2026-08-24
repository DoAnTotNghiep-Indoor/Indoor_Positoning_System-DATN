# Công cụ hỗ trợ (Cách 2): Click chuột lên ảnh sơ đồ mặt bằng để lấy tọa độ (x, y) mét cho từng RP.
# Chạy trong Google Colab. Cần: 1 ảnh sơ đồ mặt bằng (floor_plan.png/jpg) đã upload.

from google.colab import files
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd

print("Upload ảnh sơ đồ mặt bằng (floor plan):")
uploaded = files.upload()
IMG_PATH = list(uploaded.keys())[0]

img = mpimg.imread(IMG_PATH)
fig, ax = plt.subplots(figsize=(12, 10))
ax.imshow(img)
ax.set_title("Click 2 điểm mốc đã biết khoảng cách thật (để tính tỷ lệ), theo thứ tự")
plt.show()

print("\n--- BƯỚC 1: Xác định tỷ lệ ---")
print("Click vào 2 điểm mốc trên ảnh mà bạn ĐÃ BIẾT khoảng cách thật giữa chúng (ví dụ 2 đầu 1 bức tường dài 10m).")
ref_points_px = plt.ginput(2, timeout=0)
plt.close(fig)

real_distance_m = float(input("Nhập khoảng cách THẬT giữa 2 điểm mốc vừa click (đơn vị mét): "))

import math
px_distance = math.dist(ref_points_px[0], ref_points_px[1])
scale = real_distance_m / px_distance  # mét / pixel
print(f"Tỷ lệ quy đổi: {scale:.6f} mét/pixel")

print("\n--- BƯỚC 2: Xác định gốc tọa độ (0,0) ---")
fig, ax = plt.subplots(figsize=(12, 10))
ax.imshow(img)
ax.set_title("Click vào điểm bạn chọn làm gốc tọa độ (0, 0)")
plt.show()
origin_px = plt.ginput(1, timeout=0)[0]
plt.close(fig)

print("\n--- BƯỚC 3: Click lần lượt từng RP theo đúng thứ tự đã chuẩn bị ---")
rp_ids = pd.read_csv("reference_points_template.csv")["rp_id"].tolist()
print(f"Sẽ click {len(rp_ids)} điểm theo thứ tự: {rp_ids}")

fig, ax = plt.subplots(figsize=(14, 12))
ax.imshow(img)
ax.set_title(f"Click lần lượt {len(rp_ids)} điểm RP theo đúng thứ tự trong danh sách")
plt.show()
rp_points_px = plt.ginput(len(rp_ids), timeout=0)
plt.close(fig)

# Quy đổi pixel -> mét, gốc tọa độ = origin_px, trục y lật ngược (ảnh có gốc trên-trái)
records = []
for rp_id, (px, py) in zip(rp_ids, rp_points_px):
    x_m = (px - origin_px[0]) * scale
    y_m = (origin_px[1] - py) * scale  # đảo dấu vì trục y ảnh hướng xuống
    records.append({"rp_id": rp_id, "x": round(x_m, 2), "y": round(y_m, 2), "description": ""})

rp_coords = pd.DataFrame(records)
rp_coords.to_csv("reference_points.csv", index=False)
print("\nĐã lưu reference_points.csv:")
print(rp_coords)

files.download("reference_points.csv")
