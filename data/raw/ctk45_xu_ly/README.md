# Dữ liệu đã xử lý của CTK45 — nguồn của đợt B

`combined_data_sorted.csv`, `test_split.csv`, `text.json` lấy nguyên từ nhánh `Backup` của
`github.com/NgocSongNe/IPS` (thư mục `assets/`). Không sửa tệp nào.

`combined_data_sorted.csv`: 6.338 dòng, mỗi dòng một lần quét dạng bảng rộng — `ID_RP`, toạ độ
`X`, `Y` (theo Bảng 4 báo cáo CTK45) và 72 cột BSSID, AP không bắt được ghi −100.

## Hai đợt đo

Báo cáo CTK45 (tr. 40–41): mỗi RP đo 80 lần (4 hướng × 20 mẫu) bằng 4 máy Android khác nhau,
tổng 3.200 lần. Dữ liệu thô có trong tay (`data/raw/combined_data.csv`) chỉ là phần của một máy.

| Đợt | Nguồn | Lần quét | Máy |
|---|---|---:|---|
| A | `data/raw/combined_data.csv` (dữ liệu thô) | 802 | Samsung SM-S908E |
| B | phần còn lại của `combined_data_sorted.csv` | 2.349 | ba máy còn lại (báo cáo nhắc Galaxy Tab S6 Lite); tệp không có cột tên máy |

Cách tách đợt B (`ml.preprocess.nap_dot_b`):

1. Bỏ các dòng trùng nhau trong tệp (6.338 → 3.150 dòng khác nhau).
2. Bỏ các dòng trùng khít một lần quét của đợt A trên 72 cột (802 dòng) — 802/802 lần quét
   đợt A đều có mặt trong tệp, cùng nhãn RP (20 lần "RP41" của dữ liệu thô là RP26).
3. Còn 2.349 dòng, khoảng 60 mỗi RP, đủ 40 RP. Giá trị −100 coi là không bắt được, như ô
   trống của đợt A.

Đợt B nhiễu hơn đợt A: trong cùng một RP độ phân tán gấp đôi (13,2 so với 5,9 dB mỗi AP), mỗi
lần quét nghe ít AP hơn (trung vị 25 so với 31). Lệch trung bình giữa hai đợt chỉ +1 dB nhưng
không đều theo AP và RP. Thứ tự dòng trong tệp đã xáo, không tách được từng máy.

Toạ độ của cả hai đợt lấy từ `data/reference/reference_points.csv` theo `rp_id`, không dùng cột
`X`, `Y` của tệp.
