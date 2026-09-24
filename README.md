# Hệ thống định vị trong nhà bằng WiFi Fingerprinting

Đồ án tốt nghiệp — Nhóm 15, Khoa Công nghệ Thông tin, Trường Đại học Đà Lạt.
GVHD: TS. Nguyễn Thị Lương.

Nghiên cứu hệ thống định vị trong nhà bằng kỹ thuật WiFi Fingerprinting và xây dựng
**ứng dụng di động Android** định vị theo thời gian thực, chỉ đường tới địa điểm
được chọn (đề cương bản 24.9, `docs/[24.9]Nhom15_DeCuong_DATN_edited_v3.docx`).
Ứng dụng di động là sản phẩm chính; Web Dashboard là công cụ giám sát cho quản
trị viên.

## Bài toán

- **Input**: vector cường độ tín hiệu RSSI từ các Access Point `[AP_1, ..., AP_n]`
- **Output**: tọa độ người dùng `(x, y)` trên lưới mặt bằng (đơn vị lưới của
  Bảng 4 CTK45); nhân `0,3508` ra mét
- **Đánh giá**: `error = sqrt((x_pred - x_true)² + (y_pred - y_true)²)`, kèm CDF
  tại các mức 50%, 75%, 90%

> **Đơn vị.** Mọi bảng trong `reports/tables/` và mọi số in ra từ `ml.*` tính theo
> **đơn vị lưới**, không phải mét, dù tên cột có chữ `_m`. Riêng `quet_k.csv`,
> `mlp.csv` có thêm cột `*_m` đã quy đổi, và `ket_hop.csv` ghi thẳng mét. Các
> bảng trong tài liệu này đã quy ra mét.

Đề cương phát biểu bài toán dưới dạng **hồi quy toạ độ** chứ không phân lớp điểm
tham chiếu, để đánh giá trực tiếp bằng mét. Mô hình cơ sở đối chứng theo đề cương:
**kNN và WKNN**; mô hình đề xuất ban đầu: **XGBoost Regression**. Làm thêm: Random
Forest, kNN vân tay (Bray-Curtis), hai mạng MLP, và **kNN vân tay k động** — mô
hình kết hợp đang được triển khai.

Kết quả **phụ thuộc vào cách chia dữ liệu**, nên báo cáo bằng hai giao thức chứ
không một. Mỗi điểm tham chiếu chỉ được đo trong đúng một phiên chừng 14 phút,
cùng máy, cùng ngày; chia ngẫu nhiên theo lần quét thì cả 40 điểm đều có mặt
đồng thời ở train lẫn test, và 75% bản ghi test có láng giềng train gần nhất nằm
ngay tại điểm của chính nó.

Sai số trung bình, **mét**:

| Mô hình | Chia ngẫu nhiên (seed 42) | Chia ngẫu nhiên, 10 seed | Bỏ trọn một điểm tham chiếu |
|---|---:|---:|---:|
| **kNN vân tay, k động** (triển khai) | **1,13 m** ① | 1,02 ± 0,12 m | **4,84 m** ① |
| XGBoost | 2,57 m | 2,46 ± 0,14 m | 5,25 m |
| WKNN | 1,23 m | 1,36 ± 0,14 m | 5,42 m |
| Random Forest | 2,43 m | 2,32 ± 0,23 m | 5,42 m |
| kNN vân tay, k = 1 | 1,21 m | **0,91 ± 0,13 m** ① | 5,71 m |
| kNN | 1,21 m | 1,20 ± 0,22 m | 5,83 m |
| MLP phân lớp | — | 2,27 ± 0,36 m | 5,04 m |
| MLP hồi quy | — | 2,91 ± 0,18 m | 4,89 m |

Hai cột chia ngẫu nhiên là **chặn lạc quan**: chúng đo "nhận lại được lần quét vài
phút trước, cùng chỗ, cùng máy không". Cột cuối là **chặn bi quan**: toạ độ cần
đoán chưa từng xuất hiện lúc học, mà các điểm cách điểm gần nhất trung vị 2,5 m;
mỗi lần gấp làm lại bước 5-10 chỉ trên phần học để điểm bị giữ không rò vào bộ
AP, giá trị điền hay Hampel. Thứ hạng đảo ngược giữa hai giao thức — chia ngẫu
nhiên thưởng cho mô hình biết ghi nhớ phiên đo. Seed 42 là cách chia xấu bất
thường cho kNN vân tay (dẫn đầu 7/10 seed), nên con số của riêng seed 42 phải đọc
kèm cột giữa. Hai dòng MLP chạy riêng bằng `ml.mlp`, không có cột seed 42.

Sai số lúc triển khai nằm giữa hai chặn. Chốt được nó cần một đợt đo lần hai tại
chính 40 điểm cũ, khác ngày và khác máy; xem mục **Hạn chế đã biết**. Sinh
lại bảng bằng `python -m ml.train`, `python -m ml.on_dinh` và `python -m ml.danh_gia_cheo`.

### Mô hình đang triển khai: kNN vân tay, k động

`ml.quet_k` cho thấy không có một k cố định nào tốt cho cả hai giao thức: k = 1
tốt nhất khi điểm đã khảo sát (0,91 m) nhưng tệ khi chưa (5,71 m); k = 41 ngược
lại (2,75 m và 4,57 m). Máy chủ không biết người dùng đứng đâu, nhưng biết lần
quét giống vân tay đã có tới mức nào — khoảng cách Bray-Curtis tới vân tay gần
nhất, d1:

    d1 < 0,19  ->  k = 1   (trả đúng toạ độ điểm đã khảo sát)
    ngược lại  ->  k = 31  (nội suy giữa các điểm lân cận)

Ngưỡng và k lớn **tự chọn lúc `fit`**, chỉ trên dữ liệu học, bằng hai tình huống
giả lập nặng như nhau: chia ngẫu nhiên 80/20 (đã khảo sát) và bỏ trọn từng điểm
(chưa khảo sát). Trên test khoảng 70% lần quét dùng k = 1; mỗi lần dự đoán ~10 ms.

Mô hình triển khai **chỉ định** bằng `MO_HINH_TRIEN_KHAI` trong `ml/config.py`
chứ không lấy mô hình có sai số validation thấp nhất: validation chia ngẫu nhiên
nên luôn chọn k = 1. Đặt `None` để quay về chọn theo validation. So sánh các cách
kết hợp khác (trung bình hai k, trung bình kNN + XGBoost, trộn mềm) ở
`python -m ml.ket_hop`. `GET /health` luôn cho biết mô hình nào đang chạy.

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

Chỉ `scaler.pkl`, `model_fingerprint_knn_dong.pkl` (đang triển khai) và
`model_fingerprint_knn.pkl` (k = 1, để quay lui) được commit. Muốn có đủ sáu mô
hình, biểu đồ và bảng thì chạy các lệnh ở mục dưới.

## Chạy phần máy học

```bash
# 1. Tiền xử lý 12 bước -> artifacts/ + data/splits/
python -m ml.pipeline

# 2. Rà soát dữ liệu trước khi huấn luyện (rò rỉ, độ ổn định, chất lượng buổi thu)
python -m ml.audit

# 3. Huấn luyện và so sánh 6 mô hình -> artifacts/*.pkl + reports/tables/
python -m ml.train
python -m ml.train --nhanh              # lưới tham số rút gọn, dùng lúc thử
python -m ml.train --mo-hinh knn wknn   # chỉ chạy một số mô hình

# 4. Sinh biểu đồ cho báo cáo -> reports/figures/
python -m ml.report

# 5. Độ ổn định qua 10 seed, và giao thức bỏ trọn một điểm -> reports/tables/
python -m ml.on_dinh
python -m ml.danh_gia_cheo

# 6. Thí nghiệm bổ sung -> reports/tables/ (+ reports/figures/quet_k.png)
python -m ml.quet_k      # quét k = 1..61 cho kNN, WKNN, kNN vân tay, ba cách đánh giá
python -m ml.mlp         # hai mạng MLP (hồi quy, phân lớp), ~4 phút
python -m ml.ket_hop     # các cách kết hợp mô hình, gồm k động, ~3,5 phút

# 7. Chỉ đường: sai số quãng đường, và so sánh 6 thuật toán tìm đường -> reports/tables/
python -m tools.danh_gia_chi_duong
python -m tools.so_sanh_tim_duong

# Kiểm thử
python -m pytest tests/ -q
```

Chạy đúng thứ tự trên: `ml.train` cần artifact do `ml.pipeline` sinh ra, và
`ml.report` đọc kết quả của `ml.train`.

## Chạy ứng dụng di động

> Ứng dụng di động là **sản phẩm chính** theo đề cương bản 24.9: người dùng cuối
> định vị, xem bản đồ và được chỉ đường trên app. Web Dashboard chỉ là công cụ
> giám sát.

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

## Web Dashboard (giám sát)

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

## Đối chiếu với đề cương

Đề cương bản v4 (`docs/[24.9]Nhom15_DeCuong_DATN_edited_v4.docx`) — từng mục ánh
xạ sang chỗ nào trong kho:

| Mục đề cương | Trong kho | Trạng thái |
|---|---|---|
| I.1. Ứng dụng di động Android là sản phẩm chính | `mobile/` | Đã làm |
| I.2. Mô hình học máy sai số thấp hơn kNN, WKNN | `ml/models/fingerprint_knn_dong.py`, bảng ở đầu tài liệu | Đã làm; thấp hơn ở giao thức bỏ trọn một điểm, xem ghi chú dưới bảng |
| I.3. Back-end phục vụ định vị, bản đồ, tìm đường; kèm Web giám sát | `backend/`, `frontend/` | Đã làm |
| II. Phạm vi — tầng 1, định vị 2D, kết quả ở mức khu vực | Toàn bộ dữ liệu và bản đồ là tầng 1; `ml.audit` mục 4 kiểm giả thiết một mặt phẳng | Đúng phạm vi |
| III + Chương 3.1. Tiền xử lý RSSI tái lập được | `ml/preprocess.py`, `ml/pipeline.py` — 12 bước | Đã làm |
| III + Chương 3.2. Mô hình cơ sở và mô hình so sánh | `ml/models/`, `ml/mlp.py` | Đã làm |
| III + Chương 3.3. Khảo sát k, đề xuất mô hình kết hợp k động | `ml/quet_k.py`, `ml/ket_hop.py`, `ml/models/fingerprint_knn_dong.py` | Đã làm |
| Chương 2. Phân tích và thiết kế hệ thống | `docs/Phan_Tich_Thiet_Ke_He_Thong.md` | Đã làm |
| Chương 3.4. Hậu xử lý gộp lần quét, ánh xạ về khu vực | `ml/postprocess.py`, `backend/services/smoothing_service.py` | Đã làm, **khác cách**: đồng thuận không gian thay EMA |
| Chương 4.1–4.2. Thực nghiệm, CDF 50/75/90, hai giao thức | `reports/tables/`, `reports/figures/` | Đã làm |
| Chương 4.3. Kiểm thử thực địa; đánh giá theo mật độ người | Đã kiểm luồng định vị và chỉ đường trên máy Android thật | **Chưa chạy trọn vẹn tại thư viện**, và phần mật độ người chưa làm được — xem Hạn chế đã biết |
| Chương 5.1–5.2. Back-end và ứng dụng Flutter | `backend/`, `mobile/` | Đã làm |
| Chương 5.3. Chỉ đường, so sánh thuật toán tìm đường | `backend/services/routing_service.py`, `tools/so_sanh_tim_duong.py` | Đã làm |
| Chương 5.4–5.5. Web giám sát, kết quả giao diện | `frontend/`, `tests/` | Đã làm |
| V. Công cụ | Python, FastAPI, Uvicorn, Flutter/Dart, scikit-learn, XGBoost, NumPy, Pandas, SQLite, Colab, Git | Đúng đề cương |
| VI.1–VI.3. Dữ liệu sạch, mô hình kết hợp, bảng so sánh | `data/`, `artifacts/`, `reports/` | Đã làm |
| VI.4–VI.7. Back-end, ứng dụng, chỉ đường, Web giám sát | `backend/`, `mobile/`, `frontend/` | Đã làm |

Hai chỗ làm khác đề cương, đều cố ý:

1. **Hậu xử lý dùng đồng thuận không gian thay cho EMA**: chọn dự đoán có tổng
   khoảng cách tới các dự đoán còn lại nhỏ nhất, nên loại được lần quét dị
   thường lẻ loi thay vì bị nó kéo trung bình. Lý do và số đo ở
   `docs/Phan_Tich_Thiet_Ke_He_Thong.md` §2.4.1.
2. **WebSocket là kênh dự phòng đúng như mục V của đề cương**: hai lối truyền
   thời gian thực chọn bằng `WEBSOCKET` trong `.env`, cấu hình mặc định trong
   kho đi REST theo chu kỳ quét.

## Cấu trúc thư mục

| Thư mục | Nội dung |
|---|---|
| `data/` | Dữ liệu thô, đã xử lý, tập chia, số liệu đo đạc tham chiếu, sơ đồ mặt bằng |
| `artifacts/` | **Hợp đồng giữa ML và Backend**: `feature_list.json`, `scaler.pkl`, model |
| `notebooks/` | Notebook chạy trên Google Colab |
| `ml/` | Mã nguồn tiền xử lý và huấn luyện, tái sử dụng được |
| `mobile/` | **Sản phẩm chính**: ứng dụng Flutter — 5 màn hình, song ngữ, sáng/tối, quét WiFi thật |
| `backend/` | FastAPI + SQLite — 8 endpoint, đã chạy |
| `frontend/` | Web Dashboard giám sát — HTML/CSS/JS thuần, không thư viện ngoài |
| `tools/` | Công cụ chạy một lần rồi commit kết quả (trích hình học từ sơ đồ) |
| `tests/` | Kiểm thử endpoint REST API (`test_api.py`) |
| `reports/` | Biểu đồ và bảng phục vụ viết báo cáo |
| `docs/` | Tài liệu phân tích, thiết kế |

Chi tiết đầy đủ: `docs/Cau_Truc_Thu_Muc_Du_An.md`


## Hạn chế đã biết

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
- `docs/tai_lieu_tham_khao/` — bốn công trình liên quan đã đọc, dùng trong slide khảo sát
