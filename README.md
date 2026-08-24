# Hệ thống định vị trong nhà bằng WiFi Fingerprinting

Đồ án tốt nghiệp — Nhóm 15, Khoa Công nghệ Thông tin, Trường Đại học Đà Lạt.
GVHD: TS. Nguyễn Thị Lương.

Nghiên cứu hệ thống định vị trong nhà bằng kỹ thuật WiFi Fingerprinting và xây dựng
Web Dashboard hiển thị vị trí người dùng theo thời gian thực.

## Bài toán

- **Input**: vector cường độ tín hiệu RSSI từ các Access Point `[AP_1, ..., AP_n]`
- **Output**: tọa độ người dùng `(x, y)` theo đơn vị mét
- **Đánh giá**: `error = sqrt((x_pred - x_true)² + (y_pred - y_true)²)`

Mô hình chính: **XGBoost Regression**. Mô hình cơ sở đối chứng: kNN, WKNN.

## Cài đặt

```bash
python -m venv venv
venv\Scripts\activate           # Windows
pip install -r requirements.txt
copy .env.example .env          # rồi điền thông tin thật
alembic upgrade head
```

## Chạy

```bash
# Backend
uvicorn backend.main:app --reload

# Frontend
python -m http.server 5500 --directory frontend

# Pipeline tiền xử lý dữ liệu
python -m ml.pipeline
```

## Cấu trúc thư mục

| Thư mục | Nội dung |
|---|---|
| `data/` | Dữ liệu thô, đã xử lý, tập chia, và số liệu đo đạc tham chiếu |
| `artifacts/` | **Hợp đồng giữa ML và Backend**: `feature_list.json`, `scaler.pkl`, model |
| `notebooks/` | Notebook chạy trên Google Colab |
| `ml/` | Mã nguồn tiền xử lý và huấn luyện, tái sử dụng được |
| `backend/` | FastAPI + WebSocket + PostgreSQL |
| `frontend/` | Web Dashboard (HTML5 + Tailwind CSS) |
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

## Tài liệu

- `docs/Phan_Tich_Thiet_Ke_He_Thong.md` — phân tích & thiết kế hệ thống
- `docs/Phan_Tich_Ky_Thuat_DoAnCu_va_Cai_Tien.md` — phân tích đồ án kế thừa và cải tiến
- `docs/Cau_Truc_Thu_Muc_Du_An.md` — cấu trúc thư mục
