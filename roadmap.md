# Lộ trình công việc

Hệ thống định vị trong nhà bằng WiFi Fingerprinting — Thư viện Đại học Đà Lạt.
Nhóm 15, GVHD: TS. Nguyễn Thị Lương.

Các mục dưới đây rút ra từ đợt rà soát repo đồ án kế thừa CTK45
(`https://github.com/NgocSongNe/IPS`, 253 đường dẫn trên 9 nhánh, ngày 30/08/2026)
và đối chiếu với hiện trạng dự án.

## Trạng thái các giai đoạn

Đánh số giai đoạn theo PHẦN 5 của `docs/Cau_Truc_Thu_Muc_Du_An.md` — bảng duy
nhất trong dự án ánh xạ giai đoạn sang mốc thời gian của đề cương. Bản trước ở
đây đánh số khác (giai đoạn 4 là ứng dụng Flutter), gây lệch khi ai đó nói
"giai đoạn 4".

| Giai đoạn | Phạm vi | Mốc đề cương | Trạng thái |
|---|---|---|---|
| 1 | `data/`, `notebooks/`, `ml/preprocess.py`, `artifacts/` | 20/08–31/08 | Xong |
| 2 | `ml/models/`, `ml/evaluate.py`, `reports/` | 01/09–15/10 | Xong. Năm mô hình, hai giao thức đánh giá, hậu xử lý gộp |
| 3 | `backend/` toàn bộ, `tests/` | 16/10–31/10 | Xong. Đồ thị đi lại đã dò tường, chỉ đường có hướng rẽ |
| 4 | `frontend/` | 01/11–10/11 | Xong. Dashboard web chạy được, phục vụ thẳng từ uvicorn |
| 5 | `docs/`, `README.md` | 11/11–24/11 | Xong ngày 01/09/2026; rà lại và sửa số liệu ngày 07/09/2026 |

**Ngoài đề cương** — không thuộc giai đoạn nào vì đề cương không nhắc tới ứng
dụng di động (mục I và VI chỉ nêu ứng dụng Web):

| Phạm vi | Trạng thái |
|---|---|
| `mobile/` — ứng dụng Flutter 5 màn hình | Xong. Quét WiFi thật, nối `POST /predict`, sơ đồ và ảnh khu vực là dữ liệu thật, tuỳ chọn lưu xuống đĩa. Đây là nguồn quét thật cho hệ thống và là cách kiểm thử thực địa |
| `tools/` — công cụ chạy một lần rồi commit kết quả | Xong. Trích hình học từ `Map.png`, sinh bản nhúng khu vực, thu vân tay qua cáp USB |

Đối chiếu với mục VII đề cương: các mốc 1–8 đã xong, mốc 7 và 8 (backend,
Dashboard) làm sớm hơn kế hoạch. Đang ở mốc 9 — kiểm thử và viết báo cáo.

---

## Nhóm 1 — Sửa lỗi dữ liệu

Ưu tiên cao nhất, làm riêng vì thay đổi toàn bộ số liệu báo cáo.

### A. Sửa 4 toạ độ điểm tham chiếu

`data/reference/reference_points.csv` chép từ Bảng 4 trang 46 báo cáo CTK45.
Đối chiếu với `assets/combined_data_sorted.csv` của họ — cùng hệ mét, 6.338 lần
quét — thì 36/40 điểm khớp từng chữ số, 4 điểm lệch:

| RP | Đang dùng | Đúng | Lệch | Dấu hiệu |
|---|---|---|---|---|
| RP07 | (30, 0) | (30, 10) | 10 m | RP04, RP05, RP06 đều y=10, RP07 là điểm thứ tư cùng hàng |
| RP17 | (42, 27) | (42, 24) | 3 m | RP16 ở (−42, 24), đây là cặp đối xứng |
| RP26 | (3,0 · 4,5) | (−13, 41) | 39,7 m | (3 · 4,5) trùng khít cột `xy` trong POI.geojson — hệ lưới, không phải mét |
| RP27 | (7,0 · 4,5) | (13, 41) | 37,0 m | như trên |

RP07, RP17, RP27 **có trong dữ liệu huấn luyện**, mỗi điểm 20 lần quét. Đo trên
tập test: ba điểm này chiếm 7,6% số mẫu nhưng đóng góp 18,6% tổng sai số, và
RP27 chính là kỷ lục 56,18 m của toàn mô hình.

### B. Mở rộng lưới tham số chạm biên

Sau khi sửa toạ độ, rà lại tham số mà mỗi mô hình chọn thì thấy nhiều lưới có
tối ưu rơi đúng vào biên — dấu hiệu điểm tốt hơn nằm ngoài lưới:

| Mô hình | Tham số chạm biên | Lưới cũ | Lưới mới |
|---|---|---|---|
| kNN vân tay | `beta` = 2,0 (cận trên) | 1,25–2,0 | 1,5–3,5 |
| kNN, WKNN | `n_neighbors` = 3 (cận dưới) | 3–11 | 1–11 |
| XGBoost | `reg_lambda` = 1, `colsample` = 0,8 (cận dưới) | — | thêm 0,5 và 0,6 |
| Random Forest | không chạm biên | giữ nguyên | giữ nguyên |

Quét rộng `beta` trên validation cho thấy cực trị thật ở 2,75–3,0 và sai số tăng
trở lại từ 3,5, nên lưới mới đã bao trọn cực trị.

Kèm một tối ưu nhỏ trong `ml/train.py`: mô hình có thể khai báo `to_hop_trung`
để tự loại tổ hợp trùng kết quả. `fingerprint_knn` dùng nó bỏ 16 tổ hợp, vì khi
`n_neighbors = 1` thì chỉ có một láng giềng nên `power` không tác dụng.

### Kết quả

| Mô hình | Gốc | Sau sửa toạ độ | Sau mở rộng lưới | Sau sửa rò rỉ (07/09) |
|---|---|---|---|---|
| **kNN vân tay (Bray-Curtis)** | 2,5567 m | 2,4268 m | 1,9184 m | **2,2990 m** |
| WKNN | 5,7074 m | 4,8077 m | 5,1537 m | 4,6004 m |
| kNN | 5,7838 m | 4,8921 m | 5,1537 m | 5,4949 m |
| XGBoost | 8,5436 m | 7,0566 m | 6,4823 m | **6,2620 m** |
| Random Forest | 8,5054 m | 7,5507 m | 7,5507 m | 6,5900 m |
| **Sau khi gộp 3 lần quét** | 0,7334 m | 0,7334 m | 0,3846 m | **0,0000 m** |
| **Số vị trí còn sai** | 2/39 | 2/39 | 1/39 | **0/39** |

Cột cuối là sau khi chặn Hampel vá ô điền thiếu và bắt bước 5, 7 chỉ học trên
train. Nó làm kNN vân tay xấu đi (1,92 → 2,30 m) vì mô hình ấy đang hưởng lợi từ
chính chỗ rò rỉ, còn XGBoost và Random Forest thì tốt lên. Sau khi gộp 3 lần
quét thì không còn vị trí nào sai — RP35 của vòng trước đã hết.

Cần nói rõ khi bảo vệ: **kNN và WKNN tốt lên trên validation (4,33 và 4,21
xuống 3,76 m) nhưng xấu đi trên tập test** (4,89 và 4,81 lên 5,15 m). Chọn mô
hình chỉ được nhìn validation, nên vẫn giữ nguyên kết quả này thay vì quay lại
lưới cũ. Đây là chênh lệch validation/test bình thường với 117 và 118 mẫu.

Hai mô hình đó nay cho số liệu giống hệt nhau vì cùng chọn `k = 1`; khi chỉ có
một láng giềng thì phép trọng số nghịch đảo khoảng cách của WKNN không còn tác
dụng, hai mô hình trở thành một.

Chi phí: lưới XGBoost tăng từ 324 lên 648 tổ hợp, quét mất 557 giây.

### Kiểm chứng

- Dấu vân hợp đồng dữ liệu **không đổi**, `scaler.pkl` **giống hệt từng byte** —
  backend không phải sửa gì.
- Phát lại toàn bộ 118 mẫu test qua HTTP cho 1,9184 m, khớp bảng ngoại tuyến.
- **Tái lập được**: chạy lại `ml.pipeline` + `ml.train` cho ra 5 tệp mô hình,
  scaler và 3 tệp split giống hệt từng byte; mọi chỉ số khớp tới 10 chữ số thập
  phân. Khác biệt duy nhất là trường `created_at`.
- Đồ thị đi lại: cạnh dài nhất giảm từ 22,36 m xuống 21,02 m.
- `ml.audit` xếp RP27 vào buổi thu 13/01 cùng nhóm RP28–RP40 — trước khi sửa nó
  nằm ở đầu kia toà nhà nhưng lại đo cùng buổi với nhóm đó.
- 73/73 kiểm thử Python qua.
- **Tái lập lần nữa với lưới mới**: 5 tệp mô hình và `scaler.pkl` giống hệt từng
  byte, tham số chọn lại y nguyên, mọi chỉ số khớp tới 10 chữ số thập phân.

### Biểu đồ báo cáo

`reports/figures/` có 7 tệp nhưng `ml.report` chỉ sinh ra 5. Hai tệp còn lại là
tàn dư của một lần chạy tay: `error_distribution.png` từ 25/08 vẫn ghi số liệu
gốc (5,8 · 5,7 · 8,5 · 8,5 · 2,6 m) và `ap_appearance_rate.png` từ 24/08 tuy số
còn đúng nhưng không ai tái tạo được, lại khác phong cách 5 tấm kia.

Đã bổ sung `phan_bo_sai_so` và `ti_le_xuat_hien_ap` vào `ml/report.py`. Hình tỉ
lệ xuất hiện đọc thẳng `reports/tables/ap_appearance_rate.csv` do `ml/pipeline.py`
ghi ra, không tự tính lại, nên luôn khớp đúng lần chạy pipeline hiện tại.

Nay cả 7 biểu đồ sinh từ một lệnh `python -m ml.report`.

**Trạng thái: xong**

### Rà soát giai đoạn 1 và 2

Rà lại toàn bộ `ml/` (1.939 dòng, 15 tệp) sau khi số liệu đổi:

**Mã chết đã gỡ.** `ml/config.py` giữ ba hằng `SMOOTHING_ALPHA`,
`MAX_JUMP_DISTANCE_M`, `RESET_AFTER_SECONDS` kèm chú thích *"backend dùng lại
qua biến môi trường"* — không nơi nào dùng, và chú thích sai: backend tự khai
`cua_so_gop` với `reset_after_seconds` riêng trong `backend/config.py`. Đây là
tàn dư của thiết kế EMA đã bị thay bằng đồng thuận không gian. Gỡ luôn
`COL_SSID` vì pipeline chỉ dùng BSSID.

**Số liệu trong docstring đã đo lại.** Hai chỗ còn ghi kết quả cũ:

| Nơi | Cũ | Mới |
|---|---|---|
| `fingerprint_knn.py` — tỉ lệ đúng điểm, Bray-Curtis so với Euclid | 82,9% / 70,1% | **84,6% / 73,5%** |
| `postprocess.py` — ví dụ tổng khoảng cách tại RP39 | 47,5 / 54 / 87,5 m (RP11) | **25,0 / 26,3 / 37,3 m** (RP21) |

**Không có vấn đề** ở `evaluate.py`, `audit.py`, `pipeline.py`, `preprocess.py`.
Thứ tự bước 9 trước bước 8 là cố ý và có chú thích: chia tập trước rồi mới lọc
Hampel, để phép lọc chỉ chạy trên train. `ml.audit` vẫn báo đúng 11 điểm bất ổn
như docstring ghi.

### Đồng bộ tài liệu thiết kế với bản đã dựng

Tài liệu mô tả **EMA smoothing** xuyên suốt trong khi hệ thống dùng **đồng thuận
không gian** — hai thuật toán khác hẳn nhau. Chọn cách giữ nguyên phần thiết kế
ban đầu làm dấu vết quá trình, thêm mục đối chiếu ghi rõ đã đổi gì và vì sao.

| Tài liệu | Đã thêm | Đã sửa thẳng |
|---|---|---|
| `Phan_Tich_Thiet_Ke_He_Thong.md` | mục **2.4.1 Đối chiếu với bản đã thực hiện** — 5 điểm khác biệt kèm số đo | — |
| `Cau_Truc_Thu_Muc_Du_An.md` | bảng đối chiếu 7 dòng ở đầu PHẦN 2 | `model_x/y.pkl` → 5 tệp thật; `PositionSmoother (EMA)` → `BoGop`; `.env` bỏ `SMOOTHING_ALPHA` và `MAX_JUMP_DISTANCE_M` |
| `Phan_Tich_Ky_Thuat_DoAnCu_va_Cai_Tien.md` | ghi chú tình trạng V1–V12, nói rõ V7 và V12 làm khác đề xuất | — |

Năm điểm khác biệt ghi trong mục 2.4.1: hậu xử lý đổi thuật toán, thêm mô hình
thứ năm không có trong thiết kế, giá trị điền thiếu tính từ dữ liệu thay vì đặt
cứng, lưới tham số mở rộng, và lý do `device_holdout`/`time_holdout` không thực
hiện được.

Đã đối chiếu lại 13 con số đưa vào tài liệu với `model_metadata.json`,
`feature_list.json` và dữ liệu thô — tất cả khớp.

---

## Nhóm 2 — Ứng dụng di động chạy thật

Khoảng trống lớn nhất lúc bấy giờ: app chạy hoàn toàn trên dữ liệu demo tĩnh.

### B. Khai báo quyền Android

`mobile/android/app/src/main/AndroidManifest.xml` hiện **không có quyền nào**.
Thiếu chúng thì không quét được WiFi dù mã đúng đến đâu. Cần:

```
ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, ACCESS_BACKGROUND_LOCATION,
ACCESS_WIFI_STATE, CHANGE_WIFI_STATE, NEARBY_WIFI_DEVICES, INTERNET
+ uses-feature android.hardware.wifi
```

### C. Quét WiFi thật và nối vào POST /predict

Port `lib/ultils/wifi_scanner.dart` của CTK45 (48 dòng, xin quyền rồi quét, chờ
2 giây lấy kết quả).

Chỉ lấy phần quét. **Không** chép `wifi_service.dart` của họ: nó gửi
`{'rssi': [mảng số trần]}` với danh sách MAC viết cứng — đúng lỗi mà cả dự án
này lấy làm điểm cải tiến. Giữ hợp đồng `{bssid, rssi}` kèm cặp của ta.

### Đã làm

Ba dịch vụ mới trong `mobile/lib/services/`:

| Tệp | Việc |
|---|---|
| `quet_wifi.dart` | Quét WiFi, phân loại 5 nguyên nhân hỏng riêng biệt vì mỗi cái cần một cách xử lý khác |
| `api_dinh_vi.dart` | Gọi `POST /predict`, đọc `x_smooth`/`y_smooth` |
| `theo_doi_vi_tri.dart` | Vòng lặp 5 giây, giữ toạ độ mới nhất cho giao diện |

Địa chỉ máy chủ sửa được ngay trong Cài đặt chứ không viết cứng như CTK45 — máy
ảo dùng `10.0.2.2`, điện thoại thật cần IP nội bộ.

Bốn điểm kỹ thuật đáng ghi:

- **BSSID hạ về chữ thường** trước khi gửi. `feature_list.json` lưu chữ thường,
  máy Android trả hoa hay thường tuỳ hãng; không chuẩn hoá thì số AP khớp về 0
  mà không báo lỗi gì.
- **Chu kỳ 5 giây** chứ không nhanh hơn: Android chặn ứng dụng nền trước ở 4 lần
  `startScan` mỗi 2 phút, quét dày hơn chỉ nhận lại kết quả cũ trong bộ đệm.
- **Quá hạn quét vẫn đọc bộ đệm** thay vì báo lỗi — kết quả lần trước còn dùng
  được, tốt hơn là hiện lỗi cho người dùng.
- **`NEARBY_WIFI_DEVICES` kèm `neverForLocation`**: Android 13 trở lên chấp nhận
  quyền này thay cho quyền vị trí, khai cả hai để chạy trên cả máy cũ lẫn mới.

7 bài kiểm thử mới trong `mobile/test/dinh_vi_test.dart`, trong đó bài quan
trọng nhất khoá đúng hợp đồng dữ liệu: thân JSON phải là `{bssid, rssi}` kèm
cặp và không được có khoá `rssi` chứa mảng số trần.

Đã kiểm chứng đầu-cuối với backend thật: gửi đúng thân JSON mà app sinh ra thì
nhận HTTP 200 với đủ 9 trường, AP lạ bị bỏ qua đúng cách (12/13 khớp), còn thân
kiểu CTK45 bị từ chối 422.

Kiểm thử mobile tăng từ 19 lên **26 bài**, `flutter analyze` sạch.

**Chưa làm trong nhóm này:** marker trên sơ đồ vẫn đứng yên ở vị trí demo. Muốn
di chuyển nó cần phép biến đổi mét sang hệ toạ độ sơ đồ, và đó là mục E.

### Rà soát lại sau khi làm xong

Tự rà lại 423 dòng vừa viết, tìm ra ba lỗi thật và đã sửa:

| | Triệu chứng | Sửa |
|---|---|---|
| Lỗi ngoài hai loại đã bắt (`PlatformException` từ wifi_scan) | Trạng thái kẹt ở `dangChay`, người dùng nhìn "Đang quét…" mãi mà không biết vì sao | Thêm nhánh bắt chung |
| `notifyListeners()` sau `dispose()` | `A TheoDoiViTri was used after being disposed` khi đóng ứng dụng giữa lúc quét | Chốt `_daHuy` |
| `LoiApi.quaHan` khai báo nhưng không bao giờ ném | Máy chủ trả lời chậm bị báo nhầm thành "không kết nối được" | Bắt riêng `TimeoutException` |

Ba chỗ khác chưa sai nhưng dễ hỏng, đã dọn:

- `doiMayChu` đóng client HTTP rồi dựng cái mới — lần quét đang bay dở dùng
  chính client đó. Nay `ApiDinhVi.diaChi` đổi được tại chỗ, không đóng gì.
- `AppSettingsScope.of(context)` chỉ gọi trong nhánh có lỗi. Đăng ký phụ thuộc
  theo nhánh thì widget không dựng lại khi người dùng sửa địa chỉ. Nay đọc vô
  điều kiện.
- Số 3 viết cứng trong giao diện để đoán cửa sổ gộp — kích thước đó do máy chủ
  quyết định (`cua_so_gop`), viết cứng là nhân đôi hằng số qua hai tầng.

Thêm **quét tạm dừng khi ứng dụng xuống nền** và quét lại khi quay lên, chỉ tự
quét lại nếu trước đó đang chạy. Quét WiFi tốn pin đáng kể mà vị trí lúc màn
hình tắt thì không ai xem.

Đã kiểm chứng từng bài test mới đều đỏ khi hoàn nguyên đúng bản sửa của nó.
Kiểm thử mobile tăng lên **32 bài**.

**Trạng thái: xong phần quét và gọi API; marker chờ mục E**

---

## Nhóm 3 — Dữ liệu bản đồ

### D. Tên, mô tả và nhóm cho từng điểm tham chiếu ✅

`reference_points.csv` trước đây chỉ có `rp_id, x, y`. CTK45 có đủ cho cả 40
điểm: tên (`POI.geojson`), mô tả (`getPOIDescriptions`), nhóm khu vực và thư mục
ảnh (`rpToFolderMap`).

**Kiểm định trước khi dùng.** Số điểm tham chiếu của CTK45 phải ứng đúng số điểm
của nhóm, nếu không thì gán nhầm tên cho cả 40 điểm. Dùng tính đối xứng của toà
nhà làm phép thử: trong 16 cặp điểm đối xứng qua trục giữa, **13 cặp trùng tên**,
trong khi đánh số ngẫu nhiên chỉ cho trung bình 2,68 cặp — **p < 0,00001**. Ba
cặp lệch đều hợp lý về công năng (TV3,4 ↔ Hội trường, Khu tự học ↔ Căn tin, Cửa
ra vào ↔ Phòng tạp chí).

Phép thử này cũng xác nhận độc lập phần sửa toạ độ ở nhóm 1: RP26(−13, 41) và
RP27(13, 41) tạo thành một cặp đối xứng cùng tên "Khu vực đọc", điều không thể
xảy ra với toạ độ sai cũ (3 · 4,5) và (7 · 4,5).

**Đã làm.** Thêm 4 cột `ten`, `nhom`, `thu_muc_anh`, `mo_ta` vào
`data/reference/reference_points.csv`. Chạy lại `ml.pipeline` để kiểm chứng:
`scaler.pkl`, `train.csv`, `test.csv` và dataset cuối **giống hệt từng byte** —
thêm cột là thay đổi trơ với phần máy học, không phải huấn luyện lại.

`GET /map` trả kèm `ten`, `nhom`, `mo_ta`, `thu_muc_anh` cho từng điểm.
`POST /route` trả kèm `ten` và `nhom` nhưng **không** kèm mô tả: nhân với số
chặng chỉ làm nặng response mà không ai đọc. Nhờ vậy chỉ đường đọc được thành
câu — *TV3,4 → Cầu thang ×4 → Bàn thủ thư → Phòng tạp chí* thay vì *RP01 → RP05
→ … → RP39*.

Ứng dụng tải `/map` một lần khi bắt đầu định vị và hiện **tên khu vực** thay cho
toạ độ mét. Tải hỏng thì lùi về hiện toạ độ, không chặn vòng quét.

Một chi tiết bắt được lúc viết kiểm thử: máy chủ gửi `Content-Type:
application/json` **không kèm charset**, nên `http.Response.body` của Dart giải
mã bằng latin-1 và làm hỏng mọi tên tiếng Việt. Phải dùng
`utf8.decode(bodyBytes)`. Đã kiểm chứng bài test đỏ nếu đổi ngược lại.

Kiểm thử: Python 73 → **76**, mobile 32 → **35**.

### E. Sơ đồ mặt bằng thật ✅

`assets/Map.png` (1053×651) của CTK45 là bản số hoá tầng 1. Đã chép về
`data/reference/Map.png` và `mobile/assets/map/Map.png`.

**Lưới chấm trong ảnh chính là hệ toạ độ mét.** Lưới trải đúng 1000 px ngang và
605 px dọc, trong khi hộp bao 44 điểm tham chiếu là 86 m × 52 m:

| | |
|---|---|
| 1000 px / 86 m | **11,628 px/m** |
| 605 px / 52 m | **11,635 px/m** |

Hai trục tính độc lập mà khớp tới 4 chữ số có nghĩa — không thể là trùng hợp.

**Chiều trục chốt bằng hai bằng chứng độc lập, không phải chọn tuỳ ý.**

*Trục y hướng lên.* Toà nhà hình chữ thập, thắt eo ở giữa: rộng 1000 px ở hai
đầu nhưng chỉ 775 px ở đoạn giữa. Nếu y hướng lên, đoạn eo ứng với
y ∈ [6,4; 21,3] m, và cả 8 điểm nằm trong khoảng đó đều thoả |x| ≤ 30 m — vừa
lọt. Nếu y hướng xuống, đoạn eo lại phải chứa các điểm y ∈ [31; 45] m, trong đó
RP22 và RP25 ở |x| = 43 m — rộng hơn cả eo, bất khả. Vậy **y = 0 ở đầu có cửa ra
vào** (hàng RP01–RP03), y = 52 ở đầu kia.

*Trục x không lật.* Khớp 39 điểm với toạ độ GPS trong `POI.geojson` bằng phép
quay–co–tịnh tiến: không lật cho RMS 3,15, lật cho 13,84. (Tỉ lệ khớp ra 0,39 —
về sau hoá ra gần đúng: một đơn vị lưới là 0,3508 m, xem mục ngày 14/09/2026.)

**Kiểm chứng.** Phủ cả 40 điểm lên ảnh: 33 điểm rơi gọn trong lòng nhà, 7 điểm
còn lại lệch nhiều nhất 1,63 m và đều rơi trúng một cấu trúc **đúng tên của
chính nó**:

| Nét vẽ trong Map.png | Điểm rơi trúng | Tên điểm |
|---|---|---|
| Khối 88×98 px trái | RP20 (−22, 34) | Cầu thang |
| Khối 86×98 px phải | RP21 (22, 34) | Cầu thang |
| Vạch dài 544×51 px | RP05, RP06 (∓8, 10) | Cầu thang |
| Vạch dọc 15×157 px sát tường | RP22, RP25 (∓43, 35) | Khu vực đọc |

Sáu trên bảy điểm "lệch" hoá ra là bằng chứng khớp chứ không phải sai số.

**Đã làm.** Tab Bản đồ nay vẽ sơ đồ thật (`mobile/lib/widgets/so_do_that.dart`) thay cho
bản vẽ tay 393×852. Chấm vị trí đặt theo đúng toạ độ mét mô hình trả về; nhãn
khu vực lấy từ `GET /map`, mỗi `nhom` một nhãn đặt ở trọng tâm nhóm. Ở chế độ
tối, ảnh được đảo RGB nên nét đen thành trắng còn nền vẫn trong suốt.

Bản vẽ tay **không** bị xoá: nó vẫn là nền của màn Chi tiết khu vực. Nhưng cần
nói rõ trong báo cáo — hình học của nó là hình minh hoạ, không khớp toà nhà
thật (cầu thang thật ở (±22, 34) trong khi bản vẽ tay đặt ở giữa nhà).

### F. Đồ thị đi lại dựng từ tường thật ✅

`tools/trich_ban_do.py` dò từng cặp điểm xem đoạn thẳng nối chúng có nằm trọn
trong một mảng sàn không, rồi ghi ra `data/reference/ban_do_tang1.json`. Backend
chỉ đọc JSON nên không thêm phụ thuộc Pillow/SciPy lúc chạy.

**Tách tường khỏi lưới chấm bằng kích thước.** Ảnh chỉ có nét đen và màu xám
#D9D9D9; chấm lưới đều đúng 16 px, mọi khối xám lớn hơn là vật cản. Ngưỡng 17 px
quan trọng hơn vẻ ngoài của nó: 5 khối 21×21 px chính là nút bịt các khe hở ở
góc lõm của đường bao — bỏ sót chúng thì phép loang "bên ngoài" tràn vào khắp
nhà và mặt nạ sàn chỉ còn 34 pixel.

**Không dùng ngưỡng "dày bao nhiêu mét thì coi là tường".** Vách mỏng nhất trong
ảnh chỉ 1 px nên mọi ngưỡng đều hoặc bỏ sót vách mỏng, hoặc cắt nhầm cạnh chỉ
chạm mép. Xét theo mảng sàn liên thông thì không cần ngưỡng nào.

**Kết quả.** 103 cặp trong bán kính 25 m bị tường chặn, trong đó 23 cặp nằm
trong đồ thị k=3 cũ. Danh sách bị chặn **đối xứng gương gần như hoàn toàn** —
RP20–RP22 ↔ RP21–RP25, RP08–RP16 ↔ RP09–RP17, RP20–RP29 ↔ RP21–RP32… — dấu hiệu
phép dò bắt đúng cấu trúc toà nhà chứ không bắt nhiễu. Năm trường hợp không có
cặp gương đều dính tới RP10, RP18, RP19 là đúng những điểm bản thân không đối
xứng.

**Map.png vẽ tường nhưng không vẽ cửa.** Chặn hết cạnh cắt tường thì đồ thị vỡ
thành 7 mảnh. Công cụ nối lại bằng số cạnh ít nhất, mỗi lần chọn cạnh **ngắn
nhất** giữa hai mảnh — chỗ nhiều khả năng là cửa nhất. Sáu cạnh chọn ra:

| Cạnh | Dài | Nối |
|---|---|---|
| RP19–RP28 | 8,0 m | Cầu thang → Cầu thang |
| RP18–RP20 | 9,1 m | Khu vực tự học → Cầu thang |
| RP16–RP22 | 11,1 m | Hành lang → Khu vực đọc |
| RP17–RP25 | 11,1 m | Hành lang → Khu vực đọc |
| RP20–RP23 | 14,0 m | Cầu thang → Khu vực tự học |
| RP21–RP24 | 14,0 m | Cầu thang → Khu vực tự học |

Bốn cạnh sau là hai cặp gương, và cả sáu đều nối những chỗ mà cửa *phải* có:
hành lang vào phòng đọc, cầu thang sang khu tự học. Cạnh ngắn nhất RP19–RP28
nối hai điểm **cùng tên "Cầu thang"** — thuật toán chỉ nhìn hình học, tên điểm
xác nhận độc lập.

Sáu cạnh này là **giả định chưa kiểm chứng**, để riêng trong trường
`cua_gia_dinh` chứ không trộn vào phần suy ra được từ ảnh. Ra thực địa cần đối
chiếu đúng sáu chỗ này.

**Đồ thị cuối:** 62 cạnh, liền một mảnh, cạnh dài nhất **giảm từ 21,0 m xuống
16,1 m**. Đường RP01 → RP39 dài 119,4 m qua 11 chặng thay vì 80,1 m qua 7 chặng —
đường cũ ngắn hơn vì nó đi xuyên tường. (Số đo lại ngày 07/09/2026, sau khi thêm
hai điểm cầu thang RP44/RP45; bản trước ghi 58 cạnh, 17,2 m, 108,3 m qua 9 chặng.)

Hình kiểm chứng: `reports/figures/do_thi_di_lai.png`.

### G. Ảnh thật của thư viện ✅

38 ảnh trong 11 thư mục, lấy từ nhánh `Backup` của kho CTK45 (nhánh `master`
đang trỏ tới không có chúng). Bản gốc 1920×2560, tổng 24,9 MB → thu về cạnh dài
1024 px, JPEG q80, còn **4,0 MB** (106 KB/ảnh). Xuất xứ và tham số nén ghi tại
`mobile/assets/images/NGUON.md`.

Tên thư mục giữ nguyên vì khớp đúng cột `thu_muc_anh` — `GET /map` trả về tên
thư mục là app biết lấy ảnh nào, không cần bảng tra thứ hai.

**Nối vào giao diện.** Màn Chi tiết khu vực nhận thêm tham số `khuVuc`: có nó
thì tiêu đề, mô tả và dải ảnh đều là dữ liệu thật; không có thì giữ nguyên nội
dung demo như cũ. Trên Trang chủ, tên khu vực đang đứng trở thành nút bấm mở
thẳng màn đó. Không gán ảnh mặc định cho khu chưa chụp: gán nhầm ảnh còn tệ hơn
là không có ảnh.

### Kiểm thử và số liệu

| | Trước | Sau |
|---|---|---|
| Kiểm thử Python | 76 | **81** |
| Kiểm thử mobile | 35 | **47** |
| Cạnh dài nhất trong đồ thị | 21,0 m | **17,2 m** |
| Dung lượng ảnh | — | 24,9 MB → **4,0 MB** |

`flutter analyze` sạch. Đã kiểm chứng bài test đỏ khi lật trục y, khi xoá
`ban_do_tang1.json`, và khi sai đường dẫn ảnh.

**Sửa kèm — xuống dòng CRLF.** Bảy tệp sinh tự động (`feature_list.json`,
`model_metadata.json`, `pipeline_manifest.json`, dataset, `reference_points.csv`,
hai bảng kết quả) đang là CRLF trong khi bản trên GitHub là LF, nên `git diff`
báo đổi **cả tệp** dù nội dung y hệt — và phép so "giống hệt từng byte" giữa hai
lần chạy pipeline mất sạch ý nghĩa. Nguyên nhân: `Path.write_text` và
`DataFrame.to_csv` tự đổi sang CRLF trên Windows. Đã gom thành `config.ghi_json`
và `config.ghi_csv` ép LF ở đúng một chỗ, thay cho 10 chỗ gọi rải rác. Chạy lại
pipeline: dataset **giống hệt từng byte**, hai tệp JSON chỉ khác ở dấu thời gian.

---

## Nhóm 4 — Tính năng bổ sung

### H. Chỉ dẫn rẽ từng chặng cho POST /route ✅

`/route` nay trả thêm mảng `chi_dan`, mỗi phần tử là một bước đi kèm hướng rẽ
và số mét. Đường RP01 → RP39 (9 chặng) rút thành 6 bước:

```
Đi 17,2 m tới Cầu thang
Rẽ phải 17 m tới Cầu thang
Chếch trái 4,47 m tới Khu vực tự học
Rẽ phải 13,6 m tới Cầu thang
Rẽ trái 34 m tới Bàn thủ thư
Rẽ phải 22 m tới Phòng tạp chí
```

**Trả mã hướng, không trả câu.** `huong` là một trong `bat_dau`, `di_thang`,
`chech_trai`, `chech_phai`, `re_trai`, `re_phai`, `quay_dau`; câu chữ do client
tự ghép. Ứng dụng di động chạy hai ngôn ngữ — đóng cứng câu tiếng Việt ở máy chủ
là ép nó về một thứ tiếng.

**Ngưỡng phân loại góc.** Dưới 20° là độ lệch người đi bộ không nhận ra là một
cú rẽ; gọi nó là "rẽ" thì chỉ dẫn kêu liên tục ở mọi chặng. 20–60° là chếch,
60–135° là rẽ, trên 135° là quay đầu — phải nói khác hẳn "rẽ" để người dùng biết
mình đang vòng ngược lại chỗ vừa đi qua.

**Gộp chặng đi thẳng liên tiếp.** "Đi thẳng 12 m rồi đi thẳng 22 m" là hai câu
cho cùng một hành động. Các điểm ở giữa vẫn còn nguyên trong `duong_di` nếu
client cần vẽ tuyến.

**Chặng đầu không có trái/phải.** Góc quay tính so với hướng của chặng liền
trước, mà ở bước đầu hệ chỉ biết người dùng đứng ở đâu chứ không biết đang quay
mặt về đâu — ứng dụng chưa đọc la bàn. Muốn nói được "rẽ trái ngay từ đầu" thì
phải thêm cảm biến từ kế, không phải sửa hàm này.

**Viết lại sạch, không chép CTK45.** `getDirection` của họ trả thẳng một trong
ba chuỗi "Đi thẳng" / "Rẽ trái" / "Rẽ phải". Hàm mình trả về GÓC, phân loại là
việc của tầng trên. Khác biệt đó gỡ được hai hạn chế của họ: quay đầu 179° đọc
thành "rẽ trái" vì không có mức thứ tư, và hai điểm trùng nhau làm mẫu số
`mag1 * mag2` bằng 0 nên `acos` cho NaN, mọi phép so đều sai và hàm rơi xuống
nhánh cuối trả "Rẽ phải" cho một chặng không hề rẽ.

Ngưỡng đi thẳng của họ là 10°, của mình 20° — dưới 20° người đi bộ không nhận ra
là một cú rẽ, gọi nó là "rẽ" thì chỉ dẫn kêu liên tục ở mọi chặng.

Lộn dấu trái/phải không làm chương trình sập nên không có gì báo, vì thế vẫn
phải chốt bằng test: `test_re_trai_phai_dung_chieu` dùng một ví dụ tính được
bằng tay, đã kiểm chứng test đỏ khi đảo dấu góc.

Thêm một bài nữa dựa vào tính đối xứng: lấy một tuyến rồi lấy tuyến ảnh gương
của nó qua trục x = 0 thì mọi góc quay phải đổi dấu và mọi câu trái/phải phải
hoán vị.

### I. Dashboard web ✅

`frontend/index.html` là một trang theo dõi thời gian thực, chạy được ngay:

```
uvicorn backend.main:app        →  http://127.0.0.1:8000
```

**Máy chủ API phục vụ luôn giao diện.** `app.mount("/")` với `StaticFiles`, đặt
ở CUỐI `backend/main.py` vì mount ở `/` nhận mọi đường dẫn còn lại — đăng ký
trước thì nó nuốt luôn `/health`, `/map` và `/predict`, toàn bộ API trả 404 dù
mã của chúng không đổi một dòng. Có `test_mount_tinh_khong_che_mat_cac_endpoint`
canh đúng chuyện đó. Đổi lại: một lệnh là có cả API lẫn Dashboard, không phải
dựng thêm máy chủ tĩnh và cũng không vướng CORS.

**Nội dung trang.** Sơ đồ mặt bằng thật (`GET /map/so-do.png` phục vụ thẳng từ
`data/reference/Map.png`, không chép bản thứ ba) với 44 điểm tham chiếu, marker
thiết bị đang định vị kèm vệt đường đã đi; thẻ trạng thái mô hình từ `/health`;
bảng thiết bị đang kết nối; hộp chỉ đường dùng `chi_dan` của mục H; biểu đồ
khoảng cách giữa toạ độ thô và toạ độ đã gộp; bảng lịch sử từ `/predictions`.

**Không nạp thư viện ngoài.** Cả biểu đồ lẫn sơ đồ vẽ bằng canvas thuần. Thêm
một gói CDN là thêm một thứ phải có mạng mới chạy — máy chấm có thể không nối
Internet, và lúc đó biểu đồ biến mất mà không báo gì.

**WebSocket tự nối lại**, giãn dần 1 → 15 giây. Chỉ nối lại ở `onclose` chứ
không ở cả `onerror`: mỗi lần hỏng trình duyệt bắn `onerror` rồi `onclose`, xử
lý cả hai là hẹn hai lần và thời gian chờ tăng gấp đôi mỗi vòng.

**Chốt ba nơi dùng chung phép biến đổi mét↔pixel.** Python (`tools/`), Dart
(`floor_map.dart`) và JavaScript (`coordinate.js`) đều giữ một bản hằng số.
`tests/test_dashboard.py` đối chiếu cả ba với `ban_do_tang1.json`. Lệch ở đây
thì cùng một toạ độ hiện ở hai chỗ khác nhau trên hai màn hình, mà triệu chứng
nhìn y hệt "mô hình đoán sai".

**Bắt lỗi kiểu JavaScript.** Gõ sai một id thì `querySelector` trả `null` và
trang chết lặng ở đúng chỗ đó. Test soát mọi selector trong JS phải có id tương
ứng trong HTML, soát chiều ngược lại để không còn id thừa, và soát mọi `import`
phải có `export` tương ứng.

**Kiểm chứng chạy thật.** Ngoài test, đã chạy `dashboard.js` bằng Node với một
lớp DOM tối thiểu, trỏ vào máy chủ thật: bản đồ nạp đúng (86 × 52 m, 44 điểm,
62 cạnh), 44 mục trong ô chọn, bấm "Tìm đường" ra đủ 6 bước, gửi một lần quét
lên `/predict` thì WebSocket đẩy về và bảng thiết bị lên 1 — không lỗi JS nào.

**Còn lại lúc đó.** Sáu trang khung rỗng trong `frontend/pages/` (dataset,
models, evaluation, history, collection, settings) chưa làm: chúng cần endpoint
mà backend không có (thống kê dataset, danh sách mô hình, bảng đánh giá). Số
liệu cho chúng nằm ở `reports/tables/*.csv` và `reports/figures/*.png` dưới dạng
tệp tĩnh.

*Đã xử lý ở đợt sau: xoá hẳn sáu trang. Không trang nào có nội dung, mà giữ lại
chỉ là giữ sáu đường dẫn 404 có tiêu đề. Xem mục 2.7.1 của tài liệu thiết kế.*

### Kiểm thử

| | Trước | Sau |
|---|---|---|
| Kiểm thử Python | 89 | **100** |

Đã kiểm chứng test đỏ khi đảo dấu góc quay.

---

## Rà soát toàn dự án — sửa lỗi tìm được

### README nói sai về chính dự án ✅

Tệp hội đồng đọc đầu tiên đang mô tả trạng thái của ba tuần trước: *"Ứng dụng
chạy trên dữ liệu demo tĩnh, chưa nối API"*, *"Dashboard web chưa viết"*, và
lệnh chạy Dashboard trỏ vào `python -m http.server` trong khi máy chủ API đã
phục vụ luôn giao diện.

Đã sửa cả sáu chỗ, thêm mục "Web Dashboard", thêm `tools/` vào bảng cấu trúc, và
thêm nguyên tắc 5 — `data/reference/` là nguồn sự thật duy nhất về không gian.

**Chỗ đáng nói nhất:** README ghi *"Mô hình chính: XGBoost"* trong khi
`mo_hinh_active = fingerprint_knn` và `/predict` trả về đúng tên đó. Tài liệu
thiết kế §2.4.1 vốn đã nêu sòng phẳng cả hai con số (1,92 m so với 6,48 m),
riêng README thì không. Nay README nói rõ hai việc khác nhau: XGBoost là mô hình
chính **của đề tài**, còn mô hình **đang triển khai** chọn theo validation và
hiện là kNN vân tay. `GET /health` luôn cho biết cái nào đang chạy.

### Múi giờ: Dashboard hiện sai 7 tiếng ✅

`/predictions` trả về `"2026-08-31T07:05:43.288771"` — đúng giá trị UTC nhưng
**không có hậu tố Z**. Theo chuẩn ECMAScript, chuỗi date-time không mang offset
bị `new Date()` hiểu là **giờ địa phương**, nên cột "Lúc" hiện 07:05 trong khi
giờ thật là 14:05.

Lần sửa đầu bằng `DateTime(timezone=True)` **không ăn**: SQLite không có kiểu
ngày giờ riêng nên SQLAlchemy bỏ qua cờ đó. Phải viết `MocThoiGian`
(`TypeDecorator`) quy về UTC lúc ghi và gắn lại `tzinfo` lúc đọc. Vẫn lưu dạng
trần để SQLite còn so sánh và sắp xếp được bằng thứ tự chuỗi.

Đặt ở tầng kiểu chứ không ở schema Pydantic: sửa tại chỗ đó thì mọi nơi đọc mô
hình đều nhận giá trị đúng, không riêng một endpoint.

### Phiên định vị không bao giờ kết thúc ✅

Hai tầng hiểu "phiên" khác nhau:

- `BoGop`: im lặng quá `reset_after_seconds` → coi như người dùng đi chỗ khác
  rồi quay lại, xoá lịch sử gộp.
- `repository.lay_hoac_tao_phien`: luôn lấy lại bản ghi cũ nhất của thiết bị,
  chỉ cập nhật `lan_cuoi`.

Hệ quả: một máy quay lại sau một tuần vẫn nối vào phiên cũ, `bat_dau` trở thành
"lần đầu máy này từng xuất hiện", và bảng `positioning_sessions` không phân định
được lượt ghé nào với lượt nào. Nay tầng lưu trữ dùng chung đúng ngưỡng đó.

### Bốn lỗi Nhóm 2 ✅

**1. Bấm Dừng giữa lúc đang quét.** `dungLai()` huỷ timer nhưng lần quét đang bay
dở vẫn về đích 2–3 giây sau và ghi đè trạng thái thành `dangChay`. Nút đổi lại
thành "Dừng", màn hình nói đang theo dõi, mà không còn gì chạy nữa.

Sửa bằng biến đếm lượt: `batDau()` và `dungLai()` đều tăng nó, mỗi vòng quét giữ
số lượt của mình và chỉ được ghi kết quả nếu số đó chưa đổi. Chọn cách này thay
vì kiểm `_hen != null` vì nó xử lý được cả trường hợp bật → tắt → bật nhanh, lúc
đó `_hen` khác null nhưng vòng quét cũ vẫn là kết quả cũ.

**2. Gõ sai địa chỉ máy chủ thì app báo "Quét WiFi thất bại".** `http` ném
`ArgumentError` khi URI thiếu host — mà `ArgumentError` là `Error` chứ không phải
`Exception` nên `on Exception` để lọt, và vòng quét bắt nhầm thành lỗi quét.
Người dùng vừa gõ sai địa chỉ lại đi kiểm tra quyền và WiFi.

Thêm `LoiApi.diaChiSai` và dựng URL qua `_url()` có kiểm tra. Bốn cách gõ đều
được bắt đúng: `192.168.1.5`, `localhost:8000`, `may-chu`, `http://`.

Một cái bẫy lúc sửa: `_url()` ném `NgoaiLeApi`, mà nó *là* `Exception`, nên gọi
trong `try` thì chính khối `on Exception` bên dưới nuốt mất và lại báo thành mất
kết nối. Phải dựng URL **ngoài** `try`.

**3 và 4. Cài đặt luôn nói "Đã cấp", và `permission_handler` khai mà không
dùng.** Hai lỗi này giải cùng nhau: `mobile/lib/services/quyen_truy_cap.dart` bọc
`permission_handler` thành ba trạng thái — chưa cấp, đã cấp, bị chặn — và dòng
trong Cài đặt đọc trạng thái **thật**, chạm vào thì xin quyền, hoặc mở Cài đặt hệ
điều hành nếu đã bị chặn hẳn.

Coi là đã cấp khi **một trong hai** quyền được cấp chứ không phải cả hai: từ
Android 13 `NEARBY_WIFI_DEVICES` dùng thay quyền vị trí, và máy mới trả `denied`
vĩnh viễn cho quyền vị trí.

Lớp này tiêm được, nên bài test không phải đụng kênh nền tảng. Khi không đọc
được quyền (chạy trong test, hoặc trên web) thì hiện "Đang kiểm tra…" chứ không
bịa ra một trạng thái.

### Kiểm chứng

| | Trước | Sau |
|---|---|---|
| Kiểm thử Python | 100 | **108** |
| Kiểm thử mobile | 47 | **60** |

Hoàn tác từng sửa đổi để chắc bài test bắt được thật: bỏ biến đếm lượt → 1 bài
đỏ; bỏ kiểm tra địa chỉ → 4 bài đỏ; bỏ `MocThoiGian` và ranh giới phiên → 4 bài
đỏ.

Một bài test lúc đầu không tin được: trỏ vào `khong-ton-tai.invalid` để thử
trường hợp không kết nối được, nhưng máy này có DNS bắt tên sai và trả về trang
lỗi thật, nên nhận `mayChuLoi` thay vì `khongKetNoi`. Đã đổi sang client giả ném
`SocketException`.

### Còn lại, chưa làm

*Cập nhật 01/09/2026: ba trong bốn mục dưới đây đã xử lý, xem vòng rà soát ở
cuối tài liệu.*

- ✅ **Quét rỗng vẫn ra toạ độ tự tin** — đã chặn bằng ngưỡng `min_ap_per_scan`,
  máy chủ trả 422.
- ✅ **Tài liệu `docs/` còn vài chỗ cũ** — đã đồng bộ toàn bộ.
- 📄 **`/ws/location` phát toạ độ của mọi thiết bị cho mọi kênh đang mở**, kèm cả
  `device_id`. Không sửa: Dashboard cần đúng như thế. Đã ghi vào mục "Hạn chế đã
  biết" của README.
- ⏸ **Gộp buổi thu 06/09/2026 — đã thử, đang hoãn.** Gộp làm kNN vân tay xấu đi
  2,30 → 3,54 m, và thiệt hại nằm trên chính những điểm cũ (2,30 → 4,08 m) chứ
  không phải điểm mới (0,49 m). Nguyên nhân là lệch thiết bị Samsung/Redmi. Công
  tắc `ml.config.GOP_BUOI_BO_SUNG = False`; bằng chứng đầy đủ ở
  `data/raw/nhom15_2026/README.md`. Mở lại sau khi đo độ lệch hai máy.

- ⏳ **Năm điểm có toạ độ nhưng không có mẫu đo nào** — 44 điểm trên bản đồ, 39
  điểm có dữ liệu: RP26 (Khu vực đọc, kế thừa CTK45 nhưng buổi thu 2025 bỏ sót),
  RP42/RP43 (WC) và RP44/RP45 (cầu thang) do nhóm 2025 thêm. `/route` dẫn tới cả
  năm, mô hình thì vĩnh viễn không báo được chúng. Muốn sửa phải đo tại chỗ.
  `ml.audit` mục 5 theo dõi con số này để nó không trôi.

### Đã kiểm, sạch

Dựng một bản clone chỉ gồm tệp git theo dõi rồi chạy thử: **223 tệp, 12 MB, 67
passed / 33 skipped**, mọi bài bỏ qua đều đúng lý do "chưa có mô hình".

Không toạ độ nào lệch giữa `reference_points.csv` và dataset. Chạy lại
`ml.report` cho ra hình **giống hệt từng byte** — biểu đồ không lỗi thời. Quét
toàn repo không còn chuỗi kết nối hay mật khẩu nào.

---

## Cân nhắc riêng — dữ liệu CTK45

CTK45 có 6.338 lần quét trên đúng 40 điểm, 120–164 lần mỗi điểm, so với 802 lần
của ta. Cả 34 cột AP của họ đều nằm trong 36 cột hợp đồng của ta.

**Không ghép thẳng vào tập huấn luyện.** Khác máy, khác đợt thu, giá trị điền
thiếu −100 thay vì −96; ghép vào sẽ khiến người phản biện hỏi dữ liệu nào của
nhóm nào.

Nên dùng làm **tập kiểm định độc lập**. Cách này còn mở khoá được hai thí nghiệm
`device_holdout` và `time_holdout` mà tài liệu thiết kế ghi là bắt buộc nhưng đã
kết luận không làm được, do mỗi điểm tham chiếu của ta chỉ đo trong đúng một buổi.

---

## Phần đã rà soát và quyết định KHÔNG lấy

| Tệp CTK45 | Lý do |
|---|---|
| `wifi_service.dart` | Gửi mảng số trần, 8 MAC viết cứng — đúng lỗi ta đang cải tiến |
| `mapcontroller.dart` | Lấy 3 RSSI mạnh nhất đã sắp xếp, bỏ hẳn thông tin AP nào |
| `map_widget.dart` | Mapbox với token để nguyên `your_mapbox_access_token_here` |
| `route_service.dart` | Haversine cho khoảng cách 40 m; nhầm lat/lon với x/y |
| `POISelectionScreen.dart` | 1.360 dòng gộp Dijkstra, TTS, la bàn, vẽ và UI vào một lớp |
| `wifi_mlp_model.tflite` | MLP 18 KB, kém xa fingerprint_knn của ta |
| `Wall.geojson` | Chỉ 56 m, không phải đường bao toà nhà |
| 15 tệp giao diện | Giao diện hiện tại của ta hoàn thiện hơn |

---

## Vòng rà soát 01/09/2026

Rà lại toàn dự án sau khi đẩy 8 commit lên GitHub. Mười ba phát hiện, đã xử lý
mười hai; mục còn lại cần đo thực địa.

### Lỗi thật

**WKNN và kNN cho kết quả trùng khít.** Đợt nới lưới tham số trước đó thêm `k=1`
vào cả hai mô hình. Với một láng giềng duy nhất thì trọng số không có gì để cân,
nên WKNN ở k=1 chính là kNN ở k=1 — bảng so sánh có hai dòng giống nhau tới 16
chữ số, tức mất một mô hình cơ sở mà không ai thấy. Đã bắt lưới WKNN bắt đầu từ
k=2. Huấn luyện lại: WKNN 5,1537 → **4,5885 m**, các mô hình khác giữ nguyên
từng chữ số, và năm biểu đồ không đổi một byte.

**Trang chủ bịa tên phòng khi chưa định vị.** Chỗ tiêu đề hiện sẵn "Phòng học
nhóm" — một cái tên không có trong dữ liệu khảo sát lẫn mã nguồn CTK45 — nên ứng
dụng trông như đã định vị xong ngay khi vừa mở. Nay nói "Chưa xác định vị trí".

**Header Bản đồ luôn ghi "cập nhật 2 giây trước"** vì lấy một hằng số viết cứng,
đúng hai giây trong cả vòng đời ứng dụng kể cả lúc định vị đang tắt. Nay lấy mốc
thời gian thật, và bỏ hẳn vế thời gian khi chưa có toạ độ nào.

**Hai công tắc trong Cài đặt không nối vào đâu.** "Tự động cập nhật vị trí" mặc
định bật, tắt đi thì vòng quét vẫn chạy y nguyên. Đã bỏ cả hai; nhóm "ĐỊNH VỊ"
giữ một dòng thông tin đúng sự thật về chu kỳ quét 5 giây.

### Chỗ khiến lỗi lọt qua kiểm thử

**Hằng số dịch trục không nơi nào kiểm.** Phép đổi mét ↔ pixel có bốn hằng số
được `test_dashboard.py` đối chiếu, nhưng số hạng `+ 43` thì viết trần ở bốn chỗ
và không tệp nào khai nó — sửa lệch một nơi thì lệch tới 86 m mà mọi bài test
vẫn xanh. Nay có tên `goc_met_x` / `gocMetX`, ghi vào `ban_do_tang1.json` và neo
vào chính `x.min()` của bảng toạ độ.

**Hai bản `Map.png` không gì buộc phải giống nhau.** Flutter chỉ đóng gói được
asset trong `mobile/` nên phải có bản chép. Nay có bài test so sha256.

### Tài liệu

Đồng bộ toàn bộ `.md` với hiện trạng, giữ nguyên phần đã làm đúng đề cương:

- Bỏ hẳn khuyến nghị PostgreSQL. Mục 2.5 lật thành "Đã chốt: SQLite", giữ ba lý
  do ủng hộ PostgreSQL rồi trả lời từng lý do bằng cái đã đo được. Trùng khớp
  luôn với mục V đề cương, nên mâu thuẫn SQLite ↔ PostgreSQL không còn.
- Thêm mục đối chiếu cho API (2.6.1), giao diện (2.7.1) và rủi ro (2.8.1).
- Mục 2.9 chép đúng 12 mốc của đề cương kèm tình trạng từng mốc.
- Nói thẳng kết quả XGBoost so với cam kết mục VI đề cương, và nó **phụ thuộc giao
  thức đánh giá**: chia ngẫu nhiên theo lần quét thì XGBoost cao hơn kNN 14,0% và
  cao hơn WKNN 36,1% — không đạt; bỏ trọn một điểm tham chiếu thì XGBoost đứng đầu
  với 14,60 m, thấp hơn kNN 13,6% và thấp hơn WKNN 6,4% — đạt với kNN. Nguyên nhân
  là tính chất dữ liệu, không phải thiếu tinh chỉnh. XGBoost vẫn là mô hình chính.
- Ghi rõ ứng dụng di động nằm **ngoài phạm vi đề cương**, và front-end không
  dùng Tailwind như mục V ghi.
- `mobile/README.md` viết lại toàn bộ: bản cũ vẫn mô tả "bản demo giao diện chưa
  nối API" và trỏ tới những tệp đã xoá.
- README có thêm mục "Hạn chế đã biết".

### Việc lặt vặt

Thêm `shared_preferences`: địa chỉ máy chủ, ngôn ngữ và chế độ sáng/tối được nhớ
giữa hai lần mở app — bắt gõ lại IP mỗi lần mở là hỏng buổi demo. Đã build APK
thật để chắc không tái diễn xung đột Kotlin như hồi thêm `wifi_scan`.

Dọn mã chết trong `demo_data.dart`, ba khoá `.arb` không ai dùng, vế
`asyncio.TimeoutError` thừa trong `except`, và `backend/main.py` thiếu ký tự
xuống dòng cuối tệp.

### Kiểm chứng

| | Trước | Sau |
|---|---|---|
| Kiểm thử Python | 125 | **128** |
| Kiểm thử mobile | 57 | **65** |

Mọi bài test mới đều đã kiểm là đỏ trước khi sửa: đổi `gocMetX` sang −42 → 1 bài
đỏ; thêm một byte vào `Map.png` bản mobile → 1 bài đỏ.

Một bài test lúc đầu vô nghĩa: dùng `find.byType(Switch)` để chốt việc bỏ công
tắc chết, nhưng `GlassSwitch` tự vẽ chứ không bọc `Switch` của Material nên phép
so đó xanh vĩnh viễn. Đã đổi sang `find.byType(GlassSwitch)`.

### Còn lại

- 7 cửa ra vào trong `ban_do_tang1.json` vẫn là giả định chưa đối chiếu
  thực địa.
- Mục 4.3 đề cương — đánh giá độ ổn định theo mật độ người — cần một đợt đo mới.
- **RP41**: đã thu 20 lần quét nhưng chưa đo toạ độ, nên pipeline bỏ cả 20. Ước
  lượng thô từ vân tay RSSI khoảng (−14,5 · 40,7); chỉ cần một buổi đo là dùng
  được.
- Hai thư mục rỗng còn lại từ thiết kế cũ: `backend/migrations/` và
  `frontend/assets/icons/`.

---

## Cập nhật 05/09/2026 — số liệu hiện hành

Các mục ✅ bên trên ghi số liệu **đúng tại thời điểm làm xong**, giữ nguyên làm
nhật ký. Sau đợt sửa toạ độ và bổ sung điểm của nhóm 2025, số hiện hành là:

| | Lúc ghi ở trên | Hiện nay |
|---|---:|---:|
| Điểm tham chiếu có toạ độ | 40 | **44** |
| Nhóm khu vực | 11 | **12** |
| Cạnh đồ thị đi lại | 58 | **62** |
| Cửa giả định | 6 | **7** |
| Mảnh rời trước khi nối | 7 | **8** |
| Cạnh dài nhất | 17,2 m | **16,12 m** |
| Kiểm thử Python | 144 | **160** |
| Kiểm thử Flutter | 98 | **101** |

Bảng so sánh mô hình cũng đổi theo vì nhãn toạ độ của RP01, RP03, RP09 đã sửa:

| Mô hình | Chia ngẫu nhiên | Bỏ trọn một điểm |
|---|---:|---:|
| XGBoost | 6,26 m | **14,60 m** ① |
| Random Forest | 6,59 m | 15,03 m |
| WKNN | 4,60 m | 15,60 m |
| kNN vân tay | **2,30 m** ① | 16,54 m |
| kNN | 5,50 m | 16,90 m |

Bốn điểm mới chưa có lần quét WiFi nào (RP42, RP43 là WC; RP44, RP45 là cầu
thang) nên chúng vào bản đồ và làm đích dẫn đường được, nhưng không vào dữ liệu
huấn luyện — dữ liệu vẫn là 782 mẫu trên 39 điểm.

### Còn lại sau đợt này

- Nhóm **WC chưa có ảnh thực tế**, nên `tests/test_khu_vuc.py` đang đỏ một bài.
- **Hành lang nam chưa thành đường đi**: RP45 (−28) ↔ RP02 (0) ↔ RP44 (28) cách
  nhau 28,1 m, đi thẳng không vướng tường nhưng xa hơn ba láng giềng gần nhất
  của cả hai đầu nên `SO_LANG_GIENG = 3` không sinh cạnh. Tuyến từ TV3,4 sang
  Hội trường vì thế vòng lên giữa nhà, dài gấp 1,5 lần đường thẳng.
- **Lưới tham số chạm biên trở lại**: cả 5 mô hình đều có tham số tối ưu rơi vào
  mép lưới, riêng XGBoost tì biên ở 5 chiều cùng lúc.

## Rà soát 11/09/2026 — lỗi tiềm tàng giai đoạn 1, 2

- **Giao thức bỏ trọn một điểm rò rỉ**: nó đọc `fingerprint_dataset_raw.csv`, mà
  bộ AP, giá trị điền và Hampel trong tệp đó đã học từ tập train có mặt mọi
  điểm. Nay mỗi lần gấp làm lại bước 5-10 chỉ trên phần học. XGBoost 14,60 →
  **15,01 m**, vẫn đứng đầu, thấp hơn kNN 11,6% và WKNN 5,4%; bảng 05/09 ở trên
  giữ nguyên làm mốc lịch sử.
- **0 dBm không còn là số đo hợp lệ**, ở cả backend lẫn pipeline — đó là số trình
  điều khiển trả khi AP quá gần. Dữ liệu thô không có số đọc nào như vậy nên
  artifact không đổi.
- **Cảnh báo phân tầng bỏ sót lần tách val/test**: điểm có 3 mẫu qua được lần cắt
  đầu nhưng tập tạm chỉ còn 1, sklearn lặng lẽ chia thường. Dữ liệu hiện tại mỗi
  điểm 20-21 mẫu nên chưa dính.
- Ba chú thích khẳng định "luôn rơi đúng một điểm tham chiếu" nay ghi rõ đó là
  hệ quả của mô hình k=1 hiện tại, không phải bất biến.

## Rà soát 11/09/2026 — lỗi tiềm tàng giai đoạn 3, 4

- **Số vô hạn làm 422 hoá 500**: `1e999` là JSON hợp lệ và đọc ra inf. `/route`
  nhận nó làm `tu_x`, còn mọi lỗi schema chép lại giá trị gửi lên vào thân 422,
  mà inf/NaN không tuần tự hoá được. Nay `tu_x`/`tu_y` từ chối số không hữu hạn
  và thân 422 bỏ trường `input`.
- **Khung WebSocket nhị phân làm đứt kênh** (`KeyError: 'text'` trong
  `receive_json`). Nay đọc được cả khung chữ lẫn khung nhị phân.
- **Phát toạ độ lần lượt**: mỗi dashboard treo cộng thêm 2 s vào độ trễ của
  `POST /predict`. Nay gửi song song, tối đa một hạn giờ.
- Dashboard: `api.js` huỷ hẹn giờ trước khi đọc xong thân và để lỗi đọc JSON
  lọt ra dạng `SyntaxError`; bấm "Tìm đường" hai lần có thể vẽ tuyến của lần
  trước; socket cũ bắn `onclose` sau khi đã mở socket mới thì sinh thêm một
  chuỗi nối lại.
- Đã kiểm, sạch: chạy test không ghi vào `data/ips.db` thật; máy chủ chỉ phục vụ
  đúng 11 tệp của `frontend/`; mọi chỗ hiện dữ liệu máy chủ đều qua `textContent`.

Vòng hai, cùng ngày:

- **Một lần CSDL lỗi làm đứt kênh WebSocket.** Nay trả `{"loi": "may_chu_loi"}`
  rồi nghe tiếp; ứng dụng di động vốn xếp mã lạ vào `mayChuLoi`.
- **Client bị loại khỏi danh sách phát không bị đóng**, nên Dashboard vẫn báo
  "Đang kết nối" mà không nhận gì và không tự nối lại. Nay đóng mã 1011.
- **Mã không giới hạn độ dài**: `tu_rp` 2 MB được trả nguyên văn trong thân 404.
  Nay `bssid`, `tu_rp`, `den_rp`, `den_nhom` tối đa 64 ký tự; `den_rp`,
  `den_nhom` cũng cắt khoảng trắng như `tu_rp`.
- **`CUA_SO_GOP=0` làm mọi `/predict` vỡ `IndexError`**. Nay cấu hình từ chối
  ngay lúc khởi động.
- Dashboard tự thử lại khi mở trang lúc máy chủ chưa lên.
- Đã đo, KHÔNG phải lỗi: 5 yêu cầu đồng thời của một thiết bị mới vẫn chỉ mở 1
  phiên.
- Chú thích và docstring ở `backend/`, `frontend/` giảm từ 424 xuống 187 dòng;
  AST Python và các dòng mã JS so với trước khi nén y hệt.

## Sửa theo mức ưu tiên — 11/09/2026

- **Cửa sổ trượt đo sai thứ tự.** Phép mô phỏng chạy theo thứ tự dòng trong
  `test.csv` chứ không theo thời gian; chỉ 6/39 điểm tình cờ đúng thứ tự. Nay
  chạy theo thời gian, và đo thêm trên chuỗi dài train+val đoán ngoài phần.
- **Hoà thì lấy dự đoán mới nhất.** Chọn trên train+val theo thời gian, cả bốn
  mô hình đều tốt hơn lấy cái cũ. kNN vân tay, cửa sổ 3: test 2,30 → 1,72 m
  (sai 18 → 14/118), chuỗi dài 1,69 → 0,86 m (sai 76 → 40/664). Con số 1,40 m
  cũ bỏ ở mọi nơi.
- **Bảng qua 10 seed** (`python -m ml.on_dinh`, `model_stability.csv`): seed 42
  xấu bất thường cho kNN (5,50 m so với 3,61 ± 0,78); XGBoost thua kNN ở 10/10
  seed; riêng seed 42 hai mô hình chồng khoảng tin cậy.
- `ml.report` vẽ theo mô hình đang triển khai, không chọn theo sai số test.
- Lưới `beta` thêm 4,0 để cực trị 3,5 nằm trong lưới; nới biên XGBoost và RF
  thêm một nấc đổi validation dưới 0,1 m nên giữ nguyên lưới.
- Backend bật thực thi khoá ngoại SQLite; Swagger khai mã 404/409/422.
- CSDL local dọn còn 37 dự đoán của điện thoại thật, có sao lưu trước khi dọn.
- Tài liệu: 7 cửa giả định, 12 khu vực, 40 ảnh/12 thư mục, bỏ các con số dễ lỗi
  thời; `.env.example`; `requirements.txt` thêm Pillow, scipy cho `tools/`.
- Giữ nguyên, có lý do: giá trị điền −96 (đổi dữ liệu thì mã băm hợp đồng bắt
  được); 32/36 đặc trưng là BSSID ảo — chất liệu phân tích, chưa phải lỗi.

## Chỉ đường theo đồ thị tầm nhìn — 11/09/2026

- **Tuyến vòng vo vì đồ thị quá thưa.** Mỗi điểm chỉ nối 3 điểm gần nhất nên
  RP20 (cầu thang tây) tới Căn tin đi 111 m qua 10 chặng, trong khi đường thẳng
  là 65,8 m. Nay nối thẳng mọi cặp điểm nhìn thấy nhau trên sơ đồ (246 cặp, dò
  bằng `tools/trich_ban_do.py`) cộng 7 cửa giả định cũ: còn 72,6 m qua 2 điểm
  mốc. Trên 946 cặp: độ vòng trung vị 1,50 → 1,11, số chặng 6,3 → 2,6, không
  cặp nào dài ra. Chọn đích theo chim bay sai 16,1% → 5,1%. Cầu thang sát Căn
  tin là RP44, 11 m.
- **Khoảng cách hiển thị là quãng đường còn lại.** App tính lại tuyến mỗi khi
  điểm gần nhất đổi; vào khu vực đích thì chip báo "Đã tới …" và ẩn tuyến, đi
  khỏi thì tính lại.
- Back ở màn Tìm kiếm đóng tìm kiếm rồi về Trang chủ, không thoát app.
- Thẻ "Bạn đang ở" và chip tuyến đường thôi gộp ngữ nghĩa cả khối: TalkBack
  chạm được riêng nút định vị, tên khu vực và nút xoá tuyến.
- Mất máy chủ thì Trang chủ ghi vị trí đang hiện đã cập nhật cách đây bao lâu.
- Bước đầu của chỉ dẫn nói "Đi", không "Đi thẳng" — chưa biết người dùng quay
  mặt về đâu.
- Giữ nguyên: tìm kiếm không phân biệt dấu ("tin" khớp "tính"), để gõ không dấu
  vẫn tìm được.

## Chỉ đường trên lưới đi lại, tỉ lệ mét — 14/09/2026

- **Một đơn vị lưới không phải một mét.** Hình 7 báo cáo CTK45 ghi toà nhà cao
  4 + 5,2 + 8,8 + 1,6 = 19,6 m trên 55,87 đơn vị: 0,3508 m/đơn vị. Đa giác
  OpenStreetMap chỉ chứa trọn mặt bằng khi ≤ 0,35 (ở 1,0 chỉ 74% lọt); GPS của
  `POI.geojson` cho trung vị 0,40. Câu "cách nhau 7 mét" từng dùng làm căn cứ nằm
  trong đoạn CTK45 chép từ bài báo khác. Tuyến Cầu thang → Căn tin: 72,6 → 23,2 m.
- **A* và Dijkstra chạy trên góc vật cản.** Nút là 417 góc lồi dò từ `Map.png`
  cộng 44 RP, 17.209 cạnh nhìn thấy nhau; tuyến đi từ đúng vị trí người dùng.
  Sai so với mốc (Dijkstra lưới điểm ảnh 80 hướng), 4.400 cặp: trung bình 2,40 →
  0,03 m, lớn nhất 31,1 → 0,17 m. A* mở 32,7 nút, Dijkstra 253,7, cùng quãng đường.
- **Trên tập test:** quãng đường hiển thị từ vị trí dự đoán so với quãng đường
  thật, cửa sổ 3: ứng dụng cũ sai trung bình 31,5 m, nay 0,44 m (trung vị 0,03).
- Chỉ dẫn: góc vật cản mang tên đích; chặng dưới 0,5 m dồn vào chặng kề.
- App: "cách X m" nhân tỉ lệ; đi từ 1 m cũng tính lại quãng đường còn lại.
- `/map` trả `don_vi: don_vi_luoi` và `met_moi_don_vi`; `/route` nhận `thuat_toan`.
- Chưa đổi: bảng sai số định vị ở mục 2.4 vẫn là đơn vị lưới dưới nhãn "m".

## Thu gọn kiểm thử — 14/09/2026

- Chỉ giữ kiểm thử REST API, bỏ phần còn lại (kể cả kiểm thử WebSocket) theo yêu cầu.
  Tính năng WebSocket vẫn giữ, chỉ không còn kiểm thử.
- Backend: 277 → 58 ca. `tests/test_api.py` gom 52 kiểm thử endpoint HTTP từ 9 tệp.
- Flutter: 112 → 19 ca, `test/api_test.dart` (lớp gọi API).
- Không còn kiểm thử cho tiền xử lý, huấn luyện, đánh giá chéo, hậu xử lý, đồ thị
  và lưới chỉ đường, hằng số đổi toạ độ giữa ba ngôn ngữ, giao diện ứng dụng.

## Tạm tắt WebSocket, dùng REST — 14/09/2026

- Backend: `WEBSOCKET` (mặc định `false`). Tắt thì `/ws/location` đóng ngay bằng
  403 thay vì rơi xuống StaticFiles vỡ 500, `/predict` không phát tin; `/health`
  trả `websocket`. Mã WebSocket giữ nguyên, bật lại không phải sửa gì.
- `/predictions` thêm `device_id` và `do_tre_ms` để Dashboard vẽ được thiết bị.
- Dashboard: tắt WebSocket thì hỏi `/predictions` mỗi 2 giây; lượt đầu chỉ lấy mốc để
  lịch sử cũ không hiện thành thiết bị đang định vị.
- Ứng dụng: `_dungWebSocket = false`, gửi lần quét qua `POST /predict`.
- Kiểm chứng: 59 kiểm thử REST đạt, kiểm thử công tắc đỏ khi bật WebSocket; máy chủ
  thật trả 403 cho `/ws/location`; logic hỏi định kỳ chạy thử bằng Node. Chưa xem
  Dashboard trên trình duyệt thật.

## Toạ độ RP01, RP03, RP09 theo Bảng 4 — 14/09/2026

- Dữ liệu chép từ CTK45 nên toạ độ theo đúng Bảng 4 và `combined_data_sorted.csv`
  của họ: RP01 (−16, 0), RP03 (16, 0), RP09 (30, 14). Giá trị ±41 và (38, 7) từng
  được đổi trong commit `8de69f7` mà không ghi căn cứ. Cột `note` nay ghi nguồn.
- Sinh lại pipeline, mô hình, báo cáo, 10 seed, bỏ trọn một điểm, bản đồ,
  `khu_vuc_thu_vien.dart`. Hợp đồng dữ liệu không đổi (chỉ `created_at`).
- Mô hình (test seed 42): kNN vân tay 2,32 · WKNN 4,60 · kNN 5,41 · XGBoost 5,82 ·
  RF 6,69. Bỏ trọn một điểm: XGBoost 14,26 đứng đầu. Chuỗi dài sau gộp 0,82 m.
- Bản đồ: cửa giả định 7 → 6, cặp nhìn thấy nhau 246 → 257, lưới đi lại 347 góc.
  RP20 → Căn tin nay nối thẳng 55,7 đơn vị = 19,4 m.
- Chỉ đường: sai so với mốc 0,03 m; A* mở 36,2 nút, Dijkstra 195,2.
- `test_route_chon_thuat_toan` đổi điểm xuất phát: (30, 14) nay chính là Căn tin.

## Rà dữ liệu đầu vào, giai đoạn 1 và huấn luyện lại — 14/09/2026

- Dữ liệu thô sạch: 25.712 dòng, 802 lần quét, không trùng, RSSI −95…−19, mỗi lần quét
  một điểm; 237 ô trống đều là SSID ẩn (không dùng). 40 toạ độ khớp dữ liệu CTK45.
- Lỗi thật: nhãn "RP41" là RP26 — 20/20 lần quét trùng khít RP26 trong
  `combined_data_sorted.csv` của CTK45, đo giữa phiên RP27 và RP28. Pipeline bỏ 20
  lần quét và mất vị trí RP26. Sửa lúc nạp (`NHAN_RP_SUA`), không sửa tệp thô.
- Mã giai đoạn 1 không có lỗi logic mới. Hợp đồng dữ liệu giữ nguyên 36 AP, −96 dBm.
- Huấn luyện lại trên 802 lần quét, 40 điểm (train 561 · val 120 · test 121):
  test seed 42 kNN 3,44 · kNN vân tay 3,47 · WKNN 3,52 · XGBoost 6,28 · RF 6,67;
  10 seed kNN vân tay 2,44 ± 0,34 dẫn 9/10; bỏ trọn một điểm XGBoost 14,21 đứng đầu.
- Seed 42 nay xấu bất thường cho kNN vân tay chứ không cho kNN.
- Sinh lại 7 biểu đồ đánh giá; chỉ đường đầu–cuối 0,59 m (trung vị 0,03 m).

## Rà soát giai đoạn 3, 4 sau khi huấn luyện lại — 14/09/2026

- Hợp đồng giai đoạn 1 → 3: 121/121 lần quét test dựng lại từ dữ liệu thô, gửi qua
  `POST /predict`, trùng khít dự đoán ngoại tuyến (lệch 0); suy luận trung vị 0,9 ms.
- Chạy mọi endpoint trên máy chủ thật: `/route` 528 cặp x A*/Dijkstra khớp nhau, các ca
  lỗi đúng mã 404/422, `/ws/location` 403, tệp tĩnh Dashboard 200, log không traceback.
- Gọi `localhost` trên Windows chậm 2 s mỗi yêu cầu do thử IPv6 trước — lỗi phía gọi,
  `127.0.0.1` còn 6 ms. App và Dashboard dùng IP LAN nên không bị.
- Sửa nhãn đơn vị: toạ độ là đơn vị lưới nhưng Dashboard ghi phạm vi "86 × 52 m" (nay
  30,2 × 18,2 m), cột "x (m)"/"y (m)" hai bảng, thông báo ngoài phạm vi; app ghi
  "x … m · y … m".
- Chạy `api.js` và vòng hỏi REST thật của Dashboard bằng Node với máy chủ thật: đạt.


## Toạ độ RP01, RP03, RP09 theo bản vẽ mặt bằng, nhãn từng điểm — 14/09/2026

- Nhóm chốt toạ độ theo `reports/figures/ban_ve_kieu_ctk45.png`: RP01 (−41, 0),
  RP03 (41, 0), RP09 (38, 7). Bảng 4 và dữ liệu CTK45 ghi (−16, 0), (16, 0), (30, 14);
  cột `note` ghi cả hai.
- Sơ đồ app: mỗi điểm một nhãn (44 nhãn) thay vì một nhãn mỗi cụm; thước 10 m lùi vào
  để khỏi đè nhãn TV3,4.
- Sinh lại bản đồ (7 cửa giả định, 246 cặp nhìn thấy nhau, lưới 417 góc / 17.275 cạnh),
  `khu_vuc_thu_vien.dart`, pipeline, mô hình, báo cáo, 10 seed, bỏ trọn một điểm, hình.
- Test seed 42: kNN 3,44 · kNN vân tay 3,45 · WKNN 3,51 · RF 6,92 · XGBoost 7,02;
  10 seed kNN vân tay 2,58 ± 0,36 dẫn 9/10; bỏ trọn một điểm XGBoost 14,80 đứng đầu.
- Chỉ đường: sai so với mốc 0,03 m; A* mở 32,7 nút, Dijkstra 253,7; đầu–cuối 0,59 m.
- 59 kiểm thử backend, 19 Flutter đạt; kiểm trên máy thật.

## Nối thêm 5 cạnh nhóm chỉ định — 15/09/2026

- `CUA_NHOM_CHI_DINH` trong `tools/trich_ban_do.py`: RP26-RP19, RP27-RP19, RP29-RP20,
  RP32-RP21, RP06-RP02. Mở trên mặt nạ đi lại như cửa giả định, `/graph` gắn cờ
  `cua_gia_dinh`, hình `do_thi_di_lai.png` vẽ nét đỏ riêng. Cửa giả định 7 → 12.
- Lưới đi lại 512 góc / 23.009 cạnh. Tuyến qua cạnh mới dài bằng đường thẳng
  (RP26→RP19 5,37 m; RP06→RP02 4,51 m).
- Chỉ đường: sai so với mốc 0,03 m; A* mở 26,0 nút, Dijkstra 290,3; đầu–cuối 0,52 m.

## Luật nối RP01, RP03, RP18-RP20 và cạnh 20-26, 21-27 — 15/09/2026

- `CHI_NOI`: RP01 chỉ nối RP45, RP02; RP03 chỉ nối RP44, RP02 — áp cho cạnh nhìn thấy,
  lưới đi lại (không nối góc nào) và điểm xuất phát (không đi thẳng vào hai điểm này).
- `CAM_NOI` bỏ RP18-RP20; `CUA_NHOM_CHI_DINH` thêm RP20-RP26, RP21-RP27.
- Cửa giả định cố định: `CUA_CU` giữ 6 cửa tự động cũ để luật mới không làm vòng nối
  chọn lại khác (thử thì sinh cửa lạ RP04-RP43 xuyên tường). Tổng 13 cửa.
- Cửa đổi từ khoét lối 3 px trên mặt nạ sang cạnh nối đúng hai điểm: khoét lối thì
  RP18 đi tắt vào giữa lối 20-26, tới RP20 chỉ 3,67 m; nay phải qua RP26, 7,21 m.
- Lưới 286 góc / 9.460 cạnh. Sai so với mốc: 0,03 m trên 3.492 cặp không chịu luật;
  908 cặp qua RP01/RP03 lệch TB 1,07 m có chủ ý. A* 28,9 nút, Dijkstra 165,7.

## WC không nối điểm nào, bỏ cạnh quanh RP44/RP45 — 15/09/2026

- `KHONG_NOI` = RP42, RP43: không cạnh tới điểm tham chiếu nào, vẫn là đích (tới qua
  góc lối đi); không tuyến nào đi xuyên qua WC.
- `CAM_NOI` thêm 45-12, 45-13, 45-20, 44-14, 44-15, 44-21 (yêu cầu ghi "45-10": cạnh
  45-10 không tồn tại, đường kẻ sát RP10 là 45-13, đối xứng với 44-14).
  `CUA_NHOM_CHI_DINH` thêm 05-45, 06-44 (bị tường chặn nên thành cửa). Tổng 15 cửa.
- Điểm xuất phát theo luật của RP gần nhất (`cam_noi`, `khong_noi` trong JSON): đứng ở
  RP20 không đi thẳng vào nút RP45. Nhưng hai điểm nhìn thấy nhau trên sơ đồ nên tuyến
  qua một góc sát bên vẫn gần thẳng (10,70 m so với 10,67 m).
- 59 kiểm thử backend đạt.

## Đánh giá lại các mốc vừa đổi với dữ liệu hiện có — 15/09/2026

- Vân tay WiFi KHÔNG phân biệt được tường: cặp cách ≤ 8 m bị tường chặn lệch RSSI TB
  7,4 dB, nhìn thấy nhau 7,3 dB (p = 0,39; cùng ngày đo p = 0,99). Nên dữ liệu không
  xác nhận hay bác bỏ được cạnh nào; 05-45, 06-44, mọi cạnh của RP42–45 còn không có
  lần quét. Cạnh là quyết định của nhóm, cần đối chiếu thực địa.
- Toạ độ RP01 (−41, 0), RP03 (41, 0) hợp vân tay hơn ±16 một chút (Spearman +0,04, thắng
  76–79% lượt bootstrap) nhưng KTC95 chứa 0; RP09 hoà. Không đủ để kết luận.
- Sửa lỗi phát hiện khi đánh giá: áp `khong_noi` cho điểm xuất phát làm người đứng cạnh
  WC tới Căn tin cách 0,97 m bị vòng 4,31 m. Bỏ; WC vẫn không có cạnh.
- Chỉ đường: 3.492 cặp không chịu luật RP01/RP03 sai TB 0,03 m, lớn nhất 0,30 m; 908 cặp
  chịu luật lệch TB 1,01 m có chủ ý. Đầu–cuối 0,79 m (trung vị 0,03). A* 27,4 nút,
  Dijkstra 165,8. Đồ thị RP cũ không còn tới được WC.

## Đối chiếu kỹ các mốc vừa đổi với vân tay — 15/09/2026

- (A) Hồi quy lệch RSSI theo log khoảng cách + cùng ngày + "sơ đồ chặn", 321 cặp ≤ 12 m,
  hoán vị trong dải 2 m: độ đo MAE cho hệ số tường −0,8 dB (cặp bị chặn lại GIỐNG nhau
  hơn, p 0,001), độ đo tương quan 0,00 (p 0,93). (B) Tỉ lệ nhầm lẫn giữ-trọn-một-điểm, so
  trong cùng dải 1,5 m và cùng tình trạng ngày: cặp nhìn thấy nhau không nhầm nhiều hơn cặp
  bị chặn (p 0,84). Kết luận: tường trên `Map.png` không để lại dấu vết đo được trong vân
  tay, nên dữ liệu không xác nhận hay bác bỏ được cạnh nào (thêm hay xoá). RP42–RP45 không
  có lần quét.
- (C) Mô hình suy hao log-khoảng cách mỗi AP, khớp trên 37 điểm; hiệu chuẩn giữ-một-điểm
  sai trung vị 4,3 m. RP01: ước lượng (−37, 16), gần (−41, 0) hơn (5,8 so với 9,3 m), thắng
  100% bootstrap theo radio; nhầm nhiều nhất với RP16, RP08, RP04 (đều phía tây) — hai
  cách cùng ủng hộ (−41, 0). RP03: ước lượng (29, 10), cách hai phương án 5,5 và 5,8 m — không
  phân định. RP09: ước lượng (24, 18), gần (30, 14) hơn (2,5 so với 6,2 m), (30, 14) thắng 99%;
  nhầm nhiều nhất với RP15 (26, 22), RP14 — hai cách cùng nghiêng về toạ độ Bảng 4, trái
  với (38, 7) đang dùng. Hai phương án RP09 chỉ cách 3,7 m, dưới độ phân giải 4,3 m của
  phương pháp, nên là dấu hiệu chứ chưa phải bằng chứng. Chưa sửa dữ liệu.

## Chọn toạ độ RP01, RP03, RP09 theo kết quả chạy lại dữ liệu mẫu — 15/09/2026

- `D:\Nam5\DATN\combined_data.csv` trùng từng byte `data/raw/combined_data.csv`, không có
  cột toạ độ. Chạy 8 tổ hợp (bản vẽ / Bảng 4 cho từng điểm) trên bản sao: pipeline, 10 seed
  và bỏ trọn một điểm, cùng tham số, cùng các lần chia; 5 mô hình.
- RP09: (30, 14) tốt hơn (38, 7) ở cả 4 cặp so sánh, cả 10 seed (−0,09) lẫn bỏ-một-điểm
  (−0,3), kể cả sau khi chia cho sai số đoán tâm. RP01: (−41, 0) tốt hơn (−16, 0) ở bỏ-một-
  điểm (+0,1…+0,2 nếu dùng −16) dù −16 nằm giữa nhà. RP03: (16, 0) cho số thô thấp hơn nhưng
  chia cho sai số đoán tâm thì hơn kém nhau đổi chiều — phần lợi là do điểm dời vào giữa.
- Tổ hợp số thô tốt nhất: RP01 (−41, 0), RP03 (16, 0), RP09 (30, 14) — TB 5 mô hình 10 seed
  4,49, bỏ-một-điểm 15,33 (đang dùng: 4,67 và 15,72). Nhóm chốt GIỮ NGUYÊN RP01 (−41, 0),
  RP03 (41, 0), RP09 (38, 7) theo bản vẽ; không áp dụng.

## Chạy lại giai đoạn 1, 2, báo cáo, bản đồ — 15/09/2026

- Pipeline, huấn luyện, báo cáo, 10 seed, bỏ trọn một điểm, bản đồ, `khu_vuc_thu_vien.dart`,
  đánh giá chỉ đường, hình: số liệu trùng khít lần trước (dữ liệu và toạ độ không đổi):
  test seed 42 kNN 3,44 · kNN vân tay 3,45 · WKNN 3,51 · RF 6,92 · XGBoost 7,02; 10 seed kNN
  vân tay 2,58 ± 0,36; bỏ trọn một điểm XGBoost 14,80; chỉ đường đầu–cuối 0,79 m. 59 test đạt.
- Sửa nhãn đơn vị trong `tools/ve_ban_ve.py` (lỗi còn từ khi toạ độ đổi sang đơn vị lưới):
  trục ghi "đơn vị lưới"; kích thước bao 86 × 52 → 30,2 × 18,2 m; tỉ lệ "px/m" → px/đơn vị
  lưới; diện tích hai mảng sàn 149 và 338 m²; số trên chặng tuyến mẫu đổi sang mét (cộng
  đúng 31,0 m); thước "10 m" trước dài 10 đơn vị (3,5 m), nay dài đúng 10 m, đặt góc phải dưới.

## Chạy giai đoạn 3, 4 — 15/09/2026

- Máy chủ thật (cổng 8123, CSDL tạm, WebSocket tắt). Hợp đồng giai đoạn 1 → 3: 121/121 lần
  quét test qua `POST /predict` trùng dự đoán ngoại tuyến (lệch 0), sai TB 3,450 như bảng
  huấn luyện, suy luận trung vị 1,1 ms.
- 31/31 kiểm tra endpoint đạt: `/map` 44 điểm, `/graph` 238 cạnh / 15 cửa, luật nối qua API
  (RP01 = {02, 45}, RP03 = {02, 44}, WC không cạnh, 18→20 qua 26, 43→01 qua 45), `/route`
  528 cặp × A*/Dijkstra khớp, các ca lỗi 404/422, `/predictions`, tệp tĩnh. `/ws/location`
  403. Log không traceback, không 5xx.
- Dashboard: `api.js` và vòng hỏi REST thật chạy bằng Node đạt; chụp bằng Edge headless hiện
  sơ đồ 30,17 × 18,24 m, 238 cạnh, 15 cửa nét đứt, huy hiệu "REST · 2 s".

## Chạm một điểm trên sơ đồ thì dẫn tới đúng điểm đó — 15/09/2026

- Lỗi nhóm phát hiện khi tự test trên máy: chạm "Cửa ra vào" tại RP02 rồi "Đi tới đây"
  thì app dẫn tới RP34, vì chạm chỉ nhận ra KHU VỰC và máy chủ chọn điểm gần nhất của cả
  khu vực theo đường đi.
- Sửa: sơ đồ nhận điểm tham chiếu gần chỗ chạm nhất; tấm tóm tắt gửi `den_rp`; tính lại
  tuyến khi di chuyển và báo "Đã tới" theo đúng điểm đó. Chỉ đường từ Trang chủ/Tìm kiếm
  vẫn tới điểm gần nhất của khu vực.
- Kiểm trên máy thật từ RP20: chip 13,7 m tới RP02 (máy chủ 13,74 m, qua RP05), tuyến kết
  thúc ở RP02; tới RP02 báo "Đã tới Cửa ra vào"; sang RP34 (cùng khu vực) không báo tới
  mà tính lại 20,6 m về RP02 (máy chủ 20,64 m). `flutter analyze` sạch, 19 test đạt.

## "Đi tới đây" ở màn Chi tiết chuyển thẳng sang Bản đồ — 15/09/2026

- Trước: nhấn "Đi tới đây" bật tấm chỉ dẫn từng bước đè lên màn Chi tiết. Nay tìm tuyến xong
  thì đóng màn Chi tiết (`popUntil` về khung chính) và chuyển tab Bản đồ qua
  `AppShell.moBanDo()`; tuyến và chip quãng đường tự hiện. Gỡ `_hienChiDan`, `_cauHuong`.
  Các chuỗi `routeStep`, `routeSummary`, `step*` trong ARB không còn dùng.
- Kiểm trên máy thật từ RP20: Trang chủ → Phòng tạp chí → "Đi tới đây" → tab Bản đồ, chip
  "17,2 m tới Phòng tạp chí" (máy chủ 17,24 m), không có tấm bật lên. Analyze sạch, 19 test đạt.

## Đo tốc độ phản hồi app trên máy thật — 15/09/2026

- Gắn bộ ghi thời gian khung hình (tệp tạm, đã xoá), chạy cùng kịch bản: đổi tab, mở/đóng
  chi tiết, chạm sơ đồ, "Đi tới đây", tìm kiếm.
- Bản debug: build trung vị 9–14 ms, gần như mọi khung > 16,7 ms. Profile/release: build
  1–4 ms, nhưng raster (GPU) vẫn 11–17 ms. Máy đang bật Tiết kiệm pin (`low_power=1`,
  khoá 60 Hz, hạ CPU/GPU) — raster không đổi dù thử bỏ lớp làm mờ nền và hạ kính
  premium → standard, nên hai thay đổi đó đã gỡ lại.
- Khi đứng yên app không vẽ thừa (Trang chủ, Bản đồ, Cài đặt, Chi tiết ~0 khung/s), trừ ô
  tìm kiếm đang focus: `CupertinoTextField` của thư viện kính cho con trỏ mờ dần, vẽ 61
  khung/s. Sửa: mở kết quả tìm kiếm thì bỏ focus trước — Chi tiết mở từ tìm kiếm 60 → 0
  khung/s, bàn phím tự đóng.
- Cài bản release lên máy. Không tìm thấy trễ ở xử lý chạm (không có onDoubleTap).

## Giảm dung lượng app — 15/09/2026

- Trên máy 127 MB = APK 58,7 + dữ liệu 67,5 + cache 0,6. APK release gộp 3 kiến trúc 57,7 MB.
- Chỉ arm64: 23,1 MB (engine 11,75 · Dart 6,10 · ảnh 4,17 · dex 0,39). Thêm `--obfuscate
  --split-debug-info`: Dart 6,10 → 5,05 MB. 39 ảnh JPEG → WebP chất lượng 80, cùng kích
  thước, không metadata: 4,06 → 2,58 MB (PSNR 40,6 dB). APK còn 19,6 MB, trên máy 20,6 MB.
- Lệnh build ghi ở `mobile/README.md`. Dữ liệu 67,5 MB nghi là phần giải nén của các bản
  debug/profile cài đè trước đó; cài đè bản release không xoá, cần gỡ app hoặc xoá dữ liệu.
- Gỡ và cài lại bản release tối ưu (theo yêu cầu nhóm) để xoá 67,5 MB dữ liệu thừa; cấp lại
  quyền vị trí/WiFi bằng `pm grant`, địa chỉ máy chủ vẫn `http://127.0.0.1:8000`. Định vị
  chạy lại bình thường (Cầu thang, khớp 36 AP).

## Kiểm tra clone về chạy được — 15/09/2026

- Dựng đúng thứ GitHub sẽ trả về: chỉ mục git tạm + `git add -A` + `git archive` (238 tệp,
  12 MB), môi trường Python 3.14 mới cài từ `requirements.txt`.
- Sửa trước khi thử: `.gitignore` bỏ qua mọi `artifacts/*.pkl` nên clone về backend không
  chạy → mở ngoại lệ cho `scaler.pkl`, `model_fingerprint_knn.pkl` (~205 KB).
  `.gitattributes` thêm `*.webp binary`, `*.bat`/`*.cmd` giữ CRLF. `mobile/README.md` bỏ
  đường dẫn tuyệt đối. AGENTS.md, .agents/ chặn bằng `.git/info/exclude` (cục bộ).
- Trên bản sao: cài đặt đạt; 59 test đạt khi chưa chạy pipeline; backend chạy ngay
  (`/predict` một lần quét RP20 ra đúng (−22, 34)); Dashboard, `/docs` 200; Flutter
  pub get, analyze sạch, 19 test đạt, build APK release 19,5 MB. Pipeline + huấn luyện đầy
  đủ trên bản sao cho bảng so sánh trùng máy này (lệch ≤ 2·10⁻¹⁵), `scaler.pkl` trùng từng byte.
- Build APK hỏng khi bản sao nằm ở đường dẫn quá dài (biên dịch shader vượt 260 ký tự
  của Windows); đường dẫn ngắn build được. Đã ghi lưu ý và yêu cầu phiên bản vào README.
- Sửa tài liệu cấu trúc: artifacts commit 2 tệp, thêm `data/raw/nhom15_2026/`,
  `diem_can_do.csv`, 39 ảnh WebP; README `/graph` 15 cửa.
