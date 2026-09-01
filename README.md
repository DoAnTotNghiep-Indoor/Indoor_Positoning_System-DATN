# Hệ thống định vị trong nhà bằng WiFi Fingerprinting

Đồ án tốt nghiệp — Nhóm 15, Khoa Công nghệ Thông tin, Trường Đại học Đà Lạt.
GVHD: TS. Nguyễn Thị Lương.

Nghiên cứu hệ thống định vị trong nhà bằng kỹ thuật WiFi Fingerprinting và xây dựng
Web Dashboard hiển thị vị trí người dùng theo thời gian thực.

## Bài toán

- **Input**: vector cường độ tín hiệu RSSI từ các Access Point `[AP_1, ..., AP_n]`
- **Output**: tọa độ người dùng `(x, y)` theo đơn vị mét
- **Đánh giá**: `error = sqrt((x_pred - x_true)² + (y_pred - y_true)²)`

Mô hình chính của đề tài: **XGBoost Regression**. Mô hình cơ sở đối chứng: kNN,
WKNN, Random Forest.

Mô hình **đang được triển khai** thì chọn theo sai số trên tập validation, và
hiện là `kNN vân tay (Bray-Curtis)` — 1,92 m so với 6,48 m của XGBoost. Lý do:
dữ liệu chỉ có 39 toạ độ khác nhau vì thu đúng tại các điểm tham chiếu, nên bài
toán gần với phân lớp hơn hồi quy. Xem `docs/Phan_Tich_Thiet_Ke_He_Thong.md`
§2.4.1. `GET /health` luôn cho biết mô hình nào đang chạy.

## Cài đặt

```bash
python -m venv venv
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

## Chạy phần máy học

```bash
# 1. Tiền xử lý 12 bước -> artifacts/ + data/splits/
python -m ml.pipeline

# 2. Rà soát dữ liệu trước khi huấn luyện (rò rỉ, độ ổn định, chất lượng buổi thu)
python -m ml.audit

# 3. Huấn luyện và so sánh 5 mô hình -> artifacts/*.pkl + reports/tables/
python -m ml.train
python -m ml.train --nhanh              # lưới tham số rút gọn, dùng lúc thử
python -m ml.train --mo-hinh knn wknn   # chỉ chạy một số mô hình

# 4. Sinh biểu đồ cho báo cáo -> reports/figures/
python -m ml.report

# Kiểm thử
python -m pytest tests/ -q
```

Chạy đúng thứ tự trên: `ml.train` cần artifact do `ml.pipeline` sinh ra, và
`ml.report` đọc kết quả của `ml.train`.

## Chạy ứng dụng di động

```bash
cd mobile
flutter pub get
flutter run          # cần máy Android thật hoặc máy ảo đang bật
flutter test
flutter analyze
```

Ứng dụng **quét WiFi thật** và gọi `POST /predict` mỗi 5 giây (chu kỳ này bị
Android chặn ở 4 lần quét mỗi 2 phút, nhanh hơn chỉ tốn pin). Tab Bản đồ vẽ sơ
đồ mặt bằng đã số hoá kèm chấm vị trí; màn Chi tiết khu vực hiện ảnh thật và mô
tả lấy từ `GET /map`.

Địa chỉ máy chủ sửa được trong Cài đặt — mặc định `http://10.0.2.2:8000` là lối
tắt máy ảo Android gọi về máy đang chạy nó, điện thoại thật phải đổi sang IP nội
bộ. Danh sách "Gần bạn" và kết quả tìm kiếm vẫn là dữ liệu demo.

Giao diện đủ 5 màn hình, hai ngôn ngữ Việt/Anh và chế độ sáng/tối.

## Chạy backend

```bash
uvicorn backend.main:app --reload
```

Mở `http://127.0.0.1:8000/docs` để thử API bằng giao diện Swagger.

| Endpoint | Việc |
|---|---|
| `GET /health` | Xác nhận mô hình đã nạp và hợp đồng dữ liệu khớp |
| `POST /predict` | Nhận `{device_id, scan:[{bssid, rssi}]}` → trả `{x, y, x_smooth, y_smooth, …}` |
| `GET /predictions` | Lịch sử vị trí đã lưu |
| `WS /ws/location` | Kênh thời gian thực: gửi lần quét, nhận toạ độ; dashboard chỉ xem thì nhận toạ độ của mọi thiết bị |
| `GET /map` | Toàn bộ dữ liệu không gian trong một response: phạm vi, 40 điểm tham chiếu, thống kê đồ thị |
| `GET /graph` | Danh sách cạnh của đồ thị đi lại |
| `POST /route` | Chỉ đường giữa hai điểm tham chiếu (Dijkstra), điểm đầu cho bằng `tu_rp` hoặc toạ độ mét. Trả kèm `chi_dan` — từng bước "đi thẳng / rẽ trái / rẽ phải" và số mét |
| `GET /map/so-do.png` | Ảnh sơ đồ mặt bằng, phục vụ thẳng từ `data/reference/Map.png` |
| `GET /` | Web Dashboard (xem mục dưới) |

`WS /ws/location` và `POST /predict` đi chung một đường xử lý, nên toạ độ gửi
bằng cách nào cũng được ghi CSDL và phát cho dashboard giống hệt nhau.

CSDL là **SQLite**, tự tạo tại `data/ips.db` lúc khởi động — không cần cài
server, không cần migration. Đã bỏ hẳn PostgreSQL; schema viết tránh cú pháp
riêng của engine nên đổi engine chỉ phải đổi `DATABASE_URL` trong `.env`.

Bước quan trọng nhất là `POST /predict` phải nhận **`{bssid, rssi}` kèm cặp**,
không nhận mảng số trần. Đây là chỗ đồ án CTK45 sai: client gửi đủ số lượng
nhưng sai thứ tự thì mô hình vẫn chạy trơn và trả toạ độ sai không cảnh báo.
`artifacts/feature_list.json` là nguồn sự thật duy nhất về thứ tự cột.

## Web Dashboard

Không cần máy chủ tĩnh riêng: chính `uvicorn` ở trên phục vụ luôn giao diện.

```bash
uvicorn backend.main:app      # rồi mở http://127.0.0.1:8000
```

Trang hiển thị sơ đồ mặt bằng với 40 điểm tham chiếu và marker của thiết bị đang
định vị kèm vệt đường đã đi, bảng thiết bị đang kết nối, hộp chỉ đường, biểu đồ
hiệu quả bước gộp, và lịch sử định vị.

Viết bằng HTML + CSS + JavaScript thuần, **không nạp thư viện ngoài** — thêm một
gói CDN là thêm một thứ phải có mạng mới chạy. Dùng ES module nên bắt buộc mở
qua `http://`; mở thẳng tệp bằng `file://` sẽ bị trình duyệt chặn.

Phép đổi mét ↔ pixel của sơ đồ nằm ở ba nơi (Python, Dart, JavaScript) và
`tests/test_dashboard.py` đối chiếu cả ba với `data/reference/ban_do_tang1.json`:
lệch nhau thì cùng một toạ độ hiện ở hai chỗ khác nhau trên hai màn hình.

## Cấu trúc thư mục

| Thư mục | Nội dung |
|---|---|
| `data/` | Dữ liệu thô, đã xử lý, tập chia, số liệu đo đạc tham chiếu, sơ đồ mặt bằng |
| `artifacts/` | **Hợp đồng giữa ML và Backend**: `feature_list.json`, `scaler.pkl`, model |
| `notebooks/` | Notebook chạy trên Google Colab |
| `ml/` | Mã nguồn tiền xử lý và huấn luyện, tái sử dụng được |
| `mobile/` | Ứng dụng Flutter — 5 màn hình, song ngữ, sáng/tối, quét WiFi thật |
| `backend/` | FastAPI + WebSocket + SQLite — 9 endpoint, đã chạy |
| `frontend/` | Web Dashboard — HTML/CSS/JS thuần, không thư viện ngoài |
| `tools/` | Công cụ chạy một lần rồi commit kết quả (trích hình học từ sơ đồ) |
| `tests/` | Kiểm thử tự động |
| `reports/` | Biểu đồ và bảng phục vụ viết báo cáo |
| `docs/` | Tài liệu phân tích, thiết kế |

Chi tiết đầy đủ: `docs/Cau_Truc_Thu_Muc_Du_An.md`

## Nguyên tắc quan trọng

1. **`artifacts/` là nguồn sự thật duy nhất** cho việc tiền xử lý. Backend đọc
   `feature_list.json` để ánh xạ BSSID theo đúng thứ tự cột đã học — không hardcode.
2. **Không fit scaler trên toàn bộ dataset**. Chỉ fit trên tập train, sau đó transform
   cho validation/test để tránh rò rỉ dữ liệu.
3. **Không commit thông tin nhạy cảm**. Mọi cấu hình đọc từ biến môi trường qua `.env`.
4. **Chỉ commit dữ liệu không sinh lại được** — `data/reference/reference_points.csv`
   là số liệu đo đạc thực tế nên phải commit; `train.csv` sinh ra từ pipeline thì không.
5. **`data/reference/` là nguồn sự thật duy nhất về không gian.** Toạ độ điểm
   tham chiếu, sơ đồ `Map.png` và hình học suy ra từ nó (`ban_do_tang1.json`)
   đều nằm ở đây. Backend, ứng dụng di động và Dashboard đọc lại từ đó chứ không
   tự giữ bản riêng — trừ ảnh sơ đồ trong `mobile/assets/`, vì Flutter chỉ đóng
   gói được asset nằm trong `mobile/`.

## Tài liệu

- `docs/Phan_Tich_Thiet_Ke_He_Thong.md` — phân tích & thiết kế hệ thống
- `docs/Phan_Tich_Ky_Thuat_DoAnCu_va_Cai_Tien.md` — phân tích đồ án kế thừa và cải tiến
- `docs/Cau_Truc_Thu_Muc_Du_An.md` — cấu trúc thư mục
