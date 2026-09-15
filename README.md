# Hệ thống định vị trong nhà bằng WiFi Fingerprinting

Đồ án tốt nghiệp — Nhóm 15, Khoa Công nghệ Thông tin, Trường Đại học Đà Lạt.
GVHD: TS. Nguyễn Thị Lương.

Nghiên cứu hệ thống định vị trong nhà bằng kỹ thuật WiFi Fingerprinting và xây dựng
Web Dashboard hiển thị vị trí người dùng theo thời gian thực — đúng hai mục tiêu
ở mục I của đề cương.

## Bài toán

- **Input**: vector cường độ tín hiệu RSSI từ các Access Point `[AP_1, ..., AP_n]`
- **Output**: tọa độ người dùng `(x, y)` theo đơn vị mét
- **Đánh giá**: `error = sqrt((x_pred - x_true)² + (y_pred - y_true)²)`, kèm CDF
  tại các mức 50%, 75%, 90%

Đề cương phát biểu bài toán dưới dạng **hồi quy toạ độ** chứ không phân lớp điểm
tham chiếu, để đánh giá trực tiếp bằng mét. Mô hình chính: **XGBoost Regression**.
Mô hình cơ sở đối chứng theo đề cương: **kNN và WKNN**; Random Forest và kNN vân
tay là hai mô hình làm thêm, không nằm trong đề cương.

Kết quả **phụ thuộc vào cách chia dữ liệu**, nên báo cáo bằng hai giao thức chứ
không một. Mỗi điểm tham chiếu chỉ được đo trong đúng một phiên chừng 15 phút,
cùng máy, cùng ngày; chia ngẫu nhiên theo lần quét thì cả 40 điểm đều có mặt
đồng thời ở train lẫn test, và 75% bản ghi test có láng giềng train gần nhất nằm
ngay tại điểm của chính nó.

| Mô hình | Chia ngẫu nhiên (seed 42) | Chia ngẫu nhiên, 10 seed | Bỏ trọn một điểm tham chiếu |
|---|---:|---:|---:|
| **XGBoost** | 7,02 m | 6,87 ± 0,38 m | **14,80 m** ① |
| WKNN | 3,51 m | 3,88 ± 0,40 m | 15,44 m |
| Random Forest | 6,92 m | 6,61 ± 0,66 m | 15,45 m |
| kNN vân tay | 3,45 m | **2,58 ± 0,36 m** ① | 16,29 m |
| kNN | **3,44 m** ① | 3,41 ± 0,63 m | 16,63 m |

Hai cột chia ngẫu nhiên là **chặn lạc quan**: chúng đo "nhận lại được lần quét vài phút trước, cùng
chỗ, cùng máy không". Cột cuối là **chặn bi quan**: toạ độ cần đoán chưa từng
xuất hiện lúc học, mà lưới điểm cách nhau trung vị 7 m; mỗi lần gấp làm lại bước
5-10 chỉ trên phần học để điểm bị giữ không rò vào bộ AP, giá trị điền hay
Hampel. Thứ hạng đảo ngược hoàn
toàn giữa hai giao thức — cách chia ngẫu nhiên thưởng cho mô hình biết ghi nhớ phiên
đo và phạt mô hình hồi quy liên tục, tức phạt đúng XGBoost. Cột giữa chia lại
10 seed với cùng tham số: seed 42 là cách chia xấu bất thường cho kNN vân tay
(3,45 m, cao hơn cả 10 seed kia, dẫn đầu 9/10 seed), nên con số tính từ riêng
seed 42 phải đọc kèm cột này.

Sai số lúc triển khai nằm giữa hai chặn. Chốt được nó cần một đợt đo lần hai tại
chính 40 điểm cũ, khác ngày và khác máy; xem mục **Hạn chế đã biết**. Sinh
lại bảng bằng `python -m ml.train`, `python -m ml.on_dinh` và `python -m ml.danh_gia_cheo`.

Mô hình **đang được triển khai** chọn theo sai số trên tập validation — mà tập
validation chia theo cùng cách ngẫu nhiên nên mang cùng phần rò rỉ — và hiện là
`kNN vân tay (Bray-Curtis)`. Ứng dụng chỉ đường cần toạ độ xuất phát sát nhất có
căn cứ đo được, nên mô hình triển khai đi theo số đo; XGBoost vẫn là mô hình
chính của phần nghiên cứu. `GET /health` luôn cho biết mô hình nào đang chạy.
Chi tiết ở `docs/Phan_Tich_Thiet_Ke_He_Thong.md` §2.4.1.

## Cài đặt

Cần **Python 3.14** 64-bit (các phiên bản trong `requirements.txt` ghim theo máy đã
chạy trọn dự án) và, nếu chạy ứng dụng di động, **Flutter 3.47** cùng Android SDK.
Trên Windows nên clone hoặc giải nén vào đường dẫn ngắn (ví dụ `D:\System_Indoor`):
đường dẫn quá dài làm bước biên dịch shader khi build APK vượt giới hạn 260 ký tự.

```bash
git clone <địa chỉ kho> System_Indoor
cd System_Indoor
python -m venv venv
venv\Scripts\activate           # Windows; macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -q       # 59 kiểm thử, không cần chạy pipeline trước
uvicorn backend.main:app         # chạy được ngay: kho đã kèm scaler.pkl và mô hình đang triển khai
```

Chỉ `scaler.pkl` và `model_fingerprint_knn.pkl` được commit. Muốn có đủ năm mô
hình, biểu đồ và bảng thì chạy các lệnh ở mục dưới.

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

# 5. Độ ổn định qua 10 seed, và giao thức bỏ trọn một điểm -> reports/tables/
python -m ml.on_dinh
python -m ml.danh_gia_cheo

# 6. Sai số quãng đường chỉ đường so với đường ngắn nhất thật -> reports/tables/
python -m tools.danh_gia_chi_duong

# Kiểm thử
python -m pytest tests/ -q
```

Chạy đúng thứ tự trên: `ml.train` cần artifact do `ml.pipeline` sinh ra, và
`ml.report` đọc kết quả của `ml.train`.

## Chạy ứng dụng di động

> Đề cương chỉ yêu cầu ứng dụng **Web**. Ứng dụng di động là phần làm thêm: nó
> là nguồn quét WiFi cho hệ thống và là cách kiểm thử thực địa, không thay thế
> Web Dashboard.

```bash
cd mobile
flutter pub get
flutter run          # cần máy Android thật hoặc máy ảo đang bật
flutter test
flutter analyze
```

Ứng dụng **quét WiFi thật** và gửi lên qua `POST /predict` mỗi 5 giây. Chu kỳ
5 giây do Android chặn ở 4 lần quét mỗi 2 phút quyết định. Kênh WebSocket đang
tạm tắt (`_dungWebSocket` trong `mobile/lib/main.dart`). Tab Bản đồ vẽ sơ đồ mặt bằng đã số hoá kèm chấm vị trí và
nón hướng la bàn; màn Chi tiết khu vực hiện ảnh thật và mô tả lấy từ `GET /map`.

Địa chỉ máy chủ sửa được trong Cài đặt — mặc định `http://10.0.2.2:8000` là lối
tắt máy ảo Android gọi về máy đang chạy nó, điện thoại thật phải đổi sang IP nội
bộ. Danh sách "Gần bạn" và kết quả tìm kiếm cũng lấy từ `GET /map`, sắp theo
khoảng cách thật tới chỗ đang đứng; chưa nối được máy chủ thì lùi về bản 12 khu
vực nhúng sẵn trong ứng dụng.

Giao diện đủ 5 màn hình, hai ngôn ngữ Việt/Anh và chế độ sáng/tối. Địa chỉ máy
chủ, ngôn ngữ và chế độ sáng/tối được nhớ giữa hai lần mở app. Chi tiết ở
`mobile/README.md`.

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
| `WS /ws/location` | **Tạm tắt** — trả 403. Bật bằng `WEBSOCKET=true`: gửi lần quét, nhận toạ độ; dashboard chỉ xem thì nhận toạ độ của mọi thiết bị |
| `GET /map` | Toàn bộ dữ liệu không gian trong một response: phạm vi, điểm tham chiếu, thống kê đồ thị. Toạ độ theo đơn vị lưới Bảng 4; `met_moi_don_vi` (0,3508, lấy từ Hình 7 báo cáo CTK45) đổi ra mét |
| `GET /graph` | Danh sách cạnh của đồ thị đi lại. Cạnh có `cua_gia_dinh: true` là 15 chỗ nhóm tự nối tay vì `Map.png` không vẽ cửa — chưa ai đối chiếu thực địa |
| `POST /route` | Đường ngắn nhất từ đúng vị trí người dùng, đi qua góc vật cản trên sơ đồ, bằng A* (mặc định) hoặc Dijkstra (`thuat_toan`) — mục 4.3 báo cáo CTK45. Điểm đầu cho bằng `tu_rp` hoặc toạ độ lưới; đích cho bằng `den_rp`, hoặc `den_nhom` để máy chủ chọn điểm gần nhất **theo đường đi**. Quãng đường và `chi_dan` tính bằng mét; kèm `so_nut_mo` để so hai thuật toán |
| `GET /map/so-do.png` | Ảnh sơ đồ mặt bằng, phục vụ thẳng từ `data/reference/Map.png` |
| `GET /` | Web Dashboard (xem mục dưới) |

Khi WebSocket tắt, Dashboard hỏi `GET /predictions` mỗi 2 giây để vẽ thiết bị
đang định vị; `/health` trả `websocket` để Dashboard biết đi lối nào. Bật lại thì
`WS /ws/location` và `POST /predict` đi chung một đường xử lý như trước.

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

Trang hiển thị sơ đồ mặt bằng với 44 điểm tham chiếu và marker của thiết bị đang
định vị kèm vệt đường đã đi, bảng thiết bị đang kết nối, hộp chỉ đường, biểu đồ
hiệu quả bước gộp, và lịch sử định vị.

Viết bằng HTML + CSS + JavaScript thuần, **không nạp thư viện ngoài** — thêm một
gói CDN là thêm một thứ phải có mạng mới chạy. Dùng ES module nên bắt buộc mở
qua `http://`; mở thẳng tệp bằng `file://` sẽ bị trình duyệt chặn.

Phép đổi toạ độ ↔ pixel của sơ đồ nằm ở ba nơi (Python, Dart, JavaScript), cùng
lấy số từ `data/reference/ban_do_tang1.json`: lệch nhau thì cùng một toạ độ hiện ở
hai chỗ khác nhau trên hai màn hình.

## Cấu trúc thư mục

| Thư mục | Nội dung |
|---|---|
| `data/` | Dữ liệu thô, đã xử lý, tập chia, số liệu đo đạc tham chiếu, sơ đồ mặt bằng |
| `artifacts/` | **Hợp đồng giữa ML và Backend**: `feature_list.json`, `scaler.pkl`, model |
| `notebooks/` | Notebook chạy trên Google Colab |
| `ml/` | Mã nguồn tiền xử lý và huấn luyện, tái sử dụng được |
| `mobile/` | Ứng dụng Flutter — 5 màn hình, song ngữ, sáng/tối, quét WiFi thật |
| `backend/` | FastAPI + SQLite, WebSocket tạm tắt — 8 endpoint, đã chạy |
| `frontend/` | Web Dashboard — HTML/CSS/JS thuần, không thư viện ngoài |
| `tools/` | Công cụ chạy một lần rồi commit kết quả (trích hình học từ sơ đồ) |
| `tests/` | Kiểm thử endpoint REST API (`test_api.py`) |
| `reports/` | Biểu đồ và bảng phục vụ viết báo cáo |
| `docs/` | Tài liệu phân tích, thiết kế |

Chi tiết đầy đủ: `docs/Cau_Truc_Thu_Muc_Du_An.md`


**Không có xác thực.** Dashboard phục vụ ở `/`, và `GET /predictions` (hoặc
WebSocket khi bật) trả toạ độ của mọi thiết bị, kèm `device_id`. Ai vào được mạng LAN cũng xem
được toàn bộ. `ALLOWED_ORIGINS` mặc định là `*`. Chấp nhận được cho một hệ thống
chạy trong mạng nội bộ thư viện lúc demo, nhưng phải thêm xác thực trước khi
dùng thật.

**Chưa có đợt đo lần hai, nên chưa chốt được sai số triển khai.** Bảng hai cột ở
đầu tài liệu cho một chặn lạc quan và một chặn bi quan, không cho con số thật.
Chốt nó cần thu lại tại chính 40 điểm cũ vào ngày khác, máy khác, rồi huấn luyện
trên đợt 1 và kiểm trên đợt 2. Chuyến đo ấy đồng thời giải quyết được 15 cửa
giả định, và phương vị toà nhà hiện chỉ đo trên ảnh vệ tinh.

**Quãng đường là cận dưới.** Tuyến ôm sát góc vật cản; sai lệch so với đường
ngắn nhất trên sơ đồ trung bình 0,03 m (trừ tuyến qua RP01, RP03, xem dưới), nhưng người đi thật không đi sát tường. Tỉ
lệ 0,3508 m/đơn vị lấy từ kích thước ghi trên Hình 7 CTK45 và khớp với đa giác
toà nhà trên OpenStreetMap, chưa đo bằng thước.

**15 cửa ra vào là giả định.** `Map.png` vẽ tường nhưng không vẽ cửa. Trong
`tools/trich_ban_do.py`, `CUA_CU` giữ sáu cửa vòng nối tự động từng chọn (bỏ
18-20), `CUA_NHOM_CHI_DINH` thêm chín cạnh nhóm chỉ định (26-19, 27-19, 29-20,
32-21, 06-02, 20-26, 21-27, 05-45, 06-44); tất cả ghi vào `cua_gia_dinh` trong
`ban_do_tang1.json`. Cửa là cạnh nối đúng hai điểm, không mở lối trên mặt nạ. Các
cạnh này chưa được đối chiếu thực địa; đường đi qua chúng có thể không đi được thật.

**Luật nối nhóm chỉ định.** `CHI_NOI`: RP01 chỉ nối RP45, RP02; RP03 chỉ nối RP44,
RP02 — tuyến tới hay rời hai điểm này buộc đi qua các điểm đó, kể cả khi đường
thẳng ngắn hơn. `CAM_NOI`: bỏ cạnh 18-20, 45-12, 45-13, 45-20, 44-14, 44-15, 44-21.
`KHONG_NOI`: hai WC RP42, RP43 không nối điểm tham chiếu nào, chỉ là đích, tới qua
góc lối đi. Điểm xuất phát theo luật của điểm tham chiếu gần nhất.

**Nhãn "RP41" trong dữ liệu thô là RP26.** 20 lần quét RP41 (13/01/2025, giữa phiên
RP27 và RP28) trùng khít 20 dòng RP26 trong dữ liệu đã xử lý của CTK45, và báo
cáo CTK45 chỉ có RP01–RP40. Pipeline đổi nhãn lúc nạp (`NHAN_RP_SUA` trong
`ml/config.py`), không sửa tệp thô; nhờ vậy dùng đủ 802 lần quét, 40 điểm.

**`device_holdout` và `time_holdout` không thực hiện được** với bộ dữ liệu hiện
có — một máy đo, mỗi điểm chỉ đo một buổi. Xem mục 2.4.1 của tài liệu thiết kế.

**Chưa đánh giá độ ổn định theo mật độ người** (mục 4.3 của đề cương). Bộ dữ
liệu kế thừa không ghi lại số người có mặt lúc đo, nên muốn làm phải tổ chức một
đợt đo mới ở hai khung giờ đông và vắng.


## Tài liệu

- `docs/Phan_Tich_Thiet_Ke_He_Thong.md` — phân tích & thiết kế hệ thống
- `docs/Phan_Tich_Ky_Thuat_DoAnCu_va_Cai_Tien.md` — phân tích đồ án kế thừa và cải tiến
- `docs/Cau_Truc_Thu_Muc_Du_An.md` — cấu trúc thư mục
