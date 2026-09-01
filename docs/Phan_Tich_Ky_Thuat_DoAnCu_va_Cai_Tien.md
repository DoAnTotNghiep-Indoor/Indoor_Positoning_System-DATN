# Phân tích kỹ thuật đồ án cũ (CTK45) và giải pháp cải tiến cho đồ án mới (Nhóm 15)

Tài liệu này phân tích chi tiết cách triển khai Frontend / Backend / Database / API / công nghệ của đồ án cũ `DATN_CTK45_IPS.pdf` — dựa trên **mã nguồn thật** đọc được từ các hình chụp màn hình trong báo cáo (Hình 12–16), không chỉ dựa trên phần mô tả bằng chữ — rồi đề xuất giải pháp cải tiến cụ thể cho đồ án kế thừa.

---

## PHẦN 1 — ĐỒ ÁN CŨ ĐÃ LÀM NHƯ THẾ NÀO

### 1.1. Công nghệ sử dụng

| Tầng | Công nghệ | Ghi chú từ báo cáo |
|---|---|---|
| Frontend | Dart + Flutter (mobile app) | Báo cáo tự nhận nhược điểm: "Flutter... việc xây dựng ứng dụng trên web vẫn chưa được tối ưu" |
| Backend | Python + FastAPI + Uvicorn | RESTful API, JSON |
| Model serving | TensorFlow Lite (`tf.lite.Interpreter`) | Model CNN phân lớp, file `.tflite` |
| Database | MongoDB Atlas (NoSQL, cloud) | Driver bất đồng bộ `motor` |
| Huấn luyện | Google Colab | GPU/TPU miễn phí |
| Định dạng bản đồ | **GeoJSON** lưu trong MongoDB | POI, Doors, Hallways, Paths, Room, Stair |
| Dẫn đường | Dijkstra / A* | |

### 1.2. Cấu trúc thư mục

**Frontend (Flutter):** `android/`, `assets/`, `lib/{controller, models, ultils, services}` — điều hướng bằng `BottomNavBar`.

**Backend:**
```
BACKEND/
  __pycache__/
  model/
    model.tflite
    model2.tflite
  node_modules/        <-- bất thường trong dự án Python
  venv/                <-- không nên commit
  .env                 <-- có tồn tại nhưng KHÔNG được dùng
  backend.zip          <-- file nén commit chung mã nguồn
  convertcsv_to_json_value.py
  example.json
  main.py              <-- toàn bộ logic nằm ở đây
  package-lock.json
  package.json
  requirements.txt     <-- fastapi, uvicorn[standard], tensorflow, numpy, motor
```

### 1.3. Danh sách API (Hình 16)

| Method | Endpoint |
|---|---|
| POST | `/predict` |
| GET | `/geojson/POI` |
| GET | `/geojson/Doors` |
| GET | `/geojson/Hallways` |
| GET | `/geojson/Paths` |
| GET | `/geojson/Room` |
| GET | `/geojson/Stair` |

### 1.4. Luồng xử lý thực tế trong `main.py` (đọc từ Hình 14, 15)

```python
app = FastAPI()
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])

MONGO_URI = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority&appName=POI"
client = AsyncIOMotorClient(MONGO_URI)
db = client["Map"]

interpreter = tf.lite.Interpreter(model_path="model/model2.tflite")
interpreter.allocate_tensors()
input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()
expected_shape = input_details[0]['shape']

class RSSIInput(BaseModel):
    rssi: list[float]

def preprocess_rssi(rssi_values):
    if len(rssi_values) != expected_shape[1]:
        raise ValueError(f"Model expects {expected_shape[1]} features, but got {len(rssi_values)}")
    input_data = np.array(rssi_values, dtype=np.float32)
    input_data = (input_data + 100) / 100
    input_data = input_data.reshape(1, len(rssi_values), 1)
    return input_data

@app.post("/predict")
async def predict_rssi(data: RSSIInput):
    input_data = preprocess_rssi(data.rssi)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    predicted_class = int(np.argmax(output_data[0]))
    poi = await db["POI"].find_one({"properties.RP": str(predicted_class + 1)})
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí tương ứng trong POI")
    return {
        "prediction": predicted_class,
        "name": poi.get("properties", {}).get("Name", "Unknown"),
        "coordinates": poi.get("geometry", {}).get("coordinates", [0, 0]),
        "rp": predicted_class
    }
```

### 1.5. Hạn chế đồ án cũ tự thừa nhận (phần Kết luận)

- Bản đồ load chậm.
- Một số điểm định vị sai do dao động RSS, đặc biệt các vị trí trung tâm thư viện: **RP20, RP11**.
- Mong muốn phát triển thêm: trang admin, đăng nhập admin, bản đồ 3D để tăng tốc load, theo dõi vị trí khi di chuyển.

---

## PHẦN 2 — CÁC VẤN ĐỀ PHÁT HIỆN ĐƯỢC

Xếp theo mức độ nghiêm trọng.

### 🔴 Mức NGHIÊM TRỌNG

**V1. Lộ thông tin đăng nhập database trong mã nguồn**

`MONGO_URI` chứa **user và mật khẩu hardcode ngay trong `main.py`**, và chuỗi này đã bị in vào báo cáo tốt nghiệp — tức là đã công khai. Nghiêm trọng hơn: thư mục backend **đã có sẵn file `.env`** nhưng không được sử dụng.

Hậu quả: bất kỳ ai đọc báo cáo đều có toàn quyền đọc/ghi/xóa database. Mật khẩu cũng quá yếu (dạng `<tên trường>123`).

> *Chuỗi kết nối gốc đã được che trong tài liệu này. Thông tin đầy đủ báo riêng cho GVHD để đổi mật khẩu nếu database còn hoạt động.*

**V2. Không có ánh xạ BSSID → cột đặc trưng (nguy cơ sai lệch âm thầm)**

Đây là lỗi kiến trúc nguy hiểm nhất về mặt học máy:

```python
class RSSIInput(BaseModel):
    rssi: list[float]      # chỉ là mảng số, KHÔNG kèm BSSID
```

Backend chỉ kiểm tra **số lượng** phần tử (`len(rssi_values) != expected_shape[1]`), **không kiểm tra thứ tự AP**. Nghĩa là:
- Nếu client gửi đúng số lượng nhưng **sai thứ tự AP** → model vẫn chạy bình thường, trả về kết quả **sai hoàn toàn mà không có cảnh báo nào**.
- Nếu một AP bị tắt/thay thế trong thực tế → toàn bộ thứ tự cột lệch → hệ thống hỏng ngầm.

Đây rất có thể là **nguyên nhân thật sự** của hạn chế "một số điểm định vị sai" mà nhóm cũ ghi nhận, chứ không chỉ do dao động RSS.

### 🟠 Mức CAO

**V3. Tiền xử lý ở backend không đồng bộ với lúc huấn luyện**

```python
input_data = (input_data + 100) / 100
```

Công thức chuẩn hóa bị hardcode bằng "số ma thuật", **không phải** scaler đã fit trên tập train. Nếu quá trình huấn luyện dùng min-max thật (fit theo dữ liệu), thì phân phối dữ liệu lúc dự đoán khác lúc huấn luyện → giảm độ chính xác. Không có `scaler.pkl`, không có `feature_list.json`.

**V4. CORS cấu hình sai chuẩn bảo mật**

`allow_origins=["*"]` kết hợp `allow_credentials=True` là cấu hình vừa **không hợp lệ theo chuẩn CORS** (trình duyệt sẽ chặn), vừa là anti-pattern bảo mật.

**V5. Ràng buộc `predicted_class + 1` dễ vỡ**

```python
poi = await db["POI"].find_one({"properties.RP": str(predicted_class + 1)})
```

Ánh xạ chỉ số lớp → RP dựa vào giả định "nhãn lớp bắt đầu từ 0, RP bắt đầu từ 1", lưu dưới dạng **chuỗi**. Nếu thứ tự nhãn khi huấn luyện thay đổi, hoặc RP bị đánh số lại (đúng tình huống của Nhóm 15: có RP41, thiếu RP26) → ánh xạ sai toàn bộ.

**V6. Không có REALTIME thật sự**

Chỉ có REST `POST /predict`. Client muốn cập nhật vị trí liên tục phải **polling** — tốn pin, tốn băng thông, độ trễ cao. Không có WebSocket.

**V7. Không có làm mượt vị trí**

Mỗi lần dự đoán là độc lập → marker nhảy loạn khi RSSI dao động. Không có EMA, không giới hạn bước nhảy.

### 🟡 Mức TRUNG BÌNH

**V8. Không quản lý phiên bản model** — `model.tflite` và `model2.tflite` không rõ khác nhau gì, không biết model nào train từ dataset nào, không có metadata.

**V9. Không lưu log dự đoán** — không thể debug "tại sao lúc đó định vị sai", không có dữ liệu để cải tiến model sau triển khai.

**V10. Toàn bộ logic dồn vào `main.py`** — không tách service, khó test, khó bảo trì.

**V11. Vệ sinh dự án kém** — commit cả `venv/`, `node_modules/`, `__pycache__/`, `backend.zip` vào mã nguồn.

**V12. Bài toán phân lớp làm sai số bị lượng tử hóa** — model chỉ trả về được đúng tọa độ của 40 điểm RP cố định. Sai số tối thiểu luôn bị chặn dưới bởi khoảng cách lưới (~7m), dù model có tốt đến đâu.

---

## PHẦN 2b — RÀ MÃ NGUỒN GITHUB (bổ sung 01/09/2026)

Phần 2 ở trên viết từ báo cáo và ảnh chụp mã. Đợt này rà thẳng kho
`github.com/NgocSongNe/IPS` — 9 nhánh — nên có thêm những chỗ chỉ được đúng
dòng, và một chỗ **đính chính lại kết luận cũ của chính nhóm**.

### 2b.1. Bản đồ GeoJSON sai hình học — V13

Bản đồ Mapbox của CTK45 dựng từ `assets/geojson/`. Khớp 40 điểm trong
`POI.geojson` của họ với 40 toạ độ nhóm đã đo:

| Phép đo | Kết quả |
|---|---|
| Hộp bao 40 điểm POI, quy ra mét thật | **30,5 × 34,4 m** |
| Hộp bao thật của khu khảo sát | **86 × 52 m** |
| Khớp Procrustes (quay + co giãn đều + tịnh tiến) | RMS **5,99 m** |
| Khớp affine đầy đủ (hai trục co khác nhau) | RMS **5,08 m**, lệch lớn nhất **28,55 m** |
| 780 cặp điểm: khoảng cách GeoJSON / khoảng cách thật | trung vị **0,40×**, trải 0,06× đến 1,12× |
| 143 cặp dưới 20 m (cỡ một tuyến chỉ đường) | sai số tuyệt đối trung bình **7,5 m** |

Affine đầy đủ vẫn còn 5 m nghĩa là biến dạng **không tuyến tính** — toạ độ đặt
bằng tay chứ không theo phép chiếu nào. Hệ quả: thẻ "Tổng khoảng cách: 18.43
mét" ở Hình 23 của báo cáo là con số tính trên hình học sai. Ba cặp điểm có
khoảng cách thật 16 m, 12,8 m và 18 m thì GeoJSON cho ra 14,1 m, 7,3 m và 9,3 m.

**Đây là căn cứ để KHÔNG kế thừa `Room.geojson`, `Hallways.geojson`,
`Stair.geojson`.** Sáu đa giác phòng, năm hành lang và tám khối cầu thang đều có
sẵn và tải về được, nhưng đặt vào hệ mét của nhóm thì lệch chỗ 5 m — vẽ lên còn
tệ hơn không vẽ. Nhóm tự trích hình học từ `Map.png`, xem `tools/trich_ban_do.py`.

### 2b.2. `walls` nạp từ `Paths.geojson` — V14

`POISelectionScreen.dart:417` — `_loadWallsFromAPI()` gọi `/geojson/Paths` rồi
**gán thẳng** vào biến `walls`. `Paths` là hành lang đi được, không phải tường.
Vậy `_isPathBlocked()` chặn đúng những cạnh chạy dọc hành lang và cho qua những
cạnh xuyên tường gạch — ngược hoàn toàn với ý định.

`loadGeoJson()` cũng `walls.add()` từ `Wall.geojson` thật, nhưng cả hai hàm gọi
trong **constructor** và không `await`, nên cái nào về sau ghi đè cái kia.
`_loadWallsFromAPI` dùng phép gán nên nếu nó về sau thì dữ liệu tường thật bị xoá
sạch. Hành vi phụ thuộc độ trễ mạng, không tái lập được.

### 2b.3. Cạnh POI đến waypoint là mã chết — V15

`POISelectionScreen.dart:585` trong `_generateGraph()`: lấy ba waypoint gần nhất
rồi lặp qua chúng chỉ để gán một biến cục bộ `distance` và bỏ đi — không thêm
cạnh nào vào đồ thị. Cạnh chỉ được thêm trong nhánh dự phòng
`if (closestWaypoints.isEmpty)`.

Điểm nào nhìn thấy được ít nhất một waypoint thì **cô lập hoàn toàn** trong đồ
thị. Chỉ điểm không thấy waypoint nào mới được nối trực tiếp với điểm khác.

### 2b.4. Làm mượt tuyến không kiểm tường — V16

`_smoothRoute()` nội suy Catmull-Rom 10 đoạn mỗi chặng mà không xét vật cản, nên
đường cong mượt có thể cắt qua tường dù chặng gốc thì không. Đây là lý do tuyến
trong Hình 23 uốn cong qua giữa nhà.

Đi kèm: mỗi chấm trên tuyến là một `Marker` widget riêng, cộng 40 marker điểm và
40 thẻ nhãn — đủ giải thích câu "load bản đồ hiển thị vẫn còn chậm" mà phần Kết
luận của báo cáo tự thừa nhận.

### 2b.5. Giá trị điền thiếu lệch giữa huấn luyện và suy luận — V17

Báo cáo trang 42 ghi rõ **"giá trị RSS = −98 được đặt mặc định với các AP không
phát hiện được"**. Nhưng `wifi_service.dart:59` điền `macToRssi[mac] ?? -100`.
Huấn luyện −98, chạy thật −100 — lệch hệ thống trên mọi AP vắng mặt, mà không có
gì báo. Đây chính là lý do giá trị điền thiếu của nhóm nằm trong
`artifacts/feature_list.json` và backend đọc lại từ đó, không viết cứng hai nơi.

### 2b.6. Quyền truy cập đòi cả `locationAlways` — V18

`wifi_scanner.dart:9` nối ba quyền bằng `&&`, trong đó `locationAlways` là quyền
nền mà từ Android 11 không cấp được qua hộp thoại thường — phải vào Cài đặt hệ
thống. Thiếu một quyền là trả `false` và `scanWiFi()` trả danh sách rỗng trong im
lặng. Nhóm đặt ngưỡng ngược lại: cấp MỘT trong hai quyền vị trí hoặc
`NEARBY_WIFI_DEVICES` là đủ.

Kèm theo: `startWifiTracking` tạo `Timer.periodic` mà không giữ tham chiếu, còn
`stopWifiTracking` lại nhận timer từ nơi khác — timer ấy không bao giờ huỷ được.

### 2b.7. Đính chính — `getDirection` của CTK45 KHÔNG lộn trái/phải

Đợt rà trước kết luận hàm `getDirection` của họ hoán vị hai trục nên mọi câu
trái/phải bị đảo. **Kết luận đó sai.** Kiểm trên cả 7 nhánh có hàm này, cả bảy
đều gán `v1x` theo kinh độ và `v1y` theo vĩ độ — đúng quy ước đông/bắc, tích có
hướng dương là rẽ trái, **dấu của họ đúng**. Chỗ hoán vị trục nằm trong hàm
`orientation()` của phép kiểm cắt đoạn thẳng, mà ở đó hoán vị nhất quán chỉ là
phép soi gương nên vô hại.

Hàm ấy vẫn có hai hạn chế thật, và đó mới là chỗ nhóm cải tiến:

- Chỉ ba kết quả thẳng/trái/phải, nên một cú quay đầu 179 độ đọc thành "rẽ trái".
- Tính góc bằng `acos(dot / (mag1 * mag2))`: gặp hai điểm trùng nhau thì mẫu số
  bằng 0, `angle` thành NaN, mọi phép so đều sai và hàm rơi xuống nhánh cuối trả
  **"Rẽ phải" cho một chặng không hề rẽ**.

Hàm của nhóm trả về **góc** thay vì một nhãn, phân loại là việc của tầng trên —
nên thêm được mức "quay đầu", mức "chếch", và điểm trùng chỉ cho ra góc 0. Ngưỡng
đi thẳng cũng nới từ 10 độ lên 20 độ: dưới 20 độ người đi bộ không nhận ra là một
cú rẽ.

### 2b.8. Vụn

- `CategoryModel` có 8 loại, trong đó `Khu vực tự học` **thừa một dấu cách** ở
  cuối chuỗi. Bộ lọc so khớp theo nhãn hiển thị nên lệch một dấu cách là hỏng;
  nhóm dùng mã nhóm bất biến (`AreaCategory`) nên không dính.
- `WifiPredictor.dart` kiểm `if (_interpreter == null)` trên một trường `late`
  không nullable — nhánh chết, và truy cập trước khi gán thì ném
  `LateInitializationError` chứ không vào được nhánh đó.
- `heuristic()` dùng `firstWhere` không có `orElse`, thiếu điểm là ném lỗi giữa
  lúc đang tìm đường.

---

## PHẦN 3 — GIẢI PHÁP CẢI TIẾN CHO ĐỒ ÁN MỚI

### 3.1. Bảng đối chiếu tổng hợp

| # | Vấn đề cũ | Giải pháp mới | Ưu tiên |
|---|---|---|---|
| V1 | Mật khẩu DB hardcode | Biến môi trường + `.env` (đã bị `.gitignore`), mật khẩu mạnh | 🔴 Ngay |
| V2 | Mảng RSSI không kèm BSSID | Gửi `[{bssid, rssi}]`, server map theo `feature_list.json` | 🔴 Ngay |
| V3 | Chuẩn hóa hardcode | Load `scaler.pkl` + `missing_value` từ lúc train | 🔴 Ngay |
| V4 | CORS `*` + credentials | Allowlist origin cụ thể | 🟠 |
| V5 | `predicted_class + 1` | Hồi quy trực tiếp (x, y), không cần ánh xạ | 🟠 |
| V6 | Chỉ REST polling | WebSocket `/ws/location` push | 🟠 |
| V7 | Marker nhảy | EMA smoothing (α=0.3) + giới hạn bước nhảy | 🟠 |
| V8 | Model không version | Bảng `ml_models` + `is_active` | 🟡 |
| V9 | Không log | Bảng `position_predictions` | 🟡 |
| V10 | Dồn vào `main.py` | Tách `services/` theo trách nhiệm | 🟡 |
| V11 | Commit rác | `.gitignore` chuẩn Python | 🟡 |
| V12 | Sai số lượng tử hóa | Hồi quy tọa độ liên tục | ✅ Đã có trong đề cương |
| V13 | Bản đồ GeoJSON lệch hình học, khoảng cách chỉ bằng 0,40× thật | Tự trích hình học từ `Map.png`, kiểm bằng lưới chấm 1000 px / 86 m | 🔴 Đã làm |
| V14 | `walls` nạp từ `Paths.geojson` — chặn ngược | Đọc mặt nạ tường từ ảnh, dùng vùng liên thông chứ không dùng ngưỡng | 🔴 Đã làm |
| V15 | Cạnh POI → waypoint là mã chết, đồ thị rời rạc | Đồ thị k=3 láng giềng, có `test_duong_di_khong_chui_qua_tuong` | 🔴 Đã làm |
| V16 | Làm mượt Catmull-Rom cắt qua tường | Không làm mượt; trả đúng dãy đỉnh của đồ thị đã lọc tường | 🟠 Đã làm |
| V17 | Điền thiếu −98 lúc train, −100 lúc chạy | `missing_rssi_value` nằm trong `feature_list.json`, một nguồn duy nhất | 🔴 Đã làm |
| V18 | Đòi cả `locationAlways` nên quét trả rỗng im lặng | Cấp MỘT trong hai quyền là đủ; phân biệt 5 lý do không quét được | 🟠 Đã làm |

**Tình trạng tới 01/09/2026.** V1–V12 là bảng đề xuất ban đầu, giữ nguyên làm dấu
vết; V13–V18 thêm sau đợt rà mã nguồn GitHub ở Phần 2b. Đã làm xong V1–V6, V9,
V10, V11 và cả V13–V18. V8 chưa làm — phần quản lý phiên bản mô hình nằm ngoài
phạm vi giai đoạn 3.

Riêng **V7 đã làm khác đề xuất**: thay EMA bằng đồng thuận không gian. Lý do là
các ca sai nặng gần như luôn là một lần quét dị thường lẻ loi, mà EMA kéo trung
bình nên vẫn bị điểm lạc lôi đi; đồng thuận không gian chọn dự đoán có tổng
khoảng cách tới các dự đoán còn lại nhỏ nhất nên tự loại được điểm lạc và luôn
trả về một điểm tham chiếu có thật. Đo trên tập test: 1,92 m xuống 0,38 m, số
điểm sai từ 13/39 xuống 1/39. Chi tiết ở mục 2.4.1 của
`Phan_Tich_Thiet_Ke_He_Thong.md`.

V12 cũng khác: bài toán vẫn là hồi quy toạ độ, nhưng mô hình tốt nhất
(`kNN vân tay Bray-Curtis`) thực chất phân lớp 39 điểm tham chiếu rồi trả về toạ
độ của điểm được chọn. Dữ liệu chỉ có 39 toạ độ khác nhau vì thu đúng tại các
điểm tham chiếu, nên cách này khớp bản chất dữ liệu hơn — 1,92 m so với 6,48 m
của XGBoost hồi quy liên tục.

### 3.2. Cải tiến then chốt #1 — Hợp đồng dữ liệu có BSSID (sửa V2 + V3)

Đây là cải tiến **quan trọng nhất**, vừa sửa lỗi kiến trúc cũ vừa là điểm mạnh để trình bày trong báo cáo.

**Cũ (dễ sai ngầm):**
```json
{ "rssi": [-57, -70, -98, -62, ...] }
```

**Mới (an toàn):**
```json
{
  "device_id": "PHONE_A",
  "scan": [
    {"bssid": "88:dc:97:12:62:cf", "rssi": -57},
    {"bssid": "8e:dc:97:12:65:63", "rssi": -70}
  ]
}
```

Backend tự ánh xạ theo đúng thứ tự đã học:

```python
# services/preprocessing_service.py
import json, joblib, numpy as np

class FeatureMapper:
    """Nguồn sự thật duy nhất cho việc ánh xạ BSSID -> vector đặc trưng.
    Mọi tham số đều đọc từ artifact sinh ra lúc huấn luyện, không hardcode."""

    def __init__(self, feature_list_path: str, scaler_path: str):
        with open(feature_list_path, encoding="utf-8") as f:
            meta = json.load(f)
        self.ap_columns   = meta["ap_columns"]          # thứ tự cột CHÍNH XÁC lúc train
        self.missing_value = meta["missing_rssi_value"] # hằng số động, không phải -98 cố định
        self.min_ap        = meta["min_ap_per_scan"]
        self.index = {bssid: i for i, bssid in enumerate(self.ap_columns)}
        self.scaler = joblib.load(scaler_path)          # scaler ĐÃ fit trên train

    def transform(self, scan: list[dict]) -> np.ndarray:
        vector = np.full(len(self.ap_columns), self.missing_value, dtype=np.float32)
        matched = 0
        for item in scan:
            idx = self.index.get(item["bssid"].lower())
            if idx is not None:                 # AP lạ -> bỏ qua, không làm lệch thứ tự
                vector[idx] = item["rssi"]
                matched += 1
        if matched < self.min_ap:
            raise ValueError(
                f"Chỉ nhận diện được {matched} AP đã biết, cần tối thiểu {self.min_ap}"
            )
        return self.scaler.transform(vector.reshape(1, -1))
```

Lợi ích: AP lạ không phá thứ tự cột; AP mất tín hiệu tự động gán `missing_value`; tiền xử lý lúc dự đoán **giống hệt** lúc huấn luyện.

### 3.3. Cải tiến then chốt #2 — Bảo mật cấu hình (sửa V1 + V4)

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str                 # đọc từ biến môi trường, KHÔNG hardcode
    allowed_origins: list[str] = ["http://localhost:5173"]
    api_key: str                      # bảo vệ endpoint ghi dữ liệu
    model_dir: str = "artifacts"

    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,   # KHÔNG dùng "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)
```

`.gitignore` bắt buộc có:
```
.env
venv/
__pycache__/
*.pyc
node_modules/
*.zip
data/raw/
```

### 3.4. Cải tiến then chốt #3 — Realtime + làm mượt (sửa V6 + V7)

```python
# services/smoothing_service.py
import time, math

class PositionSmoother:
    """EMA theo từng thiết bị + chống nhảy bất thường."""

    def __init__(self, alpha=0.3, max_jump_m=5.0, reset_after_s=30.0):
        self.alpha = alpha
        self.max_jump_m = max_jump_m
        self.reset_after_s = reset_after_s
        self.state = {}   # device_id -> (x, y, last_timestamp)

    def smooth(self, device_id: str, x: float, y: float):
        now = time.time()
        prev = self.state.get(device_id)

        if prev is None or (now - prev[2]) > self.reset_after_s:
            self.state[device_id] = (x, y, now)      # lần đầu / mất tín hiệu lâu -> dùng trực tiếp
            return x, y

        px, py, _ = prev
        jump = math.hypot(x - px, y - py)
        if jump > self.max_jump_m:                    # nhảy bất thường -> kéo về giới hạn
            ratio = self.max_jump_m / jump
            x, y = px + (x - px) * ratio, py + (y - py) * ratio

        sx = self.alpha * x + (1 - self.alpha) * px
        sy = self.alpha * y + (1 - self.alpha) * py
        self.state[device_id] = (sx, sy, now)
        return sx, sy
```

```python
# WebSocket thay cho polling
@app.websocket("/ws/location")
async def ws_location(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            vector = mapper.transform(payload["scan"])
            x, y = predictor.predict(vector)
            sx, sy = smoother.smooth(payload["device_id"], x, y)
            asyncio.create_task(log_prediction(...))   # ghi log bất đồng bộ, không chặn phản hồi
            await websocket.send_json({
                "x": round(x, 2), "y": round(y, 2),
                "x_smooth": round(sx, 2), "y_smooth": round(sy, 2),
                "model": predictor.model_code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        pass
```

### 3.5. Cải tiến then chốt #4 — Quản lý phiên bản model (sửa V8 + V9)

```python
# services/prediction_service.py
class Predictor:
    """Load model MỘT LẦN lúc khởi động (đúng như đồ án cũ đã làm tốt),
    nhưng bổ sung khả năng đổi model động mà không cần restart."""

    def __init__(self, model_x, model_y, model_code: str):
        self.model_x, self.model_y = model_x, model_y
        self.model_code = model_code

    @classmethod
    def load_active(cls, db) -> "Predictor":
        row = db.query("SELECT * FROM ml_models WHERE is_active = true LIMIT 1")
        return cls(joblib.load(f"{row.artifact_path}/model_x.pkl"),
                   joblib.load(f"{row.artifact_path}/model_y.pkl"),
                   row.model_code)

    def predict(self, vector):
        return float(self.model_x.predict(vector)[0]), float(self.model_y.predict(vector)[0])
```

Mỗi dự đoán ghi vào `position_predictions` (x_pred, y_pred, x_smooth, y_smooth, model_id, visible_ap_count) → phục vụ debug và đánh giá sau triển khai, điều đồ án cũ hoàn toàn không có.

### 3.6. Cải tiến then chốt #5 — Cấu trúc mã nguồn (sửa V10 + V11)

```
backend/
  main.py                    # chỉ khởi tạo app, đăng ký router
  config.py                  # Settings từ biến môi trường
  database.py
  schemas.py                 # Pydantic models
  routers/
    predict.py
    map.py
    models.py
  services/
    preprocessing_service.py # FeatureMapper
    prediction_service.py    # Predictor
    smoothing_service.py     # PositionSmoother
    websocket_service.py     # ConnectionManager
artifacts/
  feature_list.json
  scaler.pkl
  model_x.pkl
  model_y.pkl
  model_metadata.json
```

### 3.7. Cải tiến hiệu năng — sửa "bản đồ load chậm"

Nguyên nhân gốc ở đồ án cũ: mỗi lần mở bản đồ phải gọi **7 endpoint GeoJSON riêng lẻ** (`/geojson/POI`, `/Doors`, `/Hallways`, `/Paths`, `/Room`, `/Stair`), mỗi lần là một round-trip mạng đến MongoDB Atlas trên cloud.

Giải pháp:
1. **Gộp thành 1 endpoint** `GET /map/{floor_id}` trả về toàn bộ layer trong một response.
2. **Cache trong bộ nhớ** — dữ liệu bản đồ gần như không đổi:
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=8)
   def get_map_payload(floor_id: int) -> dict:
       ...  # truy vấn DB một lần, các lần sau lấy từ cache
   ```
3. **Bật gzip**: `app.add_middleware(GZipMiddleware, minimum_size=1000)` — GeoJSON là text, nén rất hiệu quả.
4. **Ảnh nền phục vụ tĩnh**, không nhét vào JSON.

### 3.8. Điểm NÊN KẾ THỪA từ đồ án cũ

Không phải mọi thứ đều cần thay — những điểm sau đồ án cũ làm đúng:

| Điểm tốt | Lý do giữ lại |
|---|---|
| Load model **một lần** lúc khởi động (biến toàn cục) | Đúng thực hành, tránh độ trễ mỗi request |
| Dùng **GeoJSON** mô tả bản đồ trong nhà | Chuẩn mở, tách layer rõ ràng (POI/Doors/Hallways/Paths/Room/Stair), dễ vẽ ở frontend. Nên giữ. Đã dựng khác: hình học tầng 1 trích thẳng từ `Map.png` ra `data/reference/ban_do_tang1.json`, đọc từ tệp chứ không qua CSDL |
| FastAPI + Uvicorn | Phù hợp, hỗ trợ sẵn WebSocket và async |
| `motor` (async driver) | Tư duy bất đồng bộ đúng. Đã dựng: SQLAlchemy async trên `aiosqlite` |
| Kiểm tra số lượng đặc trưng đầu vào | Ý tưởng đúng, chỉ cần nâng cấp thành kiểm tra theo BSSID |
| Google Colab để huấn luyện | Phù hợp với điều kiện sinh viên |

### 3.9. So sánh REST vs WebSocket (đưa vào báo cáo)

| Tiêu chí | Đồ án cũ (REST polling) | Đồ án mới (WebSocket) |
|---|---|---|
| Kết nối | Mở/đóng mỗi lần gửi | Một kết nối duy trì |
| Độ trễ | Cao (phụ thuộc chu kỳ polling) | Thấp (server push ngay) |
| Băng thông | Lặp header HTTP mỗi request | Chỉ payload |
| Tiêu thụ pin | Cao | Thấp hơn |
| Biết trạng thái mất kết nối | Không | Có (hiển thị "Disconnected") |

---

## PHẦN 4 — THỨ TỰ TRIỂN KHAI ĐỀ XUẤT

Ánh xạ vào mốc **16/10–31/10/2026 (Xây dựng Back-end)** trong đề cương:

| Ngày | Việc | Kết quả |
|---|---|---|
| 16–18/10 | Khung dự án + `config.py` + `.gitignore` + `.env` | Không còn credential trong mã nguồn |
| 19–21/10 | `FeatureMapper` + nạp `feature_list.json`, `scaler.pkl` | Ánh xạ BSSID an toàn, tiền xử lý đồng bộ với lúc train |
| 22–24/10 | `Predictor` + `POST /predict` | Trả đúng (x, y) từ vector RSSI |
| 25–27/10 | `PositionSmoother` + `WS /ws/location` | Realtime, marker ổn định |
| 28–29/10 | `GET /map` gộp layer + cache + gzip | Sửa lỗi "bản đồ load chậm" |
| 30–31/10 | Ghi `position_predictions` + `GET /predictions` | Có dữ liệu debug và đánh giá sau triển khai |

---

## PHẦN 5 — CÁCH TRÌNH BÀY TRONG BÁO CÁO

Khi bảo vệ, phần "cải tiến so với đồ án trước" nên nêu theo thứ tự sau (mạnh → nhẹ):

1. **Chuyển từ phân lớp RP sang hồi quy tọa độ** — gỡ bỏ giới hạn sai số bị lượng tử hóa theo lưới 7m của phương pháp cũ.
2. **Hợp đồng dữ liệu dựa trên BSSID thay cho mảng vị trí** — loại bỏ nguy cơ dự đoán sai âm thầm khi hạ tầng WiFi thay đổi; nhiều khả năng đây chính là nguyên nhân sai số tại RP20/RP11 mà đồ án cũ ghi nhận.
3. **Đồng bộ tiền xử lý giữa huấn luyện và triển khai** thông qua artifact (`feature_list.json`, `scaler.pkl`), thay cho công thức hardcode `(x+100)/100`.
4. **Realtime bằng WebSocket + làm mượt EMA** thay cho REST polling không có hậu xử lý.
5. **Quản lý phiên bản dataset/model và ghi log dự đoán** — cho phép tái lập thực nghiệm và cải tiến liên tục.
6. **Khắc phục các vấn đề kỹ thuật tồn đọng**: bảo mật cấu hình, CORS, hiệu năng tải bản đồ.

> Lưu ý khi viết báo cáo: nên trình bày theo hướng **"kế thừa và khắc phục hạn chế kỹ thuật"**, dẫn đúng phần Kết luận của đồ án cũ (bản đồ load chậm, sai số tại RP trung tâm) để chứng minh các cải tiến này giải quyết đúng vấn đề đã được ghi nhận, chứ không phải thay đổi công nghệ một cách tùy ý.
>
> Riêng vấn đề lộ thông tin đăng nhập database (mục V1), **không nên nêu trực tiếp trong báo cáo** vì liên quan đến nhóm tác giả trước. Nên báo riêng cho GVHD để đổi mật khẩu MongoDB Atlas nếu database đó vẫn đang hoạt động.
