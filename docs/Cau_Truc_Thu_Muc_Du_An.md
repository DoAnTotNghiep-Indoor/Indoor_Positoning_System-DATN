# Cấu trúc thư mục dự án — Phân tích cấu trúc cũ và đề xuất cải tiến

Tài liệu này phân tích cấu trúc thư mục của đồ án cũ (`DATN_CTK45_IPS.pdf`, Chương 4.1, Hình 11–12) và đề xuất cấu trúc mới cho đồ án kế thừa của Nhóm 15.

---

## PHẦN 1 — CẤU TRÚC THƯ MỤC ĐỒ ÁN CŨ

### 1.1. Hiện trạng — Hình 11 (Flutter) và Hình 12 (Backend) của báo cáo CTK45

Trước đây mục này chép nguyên hai cây thư mục. Bỏ đi vì mọi phát hiện rút ra từ
chúng đều đã nằm trong bảng 1.2 dưới đây, và bản chép thì dài gấp ba lần bảng.
Những chỗ đáng chú ý nhất trong hai hình: `combined_data_sorted.csv` nằm trong
`assets/` của app, thư mục `model/` có mặt ở cả frontend lẫn backend,
`node_modules/` trong một dự án Python, và `venv/` + `__pycache__/` +
`backend.zip` đều được commit.

### 1.2. Các vấn đề của cấu trúc cũ

| # | Vấn đề | Ảnh hưởng |
|---|---|---|
| C1 | **Không có thư mục cho tầng ML** | Toàn bộ khâu tiền xử lý và huấn luyện nằm ngoài dự án (chỉ trên Colab) → không tái lập được thực nghiệm |
| C2 | **Dataset nằm trong `assets/` của app** (`combined_data_sorted.csv`) | Phình dung lượng ứng dụng; dữ liệu huấn luyện không thuộc về tầng trình bày |
| C3 | **Model trùng lặp** giữa `frontend/assets/model/` và `backend/model/` | Không biết bản nào đang chạy; dễ lệch phiên bản |
| C4 | **Model không đánh phiên bản** (`model.tflite`, `model2.tflite`) | Không biết model train từ dataset nào, tham số gì |
| C5 | **Toàn bộ màn hình để phẳng ở gốc `lib/`** | 8 file `.dart` lẫn với các thư mục; khó tìm khi dự án lớn |
| C6 | **Đặt tên không nhất quán** (`Location.dart`, `POISelectionScreen.dart` vs `home.dart`) | Sai quy ước Dart (snake_case cho tên file) |
| C7 | **Lỗi chính tả `ultils/`** | Nhỏ nhưng lộ ra khi trình bày báo cáo |
| C8 | **Commit rác**: `venv/`, `node_modules/`, `__pycache__/`, `backend.zip` | Repo nặng; `node_modules` trong dự án Python là thừa hoàn toàn |
| C9 | **`.env` có nhưng không dùng** | Dẫn đến hardcode mật khẩu database trong `main.py` (xem `Phan_Tich_Ky_Thuat_DoAnCu_va_Cai_Tien.md`, mục V1) |
| C10 | **Không có `tests/`** | Không kiểm thử tự động được |
| C11 | **Không có nơi chứa artifact ML** (`feature_list.json`, `scaler.pkl`) | Nguyên nhân gốc khiến backend phải hardcode công thức chuẩn hóa `(x+100)/100` |
| C12 | **Không có `docs/`** | Tài liệu thiết kế nằm rời rạc ngoài dự án |

---

## PHẦN 2 — CẤU TRÚC ĐỀ XUẤT CHO DỰ ÁN MỚI

Dự án mới khác đồ án cũ ở chỗ: thêm **Web Dashboard** bên cạnh app di động, đổi **MongoDB Atlas** sang CSDL quan hệ, và có **tầng ML độc lập** cần quản lý phiên bản.

> **Đối chiếu với bản đã dựng.** Cây thư mục dưới đây là bản đề xuất, giữ nguyên
> làm dấu vết quá trình. Tám chỗ đã làm khác đi:
>
> | Đề xuất | Đã dựng | Vì sao |
> |---|---|---|
> | `artifacts/model_x.pkl`, `model_y.pkl` | 5 tệp `model_<tên>.pkl` + `pipeline_manifest.json` | Mỗi mô hình một tệp để so sánh được. XGBoost vẫn huấn luyện riêng hai trục, nhưng `MultiOutputRegressor` gói cả hai vào một tệp |
> | PostgreSQL + `db_models/` 5 tệp | SQLite + `database.py` + `repository.py` | Không cần cài server, chạy được ngay trên máy chấm. Chỉ dựng 2 bảng thật cần thay vì 16. Kéo theo: bỏ `docker-compose.yml` và `migrations/` |
> | `frontend/` HTML5 + Tailwind, 7 trang | một `index.html`, JS thuần không thư viện ngoài | Bảy trang kia không trang nào có nội dung, mà dữ liệu chúng định hiện thì máy chủ chưa có endpoint. Bỏ CDN vì phòng bảo vệ có thể không ra được Internet |
> | `routers/models.py`, `routers/datasets.py` | đã xoá | Thuộc phần quản lý phiên bản mô hình, chưa làm |
> | `map.py` — `GET /map/{floor_id}` | `GET /map`, `GET /graph`, `POST /route` | Chỉ có một tầng; thêm đồ thị đi lại và chỉ đường |
> | `smoothing_service.py` — `PositionSmoother` (EMA) | `BoGop` (đồng thuận không gian) | Xem mục 2.4.1 của tài liệu thiết kế: 0,00 m thay vì kéo trung bình theo điểm lạc |
> | `ml/preprocess/` gói 8 tệp | `ml/preprocess.py` một tệp 358 dòng | 12 bước gọi tuần tự đúng một lần, tách tệp chỉ thêm chỗ phải nhảy qua lại |
> | `.env`: `API_KEY`, `SMOOTHING_ALPHA`, `MAX_JUMP_DISTANCE_M` | bỏ cả ba; thêm `CUA_SO_GOP` | API_KEY chưa dùng tới; hai tham số kia thuộc thiết kế EMA đã bỏ |

```
System_Indoor/                           # gốc dự án (git repository)
│
├── README.md                            # hướng dẫn cài đặt & chạy
├── .gitignore
├── .env.example                         # mẫu biến môi trường (commit được)
├── .env                                 # cấu hình thật (KHÔNG commit)
├── requirements.txt
├── docker-compose.yml                   # (tùy chọn) CSDL chạy local — đã bỏ, xem bảng đối chiếu
│
├── data/                                # dữ liệu — KHÔNG commit file lớn
│   ├── raw/
│   │   └── combined_data.csv            # dữ liệu thô 25.712 dòng
│   ├── processed/
│   │   ├── fingerprint_dataset_raw.csv    # trước chuẩn hoá, còn đơn vị dBm
│   │   └── fingerprint_dataset_sorted.csv # sau chuẩn hoá, đã sắp cột và dòng
│   ├── splits/
│   │   ├── train.csv
│   │   ├── validation.csv
│   │   └── test.csv
│   └── reference/
│       ├── reference_points.csv         # rp_id, x, y  (bắt buộc)
│       └── floor_plan.png               # ảnh sơ đồ mặt bằng
│
├── artifacts/                           # ★ HỢP ĐỒNG giữa ML và Backend
│   ├── feature_list.json                # thứ tự cột AP + missing_value
│   ├── scaler.pkl                       # scaler đã fit trên train
│   ├── model_<tên>.pkl                  # 5 mô hình đã huấn luyện
│   ├── model_metadata.json              # tham số, ngày train, dataset nguồn
│   └── pipeline_manifest.json           # tham số và thống kê của lần chạy pipeline
│
├── notebooks/                           # chạy trên Google Colab
│   ├── 01_data_exploration.ipynb
│   ├── 02_preprocessing_colab.ipynb
│   ├── 03_model_training.ipynb
│   ├── 04_evaluation.ipynb
│   └── colab_steps/                     # 12 file "từng cell copy vào Colab"
│
├── ml/                                  # mã nguồn ML tái sử dụng được
│   ├── __init__.py
│   ├── config.py                        # MIN_AP_PER_SCAN, MIN_APPEAR_RATE, HAMPEL_K...
│   ├── preprocess.py                    # cả 12 bước, xếp theo thứ tự pipeline gọi
│   ├── models/
│   │   ├── knn.py                       # baseline
│   │   ├── wknn.py                      # baseline
│   │   ├── random_forest.py             # so sánh
│   │   ├── xgboost_model.py             # mô hình chính
│   │   └── fingerprint_knn.py           # kNN vân tay Bray-Curtis
│   ├── evaluate.py                      # mean/median error, CDF 50/75/90
│   ├── postprocess.py                   # gộp nhiều lần quét, loại lần quét lạc
│   ├── audit.py                         # rà soát dữ liệu trước khi huấn luyện
│   ├── report.py                        # sinh biểu đồ cho báo cáo
│   ├── train.py                         # huấn luyện & so sánh mô hình
│   └── pipeline.py                      # chạy toàn bộ tiền xử lý bằng 1 lệnh
│
├── backend/
│   ├── main.py                          # chỉ khởi tạo app + đăng ký router
│   ├── config.py                        # Settings đọc từ biến môi trường
│   ├── database.py                      # kết nối CSDL (đã dựng: SQLite)
│   ├── schemas.py                       # Pydantic request/response
│   ├── dependencies.py                  # xác thực API key, DI
│   ├── routers/
│   │   ├── predict.py                   # POST /predict, WS /ws/location
│   │   ├── map.py                       # GET /map/{floor_id}
│   │   ├── models.py                    # GET /models, POST /models/{id}/activate
│   │   └── datasets.py                  # GET /datasets
│   ├── services/
│   │   ├── preprocessing_service.py     # FeatureMapper (ánh xạ BSSID)
│   │   ├── prediction_service.py        # Predictor (load model 1 lần)
│   │   ├── smoothing_service.py         # BoGop (đồng thuận không gian)
│   │   └── websocket_service.py         # ConnectionManager
│   ├── db_models/                       # SQLAlchemy ORM
│   │   ├── spatial.py                   # buildings, floors, floor_maps, reference_points
│   │   ├── wifi.py                      # devices, access_points, scans, scan_records
│   │   ├── dataset.py                   # fingerprint_datasets, features, splits
│   │   ├── ml.py                        # ml_models, evaluations
│   │   └── positioning.py               # sessions, predictions
│   └── migrations/                      # Alembic
│
├── frontend/                            # Web Dashboard (đã dựng: JS thuần)
│   ├── index.html
│   ├── pages/
│   │   ├── dashboard.html               # màn hình chính - realtime
│   │   ├── collection.html              # thu thập dữ liệu
│   │   ├── dataset.html                 # quản lý dataset
│   │   ├── models.html                  # huấn luyện & so sánh model
│   │   ├── evaluation.html              # biểu đồ CDF, bảng kết quả
│   │   ├── history.html                 # lịch sử di chuyển
│   │   └── settings.html
│   ├── src/
│   │   ├── js/
│   │   │   ├── api.js                   # gọi REST
│   │   │   ├── websocket.js             # kết nối realtime + tự reconnect
│   │   │   ├── map-renderer.js          # vẽ sơ đồ + marker
│   │   │   ├── coordinate.js            # quy đổi mét ↔ pixel
│   │   │   └── charts.js                # biểu đồ CDF
│   │   ├── css/
│   │   │   └── style.css
│   │   └── components/                  # thành phần dùng lại
│   │       ├── status-badge.js
│   │       ├── metric-card.js
│   │       └── data-table.js
│   └── assets/
│       ├── floor_plan.png
│       └── icons/
│
├── tests/
│   ├── test_preprocess.py
│   ├── test_feature_mapper.py           # ★ quan trọng nhất
│   └── test_smoothing.py
│
├── reports/                             # phục vụ viết báo cáo
│   ├── figures/                         # biểu đồ CDF, heatmap lỗi
│   └── tables/                          # bảng so sánh model
│
└── docs/
    ├── Phan_Tich_Thiet_Ke_He_Thong.md
    ├── Phan_Tich_Ky_Thuat_DoAnCu_va_Cai_Tien.md
    └── Cau_Truc_Thu_Muc_Du_An.md
```

### Cây thư mục THỰC TẾ (tính tới 03/09/2026)

Đây là những gì git đang theo dõi — 226 tệp đã commit cộng 9 tệp mới chưa
commit, khoảng 12 MB.

```
System_Indoor/
├── README.md  .gitignore  .gitattributes  .env.example  requirements.txt
│
├── data/
│   ├── raw/combined_data.csv            # 25.712 dòng RSSI thô, KHÔNG sinh lại được
│   ├── processed/fingerprint_dataset_sorted.csv
│   ├── splits/                          # sinh bằng pipeline, không commit
│   └── reference/
│       ├── reference_points.csv         # 44 điểm, 10 cột (toạ độ + nhãn + mô tả)
│       ├── reference_points_template.csv
│       ├── Map.png                      # sơ đồ mặt bằng do CTK45 số hoá
│       └── ban_do_tang1.json            # hình học trích từ Map.png
│
├── artifacts/                           # ★ HỢP ĐỒNG giữa ML và Backend
│   ├── feature_list.json  model_metadata.json  pipeline_manifest.json
│   └── (scaler.pkl, model_*.pkl — sinh lại được nên không commit)
│
├── notebooks/                           # Colab: 2 notebook + 12 bước tiền xử lý
│
├── ml/
│   ├── config.py  preprocess.py  pipeline.py  train.py
│   ├── evaluate.py  postprocess.py  report.py  audit.py
│   ├── danh_gia_cheo.py                 # giao thức bỏ trọn một điểm tham chiếu
│   └── models/  knn.py  wknn.py  xgboost_model.py  random_forest.py
│                fingerprint_knn.py
│
├── backend/
│   ├── main.py  config.py  database.py  repository.py  schemas.py
│   ├── dependencies.py
│   ├── routers/    predict.py  map.py
│   └── services/   preprocessing_service.py  prediction_service.py
│                   smoothing_service.py  routing_service.py
│                   websocket_service.py
│
├── frontend/                            # Web Dashboard, JS thuần
│   ├── index.html
│   └── src/  js/{api,websocket,map-renderer,coordinate,charts,dashboard}.js
│             css/style.css
│             components/{status-badge,metric-card,data-table}.js
│
├── mobile/                              # NGOÀI đề cương — xem mobile/README.md
│   ├── lib/  services/  data/  screens/  widgets/  theme/  l10n/
│   ├── assets/  map/Map.png  images/ (37 ảnh, 11 thư mục)
│   └── test/                            # 101 bài
│
├── tools/                               # chạy một lần rồi commit kết quả
│   ├── trich_ban_do.py                  # Map.png → ban_do_tang1.json
│   ├── sinh_khu_vuc.py                  # CSV → khu_vuc_thu_vien.dart
│   ├── ve_ban_ve.py                     # bản vẽ tầng 1 cho báo cáo
│   └── ve_khoi_nha.py                   # sơ đồ khối nhìn từ trên cao
│
├── tests/                               # 160 bài
│   ├── test_preprocess.py  test_feature_mapper.py  test_postprocess.py
│   ├── test_train.py  test_api.py  test_route.py
│   └── test_luu_tru.py  test_dashboard.py  test_khu_vuc.py
│       test_danh_gia_cheo.py
│
├── reports/  figures/ (14 biểu đồ)  tables/ (4 bảng)
└── docs/     3 tài liệu .md + frame thiết kế
```

Đợt dọn ngày 02/09 đã xoá hẳn phần thừa của thiết kế cũ: hai thư mục rỗng
`backend/migrations/` (Alembic, bỏ cùng PostgreSQL) và `frontend/assets/icons/`
(Dashboard không dùng tệp icon nào); hai notebook `01_data_exploration.ipynb`
cùng `04_evaluation.ipynb` không có ô nào, việc của chúng nay nằm ở
`ml/audit.py`, `ml/evaluate.py` và `ml/report.py`; và `docs/uxui.jpg` là bản
xuất raster của chính `ips-dlu-screens-v4.svg` đang giữ, nặng gấp ba lần mà
không tệp nào tham chiếu.

---

## PHẦN 3 — GIẢI THÍCH CÁC QUYẾT ĐỊNH THIẾT KẾ

### 3.1. `artifacts/` — thư mục quan trọng nhất

Đây là **hợp đồng dữ liệu** giữa tầng ML và tầng Backend, và là thứ đồ án cũ hoàn toàn không có (vấn đề C11).

```
notebooks/  →  artifacts/  →  backend/services/preprocessing_service.py
 (train)       (contract)              (predict)
```

Toàn bộ tham số tiền xử lý được ghi vào `feature_list.json` lúc huấn luyện, backend đọc lại y nguyên lúc dự đoán:

```json
{
  "ap_columns": ["88:dc:97:12:62:c6", "88:dc:97:12:62:c7", "..."],
  "feature_count": 36,
  "missing_rssi_value": -96.0,
  "min_ap_per_scan": 6,
  "min_appear_rate": 0.20
}
```

Nhờ vậy backend **không bao giờ phải hardcode** công thức như `(x + 100) / 100` của đồ án cũ.

### 3.2. Tách `data/` thành 4 tầng

| Thư mục | Nội dung | Commit? |
|---|---|---|
| `raw/` | Dữ liệu thô, không bao giờ sửa | ❌ (nặng) |
| `processed/` | Kết quả sau tiền xử lý | ❌ (sinh lại được) |
| `splits/` | train/validation/test | ❌ (sinh lại được) |
| `reference/` | Tọa độ RP, sơ đồ mặt bằng | ✅ (nhỏ, không sinh lại được) |

Nguyên tắc: **chỉ commit thứ không thể sinh lại bằng code**. `reference_points.csv` là số liệu đo đạc thực tế → phải commit. `train.csv` sinh ra từ pipeline → không commit.

### 3.3. `ml/` tách khỏi `notebooks/`

Notebook dùng để **khám phá và trình bày**; `ml/` chứa mã **tái sử dụng được**. Notebook chỉ nên gọi hàm:

```python
from ml.pipeline import run_preprocessing
fingerprint, meta = run_preprocessing("data/raw/combined_data.csv")
```

Tránh tình trạng logic bị kẹt trong ô notebook, không chạy lại được ngoài Colab (vấn đề C1 của đồ án cũ).

### 3.4. `backend/db_models/` thay vì `backend/models/`

Đặt tên `db_models/` để **không nhầm với model học máy**. Đồ án cũ dùng `model/` cho model ML còn Flutter dùng `models/` cho data class — gây nhầm lẫn khi trao đổi trong nhóm.

### 3.5. Backend tách `routers/` và `services/`

- `routers/` — chỉ nhận request, gọi service, trả response (mỏng).
- `services/` — chứa logic nghiệp vụ, **không phụ thuộc FastAPI** nên test được độc lập.

Khắc phục vấn đề C-"toàn bộ logic dồn vào `main.py`" của đồ án cũ.

### 3.6. `tests/test_feature_mapper.py` là bài test bắt buộc

Đây là điểm sinh lỗi nghiêm trọng nhất (xem vấn đề V2 trong tài liệu phân tích kỹ thuật). Test tối thiểu:

```python
def test_ap_la_khong_lam_lech_thu_tu_cot():
    """AP không có trong feature_list phải bị bỏ qua, không đẩy lệch các cột khác."""
    mapper = FeatureMapper("artifacts/feature_list.json", "artifacts/scaler.pkl")
    scan = [
        {"bssid": "88:dc:97:12:62:c6", "rssi": -57},
        {"bssid": "ff:ff:ff:ff:ff:ff", "rssi": -80},   # AP lạ
    ]
    vector = mapper.transform(scan)
    assert vector[0][mapper.index["88:dc:97:12:62:c6"]] != mapper.missing_value

def test_thieu_ap_thi_bao_loi():
    """Quét được quá ít AP đã biết phải báo lỗi, không dự đoán bừa."""
    mapper = FeatureMapper(...)
    with pytest.raises(ValueError):
        mapper.transform([{"bssid": "88:dc:97:12:62:c6", "rssi": -57}])
```

---

## PHẦN 4 — CÁC FILE CẤU HÌNH KÈM THEO

Trước đây phần này chép nguyên nội dung `.gitignore`, `.env.example`,
`requirements.txt` và khung `README.md`. Bỏ đi vì bản chép đã lệch khỏi bản
thật: doc còn giữ 7 dòng `.gitignore` không còn tồn tại (kể cả dạng chú thích
cùng dòng vốn là lỗi đã sửa — git không hiểu nó là chú thích), và liệt kê
`alembic`, `asyncpg`, `seaborn`, `websockets` vốn không hề cài, trong khi thiếu
`aiosqlite` đang dùng thật.

Đọc thẳng bản thật ở gốc kho: `.gitignore`, `.env.example`, `requirements.txt`,
`README.md`.

---

## PHẦN 5 — THỨ TỰ TẠO THƯ MỤC VÀ CÁCH ĐÁNH SỐ GIAI ĐOẠN

Không cần tạo hết ngay từ đầu. Theo đúng tiến độ trong đề cương.

**Bảng này là cách đánh số giai đoạn CHUẨN của dự án** — nói "giai đoạn 4" là nói
`frontend/`. `roadmap.md` từng đánh số khác (giai đoạn 4 là ứng dụng Flutter) và
đã sửa lại theo bảng này ngày 07/09/2026. Chốt ở đây vì đây là bảng duy nhất ánh
xạ giai đoạn sang mốc thời gian của đề cương.

Đừng lẫn với bảng "Nhóm bảng ưu tiên triển khai theo giai đoạn" ở mục 2.5 của
`Phan_Tich_Thiet_Ke_He_Thong.md` — bảng đó đánh số thứ tự dựng **bảng CSDL**, là
một trục khác.

| Giai đoạn | Tạo | Mốc đề cương |
|---|---|---|
| 1 | `data/`, `notebooks/`, `ml/preprocess.py`, `artifacts/` | 20/08 – 31/08 (tiền xử lý) |
| 2 | `ml/models/`, `ml/evaluate.py`, `reports/` | 01/09 – 15/10 (huấn luyện & đánh giá) |
| 3 | `backend/` toàn bộ, `tests/` | 16/10 – 31/10 (backend) |
| 4 | `frontend/` | 01/11 – 10/11 (dashboard) |
| 5 | `docs/`, `README.md` hoàn chỉnh | 11/11 – 24/11 (hoàn thiện) |

Riêng `.gitignore` và `.env.example` nên tạo **ngay từ ngày đầu** — để tránh lặp lại sự cố lộ mật khẩu database như đồ án cũ.

---

## PHẦN 6 — BẢNG TÓM TẮT CẢI TIẾN

| Vấn đề cũ | Cải tiến |
|---|---|
| C1 — Không có tầng ML trong dự án | Thêm `ml/` + `notebooks/`, logic tái lập được |
| C2 — Dataset trong `assets/` app | Tách hẳn sang `data/`, phân 4 tầng theo vòng đời |
| C3 — Model trùng lặp 2 nơi | Một nguồn duy nhất: `artifacts/` |
| C4 — Model không đánh phiên bản | `model_metadata.json` + bảng `ml_models` trong DB |
| C5 — Màn hình để phẳng ở gốc | `frontend/pages/` tách theo màn hình |
| C6 — Tên file không nhất quán | Thống nhất snake_case toàn bộ |
| C7 — Lỗi chính tả `ultils/` | `src/js/`, `src/components/` |
| C8 — Commit rác | `.gitignore` đầy đủ ngay từ đầu |
| C9 — `.env` không dùng | `config.py` với `pydantic-settings`, có `.env.example` |
| C10 — Không có test | `tests/`, ưu tiên `test_feature_mapper.py` |
| C11 — Không có nơi chứa artifact ML | `artifacts/` là hợp đồng ML ↔ Backend |
| C12 — Không có tài liệu trong dự án | `docs/` chứa toàn bộ tài liệu thiết kế |
