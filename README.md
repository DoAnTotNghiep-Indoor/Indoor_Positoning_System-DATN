# Hệ thống định vị trong nhà bằng WiFi Fingerprinting

Đồ án tốt nghiệp — Nhóm 15, Khoa Công nghệ Thông tin, Trường Đại học Đà Lạt.
GVHD: TS. Nguyễn Thị Lương.

Hệ thống định vị người dùng trong tầng 1 Thư viện Đại học Đà Lạt từ cường độ sóng WiFi
(RSSI) mà điện thoại quét được, rồi chỉ đường tới khu vực người dùng chọn.

## Thành phần

| Thành phần | Thư mục | Làm gì |
|---|---|---|
| Ứng dụng Android (Flutter) | `mobile/` | Quét WiFi liên tục, định vị qua máy chủ hoặc ngay trên máy, hiện vị trí và nón hướng la bàn trên sơ đồ, tra cứu khu vực, chỉ đường. Song ngữ Việt/Anh, sáng/tối |
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

App gọi quét mỗi 1 giây (lượt trước chưa xong thì bỏ qua). Máy phải tắt điều tiết quét Wi-Fi,
còn bật thì Android chỉ cho 4 lần quét mỗi 2 phút. Số liệu RSSI thật mới bao lâu một lần do
firmware quyết định (mục Hạn chế). Với nhịp này REST là đủ: Dashboard hỏi `GET /predictions`
mỗi 2 giây.

### Định vị ngay trên điện thoại (Mô hình cục bộ)

Bật **Mô hình cục bộ** trong Cài đặt của app thì bước 2–5 chạy ngay trên điện thoại, không
chờ máy chủ:

- `python -m ml.xuat_mo_hinh` xuất mô hình đang triển khai ra `mobile/assets/model/k_dong.json`
  (khoảng 790 KB): 36 BSSID, tham số chuẩn hoá, 2.668 vân tay, 40 toạ độ, ngưỡng d1 và k lớn.
  Không có trọng số nào cần học lại; kNN chỉ cần đúng bảng vân tay và các tham số này.
- App (`mobile/lib/services/dinh_vi_tren_may.dart`) làm lại đúng thuật toán: ánh xạ BSSID,
  chặn khi khớp dưới 6 AP, khoảng cách Bray-Curtis, chọn k = 1 hoặc k lớn, gộp 3 lần quét.
  `flutter test` đối chiếu với 200 lần quét test do Python đoán: lệch dưới 10⁻⁶ đơn vị lưới.
- App vẫn gửi `POST /predict` nhưng không chờ trả lời, nên máy chủ vẫn ghi lịch sử cho
  Dashboard và để phân tích. Mất mạng thì vị trí trên máy vẫn chạy.
- Bản đồ (`GET /map`) và chỉ đường (`POST /route`) vẫn cần máy chủ.

Học lại mô hình thì phải chạy lại `ml.xuat_mo_hinh` rồi build lại app;
`tests/test_xuat_mo_hinh.py` báo lỗi nếu quên.

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

Mặt bằng tầng 1 khai báo trong `data/reference/mat_bang_tang1.yaml` theo số viên gạch đếm
tại chỗ (một viên ≈ một đơn vị lưới): phòng, tường, lan can, cầu thang, cột, kệ, cửa, tên
địa điểm. Từ tệp này, `tools/ve_so_do_tang1.py` vẽ sơ đồ SVG cho app và Dashboard, còn
`tools/luoi_di_lai.py` dựng lưới đi lại vào `data/reference/ban_do_tang1.json` cho backend.
Phần chưa đo tại chỗ (sau quầy, sảnh chờ, WC, hai toà chéo) vẽ nét đứt.

Toạ độ dùng **đơn vị lưới** của bảng điểm tham chiếu (x từ −43 đến 43, y từ 0 đến 52, y = 0
ở cửa ra vào). Một đơn vị bằng **0,3508 m**, lấy từ kích thước ghi trên bản vẽ CTK45 và khớp
với đa giác toà nhà trên OpenStreetMap; đếm gạch tại chỗ lệch 1%. Sơ đồ SVG giữ khung pixel
của `Map.png` cũ (CTK45), nên phép đổi toạ độ ↔ pixel giống nhau ở app (Dart), Dashboard
(JavaScript) và công cụ vẽ (Python).

### Chỉ đường

`POST /route` tìm đường ngắn nhất từ đúng vị trí người dùng (không neo về điểm tham chiếu
gần nhất) tới một điểm hoặc một khu vực:

- **Lưới đi lại**: mặt nạ 4 điểm ảnh mỗi đơn vị lưới. Đi được trong vỏ toà, phòng, sàn, cầu
  thang; chặn bởi tường, lan can, mép sàn khác mức, giếng, quầy, cột, kệ. Cầu thang chỉ lên
  xuống ở hai đầu; cửa mở khe qua tường. Phòng không có cửa thì không vào được: chỉ đường dừng
  ở lối vào khai trong YAML hoặc điểm đi được gần nhất.
- **Đồ thị**: nút là 167 góc lồi của vật cản cộng 44 điểm tham chiếu, 3.599 cạnh nối các cặp
  nhìn thấy nhau. Đường ngắn nhất trong mặt bằng có vật cản chỉ bẻ hướng ở góc lồi, nên đồ thị
  này cho đúng đường ngắn nhất.
- **Thuật toán**: A* (mặc định, heuristic là khoảng cách thẳng tới đích gần nhất) hoặc
  Dijkstra. Đích là khu vực thì chọn điểm gần nhất **theo đường đi**, không theo đường chim
  bay; đích là toạ độ (phòng không có điểm tham chiếu) thì cách dưới 2 m coi như đã tới.
  Trên 1.892 truy vấn giữa các điểm tham chiếu, A* mở trung bình 15 nút, Dijkstra 107, cùng
  quãng đường (`python -m tools.so_sanh_tim_duong`).
- **Chỉ dẫn** (`chi_dan`): mỗi bước kèm mã hướng (`bat_dau`, `di_thang`, `chech_trai/phai`,
  `re_trai/phai`, `quay_dau`) và số mét. App tự dịch mã sang tiếng Việt/Anh. Các chặng đi
  thẳng liên tiếp được gộp lại, chặng ngắn dưới 0,5 m dồn vào chặng kề.
- **Sai số quãng đường** (`python -m tools.danh_gia_chi_duong`, so với Dijkstra trên lưới
  mịn): riêng thuật toán, từ 400 điểm xuất phát ngẫu nhiên tới mọi khu vực, lệch trung bình
  0,16 m. Cả hệ thống, quãng đường app báo khi đứng ở vị trí mô hình đoán (tập test, gộp 3 lần
  quét) so với quãng đường thật từ vị trí thật: lệch trung bình 1,45 m, trung vị 0,28 m, lớn
  nhất 29 m. Ca lớn là vị trí đoán rơi sang sàn khác mức bên kia lan can, nên tuyến phải vòng
  qua cầu thang.

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
| XGBoost | 3,20 ± 0,15 | **5,33** | 5,21 |
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
0,30 m. So với hai mô hình cơ sở kNN và WKNN, k động thấp hơn ở cả ba cột. Quét k = 1..61
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
- Đo trên vivo X300, bản release, 200 lần quét test: mô hình cục bộ trung vị 0,72 ms mỗi lần
  đoán; gọi `/predict` qua WiFi nội bộ khứ hồi trung vị 58 ms, phần lớn là mạng.
- Máy chủ trên VM Azure Central India, ra ngoài qua Cloudflare Tunnel, đo từ Việt Nam
  (`python -m tools.do_tre_may_chu <địa chỉ>`, 200 lần, trung vị): `/predict` 332 ms, `/route`
  330 ms, P99 ≤ 352 ms. Mô hình trên VM chỉ 1,7 ms; nối thẳng tới VM không qua Cloudflare 136 ms.
  Cloudflare thêm ~200 ms vì vào ở Hồng Kông còn tunnel nối ở Mumbai. Mọi con số này đều nhỏ so
  với nhịp số liệu WiFi mới (2–8 s, mục Hạn chế).
- APK release chỉ arm64: 20,5 MB (kể cả mô hình cục bộ).

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

### Máy chủ triển khai

Một VM Azure (Central India, 2 nhân, 3,8 GB RAM, Ubuntu 24.04) chạy hai bản backend dưới
systemd, ra ngoài qua một Cloudflare Tunnel có hai tên miền:

| Tên trong app | Địa chỉ | Cổng trên VM | Dịch vụ | CSDL |
|---|---|---:|---|---|
| IPS DLU PROD | `https://dlu-ips.etylix.me` | 8000 | `ips.service` | `data/ips.db` |
| IPS DLU DEMO | `https://dlu-ips-demo.etylix.me` | 8001 | `ips-demo.service` (`DEMO=true`) | `data/ips_demo.db` |

Hai bản cùng mã nguồn ở `~/IPS`; DEMO tách CSDL (`DATABASE_URL`) để lần quét phát lại không lẫn
vào dữ liệu thật. Cập nhật: `git pull` rồi `sudo systemctl restart ips ips-demo`. Tên miền phải
một cấp dưới `etylix.me`: chứng chỉ miễn phí của Cloudflare không phủ dạng `a.b.etylix.me`.

App chọn máy chủ trong Cài đặt: PROD, DEMO hoặc Tuỳ chỉnh (tự nhập, ví dụ máy chủ trên
laptop `http://<IP>:8000`). Mặc định là PROD.

### API

| Endpoint | Việc |
|---|---|
| `GET /health` | Mô hình đang chạy, số đặc trưng, cửa sổ gộp |
| `POST /predict` | `{device_id, scan: [{bssid, rssi}]}` → `{x, y, x_smooth, y_smooth, matched_ap, latency_ms, …}` |
| `GET /predictions` | Lịch sử vị trí (`device_id`, `gioi_han` ≤ 1000) |
| `GET /map` | Phạm vi, điểm tham chiếu kèm tên, nhóm, mô tả; `met_moi_don_vi` để đổi ra mét |
| `GET /graph` | Các cặp điểm tham chiếu nhìn thấy nhau, cho Dashboard vẽ |
| `POST /route` | Điểm đầu `tu_rp` hoặc `tu_x, tu_y`; đích `den_rp`, `den_nhom` hoặc `den_x, den_y`; `thuat_toan` = `a_sao` / `dijkstra` |

### Máy học

```bash
python -m ml.pipeline         # tiền xử lý 12 bước -> artifacts/, data/processed/, data/splits/
python -m ml.audit            # rà rò rỉ dữ liệu, độ ổn định, chất lượng buổi thu
python -m ml.train            # huấn luyện 5 mô hình (--nhanh: lưới rút gọn) -> artifacts/, reports/tables/
python -m ml.xuat_mo_hinh     # xuất kNN k động cho app -> mobile/assets/model/
python -m ml.report           # biểu đồ -> reports/figures/
python -m ml.on_dinh          # chia ngẫu nhiên 10 seed
python -m ml.danh_gia_cheo    # bỏ trọn một điểm
python -m ml.khac_dot         # khác đợt đo
python -m ml.quet_k           # quét k = 1..61
python -m ml.ujiindoorloc     # UJIIndoorLoc, ~10 phút; tải dữ liệu theo data/raw/ujiindoorloc/README.md
python -m tools.danh_gia_chi_duong
python -m tools.so_sanh_tim_duong
```

Chạy `ml.pipeline` trước `ml.train`, và `ml.train` trước `ml.report`, `ml.xuat_mo_hinh`.
Các bước học và đánh giá chạy song song trên mọi lõi CPU.

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

- **Nhịp số liệu WiFi do Android và firmware quyết định, không do app.** App gọi quét mỗi 1 s,
  nhưng máy có thể trả lại kết quả cũ mà không báo (vẫn ghi tuổi mới). Đo trên vivo X300 đã tắt
  điều tiết quét, 06/10/2026, qua nhật ký `dumpsys wifiscanner` và so RSSI giữa các lần:
  - đang nối một mạng WiFi: RSSI đổi đủ khoảng 7,6 s một lần (7 lần trong 57 s), lẻ tẻ từng
    phần băng tần ở giữa; ra lệnh quét nhịp 1, 2, 3 hay 5 s đều chỉ được 4–7 lần quét thật
    trong 45 s;
  - bật WiFi nhưng không nối mạng nào: số liệu mới đều 2 s một lần (một lần quét đủ băng
    1–2,5 s cộng nhịp 1 s của app).

  Người dùng trong thư viện thường đang nối WiFi thư viện, nên vị trí cập nhật thật khoảng
  5–8 s một lần; trong lúc đó app gửi lại cùng một lần quét, cửa sổ gộp 3 lần quét phần lớn gộp
  bản trùng. Mới đo một máy; hãng khác có thể khác. Cài đặt của app hiện nhịp đo được ("Số liệu
  WiFi mới mỗi … s").
- **Không có xác thực.** Ai vào được mạng LAN cũng xem được Dashboard và lịch sử vị trí của
  mọi thiết bị qua `GET /predictions`. `ALLOWED_ORIGINS` mặc định là `*`.
- **Sai số tại chỗ chưa đủ điểm.** Buổi đo 03/10/2026 mới so được 1 chỗ đứng biết toạ độ.
  Góc giữa sơ đồ và hướng bắc (dùng cho nón hướng) đo trên ảnh vệ tinh, chưa so tại chỗ.
- **Vị trí nhảy khi ở giữa các điểm tham chiếu.** Gần RP sai khoảng 1–2 m; ở giữa các RP,
  tập láng giềng đổi theo dao động RSSI nên vị trí nhảy nhiều hướng (xem Hướng phát triển).
- **Đợt B không có dữ liệu thô**: không có thời điểm quét, tên máy, hướng. Vì vậy đánh giá
  khác máy chỉ làm được ở mức đợt (một máy so với ba máy gộp), chưa tách từng máy hay
  từng buổi.
- **4 điểm trên bản đồ không có dữ liệu đo** (RP42–RP45: hai WC, hai cầu thang). `/route`
  dẫn tới được, nhưng mô hình không bao giờ báo người dùng đang ở đó.
- **Dữ liệu nhóm tự thu chưa dùng.** 7 điểm đo năm 2026 bằng Redmi K40 Pro
  (`data/raw/nhom15_2026/`) lệch RSSI so với máy Samsung của CTK45. Gộp vào thì sai số tăng,
  nên chưa gộp khi chưa đo được độ lệch giữa hai máy.
- **Một phần sơ đồ là suy đoán.** Khu sau quầy, cửa các phòng ở đó, lối vào WC (coi như
  lách qua kệ sách) và mép giữa khu đọc với mức quầy chưa kiểm tại chỗ; chỉ đường đi theo các
  giả định này. Quãng đường là cận dưới vì tuyến ôm sát góc vật cản.
- **Chưa đánh giá theo mật độ người.** Dữ liệu không ghi số người có mặt lúc đo, muốn làm
  phải đo lại vào giờ đông và giờ vắng.

## Hướng phát triển

### Ưu tiên kết quả theo hướng thiết bị

Đo trên 2.045 dự đoán buổi 03/10/2026 (máy vivo X300): chỉ 1,9% lần quét đủ gần một vân tay
để mô hình dùng k = 1; còn lại lấy trung bình 15 láng giềng. Bước nhảy thô giữa hai lần liên
tiếp có trung vị 2,4 m, P90 6,9 m; 41,7% bước dài hơn 3 m, xa hơn quãng đi bộ giữa hai lần
quét. Ở giữa các RP, lần quét giống vài RP gần ngang nhau, RSSI dao động vài dBm là tập láng
giềng đổi sang cụm khác.

Ý tưởng chưa làm: khi người dùng **đang đi**, ưu tiên ứng viên nằm phía trước theo hướng điện
thoại đang chỉ.

1. Ứng dụng gửi kèm mỗi lần quét: hướng (la bàn, đã quy về trục sơ đồ) và cờ đang đi / đứng
   yên (gia tốc kế, biên độ rung theo nhịp bước).
2. Máy chủ coi mỗi láng giềng của kNN là một ứng viên, nhân trọng số theo vị trí của nó so với
   vị trí trước:
   - đang đi: `e^(κ·cos Δθ)`, Δθ là góc giữa hướng tới ứng viên và hướng điện thoại; κ nhỏ,
     ứng viên phía trước chỉ nặng gấp 2–3 lần phía sau, vì la bàn trong nhà bị thép làm lệch
     và hướng cầm máy không luôn trùng hướng đi;
   - đứng yên: không dùng hướng, ưu tiên ứng viên gần vị trí cũ (xoay máy tại chỗ không được
     làm chấm trôi);
   - luôn luôn: không dời quá tốc độ đi bộ (~1,5 m/s × thời gian giữa hai lần quét).
3. Chạy song song với cách cũ, ghi cả hai cùng hướng và cờ đang đi vào CSDL; buổi đo sau đi
   dọc vài đường ron biết toạ độ (ví dụ trục x = 0 từ cửa tới quầy), đứng tại vài chỗ đếm được
   bằng gạch, rồi so độ nhảy và sai số của hai cách.

Đã thử và **không** hiệu quả: chỉ so lần quét với vân tay thu ở hướng gần giống (đợt A, 802 lần
quét có hướng). Chia ngẫu nhiên, k = 15: 1,85 m khi so mọi hướng, 2,35 m khi lọc ±90°, 3,67 m
khi lọc ±45°. Bỏ trọn một điểm, k = 15: 4,69 / 4,59 / 4,86 m. Mỗi RP chỉ có vài lần quét mỗi
hướng nên lọc bớt thì láng giềng bị kéo sang RP khác; đợt B lại không ghi hướng.

Hai hướng khác cùng giải quyết chuyện nhảy, không cần thu thêm vân tay: bộ lọc hạt có mô hình
bước chân và ràng buộc tường, giếng, lan can lấy từ `data/reference/mat_bang_tang1.yaml`; và
làm dày bản đồ vô tuyến bằng nội suy (Gaussian process) giữa các RP, đánh giá bằng giao thức
bỏ trọn một điểm.

## Tài liệu

- `docs/thiet_ke_he_thong.md` — thiết kế hệ thống: yêu cầu, kiến trúc, mô hình, dữ liệu
  không gian, chỉ đường, API, giao diện
- `docs/tai_lieu_tham_khao/README.md` — các công trình liên quan, kèm link

Tài liệu trực tuyến (riêng tư, mở được khi đã được chia sẻ):

| Tài liệu | Link |
|---|---|
| Đặc tả API cho nhóm hợp tác | https://claude.ai/artifact/Bvk2jmwDoMykYsYrugz7MT |
| Tài liệu thuyết trình (cơ sở viết báo cáo cuối) | https://claude.ai/artifact/AeDtxUWKmt3MceBPggzvV4 |
| Slide báo cáo tiến độ lần 1 | https://claude.ai/artifact/MkpUaFENVS1AHyCreZBBk6 |
| Slide báo cáo tiến độ lần 2 | https://claude.ai/artifact/SToAGkPmoC3LkTBponP2Gn |
| Thiết kế giao diện ứng dụng (Figma) | https://www.figma.com/design/3dzSOBhBIhb3e9zkuWOiQS |
