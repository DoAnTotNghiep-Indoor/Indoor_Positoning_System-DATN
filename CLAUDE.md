# Cách làm việc với repo IPS

Đồ án tốt nghiệp: định vị trong nhà bằng WiFi Fingerprinting, tầng 1 Thư viện ĐH Đà Lạt.
Tổng quan hệ thống ở `README.md`, thiết kế ở `docs/thiet_ke_he_thong.md`.

## Nhật ký

- `STATE.md` là nhật ký nội bộ, không nằm trong git, nên có máy không có tệp này. Nếu có thì đọc đầu phiên;
  khi mâu thuẫn với chỗ khác thì `STATE.md` đúng.
- Xong một việc đáng kể thì thêm một mục có ngày vào `STATE.md` (nếu có): làm gì, cách làm, số liệu, quyết
  định và lý do. Nhật ký dùng để viết báo cáo, nên viết ở mức người đọc báo cáo hiểu được; không ghi diff
  hay tên hàm đã sửa.
- Không tạo tài liệu rời mới khi không cần thiết. Ghi vào README, `docs/thiet_ke_he_thong.md` hoặc `STATE.md`.

## Git

- Chỉ dùng nhánh `main`, commit thẳng lên đó, không tạo nhánh phụ.
- Chỉ commit khi được yêu cầu.
- `STATE.md` và `deprecated/bao_cao_lan1/` là tài liệu nội bộ, không đưa vào git. `CLAUDE.md` có trong git
  để mọi agent làm việc giống nhau; sẽ bỏ ra khi nộp mã nguồn.

## Code

- Ưu tiên ít dòng và đơn giản. Bỏ code chết, nhánh dự phòng không bao giờ chạy, tham số không ai truyền.
- Không giữ tương thích ngược. Dự án đang xây dựng: đổi tên khoá, đổi định dạng thì sửa luôn mọi nơi dùng.
- Không xử lý ca biên quá gắt (inf/NaN, chuỗi 100.000 ký tự, toạ độ ngoài trái đất...). Chỉ kiểm những gì
  dữ liệu thật hoặc client thật có thể gửi.
- Chú thích chỉ ghi lý do không hiển nhiên, cạm bẫy, nguồn của một con số. Không nhắc lại điều code đã nói,
  không kể lịch sử ("trước đây...", "bản cũ...").
- Test gọn: gộp ca giống nhau bằng `parametrize`, không docstring kể chuyện sửa lỗi.
- Khi báo số liệu (sai số, thời gian, số dòng...) thì chạy để đo, không lấy từ tài liệu cũ.

## Tài liệu

- Viết theo hệ thống có gì, làm được gì, hoạt động thế nào, kết quả và hạn chế.
- Không viết theo kiểu "theo đề cương...", không kể lại trạng thái hay quá trình, không so sánh với đồ án cũ
  CTK45 (chỉ một mục nhỏ "cải tiến" khi cần).
- Tiếng Việt, câu ngắn, số kèm đơn vị.
- Tài liệu cũ còn giá trị để viết báo cáo thì chuyển vào `deprecated/`, ghi vào `deprecated/README.md`.

## Quy ước kỹ thuật cần nhớ

- **Đơn vị**: toạ độ và mọi bảng trong `reports/tables/` theo đơn vị lưới; 1 đơn vị = 0,3508 m. Tài liệu và
  slide luôn quy ra mét.
- **Mô hình triển khai**: Dynamic-k kNN (tiếng Việt: kNN k động), định danh code `fingerprint_knn_dong`,
  chỉ định bằng `MO_HINH_TRIEN_KHAI` trong `ml/config.py`.
- **Dữ liệu**: đợt A (802 lần quét, 1 máy) + đợt B (2.349, 3 máy) của CTK45. Dữ liệu Redmi của nhóm
  (`data/raw/nhom15_2026/`) chưa dùng.
- **Ba giao thức đánh giá**: chia ngẫu nhiên 10 seed, bỏ trọn một điểm, khác đợt đo. Luôn nêu giao thức đi
  kèm con số.
- Không dùng WebSocket: client gửi `POST /predict`, Dashboard hỏi `GET /predictions` định kỳ.
- Ứng dụng chỉ làm Android (Flutter). Nguyên tắc giao diện: kính chỉ cho phần nổi (thanh điều hướng, nút
  lọc, nhãn vị trí), nội dung nền đặc tương phản cao, font Inter, định vị luôn bật, một popup cho mọi khu vực.
  Thiết kế trên Figma: https://www.figma.com/design/3dzSOBhBIhb3e9zkuWOiQS

## Lệnh thường dùng

```bash
venv/Scripts/python -m pytest tests -q                  # test backend
DEMO=true venv/Scripts/python -m uvicorn backend.main:app --host 0.0.0.0   # máy chủ phát lại quét thật
venv/Scripts/python -m ml.pipeline && venv/Scripts/python -m ml.train      # tiền xử lý và huấn luyện
cd mobile && flutter analyze && flutter test && flutter build apk --debug
```

Máy test Android: vivo X300 qua adb không dây. Đo hiệu năng app bằng bản release hoặc profile, không bằng
bản debug.
