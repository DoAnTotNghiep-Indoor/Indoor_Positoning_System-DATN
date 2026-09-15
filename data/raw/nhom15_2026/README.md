# Dữ liệu khảo sát nhóm 15 — 2026

Tách khỏi `data/raw/combined_data.csv` **có chủ đích**, không phải để tạm.

`combined_data.csv` là 25.712 dòng nhóm CTK45 thu tháng 1/2025 bằng **Samsung
SM-S908E**. Thư mục này là dữ liệu nhóm 15 thu bằng **Redmi K40 Pro
(M2012K11C)**. Hai máy khác nhau đọc RSSI lệch nhau vài dBm ở cùng một chỗ, mà
RSSI chính là đặc trưng duy nhất của mô hình — trộn chung là đưa một biến nhiễu
vào giữa bộ dữ liệu và không tách ra được nữa.

Muốn gộp thì phải đo được độ lệch giữa hai máy trước: thu lại 2–3 điểm cũ
(RP20, RP11, RP39) bằng Redmi, so cùng vị trí cùng AP chỉ khác máy, rồi mới
quyết định hiệu chỉnh hay giữ riêng.

Số liệu thô hiện có, đo bằng cách so RSSI trung bình trên 36 AP của hợp đồng:

| Bộ | Máy | RSSI trung bình | Số dòng |
|---|---|---:|---:|
| CTK45 2025 | SM-S908E | −66,8 dBm | 24.185 |
| Nhóm 15 2026 | M2012K11C | −64,9 dBm | 3.856 |

Chênh 1,9 dB, nhưng **không tách được khỏi yếu tố vị trí** vì bảy điểm mới đều ở
hành lang nam, không trùng chỗ nào với buổi 2025.

## Đã thử gộp một lần — kết quả xấu đi, đang hoãn

Ngày 09/09/2026 đã gộp thật vào pipeline để đo chứ không đoán: thêm 7 toạ độ,
`load_raw` đọc cả hai nguồn, chạy đủ pipeline → train → report.

| | Chỉ CTK45 | Sau khi gộp |
|---|---:|---:|
| kNN vân tay | **2,299 m** | 3,535 m |
| Giảm so với mô hình cơ sở | 58,2% | 21,7% |
| Cửa sổ trượt (cách đo cũ, theo thứ tự dòng) | 1,40 m · 8/118 sai | 1,87 m · 37/139 sai |

Tách theo bộ dữ liệu trên tập test cho thấy nguyên nhân không phải "điểm mới khó
hơn":

    điểm MỚI (Redmi)     21 mẫu · 0,488 m · sai  1/21   ← dễ nhất cả tập
    điểm CŨ  (Samsung)  118 mẫu · 4,078 m · sai 44/118

Sáu trong bảy điểm mới đạt 0,00 m. Thiệt hại nằm toàn bộ trên những điểm cũ:
chính chúng xấu đi **2,299 → 4,078 m** dù dữ liệu của chúng không đổi dòng nào.
Đó là chữ ký của lệch thiết bị — vân tay Redmi tách thành cụm riêng dễ tự nhận
ra, và làm méo cấu trúc láng giềng của các điểm Samsung. `ml.audit` mục 4 bắt
độc lập: RP46 lệch vân tay hẳn so với RP01 và RP04 dù chỉ cách 7–8 m.

Kèm hai hệ quả nữa: `missing_rssi_value` đổi **−96,0 → −95,0** (chia tập lại làm
lần quét mang −95 rơi khỏi train, tức giá trị điền phụ thuộc đúng một dòng), và
7 điểm mới làm đỏ 7 bài test vì chúng chưa có `ten`/`nhom` mà `/map` thì bắt buộc.

Công tắc `ml.config.GOP_BUOI_BO_SUNG` đang `False`. Bật lại sau khi đo được độ
lệch hai máy theo cách nêu ở trên; lúc đó còn phải đặt tên/nhóm cho 7 điểm và
sinh lại `khu_vuc_thu_vien.dart`.

## Buổi 06/09/2026

Thu bằng `python -m tools.thu_van_tay RPxx`, đọc kết quả quét qua `adb` với máy
nối cáp USB. 20 lần quét mỗi điểm, cách nhau 45 giây — cùng định mức buổi 2025
(20–21 lần, giãn cách trung vị 41–45 giây), và đã chạm sát giới hạn Android chặn
4 lần `startScan` mỗi 2 phút.

7 điểm · 140 lần quét · 4,309 dòng · 14:40–17:13

| Điểm | Toạ độ (m) | Lần quét | Dòng | Khớp hợp đồng | RSSI TB | Độ lệch chuẩn |
|---|---|---:|---:|---:|---:|---:|
| RP46 | (-35.0 · 4.5) | 20 | 537 | 34/36 | -70.6 | 2.0 |
| RP47 | (-21.5 · 3.5) | 20 | 680 | 36/36 | -70.5 | 1.5 |
| RP48 | (-15.5 · 0.0) | 20 | 650 | 36/36 | -66.1 | 2.5 |
| RP49 | (-8.0 · 2.0) | 20 | 611 | 35/36 | -66.4 | 1.9 |
| RP50 | (7.5 · 2.0) | 20 | 564 | 34/36 | -62.5 | 1.9 |
| RP51 | (15.5 · 0.0) | 20 | 638 | 36/36 | -65.4 | 1.7 |
| RP52 | (21.0 · 5.0) | 20 | 629 | 34/36 | -64.2 | 2.9 |

Cột cuối là độ lệch chuẩn RSSI của các AP bắt được ≥15/20 lần — thước đo người
đo có đứng yên không. 1,5–2,9 dB là sạch.

## Cột `Student ID` đang SAI — cần sửa

Cả 7 tệp đều mang `Student ID = 2212343`. Đó là mã người thu bộ CTK45, đọc ra từ
`combined_data.csv`, **không phải thành viên nào của Nhóm 15** — đề cương ghi ba
mã 2212363, 2115199 và 2100011, và không mã nào trong ba mã đó có mặt ở bất kỳ
đâu trong kho.

Nguyên nhân: `tools/thu_van_tay.py` từng đặt `--nguoi-thu` mặc định là `2212343`.
Nay tham số ấy **bắt buộc phải gõ**, nên lỗi không lặp lại được nữa.

Bảy tệp cũ thì chưa sửa vì phải biết ai thực sự đi thu. Sửa bằng cách thay giá
trị cột `Student ID` trong 7 tệp.

## `tong_hop.csv` không được theo dõi

Tệp ấy là bản ghép nguyên văn của 7 tệp `RPxx.csv` cùng thư mục — 4.309 dòng,
trùng khớp từng dòng. Giữ trong kho là công khai hai bản của cùng một tập số
liệu, và ghép cả hai vào pipeline sẽ làm `to_wide` lấy trung bình mỗi giá trị
với chính nó. Nay `.gitignore` chặn, hàng rào bước 1 cũng bắt được nếu lọt vào.

Dựng lại khi cần:

```bash
python -c "import pandas as pd,glob; pd.concat([pd.read_csv(f) for f in sorted(glob.glob('data/raw/nhom15_2026/2026-09-06/RP*.csv'))]).to_csv('data/raw/nhom15_2026/2026-09-06/tong_hop.csv', index=False)"
```

## Chín cột cảm biến

Bảy tệp buổi 06/09 **rỗng 9 cột**, trong khi `combined_data.csv` có đủ 100%:

| Cột | CTK45 2025 | Buổi 06/09/2026 |
|---|---:|---:|
| `Magnetic x/y/z (µT)` | 100% | 0% |
| `GPS Longitude/Latitude/Altitude` | 100% | 0% |
| `Orientation Azimuth/Pitch/Roll` | 100% | 0% |
| 11 cột còn lại | 100% | 100% |

Bộ cũ ghi một giá trị mỗi lần quét (801 azimuth riêng / 802 lần quét), tức là dữ
liệu thật chứ không phải hằng số điền cho đủ.

**Bảy tệp này không vá lại được.** Giá trị cảm biến chỉ đúng tại thời điểm quét;
điền bây giờ là bịa. Chúng ở lại như hiện trạng.

Từ buổi sau, `tools.thu_van_tay` đọc cảm biến qua `tools.cam_bien_adb`
(`dumpsys sensorservice` + `dumpsys location`) và **dừng trước khi đo** nếu
thiếu — không để người đo đứng yên 15 phút rồi mới biết tệp hỏng. Dò trước bằng
`python -m tools.cam_bien_adb`.

Đã thử thật trên Redmi K40 Pro ngày 06/09/2026, kết quả **17/20 cột**:

| Cột | Lấy được? | Điều kiện |
|---|---|---|
| `Orientation Azimuth/Pitch/Roll` | có | mở khoá máy, mở **la bàn** `com.miui.compass`, để ở màn hình trước, không tắt màn hình |
| `GPS Longitude/Latitude/Altitude` | có | bật định vị, mở bản đồ một lần gần cửa sổ |
| `Magnetic x/y/z` | **chưa** | không app nào trên máy đăng ký từ kế thô |

Đã thử và loại cho ba cột từ kế: ứng dụng IPS không nghe cảm biến này (mở lên
vùng đệm vẫn cũ 1.011 giây), Google Maps cũng không, và `cmd sensorservice`
không có lệnh con nào để đăng ký. Muốn có thì phải thêm listener
`TYPE_MAGNETIC_FIELD` vào app Flutter rồi cài lại máy — chưa làm.

Công cụ **loại giá trị quá cũ** thay vì chép lại số đọng trong vùng đệm: lúc
không có app nào nghe, từ kế cũ 970 giây và rotation vector cũ 2.778 giây. Ghi
số cũ 46 phút vào cột của lần quét bây giờ cũng là bịa.

Ba cột `Orientation *` ghi nhãn `(°)` nhưng bộ cũ lưu **radian**, và
`ml.config.AZIMUTH_IS_RADIAN = True` dựa vào đúng điều đó — công cụ ghi ra radian
cho khớp. Ghi ra độ thì pipeline vẫn chạy êm nhưng azimuth lệch 57 lần.

## Toạ độ

Bảy điểm này **chưa có trong `data/reference/reference_points.csv`** — vị trí lấy
từ `data/reference/diem_can_do.csv`, là 40 chỗ trống nhất bản đồ do
`tools.ban_do_di_do` chọn. Thêm vào bảng toạ độ là bước riêng, làm cùng lúc với
quyết định gộp dữ liệu.
