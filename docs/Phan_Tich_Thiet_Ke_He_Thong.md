# Phân tích & Thiết kế Hệ thống — Đồ án "Nghiên cứu hệ thống định vị trong nhà và xây dựng ứng dụng" (Nhóm 15)

Bản phân tích & thiết kế hệ thống tổng hợp từ: đề cương của nhóm (`Nhom15_DeCuong_DATN_edited.docx`), kế hoạch phân tích chi tiết (`Kế Hoạch_phantichh_CB.docx`), đề cương/báo cáo đồ án cũ CTK45 mà nhóm kế thừa (`DATN_CTK45_IPS.pdf`), thiết kế Figma (`Design_Figma_SystemIndoor.docx`), và thiết kế CSDL PostgreSQL (`Thiết Kế Database PostgreSQL Cho Dự Án Indoor Positioning System.docx`). Viết theo cấu trúc Chương 2 trong đề cương của nhóm, để có thể chép trực tiếp vào báo cáo.

---

## 2.0. Vị trí đề tài trong dòng kế thừa

Đồ án cũ (CTK45, thư viện tầng 1 ĐH Đà Lạt) đã làm gì, và đồ án của Nhóm 15 kế thừa/khác ở đâu — đây là phần **"điểm mới"** giám khảo sẽ hỏi đầu tiên, nên cần nói rõ ràng, có số liệu đối chứng:

| Khía cạnh | Đồ án cũ (CTK45 – kế thừa) | Đồ án Nhóm 15 (đề xuất) |
|---|---|---|
| Bài toán ML | **Phân lớp** RSSI → RP_ID, sau đó tra tọa độ RP trong DB | **Hồi quy** RSSI → (x, y) trực tiếp — đánh giá được sai số mét liên tục, không bị lượng tử hóa theo lưới RP |
| Mô hình | KNN, WKNN, Random Forest, CNN (Conv1D 16-32-64 + Dense) phân lớp | KNN, WKNN (baseline) + **XGBoost Regression** (2 mô hình con cho x, y) là mô hình chính; Random Forest là phương án so sánh nếu còn thời gian |
| Kết quả đã có (để trích dẫn/so sánh) | Phòng thí nghiệm: RF 97.16%/6.02 m, KNN 89.5%/9 m, WKNN 88.7%/8 m, CNN 92%/5 m. Thực tế: RF 5–8 m, KNN 7–12 m, WKNN 6–11 m, CNN 0–8 m | Mục tiêu: sai số trung bình thấp hơn KNN/WKNN 10–20%, CDF90 giảm rõ rệt so với baseline |
| Dữ liệu | 40 RP, cách nhau ~7 m, 3200 mẫu (80 mẫu/RP × 4 hướng), 13 trường thô, rút gọn còn 37/8 đặc trưng AP, RSSI thiếu = -98 | Kế thừa đúng quy ước: RSSI thiếu = -98, ngưỡng tối thiểu 6 AP/mẫu, 30–80 mẫu/RP; bổ sung 3 cấu hình lựa chọn AP (toàn bộ / ≥20% xuất hiện / top 10–15) và quy tắc chống rò rỉ dữ liệu (fit scaler chỉ trên train) |
| Sản phẩm đầu ra | App di động Flutter, chỉ đường bằng giọng nói, AR/3D (một phần là mở rộng lý thuyết, chưa chắc đã cài đặt) | **Web Dashboard** (không phải mobile), hiển thị vị trí **realtime qua WebSocket** trên sơ đồ mặt bằng — *đã dựng cả app di động, xem bảng dưới* |
| Backend/CSDL | FastAPI (REST) + MongoDB Atlas | FastAPI + WebSocket + **PostgreSQL** — *đã chốt lại là SQLite, xem bảng dưới* |
| Hậu xử lý vị trí | Không đề cập | **EMA smoothing** (alpha = 0.3) để giảm dao động marker |
| Phạm vi | Toàn bộ tầng 1 thư viện, có định hướng mở sang AR/đa nền tảng | Giữ nguyên phạm vi 2D một tầng, **chủ động không** làm đa tầng/GPS/BLE/CNN để tập trung chất lượng mô hình |

**Cách viết "điểm mới" trong báo cáo** (đã đúng hướng theo file kế hoạch): nhấn mạnh **hồi quy tọa độ trực tiếp** thay vì phân lớp RP, **XGBoost** khai thác tốt dữ liệu bảng RSSI, đánh giá bằng **sai số mét chuẩn hóa (CDF)** thay vì accuracy phân lớp, và triển khai **realtime Web Dashboard**. Không nêu "xây dựng app định vị" làm điểm mới vì đồ án cũ đã làm.

✅ **Đã chốt sau khi triển khai.** Bảng trên là ĐỀ XUẤT ban đầu, giữ nguyên làm dấu vết quá trình. Bốn dòng đã đi khác:

| Dòng trong bảng | Đề xuất | Đã dựng | Xem thêm |
|---|---|---|---|
| Backend/CSDL | PostgreSQL | **SQLite** qua `aiosqlite` | mục 2.5 |
| Sản phẩm đầu ra | Web Dashboard, không làm mobile | **cả hai**: app Flutter quét WiFi thật, và Dashboard web | mục 2.6, 2.7 |
| Hậu xử lý vị trí | EMA `alpha = 0.3` | **đồng thuận không gian** trên 3 lần quét | mục 2.4.1 |
| Web Dashboard | HTML5 + Tailwind CSS | HTML/CSS/JS thuần, **không thư viện ngoài** — phòng bảo vệ có thể không ra được Internet | mục 2.7 |
| Mô hình | XGBoost là mô hình chính | XGBoost **vẫn là mô hình chính của đề tài**; mô hình *đang triển khai* chọn theo validation và hiện là kNN vân tay | mục 2.4.1 |

Mâu thuẫn SQLite ↔ PostgreSQL giữa đề cương (`Nhom15_DeCuong_DATN_edited.docx`, mục V) và tài liệu thiết kế CSDL riêng nay đã hết: chốt **SQLite**, đúng như đề cương ghi. Không cần sửa mục V nữa.

Mọi sơ đồ và bảng phía dưới vẫn là bản thiết kế ban đầu. Chỗ nào đã dựng khác thì có mục đối chiếu riêng chỉ ra.

---

## 2.1. Phân tích yêu cầu

### 2.1.1. Tác nhân (Actors)

| Actor | Vai trò |
|---|---|
| **Researcher/Collector** (thành viên nhóm) | Thu thập dữ liệu offline tại các RP, quản lý dataset, huấn luyện & đánh giá mô hình |
| **End-user (Viewer)** | Mở Web Dashboard, xem vị trí hiện tại của mình (hoặc thiết bị test) theo thời gian thực |
| **System/Client device** | Actor phi con người: điện thoại/laptop quét RSSI và gửi lên backend qua HTTP hoặc WebSocket |
| **Admin** (mở rộng) | Cấu hình bản đồ, danh sách AP, chọn model đang active |

### 2.1.2. Use case chính

```mermaid
flowchart LR
  Collector((Researcher/\nCollector))
  Viewer((End-user))
  Device((Client Device))
  Admin((Admin))

  UC1[Thu thập mẫu RSSI tại RP]
  UC2[Quản lý & tiền xử lý dataset]
  UC3[Huấn luyện & so sánh mô hình\nkNN/WKNN/XGBoost]
  UC4[Xem báo cáo đánh giá\nMean/Median/CDF]
  UC5[Gửi RSSI để dự đoán vị trí]
  UC6[Xem vị trí realtime trên Dashboard]
  UC7[Xem lịch sử di chuyển]
  UC8[Cấu hình bản đồ/AP/model active]

  Collector --> UC1
  Collector --> UC2
  Collector --> UC3
  Collector --> UC4
  Device --> UC5
  Viewer --> UC6
  Viewer --> UC7
  Admin --> UC8
```

### 2.1.3. Yêu cầu chức năng (đã nhóm theo module — khớp với 5 chương trong đề cương)

1. **Thu thập & tiền xử lý tín hiệu**: quét RSSI, gắn nhãn RP/tọa độ, chuẩn hóa cột AP theo BSSID, xử lý AP không phát hiện (-98), loại mẫu <6 AP, loại AP nhiễu/hiếm gặp, chia train/val/test không rò rỉ dữ liệu.
2. **Ước lượng tọa độ**: nhận vector RSSI → trả (x, y) bằng model đang active, làm mượt bằng EMA.
3. **Truyền dữ liệu thời gian thực**: WebSocket phát tọa độ mới mỗi khi có dự đoán; REST dùng cho các thao tác không cần realtime.
4. **Hiển thị trực quan**: Dashboard vẽ marker trên sơ đồ mặt bằng, trạng thái kết nối, RSSI panel, thẻ tọa độ hiện tại.
5. **Quản lý thực nghiệm**: lưu vết dataset/model theo phiên bản để tái lập kết quả, so sánh kNN/WKNN/XGBoost bằng bảng & biểu đồ CDF.

### 2.1.4. Yêu cầu phi chức năng

| Loại | Yêu cầu |
|---|---|
| Hiệu năng | Độ trễ dự đoán 1 mẫu (từ lúc nhận RSSI đến khi trả tọa độ) nên < 200 ms; model load **một lần khi khởi động** backend, không load lại mỗi request |
| Độ chính xác | Sai số trung bình XGBoost thấp hơn kNN/WKNN tối thiểu 10–20%; CDF90 < baseline |
| Khả năng tái lập | Mọi dataset/model phải gắn version, có thể huấn luyện lại từ đầu ra cùng kết quả (cố định `random_state=42`) |
| Khả năng mở rộng | Schema và kiến trúc phải chịu được việc thêm tầng/tòa nhà/route-finding sau này mà không đổi core |
| Khả dụng | Nếu mất kết nối WebSocket, Dashboard phải hiển thị rõ trạng thái "Disconnected", không đứng hình marker cũ mà không cảnh báo |
| Bảo mật (mức tối thiểu cho đồ án) | Endpoint ghi dữ liệu training/cấu hình nên có xác thực đơn giản (API key/basic auth); endpoint đọc công khai cho Dashboard |

**Đo được trên bản đã dựng:**

| Yêu cầu | Kết quả |
|---|---|
| Độ trễ < 200 ms | Đạt rất thoải mái: 0,85 ms mỗi mẫu cho mô hình đang chạy, mô hình chậm nhất là Random Forest ở 35,9 ms. Có bước chạy nóng lúc khởi động vì lần `predict` đầu tiên của scikit-learn tốn hơn hẳn |
| XGBoost thấp hơn baseline 10–20% | **Không đạt** — cao hơn 25,8%. Xem mục 2.4.1 |
| Tái lập được | Đạt: `random_state=42`, và hai lần chạy pipeline cho ra dataset giống hệt **từng byte** |
| Dashboard báo mất kết nối | Đạt: huy hiệu trạng thái đổi ngay khi WebSocket đóng, tự nối lại với thời gian chờ tăng dần |
| Xác thực | **Chưa làm** — không có endpoint ghi dữ liệu training, nhưng Dashboard và WebSocket cũng đang mở hoàn toàn. Ghi trong phần hạn chế đã biết của README |

---

## 2.2. Kiến trúc hệ thống tổng thể

Hệ thống chia 2 luồng: **Offline (huấn luyện)** và **Online (thời gian thực)**, dùng chung tầng dữ liệu.

```mermaid
flowchart TB
  subgraph Offline["OFFLINE — Giai đoạn ngoại tuyến"]
    A1[Thiết bị thu thập\nWiFi scan tại RP] --> A2[(raw_wifi_scans)]
    A2 --> A3[Pipeline tiền xử lý\npreprocess.py]
    A3 --> A4[(fingerprint_dataset\ntrain/val/test)]
    A4 --> A5[Huấn luyện\nkNN / WKNN / XGBoost]
    A5 --> A6[Đánh giá\nMean/Median/CDF]
    A6 --> A7[(Model artifacts\n.pkl/.json)]
  end

  subgraph Online["ONLINE — Giai đoạn thời gian thực"]
    B1[Client quét WiFi] -- POST /predict --> B2[FastAPI Backend]
    B2 --> B3[Preprocessing Service\nmap BSSID theo feature_list]
    B3 --> B4[Prediction Service\nload model active]
    B4 --> B5[Smoothing Service\nEMA alpha=0.3]
    B5 --> B6[(position_predictions log)]
    B5 -- WS /ws/location --> B7[Web Dashboard\nmarker realtime]
  end

  A7 -.model active.-> B4
  DB[(PostgreSQL)]
  A2 & A4 & A7 & B6 -.-> DB
```

*Sơ đồ thiết kế ban đầu. Bản đã dựng dùng SQLite thay PostgreSQL và đồng thuận không gian thay EMA — xem bảng "Đã chốt" ở đầu tài liệu.*

**Giải thích các thành phần:**

- **Data Collection**: script/ứng dụng nhỏ (web form hoặc CLI) ghi RSSI thô kèm `rp_id, x, y, device_id, direction, bssid, rssi`.
- **Preprocessing pipeline** (`ml/preprocess.py`): chuẩn hóa AP theo BSSID, xử lý thiếu, lọc mẫu/AP kém, scaling (fit trên train only), xuất `fingerprint_dataset_sorted.csv`, `feature_list.json`.
- **Training pipeline**: huấn luyện song song kNN/WKNN (baseline) và XGBoost (2 mô hình con `model_x`, `model_y`); lưu artifact + `model_metadata.json`.
- **Backend FastAPI**: expose REST (`/predict`, `/map`, CRUD dữ liệu) + WebSocket (`/ws/location`); load model **một lần lúc start** để đảm bảo độ trễ thấp.
- **Smoothing Service**: EMA theo từng `device_id`/`session`, có rule reset nếu mất tín hiệu lâu, giới hạn bước nhảy tối đa.
- **Web Dashboard**: HTML5 + Tailwind CSS, kết nối WebSocket, vẽ marker lên sơ đồ mặt bằng bằng công thức quy đổi `pixel = origin + x*scale`.

---

## 2.3. Thiết kế luồng dữ liệu (Sequence)

**(a) Luồng dự đoán realtime — quan trọng nhất, nên đưa vào báo cáo dưới dạng sequence diagram:**

```mermaid
sequenceDiagram
  participant C as Client (Device)
  participant WS as WebSocket /ws/location
  participant P as Prediction Service
  participant S as Smoothing Service
  participant DB as SQLite
  participant D as Web Dashboard

  C->>WS: scan {device_id, [{bssid, rssi}, ...]}
  WS->>P: map RSSI theo feature_list.json
  P->>P: model.predict(vector) -> (x_pred, y_pred)
  P->>S: EMA(x_pred, y_pred, state[device_id])
  S-->>DB: INSERT position_predictions
  S-->>WS: {x, y, x_smooth, y_smooth, model, timestamp}
  WS-->>D: broadcast tọa độ mới
  D->>D: cập nhật marker + tooltip
```

**(b) Luồng huấn luyện & đánh giá (offline):** Load `fingerprint_dataset` → fit scaler trên train → train kNN/WKNN/XGBoost → predict trên validation/test → tính `mean_error, median_error, cdf_50/75/90` → ghi `model_evaluations` + `model_evaluation_details` (từng mẫu, để vẽ heatmap lỗi) → chọn model tốt nhất, đặt `is_active = true`.

---

## 2.4. Thiết kế mô hình học máy

- **Phát biểu bài toán**: Input = vector RSSI `[AP_1, ..., AP_n]` (thiếu → -98); Output = `(x, y)` mét. Loss/đánh giá chính: `error = sqrt((x_pred-x_true)² + (y_pred-y_true)²)`.
- **Baseline 1 – kNN**: trung bình tọa độ của k mẫu train gần nhất; thử k ∈ {3,5,7,9,11}, distance ∈ {euclidean, manhattan}.
- **Baseline 2 – WKNN**: trọng số `1/(distance+ε)`, ε=1e-6. Dải k bắt đầu từ 2 chứ không phải 1 như kNN: với một láng giềng duy nhất thì trọng số không có gì để cân, WKNN ở k=1 chính là kNN ở k=1 và bảng so sánh mất một mô hình cơ sở.
- **(Tùy thời gian) Random Forest**: `n_estimators` ∈ {100,200,500}, dùng làm mốc so sánh thêm với XGBoost — có sẵn số liệu đối chứng từ đồ án cũ (RF đạt 97.16%/6.02m trong bài toán phân lớp, nên kỳ vọng RF cũng là baseline mạnh trong bài toán hồi quy).
- **Mô hình chính – XGBoost Regression**: train riêng `model_x`, `model_y`; tham số thử `n_estimators∈{100,300,500}`, `max_depth∈{3,5,7}`, `learning_rate∈{0.03,0.05,0.1}`, `subsample/colsample_bytree∈{0.8,1.0}`, `reg_lambda∈{1,5,10}`, `random_state=42`.
- **Chỉ số đánh giá**: Mean/Median/Min/Max/Std error (m), CDF tại 50/75/90%, MAE/RMSE theo từng trục x, y, thời gian dự đoán (ms). Biểu đồ: CDF sai số, so sánh mean error giữa model, heatmap lỗi theo bản đồ, feature importance của XGBoost, sai số theo từng RP.
- **Chia dữ liệu**: cơ bản train/val/test = 70/15/15; nâng cao (nếu có nhiều thiết bị/thời điểm) — device-holdout và time-holdout để kiểm tra tổng quát hóa thực tế (đúng bài học từ đồ án cũ: kết quả phòng thí nghiệm 88–97% nhưng thực tế rớt xuống 5–12m — cần test bằng thiết bị khác/thời điểm khác ngay từ đầu để tránh optimistic bias).
- **Hậu xử lý**: EMA `x_smooth = α·x_new + (1-α)·x_old`, α=0.3 mặc định; reset nếu mất tín hiệu quá lâu; giới hạn bước nhảy tối đa.

---

### 2.4.1. Đối chiếu với bản đã thực hiện

Mục 2.4 ở trên là **thiết kế ban đầu**, giữ nguyên làm dấu vết quá trình. Sau khi
chạy thực nghiệm có năm chỗ khác đi. Mọi số liệu dưới đây đo trên tập test 118
mẫu, chọn mô hình chỉ dựa trên validation.

**1. Hậu xử lý: EMA thay bằng đồng thuận không gian.**

Thiết kế chọn EMA `x_smooth = α·x_new + (1-α)·x_old`. Thực nghiệm cho thấy các ca
sai nặng gần như luôn là *một* lần quét dị thường lẻ loi chứ không phải dao động
đều, mà EMA thì kéo trung bình nên vẫn bị điểm lạc lôi đi. Đồng thuận không gian
chọn dự đoán có tổng khoảng cách tới các dự đoán còn lại nhỏ nhất, nên luôn trả
về một điểm tham chiếu có thật và tự loại điểm lạc.

Đo trên tập test, gộp 3 lần quét:

| Cách gộp | Sai số trung bình | Lớn nhất | Số điểm sai |
|---|---|---|---|
| Một lần quét, không gộp | 1,92 m | 37,6 m | 13/39 |
| Bình chọn đa số | 0,59 m | 18,0 m | 2/39 |
| Trung vị toạ độ | 0,38 m | 15,0 m | 1/39 |
| **Đồng thuận không gian** | **0,38 m** | **15,0 m** | **1/39** |

Hai tham số `α` và giới hạn bước nhảy vì thế không còn, thay bằng `cua_so_gop`
(số lần quét gộp, mặc định 3) và `reset_after_seconds`.

**2. Thêm mô hình thứ năm không có trong thiết kế.** Dữ liệu chỉ có 39 toạ độ
khác nhau vì thu đúng tại các điểm tham chiếu, nên bài toán gần với phân lớp hơn
hồi quy. `kNN vân tay (Bray-Curtis)` khai thác đúng tính chất đó và cho 1,92 m,
so với 5,15 m của cơ sở tốt nhất và 6,48 m của XGBoost.

Kèm theo đó là một kết quả ngược với giả thiết ban đầu, cần nói thẳng trong báo
cáo: **XGBoost không đạt mục tiêu ở mục 2.1** — thay vì thấp hơn baseline
10–20%, nó cao hơn 25,8%. Nguyên nhân là tính chất dữ liệu nêu trên chứ không
phải thiếu tinh chỉnh: lưới tham số đã nới tới khi cực trị nằm hẳn bên trong.
XGBoost vẫn là mô hình chính của đề tài và vẫn được huấn luyện, đánh giá đầy đủ
trong bảng so sánh; mô hình *đang triển khai* thì chọn theo sai số validation,
và `GET /health` luôn cho biết mô hình nào đang chạy.

**3. Giá trị điền thiếu: −98 thành −96, và nó chuyển vào hợp đồng dữ liệu.**
Không đặt cứng nữa mà tính từ dữ liệu: `min(RSSI) − 1`. Dữ liệu thu được có RSSI
thấp nhất −95 dBm.

Điều quan trọng hơn con số là **nó được ghi ở đâu**. Giá trị này nay nằm trong
`artifacts/feature_list.json` do pipeline sinh ra, và backend đọc lại từ đó lúc
khởi động — một nguồn duy nhất cho cả lúc huấn luyện lẫn lúc chạy thật.

Đồ án CTK45 cho thấy đúng cái giá của việc không làm vậy. Báo cáo của họ trang 42
ghi *"giá trị RSS = −98 được đặt mặc định với các AP không phát hiện được"*, còn
mã nguồn ứng dụng (`wifi_service.dart`, dòng 59) lại điền `?? -100`. Huấn luyện
bằng −98, chạy thật bằng −100: lệch hệ thống trên **mọi** AP vắng mặt của **mọi**
lần quét. Không có gì báo lỗi, vì cả hai đều là số hợp lệ — chỉ có sai số định vị
âm thầm lớn hơn nó đáng phải có.

Hai con số đó nằm ở hai kho mã khác nhau, do hai người viết, cách nhau nhiều
tháng. Đấy chính là lý do dự án này không cho phép bất kỳ tham số tiền xử lý nào
tồn tại ở hai nơi: `missing_rssi_value`, `min_ap_per_scan` và thứ tự 36 cột AP
đều chỉ có một bản trong `feature_list.json`, kèm `ap_columns_sha1` để backend từ
chối khởi động nếu mô hình và hợp đồng đến từ hai lần chạy pipeline khác nhau.

**4. Lưới tham số mở rộng.** Ba lưới trong mục 2.4 có tối ưu rơi đúng vào biên —
`beta` cận trên, `n_neighbors` cận dưới, `reg_lambda` cận dưới — nên đã nới cho
tới khi cực trị nằm hẳn bên trong. Riêng lưới XGBoost giữ đúng 6 tham số như
thiết kế, chỉ thêm giá trị `reg_lambda = 0,5` và `colsample_bytree = 0,6`.

**5. `device_holdout` và `time_holdout` không thực hiện được.** Toàn bộ dữ liệu
thu bằng một máy Samsung SM-S908E, nên `device_holdout` không có gì để tách. Với
`time_holdout` thì vướng hơn: mỗi điểm tham chiếu chỉ được đo trong đúng một
buổi (13/01 đo RP27–RP40, 21/01 đo RP08–RP25, 24/01 đo RP01–RP17), nên tách theo
thời gian đồng nghĩa với tách theo vị trí — tập test sẽ chứa những điểm mà tập
train chưa từng thấy, và bài toán vân tay không trả lời được. Đây là hạn chế của
cách thu dữ liệu, cần khắc phục bằng một đợt đo lại có lặp điểm qua nhiều buổi và
nhiều máy.

---

## 2.5. Thiết kế cơ sở dữ liệu

**Đã chốt: SQLite.** Bản thiết kế ban đầu khuyến nghị PostgreSQL với ba lý do — lưu nhiều phiên bản dataset/model để tái lập thực nghiệm, JSONB cho `hyperparameters`/`metadata`, và dễ mở rộng đa tầng/đa toà nhà. Thực tế triển khai cho thấy cả ba đều chưa cần đến:

- Việc tái lập thực nghiệm giải quyết bằng `artifacts/pipeline_manifest.json` và `model_metadata.json` — hai lần chạy pipeline cho ra tệp giống hệt từng byte, không cần bảng phiên bản trong CSDL.
- `hyperparameters` chỉ được đọc để in báo cáo chứ không truy vấn theo trường, nên JSONB không đem lại gì so với một chuỗi JSON.
- Phạm vi đề tài đã chủ động giới hạn ở một tầng.

Đổi lại, SQLite bỏ được cả một dịch vụ phải cài đặt, nên máy chấm chỉ cần `pip install -r requirements.txt` là chạy. Schema vẫn viết tránh cú pháp riêng của mọi engine, và toàn bộ truy cập CSDL đi qua `backend/repository.py`, nên đổi sang PostgreSQL về sau chỉ phải đổi `DATABASE_URL`. Thực tế hệ thống chỉ dựng **2 bảng** thật cần (`positioning_sessions`, `position_predictions`) trong số 16 bảng của ERD dưới đây.

ERD rút gọn (nhóm theo 6 miền dữ liệu, chi tiết từng trường đã có sẵn trong tài liệu thiết kế CSDL của nhóm — đây chỉ tổng hợp quan hệ):

```mermaid
erDiagram
  buildings ||--o{ floors : has
  floors ||--o{ floor_maps : has
  floors ||--o{ reference_points : has
  floors ||--o{ wifi_access_points : located_in
  floors ||--o{ fingerprint_datasets : scoped_to
  floors ||--o{ points_of_interest : has
  floors ||--o{ graph_nodes : has

  devices ||--o{ wifi_scans : performs
  reference_points ||--o{ wifi_scans : labels
  wifi_scans ||--o{ wifi_scan_records : contains
  wifi_access_points ||--o{ wifi_scan_records : measured_by

  fingerprint_datasets ||--o{ dataset_features : uses
  fingerprint_datasets ||--o{ dataset_splits : splits
  fingerprint_datasets ||--o{ ml_models : trains

  ml_models ||--o{ model_evaluations : evaluated_by
  model_evaluations ||--o{ model_evaluation_details : detail_of

  devices ||--o{ positioning_sessions : opens
  positioning_sessions ||--o{ position_predictions : logs
  ml_models ||--o{ position_predictions : used_by
  reference_points ||--o{ position_predictions : nearest_to

  graph_nodes ||--o{ graph_edges : connects
  points_of_interest ||--o{ graph_nodes : maps_to
```

**Nhóm bảng ưu tiên triển khai theo giai đoạn** (khớp mục 17 trong tài liệu thiết kế CSDL, ánh xạ vào mốc thời gian đề cương ở mục 2.9 bên dưới):

| Giai đoạn | Bảng | Mục tiêu |
|---|---|---|
| 1 – Lõi định vị | `buildings, floors, floor_maps, reference_points, devices, wifi_access_points, wifi_scans, wifi_scan_records` | Lưu đủ dữ liệu RSSI thô |
| 2 – Machine Learning | `fingerprint_datasets, dataset_features, dataset_splits, ml_models, model_evaluations, model_evaluation_details` | Quản lý dataset/model có versioning |
| 3 – Realtime | `positioning_sessions, position_predictions` | Log dự đoán, phục vụ Dashboard + debug |
| 4 – Mở rộng (nếu còn thời gian) | `points_of_interest, graph_nodes, graph_edges` | Chỉ đường Dijkstra/A* |

Ràng buộc quan trọng cần giữ: `wifi_access_points.bssid` UNIQUE (SSID không dùng làm khóa), `dataset_features.feature_index` unique trong 1 dataset (để backend map đúng thứ tự cột khi predict realtime — đây là điểm dễ gây bug nhất nếu thứ tự train/predict lệch nhau), dữ liệu training bắt buộc có `reference_point_id`, dữ liệu realtime thì không.

---

### 2.5.1. Dữ liệu không gian: sơ đồ mặt bằng và đồ thị đi lại

Mục 2.5 nói về CSDL quan hệ. Hệ thống còn một kho dữ liệu thứ hai không nằm
trong CSDL: **hình học của toà nhà**. Phần này ghi lại nó đến từ đâu và vì sao
không lấy sẵn của đồ án kế thừa.

#### Vì sao không kế thừa GeoJSON của CTK45

Đồ án CTK45 dựng bản đồ Mapbox từ bảy tệp GeoJSON vẽ tay: `POI`, `Room`,
`Hallways`, `Stair`, `Paths`, `Doors`, `Wall`. Cả bảy đều còn trên kho mã của họ
và tải về được. Trước khi dùng, nhóm khớp 40 điểm trong `POI.geojson` của họ với
40 toạ độ nhóm đã đo:

| Phép đo | Kết quả |
|---|---|
| Hộp bao 40 điểm POI của họ, quy ra mét thật | 30,5 × 34,4 m |
| Hộp bao thật của khu khảo sát | **86 × 52 m** |
| Khớp Procrustes (quay + co giãn đều + tịnh tiến) | RMS 5,99 m |
| Khớp affine đầy đủ (hai trục co khác nhau) | RMS **5,08 m**, lệch lớn nhất 28,55 m |
| 780 cặp điểm: khoảng cách trong GeoJSON so với khoảng cách thật | trung vị **0,40×** |
| 143 cặp cách nhau dưới 20 m | sai số tuyệt đối trung bình **7,5 m** |

Phép affine đầy đủ đã cho phép hai trục co giãn khác nhau và trượt tự do, mà vẫn
còn lệch trung bình 5 m. Nghĩa là biến dạng **không tuyến tính**: toạ độ đặt bằng
tay chứ không theo một phép chiếu nào. Không có phép biến đổi nào sửa được.

Hệ quả trực tiếp: mọi khoảng cách đo trên bản đồ ấy đều sai. Thẻ *"Tổng khoảng
cách: 18.43 mét"* trong ứng dụng của họ là con số tính trên hình học này — ba
cặp điểm có khoảng cách thật 16 m, 12,8 m và 18 m thì GeoJSON cho ra 14,1 m,
7,3 m và 9,3 m.

Vì vậy nhóm **không** dùng lại `Room`, `Hallways`, `Stair` dù chúng có sẵn sáu đa
giác phòng, năm hành lang và tám khối cầu thang. Vẽ chúng lên sẽ ra một bản đồ
đẹp mà mọi thứ lệch chỗ 5 m. `POI.geojson` chỉ được dùng cho hai việc không cần
đúng tỉ lệ: lấy **tên và mô tả** của 40 điểm, và xét **chiều trục x** bằng phép
quay-co-tịnh tiến.

#### Nguồn hình học thay thế

Nhóm trích hình học từ chính `Map.png` — sơ đồ mặt bằng tầng 1 do CTK45 số hoá,
là thứ duy nhất của họ có tỉ lệ đúng. Công cụ `tools/trich_ban_do.py` chạy một
lần rồi commit kết quả vào `data/reference/ban_do_tang1.json`, nên backend chỉ
đọc JSON và không cần thư viện xử lý ảnh lúc chạy thật.

**Phép biến đổi mét ↔ pixel được kiểm bằng hai phép đo độc lập.** Lưới chấm trong
ảnh trải đúng 1000 px ngang và 605 px dọc, trong khi hộp bao 40 điểm tham chiếu
là 86 m × 52 m — cho 11,628 và 11,635 px/m. Hai trục tính riêng mà khớp tới 4 chữ
số có nghĩa; đó là căn cứ khẳng định lưới chấm chính là hệ toạ độ mét của bộ dữ
liệu, không phải một quy ước tự đặt.

**Chiều trục cũng chốt bằng bằng chứng, không bằng quy ước.** Trục y hướng lên:
toà nhà thắt eo ở giữa, theo chiều này đoạn eo ứng với y ∈ [6,4; 21,3] m và cả 8
điểm trong khoảng đó đều có |x| ≤ 30 m — vừa lọt; chiều ngược lại buộc đoạn eo
phải chứa hai điểm ở |x| = 43 m, rộng hơn cả eo. Trục x không lật: khớp 39 điểm
với GPS trong `POI.geojson` cho RMS 3,15 m khi không lật và 13,84 m khi lật.

#### Đồ thị đi lại

Nút của đồ thị là chính 40 điểm tham chiếu, vì **RP nằm trên chỗ đi được theo
định nghĩa**: phải có người đứng đúng đó cầm máy quét mới đo ra được toạ độ.

Cạnh thì cần thêm sơ đồ, vì hai điểm gần nhau vẫn có thể có tường ở giữa. Công cụ
dựng mặt nạ tường từ `Map.png` rồi **gán nhãn vùng liên thông**: hai điểm cùng
một vùng thì đi được, khác vùng thì không. Cách này không có tham số ngưỡng nào
phải chỉnh tay. Kết quả: 103 cặp điểm trong bán kính 25 m bị loại, cạnh dài nhất
giảm từ 21,0 m xuống 17,2 m.

`Map.png` vẽ tường nhưng **không vẽ cửa**, nên chặn hết cạnh cắt tường thì đồ thị
vỡ thành 7 mảnh rời. Công cụ nối lại bằng số cạnh ít nhất, mỗi lần chọn cạnh ngắn
nhất giữa hai mảnh — chỗ nhiều khả năng có cửa nhất. Sáu cạnh ấy ghi riêng vào
khoá `cua_gia_dinh`, **không trộn** vào phần suy ra được từ ảnh, để ra thực địa
còn biết cái nào cần đối chiếu. Đây là hạn chế đã biết, nêu trong README.

Đối lập với CTK45 ở đúng chỗ này: mã của họ nạp `Paths.geojson` — tức hành lang
**đi được** — vào biến `walls` rồi dùng làm vật cản, nên phép kiểm chặn hoạt động
ngược với ý định. Chi tiết ở mục 2b.2 của
`Phan_Tich_Ky_Thuat_DoAnCu_va_Cai_Tien.md`.

#### Một phép biến đổi, ba ngôn ngữ

Cùng phép đổi mét ↔ pixel được dùng ở Python (backend và công cụ), Dart (ứng dụng
di động) và JavaScript (Dashboard). Lệch một hằng số ở một nơi thì cùng một toạ
độ hiện ra hai chỗ khác nhau trên hai màn hình, mà triệu chứng nhìn y hệt "mô
hình đoán sai" nên rất khó lần ra.

`tests/test_dashboard.py` đối chiếu cả ba với `ban_do_tang1.json`, gồm cả số hạng
dịch trục — số hạng này từng viết trần ở cả ba nơi mà không tệp nào khai nó, nên
không bài test nào so được. Nay nó có tên (`goc_met_x`) và được neo vào chính giá
trị `x` nhỏ nhất trong bảng toạ độ đã đo.

---

## 2.6. Thiết kế API & giao thức realtime

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/wifi-scans/training` | Ghi 1 lần quét offline gắn với RP |
| POST | `/predict` | Nhận `{device_id, scan:[{bssid,rssi}]}` → trả `{x, y, x_smooth, y_smooth, model, timestamp}` |
| WS | `/ws/location` | Kênh realtime: client gửi scan, server phát tọa độ đã làm mượt |
| GET | `/map` | Trả kích thước bản đồ, RP, POI, ảnh nền |
| GET | `/floors/{id}/reference-points` | Danh sách RP theo tầng |
| GET | `/models` , `/models/active` | Danh sách model, model đang dùng |
| POST | `/models/{id}/activate` | Đổi model active |
| GET | `/model-evaluations?model_id=` | Kết quả đánh giá để vẽ biểu đồ báo cáo |
| GET | `/predictions?device_id=&from=&to=` | Lịch sử vị trí (màn hình History) |
| GET | `/graph?floor_id=` , POST `/route` | (Mở rộng) chỉ đường |

Định dạng JSON response `/predict` giữ nguyên như trong tài liệu kế hoạch của nhóm — đây là hợp đồng dữ liệu giữa model và frontend, nên khóa cứng sớm để không phải sửa lại Dashboard nhiều lần.

### 2.6.1. Đối chiếu với bản đã dựng

Đã dựng 9 endpoint. Bốn nhóm trong bảng trên chưa làm, và đều có lý do:

| Endpoint đề xuất | Tình trạng |
|---|---|
| `POST /predict`, `WS /ws/location`, `GET /map`, `GET /predictions` | Đã dựng, đúng hợp đồng dữ liệu ở trên |
| `GET /graph`, `POST /route` | Đã dựng, dù bảng ghi là "mở rộng". `/route` trả kèm `chi_dan` — chỉ dẫn rẽ từng chặng |
| `GET /health`, `GET /map/so-do.png`, `GET /` | Thêm mới: trạng thái mô hình, ảnh sơ đồ, và trang Dashboard phục vụ ngay từ uvicorn |
| `POST /wifi-scans/training` | Không làm. Dữ liệu khảo sát kế thừa từ CTK45, nhóm không tổ chức đợt thu mới nên không cần đường ghi dữ liệu huấn luyện qua API |
| `GET /floors/{id}/reference-points` | Không làm. Chỉ có một tầng, `GET /map` trả luôn cả 40 điểm |
| `GET /models`, `/models/active`, `POST /models/{id}/activate`, `GET /model-evaluations` | Không làm. Thuộc phần quản lý phiên bản mô hình qua giao diện; mô hình active chọn lúc huấn luyện và ghi vào `model_metadata.json` |

---

## 2.7. Thiết kế giao diện (UI/UX)

Theo đúng cấu trúc module trong file Figma đã phác thảo — hệ thống lại theo độ ưu tiên MVP:

**MVP (bắt buộc, làm trước):**
- **Dashboard** (màn hình quan trọng nhất): sơ đồ mặt bằng chiếm 60–70%, marker vị trí + hiệu ứng pulse, panel trạng thái WebSocket/model/latency, thẻ tọa độ hiện tại, panel RSSI theo AP.
- **Data Collection**: chọn RP trên bản đồ, form nhập RP_ID/x/y/device, bảng RSSI realtime, nút start/stop/save scan.
- **Settings** cơ bản: cấu hình API/WebSocket, danh sách AP, model đang chạy.

**Bản hoàn chỉnh (sau MVP):**
- **Dataset Management**: thống kê mẫu/AP/dữ liệu thiếu, trạng thái pipeline tiền xử lý.
- **Model Training**: danh sách kNN/WKNN/XGBoost với trạng thái, mean/median/90th error, nút Train/Evaluate/Deploy.
- **Evaluation**: biểu đồ so sánh mean error, CDF 50/75/90, bảng kết quả, bản đồ heatmap lỗi.
- **History**: replay đường di chuyển, bảng log time/x/y/error/model.

**Mở rộng sau (không bắt buộc)**: đa tầng, nhiều người dùng cùng lúc, chỉ đường, quản lý nhiều khu vực, phân quyền admin/researcher/viewer.

Bố cục chung: sidebar trái (điều hướng module) + top bar (trạng thái hệ thống) + main content + right panel (log/metrics realtime) — giữ nguyên theo thiết kế Figma đã có, việc này đã khá hoàn chỉnh, không cần chỉnh sửa nhiều.

### 2.7.1. Đối chiếu với bản đã dựng

**Dashboard gộp thành một trang, không chia bảy màn.** Bảy tệp HTML từng được
tạo theo bảy module ở trên nhưng không tệp nào có nội dung, mà dữ liệu chúng
định hiển thị thì máy chủ chưa có endpoint tương ứng — giữ lại chỉ là giữ bảy
đường dẫn 404 có tiêu đề. Trang hiện tại gồm: sơ đồ mặt bằng với 40 điểm tham
chiếu và marker thiết bị kèm vệt đã đi, bảng thiết bị đang kết nối, hộp chỉ
đường, biểu đồ hiệu quả bước gộp, và bảng lịch sử định vị. Tức là phần MVP và
hai màn Evaluation, History đã có mặt dưới dạng khối trong một trang.

**Data Collection, Dataset Management, Model Training chưa làm** — cùng lý do với
các endpoint tương ứng ở mục 2.6.1.

**Không dùng Tailwind CSS** như mục V đề cương ghi: trang viết bằng HTML/CSS/JS
thuần. Tailwind qua CDN cần Internet mà phòng bảo vệ có thể không ra được mạng
ngoài; bản build tại chỗ thì phải thêm Node vào một dự án còn lại thuần Python.
Giao diện chỉ có một trang nên phần tiện lợi của Tailwind cũng không còn nhiều.

**Ngoài đề cương: ứng dụng di động Flutter** 5 màn hình (Trang chủ, Bản đồ, Chi
tiết khu vực, Tìm kiếm, Cài đặt), song ngữ Việt/Anh, sáng/tối. Đây là nguồn quét
WiFi thật cho hệ thống và là cách kiểm thử thực địa. Xem `mobile/README.md`.

Màn Bản đồ dựng theo bố cục CTK45 ở mục 4.4.3 — hàng chip lọc loại khu vực trên
sơ đồ mặt bằng — nhưng khác họ ở hai chỗ. Nhãn chip lấy thẳng từ trường `nhom`
của dữ liệu khảo sát chứ không từ một bảng loại viết riêng, nên không thể trôi
khỏi dữ liệu như `CategoryModel` của họ. Và chip ngoài nhóm đang chọn thì làm
mờ chứ không tô đậm thêm: cách của họ chỉ đổi nền các nhãn cùng loại nên màn
hình càng dày đặc hơn sau khi lọc.

Tuyến đường vẽ bằng chuỗi chấm cách đều 1,2 m theo `duong_di` — danh sách nút
đầy đủ, không phải `chi_dan` vốn đã gộp các chặng đi thẳng — kèm thẻ tổng quãng
đường. Con số trên thẻ là tổng độ dài các cạnh **đã lọc tường** trong hệ mét đo
thực địa, khác thẻ "Tổng khoảng cách" của CTK45 vốn cộng trên hình học GeoJSON
vẽ tay (mục 2.5.1). Tuyến neo ở điểm xuất phát lúc bấm và không tự tính lại khi
người dùng đi tiếp; chấm vị trí vẫn chạy thời gian thực nên vẫn thấy mình đang
ở đâu trên tuyến.

---

## 2.8. Rủi ro & giải pháp (tổng hợp, ưu tiên theo mức ảnh hưởng)

| Rủi ro | Giải pháp |
|---|---|
| RSSI dao động mạnh → marker nhảy | EMA smoothing, thu nhiều mẫu/RP, đánh giá riêng lúc đông/vắng người |
| Model tốt trên test nhưng kém khi thực tế (bài học trực tiếp từ đồ án cũ: 88-97% phòng lab nhưng 5-12m thực tế) | Bắt buộc test bằng thiết bị khác (`device_holdout`) và thời điểm khác (`time_holdout`), không chỉ dùng random split |
| AP thay đổi/biến mất theo thời gian | Dùng BSSID cố định, đánh dấu `is_active=false` cho AP tạm thời, cho phép retrain |
| Web realtime bị trễ | Load model 1 lần lúc start, không load mỗi request; giới hạn tần suất gửi RSSI |
| Lệch thứ tự cột feature giữa lúc train và lúc predict | `dataset_features.feature_index` là nguồn sự thật duy nhất, backend luôn map theo `feature_list.json` gắn với model đang active |

### 2.8.1. Rủi ro đã xảy ra thật, và thêm một rủi ro không lường trước

| Rủi ro | Thực tế |
|---|---|
| RSSI dao động → marker nhảy | Xảy ra đúng như dự đoán, nhưng dạng khác: không phải dao động đều mà là **một lần quét dị thường lẻ loi**. EMA không xử lý được vì nó kéo trung bình; đồng thuận không gian mới loại được. Xem mục 2.4.1 |
| `device_holdout` / `time_holdout` | **Không thực hiện được** với bộ dữ liệu kế thừa — một máy đo, mỗi điểm chỉ đo một buổi. Đây là hạn chế phải nêu trong báo cáo, không phải việc bỏ sót |
| Đánh giá lúc đông/vắng người (mục 4.3 đề cương) | Chưa làm được: bộ dữ liệu không ghi số người có mặt lúc đo |
| Lệch thứ tự cột feature | Đã chặn bằng `ap_columns_sha1` trong `model_metadata.json`; lệch là backend không khởi động được chứ không chạy tiếp rồi trả toạ độ sai |
| **Không lường trước:** quét thiếu AP mà mô hình vẫn trả toạ độ tự tin | Mô hình cho ra toạ độ với mọi vector đầu vào, kể cả vector toàn giá trị điền-khi-thiếu. Đo thực địa: 23 AP nhìn thấy, khớp 0, hệ thống vẫn khẳng định người dùng đứng trong thư viện. Đã chặn bằng ngưỡng `min_ap_per_scan`, trả 422 |

---

## 2.9. Ánh xạ vào lộ trình 12 mốc trong đề cương (Aug–Nov 2026)

Cột "Mốc" chép đúng mục VII của đề cương. Cột cuối là tình trạng tính tới
01/09/2026.

| # | Mốc đề cương | Thời gian | Nội dung kỹ thuật tương ứng | Tình trạng |
|---|---|---|---|---|
| 1 | Phân tích đề tài, khảo sát tài liệu | 12/08–19/08 | Chốt schema DB (SQLite, mục 2.5), chốt kiến trúc mục 2.2 | Xong |
| 2 | Tìm hiểu dữ liệu RSSI, thống kê và tiền xử lý | 20/08–31/08 | `ml/preprocess.py`, 12 bước, `feature_list.json` | Xong |
| 3 | Mô hình cơ sở kNN, WKNN | 01/09–08/09 | `ml/models/knn.py`, `wknn.py`, `evaluate.py` | Xong |
| 4 | XGBoost và tinh chỉnh siêu tham số | 09/09–20/09 | `ml/models/xgboost_model.py`, quét lưới 648 tổ hợp | Xong |
| 5 | Báo cáo tiến độ lần 1 | 25/09–30/09 | Bảng so sánh 5 mô hình + biểu đồ CDF | Sẵn sàng |
| 6 | Thực nghiệm, so sánh và đánh giá | 01/10–15/10 | Heatmap lỗi theo điểm, phân bố sai số, hậu xử lý gộp | Xong phần đo; còn mục 4.3 (mật độ người) chưa làm được |
| 7 | Back-end FastAPI, tích hợp mô hình và WebSocket | 16/10–31/10 | 9 endpoint, `/ws/location`, `BoGop` | Xong |
| 8 | Front-end Web Dashboard và ghép nối | 01/11–10/11 | `frontend/index.html`, phục vụ ngay từ uvicorn | Xong |
| 9 | Kiểm thử, hoàn thiện và viết báo cáo | 11/11–15/11 | 128 test Python, 65 test Flutter | Đang làm |
| 10 | Báo cáo tiến độ lần 2 | 16/11–18/11 | — | Chưa tới |
| 11 | Sửa chữa, hoàn thiện đồ án | 19/11–24/11 | — | Chưa tới |
| 12 | Báo cáo bảo vệ trước hội đồng | 25/11–30/11 | Demo Dashboard realtime + bảng so sánh mô hình | Chưa tới |

Các mốc 7 và 8 đã làm xong sớm hơn kế hoạch. Phần làm thêm ngoài đề cương — ứng
dụng di động Flutter, đồ thị đi lại và chỉ đường — không thay thế mốc nào, và
được ghi riêng để không lẫn với phạm vi đề cương.

---|---|
| 12/08–19/08: Phân tích đề tài | Chốt schema DB (đã chốt SQLite, mục 2.5), chốt kiến trúc ở mục 2.2 |
| 20/08–31/08: Thống kê/tiền xử lý dữ liệu | Triển khai bảng "Giai đoạn 1 – Lõi định vị", pipeline `preprocess.py` |
| 01/09–08/09: Baseline kNN/WKNN | Cài `train_knn.py`, `train_wknn.py`, `evaluate.py` |
| 09/09–20/09: XGBoost | `train_xgboost.py` + tuning theo bảng tham số ở mục 2.4 |
| 25/09–30/09: Báo cáo tiến độ 1 | Có bảng so sánh model + biểu đồ CDF sơ bộ |
| 01/10–15/10: Thực nghiệm/so sánh | Bổ sung `device_holdout`/`time_holdout`, heatmap lỗi |
| 16/10–31/10: Backend + WebSocket | Triển khai `/predict`, `/ws/location`, Smoothing Service |
| 01/11–10/11: Frontend Dashboard | Triển khai màn hình MVP ở mục 2.7 |
| 11/11–24/11: Kiểm thử & hoàn thiện | Test thực tế đứng yên/di chuyển/đông-vắng người |
| 25/11–30/11: Bảo vệ | Chuẩn bị demo Dashboard realtime + bảng so sánh model |

---

## Việc tiếp theo có thể làm

1. Vẽ các sơ đồ trên (use-case, kiến trúc, sequence, ERD) thành hình ảnh/artifact để chèn trực tiếp vào Word thay vì mã Mermaid.
2. Viết chi tiết SQL DDL theo schema đã thống nhất, nếu báo cáo cần trình bày đầy đủ 16 bảng của ERD.
3. Viết code khung dự án (`project/` structure đã đề xuất) để nhóm code luôn.
