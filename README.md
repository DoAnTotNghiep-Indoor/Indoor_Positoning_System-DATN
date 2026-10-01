# Hệ thống định vị trong nhà bằng WiFi Fingerprinting

Đồ án tốt nghiệp — Nhóm 15, Khoa Công nghệ Thông tin, Trường Đại học Đà Lạt.
GVHD: TS. Nguyễn Thị Lương.

Hệ thống định vị người dùng trong tầng 1 Thư viện Đại học Đà Lạt từ cường độ sóng WiFi
(RSSI) mà điện thoại quét được, rồi chỉ đường tới khu vực người dùng chọn.

## Thành phần

| Thành phần | Thư mục | Làm gì |
|---|---|---|
| Ứng dụng Android (Flutter) | `mobile/` | Quét WiFi mỗi 5 giây, hiện vị trí và nón hướng la bàn trên sơ đồ, tra cứu khu vực, chỉ đường. Song ngữ Việt/Anh, sáng/tối |
| Backend (FastAPI + SQLite) | `backend/` | Dự đoán toạ độ, gộp các lần quét, lưu lịch sử, phục vụ bản đồ và tìm đường |
| Web Dashboard | `dashboard/` | Giám sát: sơ đồ với các thiết bị đang định vị và vệt đường, bảng thiết bị, thử chỉ đường, lịch sử. HTML/CSS/JS thuần, không thư viện ngoài |
| Máy học | `ml/` | Tiền xử lý 12 bước, huấn luyện và so sánh 5 mô hình, đánh giá, vẽ biểu đồ |
| Công cụ | `tools/` | Trích hình học từ sơ đồ, vẽ sơ đồ SVG cho app, sinh danh sách khu vực, thu vân tay qua cáp USB, đánh giá chỉ đường |

## Hoạt động

### Định vị

1. App quét WiFi, gửi `POST /predict` với `{device_id, scan: [{bssid, rssi}]}`.
2. Backend ánh xạ từng BSSID vào đúng cột của vector đặc trưng theo
   `artifacts/feature_list.json` (36 AP). Thứ tự gửi không ảnh hưởng. BSSID lạ bị bỏ qua.
   RSSI ngoài khoảng vật lý cũng bị bỏ. AP vắng mặt điền −100 dBm.
3. Vector qua scaler rồi vào mô hình **kNN k động** (Dynamic-k kNN), ra toạ độ `(x, y)`.
4. Khớp ít hơn 6 AP (ngưỡng đã dùng để loại mẫu huấn luyện) thì trả 422 `khong_du_ap`
   thay vì đoán bừa. Đứng ngoài thư viện sẽ rơi vào trường hợp này.
5. Toạ độ được gộp với 2 lần quét trước của cùng thiết bị bằng **đồng thuận không gian**:
   chọn dự đoán có tổng khoảng cách tới các dự đoán còn lại nhỏ nhất. Cách này loại được
   một lần quét lạc thay vì bị nó kéo lệch như khi lấy trung bình. Im lặng quá 30 giây
   thì bắt đầu lại.
6. Ghi cả toạ độ thô lẫn toạ độ đã gộp vào SQLite (`data/ips.db`), trả kết quả về app.

Android chỉ cho app quét 4 lần mỗi 2 phút nên chu kỳ 5 giây là giới hạn của hệ điều hành.
Vì vậy hệ thống dùng REST: Dashboard hỏi `GET /predictions` mỗi 2 giây.

### Mô hình kNN k động (Dynamic-k kNN)

Không có k cố định nào tốt cho mọi chỗ: k = 1 trả đúng toạ độ khi người dùng đứng ở điểm
đã khảo sát nhưng tệ khi đứng giữa các điểm; k lớn thì ngược lại. Mô hình dựa vào khoảng
cách Bray-Curtis d1 từ lần quét tới vân tay gần nhất:

    d1 < 0,159  ->  k = 1   (trả đúng toạ độ điểm đã khảo sát)
    ngược lại   ->  k = 15  (nội suy giữa các điểm lân cận)

Ngưỡng và k lớn tự chọn lúc `fit`, chỉ trên dữ liệu học, bằng hai tình huống giả lập: chia
ngẫu nhiên 80/20 (đã khảo sát) và bỏ trọn từng điểm (chưa khảo sát). Trên tập test, khoảng
một nửa số lần quét dùng k = 1. Mô hình triển khai đặt bằng `MO_HINH_TRIEN_KHAI` trong
`ml/config.py`. `GET /health` cho biết mô hình nào đang chạy.

### Bản đồ và toạ độ

Sơ đồ gốc là `data/reference/Map.png` (bản số hoá tầng 1 của nhóm CTK45).
`tools/trich_ban_do.py` tách tường khỏi lưới chấm, dò vật cản rồi ghi hình học vào
`data/reference/ban_do_tang1.json`. Backend chỉ đọc tệp JSON này.

Toạ độ dùng **đơn vị lưới** của bảng điểm tham chiếu (x từ −43 đến 43, y từ 0 đến 52, y = 0
ở cửa ra vào). Một đơn vị bằng **0,3508 m**, lấy từ kích thước ghi trên bản vẽ CTK45 và khớp
với đa giác toà nhà trên OpenStreetMap. Phép đổi toạ độ ↔ pixel có ở ba nơi (Python, Dart,
JavaScript), cùng lấy hằng số từ `ban_do_tang1.json`.

App vẽ sơ đồ SVG (`mobile/assets/map/`, do `tools/ve_so_do_tang1.py` vẽ theo sơ đồ của
trường) đặt trong cùng khung pixel với `Map.png`. Dashboard dùng thẳng `Map.png`.

### Chỉ đường

`POST /route` tìm đường ngắn nhất từ đúng vị trí người dùng (không neo về điểm tham chiếu
gần nhất) tới một điểm hoặc một khu vực:

- **Đồ thị**: nút là 286 góc lồi của vật cản dò từ `Map.png`, cộng 44 điểm tham chiếu. Cạnh
  nối các cặp nhìn thấy nhau. Đường ngắn nhất trong mặt bằng có vật cản chỉ bẻ hướng ở góc
  lồi, nên đồ thị này cho đúng đường ngắn nhất.
- **Thuật toán**: A* (mặc định, heuristic là khoảng cách thẳng tới đích gần nhất) hoặc
  Dijkstra. Đích là khu vực thì chọn điểm gần nhất **theo đường đi**, không theo đường chim
  bay.
- **Chỉ dẫn** (`chi_dan`): mỗi bước kèm mã hướng (`bat_dau`, `di_thang`, `chech_trai/phai`,
  `re_trai/phai`, `quay_dau`) và số mét. App tự dịch mã sang tiếng Việt/Anh. Các chặng đi
  thẳng liên tiếp được gộp lại, chặng ngắn dưới 0,5 m dồn vào chặng kề.
- **Cửa và luật nối**: `Map.png` vẽ tường nhưng không vẽ cửa, nên 15 cửa là cạnh nhóm tự nối
  (`cua_gia_dinh`, `/graph` đánh dấu riêng). Ngoài ra có luật nối tay: RP01 chỉ nối RP45,
  RP02; RP03 chỉ nối RP44, RP02; bỏ các cạnh 18-20, 45-12, 45-13, 45-20, 44-14, 44-15,
  44-21; hai WC (RP42, RP43) chỉ là đích.

## Dữ liệu

| Bộ | Lần quét | Nguồn |
|---|---:|---|
| Đợt A | 802 | Dữ liệu thô CTK45, một máy (Samsung SM-S908E), `data/raw/combined_data.csv` |
| Đợt B | 2.349 | Phần ba máy còn lại của CTK45, chỉ có dạng đã xử lý, `data/raw/ctk45_xu_ly/` |
| UJIIndoorLoc | 19.937 + 1.111 | Bộ công khai (3 toà nhà, nhiều tầng), `data/raw/ujiindoorloc/`, dùng để so với nhóm hợp tác |

Mô hình học trên A + B: 3.141 lần quét, 40 điểm tham chiếu, chia train/validation/test
70/15/15. Mỗi điểm CTK45 đo 80 lần bằng 4 máy theo 4 hướng. Trong dữ liệu thô, nhãn "RP41"
thực chất là RP26 (20 lần quét trùng khít RP26 ở bản đã xử lý). Pipeline đổi nhãn lúc nạp
(`NHAN_RP_SUA` trong `ml/config.py`), không sửa tệp thô.

## Kết quả

Mọi bảng trong `reports/tables/` và số in ra từ `ml.*` tính theo đơn vị lưới (riêng
`ujiindoorloc.csv` là mét). Các bảng dưới đây đã quy ra mét.

### Định vị trên thư viện — sai số trung bình, mét

| Mô hình | Chia ngẫu nhiên (TB 10 seed) | Bỏ trọn một điểm | Khác đợt đo |
|---|---:|---:|---:|
| **kNN k động** | **2,30 ± 0,16** | 5,63 | **4,11** |
| XGBoost | 3,23 ± 0,17 | **5,37** | 5,29 |
| kNN | 3,32 ± 0,27 | 7,26 | 5,81 |
| WKNN | 3,32 ± 0,15 | 6,19 | 5,39 |
| Random Forest | 3,41 ± 0,14 | 5,68 | 5,46 |

- **Chia ngẫu nhiên theo lần quét** (`ml.on_dinh`): nhận lại chỗ đã đo, cùng buổi, cùng máy.
  Đây là chặn lạc quan.
- **Bỏ trọn một điểm** (`ml.danh_gia_cheo`): đứng ở chỗ chưa từng đo. Đây là chặn bi quan.
  Mỗi lần gấp làm lại bước 5–10 của tiền xử lý chỉ trên phần học.
- **Khác đợt đo** (`ml.khac_dot`): học trên một đợt, kiểm trên đợt kia (A → B 4,93 m,
  B → A 3,29 m, cột là trung bình hai chiều). Đứng ở chỗ đã khảo sát nhưng khác máy, khác
  thời điểm, gần với lúc dùng thật nhất.

k động dẫn đầu ở cột thứ nhất (cả 10 seed) và cột thứ ba; ở cột thứ hai XGBoost thấp hơn
0,26 m. So với hai mô hình cơ sở kNN và WKNN, k động thấp hơn ở cả ba cột. Quét k = 1..61
(`ml.quet_k`) cho thấy k = 1 tốt nhất khi chia ngẫu nhiên còn k lớn tốt nhất khi bỏ trọn
một điểm. Đó là lý do chọn k động.

### UJIIndoorLoc — sai số 2D, mét

Học trên tập học công bố, kiểm trên tập validation (đo sau 4 tháng, người và máy khác).
Cột thứ hai theo Torres-Sospedra và c.s. (2015): đoán toà nhà và tầng trước (kNN Sørensen +
powed, k = 7, đúng 91,18%), sai số chỉ tính trên các mẫu đoán đúng.

| Mô hình | Toàn bộ 1.111 mẫu | Mẫu đúng toà + tầng |
|---|---:|---:|
| **kNN k động** | **9,03** | **7,60** |
| WKNN | 11,46 | 10,10 |
| kNN | 12,35 | 10,73 |
| Random Forest | 12,39 | 11,36 |
| XGBoost | 20,53 | 19,58 |
| *Nhóm hợp tác — CCpos (CDAE + CNN + MLP có toà/tầng)* | *11,65* | — |
| *Nhóm hợp tác — kNN Sørensen + powed, k = 13 (đúng toà + tầng 95,2%)* | — | *6,16* |

Số của nhóm hợp tác lấy từ báo cáo của họ
(`docs/tai_lieu_tham_khao/BaoCao_nhom_hop_tac_UJIIndoorLoc.docx`). Ở cột thứ hai họ đoán
toạ độ chỉ từ các láng giềng cùng toà và tầng, còn ở đây đoán trên toàn bộ tập học.

### Chỉ đường

- **So với đường ngắn nhất tham chiếu** (Dijkstra trên lưới điểm ảnh, 4.400 cặp điểm): lệch
  trung vị 0,03 m, 90% số cặp lệch dưới 0,68 m (`tools/danh_gia_chi_duong.py`).
- **Quãng đường hiển thị từ vị trí dự đoán** so với quãng đường thật, trên tập test, cửa
  sổ gộp 3: lệch trung vị 0,03 m, p90 2,16 m.
- **So sánh 6 thuật toán** (`tools/so_sanh_tim_duong.py`, 1.892 truy vấn): A* mở trung bình
  18 nút (0,36 ms), Dijkstra 173 nút (2,0 ms), cùng quãng đường. BFS và tham lam chỉ cho
  đường ngắn nhất ở khoảng 40% số truy vấn.

### Hiệu năng

- Mô hình dự đoán khoảng 4 ms một lần quét; cả `/predict` (kèm gộp và ghi CSDL) khoảng
  10 ms; `/route` khoảng 7 ms.
- APK release chỉ arm64: 19,6 MB.

## Cài đặt và chạy

Cần **Python 3.14** 64-bit (phiên bản trong `requirements.txt` ghim theo máy đã chạy trọn
dự án). Muốn build app thì cần thêm **Flutter 3.47** và Android SDK. Trên Windows nên đặt
kho ở đường dẫn ngắn (ví dụ `D:\System_Indoor`), vì đường dẫn dài làm bước biên dịch shader
khi build APK vượt giới hạn 260 ký tự.

```bash
python -m venv venv
venv\Scripts\activate           # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -q       # không cần chạy pipeline trước
uvicorn backend.main:app --host 0.0.0.0
```

Kho kèm sẵn `scaler.pkl` và mô hình đang triển khai nên backend chạy được ngay. Mở
`http://127.0.0.1:8000` để xem Dashboard, `/docs` để thử API. Đứng ngoài thư viện thì chạy
với `DEMO=true`: máy chủ phát lại các lần quét thật của tập test, mô hình vẫn chạy thật.

### API

| Endpoint | Việc |
|---|---|
| `GET /health` | Mô hình đang chạy, số đặc trưng, cửa sổ gộp |
| `POST /predict` | `{device_id, scan: [{bssid, rssi}]}` → `{x, y, x_smooth, y_smooth, matched_ap, …}` |
| `GET /predictions` | Lịch sử vị trí (`device_id`, `gioi_han` ≤ 1000) |
| `GET /map` | Phạm vi, điểm tham chiếu kèm tên, nhóm, mô tả; `met_moi_don_vi` để đổi ra mét |
| `GET /graph` | Các cạnh nối điểm tham chiếu, đánh dấu cửa giả định |
| `POST /route` | Điểm đầu `tu_rp` hoặc `tu_x, tu_y`; đích `den_rp` hoặc `den_nhom`; `thuat_toan` = `a_sao` / `dijkstra` |
| `GET /map/so-do.png` | Ảnh sơ đồ cho Dashboard |

### Máy học

```bash
python -m ml.pipeline         # tiền xử lý 12 bước -> artifacts/, data/processed/, data/splits/
python -m ml.audit            # rà rò rỉ dữ liệu, độ ổn định, chất lượng buổi thu
python -m ml.train            # huấn luyện 5 mô hình (--nhanh: lưới rút gọn) -> artifacts/, reports/tables/
python -m ml.report           # biểu đồ -> reports/figures/
python -m ml.on_dinh          # chia ngẫu nhiên 10 seed
python -m ml.danh_gia_cheo    # bỏ trọn một điểm
python -m ml.khac_dot         # khác đợt đo
python -m ml.quet_k           # quét k = 1..61
python -m ml.ujiindoorloc     # UJIIndoorLoc, ~10 phút; tải dữ liệu theo data/raw/ujiindoorloc/README.md
python -m tools.danh_gia_chi_duong
python -m tools.so_sanh_tim_duong
```

Chạy `ml.pipeline` trước `ml.train`, và `ml.train` trước `ml.report`.

### Ứng dụng

Xem `mobile/README.md`.

## Cấu trúc thư mục

| Thư mục | Nội dung |
|---|---|
| `mobile/` | Ứng dụng Flutter |
| `backend/` | FastAPI: `routers/` (endpoint), `services/` (dự đoán, gộp, tìm đường, demo), `database.py`, `repository.py` |
| `dashboard/` | Web Dashboard |
| `ml/` | Tiền xử lý, mô hình (`ml/models/`), huấn luyện, đánh giá |
| `artifacts/` | Đầu ra huấn luyện mà backend nạp: `feature_list.json`, `scaler.pkl`, mô hình, `model_metadata.json` |
| `data/` | `raw/` dữ liệu đo, `reference/` điểm tham chiếu và bản đồ, `processed/` dữ liệu đã xử lý |
| `tools/` | Công cụ chạy một lần rồi commit kết quả |
| `tests/` | Kiểm thử API |
| `reports/` | Bảng và biểu đồ cho báo cáo |
| `docs/` | Thiết kế hệ thống, đề cương, tài liệu tham khảo |
| `deprecated/` | Mã và tài liệu cũ đã có bản thay thế, giữ để tham khảo khi viết báo cáo |

## Hạn chế

- **Không có xác thực.** Ai vào được mạng LAN cũng xem được Dashboard và lịch sử vị trí của
  mọi thiết bị qua `GET /predictions`. `ALLOWED_ORIGINS` mặc định là `*`.
- **Chưa kiểm thử trọn vẹn tại thư viện.** Luồng định vị và chỉ đường đã chạy trên máy
  Android thật, chủ yếu qua chế độ demo. Góc giữa sơ đồ và hướng bắc (dùng cho nón hướng)
  đo trên ảnh vệ tinh, chưa so tại chỗ.
- **Đợt B không có dữ liệu thô**: không có thời điểm quét, tên máy, hướng. Vì vậy đánh giá
  khác máy chỉ làm được ở mức đợt (một máy so với ba máy gộp), chưa tách từng máy hay
  từng buổi.
- **4 điểm trên bản đồ không có dữ liệu đo** (RP42–RP45: hai WC, hai cầu thang). `/route`
  dẫn tới được, nhưng mô hình không bao giờ báo người dùng đang ở đó.
- **Dữ liệu nhóm tự thu chưa dùng.** 7 điểm đo năm 2026 bằng Redmi K40 Pro
  (`data/raw/nhom15_2026/`) lệch RSSI so với máy Samsung của CTK45. Gộp vào thì sai số tăng,
  nên chưa gộp khi chưa đo được độ lệch giữa hai máy.
- **Cửa và tỉ lệ chưa đo thực địa.** 15 cửa giả định và luật nối do nhóm đặt. Tỉ lệ
  0,3508 m/đơn vị suy từ bản vẽ, chưa đo bằng thước. Quãng đường là cận dưới vì tuyến ôm sát
  góc vật cản.
- **Chưa đánh giá theo mật độ người.** Dữ liệu không ghi số người có mặt lúc đo, muốn làm
  phải đo lại vào giờ đông và giờ vắng.

## Tài liệu

- `docs/thiet_ke_he_thong.md` — thiết kế hệ thống: yêu cầu, kiến trúc, mô hình, dữ liệu
  không gian, chỉ đường, API, giao diện
- `docs/tai_lieu_tham_khao/` — các công trình liên quan
- Thiết kế giao diện ứng dụng (Figma): https://www.figma.com/design/3dzSOBhBIhb3e9zkuWOiQS
