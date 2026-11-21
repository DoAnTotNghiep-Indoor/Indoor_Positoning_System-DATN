# Nguồn ảnh

Hai nguồn, ghi tách bạch vì một bên là dữ liệu kế thừa:

| Ảnh | Nguồn |
|---|---|
| Mọi ảnh không nêu dưới đây | **Nhóm CTK45** chụp tại Thư viện ĐH Đà Lạt, lấy từ nhánh `Backup` của kho `github.com/NgocSongNe/IPS` |
| `wc_trai/1`, `wc_phai/1` | **Nhóm 15**, 07/09/2026 |
| `wc_trai/2`, `wc_phai/2`, `tv3_4/1–2`, `can_tin/3`, `ban_thu_thu/4`, `cua_chinh/3`, toàn bộ `hoc_nhom/`, `nghiep_vu_1/`, `thang_may/`, `xuong_tv1_2/`, `nha_sach/` | **Nhóm 15**, vivo X300, 18/11/2026 |
| `../panorama/` (5 ảnh toàn cảnh 360° ngang) | **Nhóm 15**, chụp bằng Google Camera, 18/11/2026 |

Ngày 18/11/2026 cũng bỏ `khu_vuc_tu_hoc/5` (trùng khít `khu_vuc_doc/3`) và hai ảnh sự kiện đông
người, thấy rõ mặt, của `hoi_truong_thu_vien`. Ảnh gốc của nhóm 15 có toạ độ GPS trong EXIF;
`python -m tools.anh_app` ghi lại không metadata (đã kiểm: không tệp nào còn EXIF).

Cũng từ 18/11/2026 mọi ảnh là **AVIF chất lượng 80** (`tools/anh_app.py`): ảnh nhóm 15 mã hoá lại từ
bản gốc, cạnh dài 2048 px; ảnh CTK45 đổi thẳng từ WebP, giữ 768×1024 vì không còn bản gốc. Riêng
ảnh toàn cảnh là WebP chất lượng 90 ở độ phân giải gốc (9216–10240 px ngang): bộ giải mã AV1 của
vivo X300 từ chối ảnh rộng quá 8192 px. Đề tài ưu tiên chất lượng trên máy đời mới; AVIF cần Android 12 trở lên. Bản gốc
để trên Drive WiLoc, không đưa vào kho mã.

`trai`/`phai` theo sơ đồ (cửa chính ở dưới): bên trái là phía TV3,4 và lối ra cửa sau, bên phải
là phía căn tin và phòng tạp chí.

Ngày 07/10/2026 chia lại ảnh CTK45 theo đúng chỗ chụp, vì bản gốc gộp mỗi nhóm một thư mục:
`cua_ra_vao` tách thành `cua_chinh` (2 ảnh) và `loi_ra` (1); `cau_thang_tang_2` tách thành
`cau_thang_tang_2_trai` và `cau_thang_tang_2_phai`; ba ảnh sofa trong `khu_vuc_doc` là ban
công nên chuyển sang `ban_cong`; ảnh góc trưng bày cờ và tranh trong `khu_vuc_doc` là ở quầy nên
chuyển sang `ban_thu_thu`. Ảnh `hanh_lang` thực ra chụp dãy kệ sách chắn lối xuống WC, giữ tạm
tới đợt chụp lại. `huong_dan.svg` là hình nhân vật hướng dẫn do nhóm 15 vẽ.

Tên thư mục khớp đúng cột `thu_muc_anh` trong
`data/reference/reference_points.csv` (địa điểm chỉ có trên sơ đồ như ban công thì khớp khoá
`anh` trong `mat_bang_tang1.yaml`) — nhờ vậy `GET /map` trả về tên thư mục là
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
