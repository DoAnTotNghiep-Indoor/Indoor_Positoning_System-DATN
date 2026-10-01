# Dữ liệu khảo sát nhóm 15 — 2026

Dữ liệu nhóm tự thu ngày 06/09/2026 bằng **Redmi K40 Pro (M2012K11C)** tại 7 điểm mới ở hành
lang phía nam (RP46–RP52). Chưa dùng để huấn luyện.

## Cách thu

`python -m tools.thu_van_tay RPxx --nguoi-thu <mã>`, đọc kết quả quét qua `adb` với máy nối cáp
USB. 20 lần quét mỗi điểm, cách nhau 45 giây (giới hạn Android 4 lần quét mỗi 2 phút).

| Điểm | Toạ độ (đơn vị lưới) | Lần quét | Dòng | Khớp hợp đồng | RSSI TB (dBm) | Độ lệch chuẩn (dB) |
|---|---|---:|---:|---:|---:|---:|
| RP46 | (−35,0; 4,5) | 20 | 537 | 34/36 | −70,6 | 2,0 |
| RP47 | (−21,5; 3,5) | 20 | 680 | 36/36 | −70,5 | 1,5 |
| RP48 | (−15,5; 0,0) | 20 | 650 | 36/36 | −66,1 | 2,5 |
| RP49 | (−8,0; 2,0) | 20 | 611 | 35/36 | −66,4 | 1,9 |
| RP50 | (7,5; 2,0) | 20 | 564 | 34/36 | −62,5 | 1,9 |
| RP51 | (15,5; 0,0) | 20 | 638 | 36/36 | −65,4 | 1,7 |
| RP52 | (21,0; 5,0) | 20 | 629 | 34/36 | −64,2 | 2,9 |

Độ lệch chuẩn tính trên các AP bắt được ít nhất 15/20 lần; 1,5–2,9 dB cho thấy người đo đứng
yên. Toạ độ lấy từ `data/reference/diem_can_do.csv` (các chỗ trống nhất bản đồ, do
`tools.ban_do_di_do` chọn), chưa thêm vào `reference_points.csv`.

## Vì sao chưa gộp vào huấn luyện

Hai máy đọc RSSI lệch nhau ở cùng một chỗ, mà RSSI là đặc trưng duy nhất của mô hình. Thử gộp
cho kết quả xấu đi:

| Sai số trên tập test (đơn vị lưới) | Chỉ CTK45 | Sau khi gộp |
|---|---:|---:|
| Toàn tập, kNN Bray-Curtis | 2,30 | 3,54 |
| Riêng các điểm cũ (Samsung) | 2,30 | 4,08 |
| Riêng các điểm mới (Redmi) | — | 0,49 |

Thiệt hại nằm trên các điểm cũ dù dữ liệu của chúng không đổi: vân tay Redmi tạo thành cụm
riêng và làm méo cấu trúc láng giềng của các điểm Samsung. Muốn gộp phải đo độ lệch giữa hai
máy trước, bằng cách thu lại vài điểm cũ (ví dụ RP20, RP11, RP39) bằng Redmi rồi so cùng vị trí,
cùng AP.

## Lưu ý về tệp

- Cột `Student ID` của cả 7 tệp ghi `2212343`, là mã người thu bộ CTK45, không phải thành viên
  nhóm. Cần thay bằng mã người thực sự đi thu.
- 9 cột cảm biến (`Magnetic x/y/z`, `GPS *`, `Orientation *`) rỗng vì lúc thu chưa đọc cảm biến.
  Không điền bù được. Từ lần thu sau, `tools.thu_van_tay` đọc cảm biến qua `tools.cam_bien_adb`
  và dừng trước khi đo nếu thiếu; trên Redmi K40 Pro lấy được hướng và GPS, chưa lấy được từ kế.
- `tong_hop.csv` (bản ghép 7 tệp) không đưa vào git. Dựng lại khi cần:

```bash
python -c "import pandas as pd,glob; pd.concat([pd.read_csv(f) for f in sorted(glob.glob('data/raw/nhom15_2026/2026-09-06/RP*.csv'))]).to_csv('data/raw/nhom15_2026/2026-09-06/tong_hop.csv', index=False)"
```
