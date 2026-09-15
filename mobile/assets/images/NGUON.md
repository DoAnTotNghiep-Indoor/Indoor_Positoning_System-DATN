# Nguồn ảnh

Hai nguồn, ghi tách bạch vì một bên là dữ liệu kế thừa:

| Thư mục | Số ảnh | Nguồn |
|---|---:|---|
| 11 thư mục còn lại | 37 | **Nhóm CTK45** chụp tại Thư viện ĐH Đà Lạt, lấy từ nhánh `Backup` của kho `github.com/NgocSongNe/IPS` |
| `wc/` | 2 | **Nhóm 15** chụp ngày 07/09/2026 |

`wc/1.webp` là nhà vệ sinh phía TV 3,4 (RP43, x = −42); `wc/2.webp` là phía căn tin
(RP42, x = +42) — đánh số theo thứ tự trái sang phải trên sơ đồ.

Tên thư mục giữ nguyên như bản gốc vì nó khớp đúng cột `thu_muc_anh` trong
`data/reference/reference_points.csv` — nhờ vậy `GET /map` trả về tên thư mục là
ứng dụng biết lấy ảnh nào mà không cần một bảng tra thứ hai.

## Xử lý trước khi đưa vào kho mã

Bản gốc 1920×2560, tổng 24,9 MB. Đã thu nhỏ về cạnh dài 1024 px, JPEG chất
lượng 80, progressive:

```python
im = Image.open(f).convert("RGB")
im.thumbnail((1024, 1024), Image.LANCZOS)
im.save(p, "JPEG", quality=80, optimize=True, progressive=True)
```

Kết quả **4,0 MB**, trung bình 106 KB mỗi ảnh. Ảnh dọc sau khi thu còn
768×1024 — vẫn thừa nét cho ô ảnh cao 164 đơn vị trên màn Chi tiết, kể cả ở
mật độ điểm ảnh 3x.

Hai ảnh trong `wc/` cũng thu về 768×1024 chất lượng 80 (từ bản gốc 960×1280,
mỗi tấm còn ~57 KB) nhưng mã hoá baseline chứ không progressive — khác biệt này
chỉ nằm ở cách nén, không đổi kích thước hay chất lượng hiển thị. Đã kiểm cả hai
tấm sau khi xử lý: **không còn trường EXIF nào, không có GPS** — quan trọng vì
đây là ảnh chụp bằng điện thoại và kho mã này công khai.

`convert("RGB")` cũng gỡ luôn mọi khối metadata. Đã kiểm tra bản gốc: không tấm
nào có EXIF hay toạ độ GPS, nhưng kho mã này là kho **công khai** nên vẫn ghi
lại để lần sau ai thêm ảnh còn biết phải kiểm.

Ngày 15/09/2026 đổi cả 39 ảnh sang WebP chất lượng 80 (`im.save(p, "WEBP",
quality=80, method=6)`), cùng kích thước, không metadata: 4,06 → 2,58 MB để
APK nhẹ hơn.

## Đánh số

Đổi tên thành `1.webp`, `2.webp`, … theo thứ tự tệp gốc. `lib/data/anh_khu_vuc.dart`
giữ số lượng ảnh mỗi thư mục và dựng đường dẫn từ đó.
