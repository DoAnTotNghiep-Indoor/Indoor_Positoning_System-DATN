# Dữ liệu khảo sát nhóm 15 — 2026

Hai buổi, không buổi nào dùng để huấn luyện:

- **06/09/2026**: Redmi K40 Pro (M2012K11C), 7 điểm mới ở hành lang phía nam (RP46–RP52). Mục
  dưới đây.
- **18/11/2026**: đo sai số tại chỗ ở 7 chỗ biết toạ độ, hai máy. Mục cuối.

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

## Buổi 18/11/2026: đo sai số tại chỗ

Mục đích là kiểm thử, không phải thu vân tay: đứng ở chỗ biết toạ độ, ghi lần quét thô, rồi chạy
cả năm mô hình đang triển khai trên cùng các lần quét. GVHD hạn chế tự thu thêm dữ liệu học nên
các lần quét này không đưa vào huấn luyện.

| Tệp | Nội dung |
|---|---|
| `2026-11-18/lien_tuc_V2515_0933.csv` | vivo X300 (V2515), 1.636 lần quét liên tục 09:33–11:02, khoảng 3 s một lần, 20 cột như `combined_data.csv`, cột điểm để trống |
| `2026-11-18/phieu.csv` | Phiếu của vivo: mã chỗ đứng, giờ bắt đầu, số giây, toạ độ (đơn vị lưới), hướng máy, cách đặt máy |
| `../quet_app/2026-11-18.jsonl` | Máy thứ hai (`device_id` `dlu-mwludjtc-28f4`), lần quét app gửi lên máy chủ 15:11–15:24 |
| `2026-11-18/phieu_dlu-mwludjtc-28f4.csv` | Phiếu của máy thứ hai, cùng 7 chỗ |

Cách thu: vivo không cắm cáp; máy tính ở nhà đọc kết quả quét qua `adb` trên Tailscale
(`python -m tools.ghi_lien_tuc --nguoi-thu <MSSV>`), điện thoại dùng 4G, Wi-Fi bật nhưng không
nối mạng, đã tắt điều tiết quét. Máy thứ hai chỉ cài app, gửi `POST /predict` tới máy chủ chạy ở
nhà qua Cloudflare quick tunnel; máy chủ ghi lần quét thô. Người đo nhắn giờ bắt đầu mỗi chỗ,
lấy 45 giây sau đó. Chỉ đo một hướng: cầm phẳng, đỉnh máy hướng ra cửa chính (cột tròn, RP36)
hoặc về quầy (cột vuông); ở đầu kệ máy đặt ở tầng giữa, đỉnh máy hướng vào tường bên.

Toạ độ đếm gạch từ giữa mép trước quầy (y = 52,75) hoặc từ cửa chính. Cột tròn trước quầy đo
được ở y ≈ 44,25, khác sơ đồ (38,8). Toạ độ hai đầu kệ (±44,9; 24,5) suy từ kệ chắn lối xuống WC
trên sơ đồ, sai được khoảng 2 viên. Lần đo cột tròn lúc 09:36 bỏ vì máy bị xê dịch.

Kết quả (sai số trung bình, mét) ở README gốc, mục "Đo tại chỗ". Script tính tạm:
`tmp/so_hai_may.py` (ngoài git).
