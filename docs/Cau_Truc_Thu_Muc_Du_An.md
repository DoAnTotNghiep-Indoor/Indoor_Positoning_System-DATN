# Cấu trúc thư mục dự án — Phân tích cấu trúc cũ và đề xuất cải tiến

Tài liệu này phân tích cấu trúc thư mục của đồ án cũ (`DATN_CTK45_IPS.pdf`, Chương 4.1, Hình 11–12) và đề xuất cấu trúc mới cho đồ án kế thừa của Nhóm 15.

---

## PHẦN 1 — CẤU TRÚC THƯ MỤC ĐỒ ÁN CŨ

### 1.1. Frontend (Flutter) — Hình 11

```
IPS_APP/
├── android/
│   ├── .gradle/
│   ├── app/
│   │   ├── src/
│   │   └── build.gradle
│   ├── gradle/wrapper/
│   │   ├── gradle-wrapper.jar
│   │   └── gradle-wrapper.properties
│   ├── .gitignore
│   ├── build.gradle
│   ├── flutter_application_1_android.iml
│   ├── gradle.properties
│   ├── gradlew / gradlew.bat
│   ├── local.properties
│   └── settings.gradle
├── assets/
│   ├── geojson/
│   ├── icon/
│   ├── images/
│   ├── model/                       ← model trùng lặp với backend
│   ├── avt_st.jpg
│   ├── canteen.jpg
│   ├── combined_data_sorted.csv     ← DATASET nằm trong app!
│   ├── info_desk.jpg
│   ├── LibDLU.jpg
│   ├── magazine_room.jpg
│   └── main_entrance.jpg
├── ips/                             ← mục đích không rõ
└── lib/
    ├── controller/
    ├── models/
    ├── services/
    ├── ultils/                      ← lỗi chính tả (utils)
    ├── account.dart
    ├── home.dart
    ├── information.dart
    ├── Location.dart                ← PascalCase
    ├── main.dart
    ├── POISelectionScreen.dart      ← PascalCase
    ├── tutorial_overlay.dart
    └── welcome_screen.dart
```

### 1.2. Backend (FastAPI) — Hình 12

```
BACKEND/
├── __pycache__/                     ← cache Python, không nên commit
├── model/
│   ├── model.tflite                 ← không rõ khác nhau gì
│   └── model2.tflite
├── node_modules/                    ← thư viện Node.js trong dự án Python
├── venv/                            ← môi trường ảo, không nên commit
├── .env                             ← tồn tại nhưng KHÔNG được dùng
├── backend.zip                      ← file nén commit chung mã nguồn
├── convertcsv_to_json_value.py
├── example.json
├── main.py                          ← toàn bộ logic dồn vào 1 file
├── package-lock.json
├── package.json
└── requirements.txt
```

### 1.3. Các vấn đề của cấu trúc cũ

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

Dự án mới khác đồ án cũ ở chỗ: **Web Dashboard** thay cho mobile app, **PostgreSQL** thay cho MongoDB, và có **tầng ML độc lập** cần quản lý phiên bản.

```
System_Indoor/                           # gốc dự án (git repository)
│
├── README.md                            # hướng dẫn cài đặt & chạy
├── .gitignore
├── .env.example                         # mẫu biến môi trường (commit được)
├── .env                                 # cấu hình thật (KHÔNG commit)
├── requirements.txt
├── docker-compose.yml                   # (tùy chọn) PostgreSQL chạy local
│
├── data/                                # dữ liệu — KHÔNG commit file lớn
│   ├── raw/
│   │   └── combined_data.csv            # dữ liệu thô 25.712 dòng
│   ├── processed/
│   │   ├── fingerprint_dataset.csv
│   │   └── fingerprint_dataset_sorted.csv
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
│   ├── model_x.pkl                      # XGBoost dự đoán x
│   ├── model_y.pkl                      # XGBoost dự đoán y
│   └── model_metadata.json              # tham số, ngày train, dataset nguồn
│
├── notebooks/                           # chạy trên Google Colab
│   ├── 01_data_exploration.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
│
├── ml/                                  # mã nguồn ML tái sử dụng được
│   ├── __init__.py
│   ├── config.py                        # MIN_AP_PER_SCAN, MIN_APPEAR_RATE, ALPHA...
│   ├── preprocess/
│   │   ├── __init__.py
│   │   ├── load.py                      # bước 1–2: đọc & gom scan
│   │   ├── pivot.py                     # bước 3–4: pivot & ghép tọa độ
│   │   ├── filter.py                    # bước 5–6: lọc AP & lọc mẫu
│   │   ├── missing.py                   # bước 7: missing value động
│   │   ├── denoise.py                   # bước 8: Hampel filter (MAD)
│   │   ├── split.py                     # bước 9: chia train/val/test
│   │   └── scale.py                     # bước 10–11: chuẩn hóa & xuất
│   ├── models/
│   │   ├── knn.py                       # baseline
│   │   ├── wknn.py                      # baseline
│   │   ├── random_forest.py             # so sánh
│   │   └── xgboost_model.py             # mô hình chính
│   ├── evaluate.py                      # mean/median error, CDF 50/75/90
│   └── pipeline.py                      # chạy toàn bộ bằng 1 lệnh
│
├── backend/
│   ├── main.py                          # chỉ khởi tạo app + đăng ký router
│   ├── config.py                        # Settings đọc từ biến môi trường
│   ├── database.py                      # kết nối PostgreSQL
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
│   │   ├── smoothing_service.py         # PositionSmoother (EMA)
│   │   └── websocket_service.py         # ConnectionManager
│   ├── db_models/                       # SQLAlchemy ORM
│   │   ├── spatial.py                   # buildings, floors, floor_maps, reference_points
│   │   ├── wifi.py                      # devices, access_points, scans, scan_records
│   │   ├── dataset.py                   # fingerprint_datasets, features, splits
│   │   ├── ml.py                        # ml_models, evaluations
│   │   └── positioning.py               # sessions, predictions
│   └── migrations/                      # Alembic
│
├── frontend/                            # Web Dashboard (HTML5 + Tailwind)
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

### 4.1. `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
venv/
.venv/
env/
*.egg-info/

# Bí mật — TUYỆT ĐỐI không commit
.env
*.key
credentials.json

# Dữ liệu lớn (sinh lại được bằng pipeline)
data/raw/
data/processed/
data/splits/
*.csv
!data/reference/*.csv          # NGOẠI LỆ: tọa độ RP phải commit

# Artifact model (nặng, sinh lại được)
artifacts/*.pkl
artifacts/*.joblib
!artifacts/feature_list.json   # NGOẠI LỆ: file nhỏ, là hợp đồng dữ liệu
!artifacts/model_metadata.json

# Node / build
node_modules/
dist/
build/

# IDE / OS
.vscode/
.idea/
.DS_Store
Thumbs.db

# Nén
*.zip
*.rar
```

### 4.2. `.env.example` (commit được — làm mẫu cho cả nhóm)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://ips_user:CHANGE_ME@localhost:5432/ips_dlu

# Bảo mật
API_KEY=CHANGE_ME_random_string
ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5500"]

# Đường dẫn artifact
MODEL_DIR=artifacts

# Tham số hậu xử lý
SMOOTHING_ALPHA=0.3
MAX_JUMP_DISTANCE_M=5.0
RESET_AFTER_SECONDS=30
```

### 4.3. `requirements.txt` (ghim phiên bản để tái lập được)

```
# Backend
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
pydantic-settings==2.6.0
sqlalchemy==2.0.36
asyncpg==0.30.0
alembic==1.14.0
websockets==13.1

# Machine Learning
numpy==2.1.3
pandas==2.2.3
scikit-learn==1.5.2
xgboost==2.1.2
joblib==1.4.2

# Trực quan hóa (dùng khi viết báo cáo)
matplotlib==3.9.2
seaborn==0.13.2

# Kiểm thử
pytest==8.3.3
httpx==0.27.2
```

> Ghi chú: đồ án cũ để `requirements.txt` không ghim phiên bản (`fastapi`, `tensorflow`, `numpy`...). Khi thư viện cập nhật, dự án có thể chạy sai hoặc không chạy được nữa — rủi ro thật khi bảo vệ đồ án cách thời điểm code vài tháng.

### 4.4. `README.md` (khung)

```markdown
# Hệ thống định vị trong nhà bằng WiFi Fingerprinting

## Cài đặt
1. `python -m venv venv && venv\Scripts\activate`
2. `pip install -r requirements.txt`
3. `copy .env.example .env` rồi điền thông tin thật
4. `alembic upgrade head`

## Chạy
- Backend: `uvicorn backend.main:app --reload`
- Frontend: mở `frontend/index.html` (hoặc `python -m http.server 5500`)
- Tiền xử lý: `python -m ml.pipeline`

## Cấu trúc
Xem `docs/Cau_Truc_Thu_Muc_Du_An.md`
```

---

## PHẦN 5 — ÁNH XẠ CÁC FILE HIỆN CÓ VÀO CẤU TRÚC MỚI

Các file bạn đã làm sẽ chuyển vào đâu:

| File hiện tại | Vị trí mới |
|---|---|
| `D:\Nam5\DATN\combined_data.csv` | `data/raw/combined_data.csv` |
| `D:\Nam5\DATN\fingerprint_dataset.csv` | `data/processed/fingerprint_dataset.csv` |
| `System_Indoor\preprocess_steps\docdulieu_1.py` → `gomscan_2.py` | `ml/preprocess/load.py` |
| `pivotdulieu_3.py` → `ghepToaDo_4.py` | `ml/preprocess/pivot.py` |
| `locAP_5.py` → `loaibomau_6.py` | `ml/preprocess/filter.py` |
| `missRSSI_7.py` | `ml/preprocess/missing.py` |
| `locnhieu_8.py` | `ml/preprocess/denoise.py` |
| `chiadulieu_9.py` | `ml/preprocess/split.py` |
| `chuanhoa_10.py` → `xuatketqua_11.py` → `sapxep_12.py` | `ml/preprocess/scale.py` |
| `01_preprocess_colab.ipynb` | `notebooks/02_preprocessing.ipynb` |
| `reference_points_template.csv` | `data/reference/reference_points.csv` (sau khi điền đủ) |
| `layout_tool_click_toado.py` | `notebooks/tools/` hoặc `ml/tools/` |
| `Phan_Tich_Thiet_Ke_He_Thong.md` | `docs/` |
| `Phan_Tich_Ky_Thuat_DoAnCu_va_Cai_Tien.md` | `docs/` |

> **Lưu ý về nhóm file `preprocess_steps/`**: các file này được viết theo dạng "từng cell copy vào Colab" nên dùng biến toàn cục (`df`, `fingerprint`, `ap_cols_selected`) chảy qua các bước. Khi chuyển sang `ml/preprocess/`, cần bọc lại thành hàm có tham số vào/ra rõ ràng để test được, ví dụ:
>
> ```python
> # ml/preprocess/denoise.py
> def hampel_filter(df: pd.DataFrame, ap_cols: list[str],
>                   group_col: str = "rp_id", k: float = 3.0) -> pd.DataFrame:
>     ...
>     return df
> ```
>
> Giữ nguyên bản Colab để chạy thử nhanh, đồng thời có bản module hóa để đưa vào dự án — không mâu thuẫn nhau.

---

## PHẦN 6 — THỨ TỰ TẠO THƯ MỤC

Không cần tạo hết ngay từ đầu. Theo đúng tiến độ trong đề cương:

| Giai đoạn | Tạo | Mốc đề cương |
|---|---|---|
| 1 | `data/`, `notebooks/`, `ml/preprocess/`, `artifacts/` | 20/08 – 31/08 (tiền xử lý) |
| 2 | `ml/models/`, `ml/evaluate.py`, `reports/` | 01/09 – 15/10 (huấn luyện & đánh giá) |
| 3 | `backend/` toàn bộ, `tests/` | 16/10 – 31/10 (backend) |
| 4 | `frontend/` | 01/11 – 10/11 (dashboard) |
| 5 | `docs/`, `README.md` hoàn chỉnh | 11/11 – 24/11 (hoàn thiện) |

Riêng `.gitignore` và `.env.example` nên tạo **ngay từ ngày đầu** — để tránh lặp lại sự cố lộ mật khẩu database như đồ án cũ.

---

## PHẦN 7 — BẢNG TÓM TẮT CẢI TIẾN

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
