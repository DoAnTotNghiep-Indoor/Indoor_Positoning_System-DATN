# UJIIndoorLoc — bộ dữ liệu công khai để so sánh

Torres-Sospedra và c.s., "UJIIndoorLoc: A new multi-building and multi-floor database for WLAN
fingerprint-based indoor localization problems", IPIN 2014. Tải tại UCI Machine Learning Repository
(mục *UJIIndoorLoc*); bản ở đây giải nén từ `ujiindoorloc.zip` (thư mục `UJIndoorLoc/`, 18/09/2014).

| Tệp | Lần quét | Ghi chú |
|---|---:|---|
| `trainingData.csv` | 19.937 | tập học công bố |
| `validationData.csv` | 1.111 | đo sau 4 tháng, người và máy khác — dùng làm tập kiểm |

520 cột `WAP001…WAP520` (RSSI dBm, **100 = không bắt được**), `LONGITUDE`, `LATITUDE` (mét, hệ
UTM), `FLOOR`, `BUILDINGID` (3 toà), `SPACEID`, `RELATIVEPOSITION`, `USERID`, `PHONEID`,
`TIMESTAMP`. Đại học Jaume I, Tây Ban Nha.

Dùng để so các mô hình của đề tài với nhóm hợp tác (few-shot, CCpos, kNN Sørensen trên cùng bộ
dữ liệu). Hai tệp CSV (45 MB) không đưa vào git; tải lại rồi đặt vào thư mục này.
