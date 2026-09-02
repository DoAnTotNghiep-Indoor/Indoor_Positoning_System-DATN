# Nguồn ảnh

37 ảnh trong 11 thư mục dưới đây do **nhóm CTK45** chụp tại Thư viện Đại học Đà
Lạt, lấy từ nhánh `Backup` của kho `github.com/NgocSongNe/IPS`
(`assets/images/`). Đây là dữ liệu kế thừa, không phải ảnh nhóm mình chụp.

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

`convert("RGB")` cũng gỡ luôn mọi khối metadata. Đã kiểm tra bản gốc: không tấm
nào có EXIF hay toạ độ GPS, nhưng kho mã này là kho **công khai** nên vẫn ghi
lại để lần sau ai thêm ảnh còn biết phải kiểm.

## Đánh số

Đổi tên thành `1.jpg`, `2.jpg`, … theo thứ tự tệp gốc. `lib/data/anh_khu_vuc.dart`
giữ số lượng ảnh mỗi thư mục và dựng đường dẫn từ đó; `test/anh_khu_vuc_test.dart`
đối chiếu con số ấy với `AssetManifest` để hai nơi không lệch nhau.
