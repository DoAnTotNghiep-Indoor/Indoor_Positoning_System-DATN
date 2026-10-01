# Hình dáng thư viện — tư liệu đối chiếu (01/10/2026)

| Tệp | Nguồn | Ghi chú |
|---|---|---|
| `so_do_truong_tang1..3.png` | thuvien.dlu.edu.vn/vi/gioi-thieu-14c37/so-do-thu-vien-truong-dai-hoc-da-lat (`/Resources/Images/SubDomain/thuvien/2024/MAP/01–03.png`) | Sơ đồ minh hoạ, không theo tỉ lệ. Phần giữa-trên tầng 1 (quầy, nghiệp vụ 2) lệch so với RP CTK45 và lời kể thực địa; CNTT, hội trường vẽ lọt trong khối chính |
| `rp_tren_so_do_truong.png` | RP26–40 chấm lên `so_do_truong_tang1.png` qua phép khớp tay (`tools/ve_so_do_tang1.py`) | Đỏ: hàng y = 52 (RP33–40, mức quầy); RP37–39 rơi vào nghiệp vụ 2 của sơ đồ trường |
| `google_maps_3d.jpg` | Ảnh chụp Google Maps trên điện thoại | Bản đồ xoay (Bắc ≈ bên phải). Khối dài ba gian + hai khối vuông xoay chéo; cửa chính ở giữa hai khối vuông |
| `ve_tinh_osm.png` | Ảnh vệ tinh Google (z19, Bắc lên trên, khung 140 m) + đa giác OSM way 542490161 (đỏ) | 5 khối mái chóp vuông ~30 m; quảng trường tròn phía Đông. Đa giác OSM thiếu khối giữa và lệch |
| `ve_tinh_chong_tang1.png` | Như trên + khung tầng 1 (xanh) theo 0,3508 m/đơn vị, phương vị trục +y 248,5°, RP (vàng) | Tầng 1 CTK45 trùng **khối giữa**; cửa chính RP02 quay về Đông. CNTT = khối Đông Nam, hội trường = khối Bắc (toà riêng, nối ở hai góc phía cửa chính). Tâm khung đặt tay vào tâm khối, chưa khớp chính xác |
| `osm_da_giac.png`, `osm_thu_vien.json` | Overpass API, way 542490161 và nhà lân cận | Toạ độ mét quanh tâm (11,9571867; 108,4449786) |

Kích thước khối giữa đo thô trên ảnh ~28 × 23 m, sơ đồ tầng 1 theo tỉ lệ 0,3508 là ~31,6 × 24 m:
tỉ lệ có thể lớn ~10%, cần đo thước (hoặc đếm gạch, một đơn vị lưới ≈ một viên gạch ~35 cm).

## GPS của CTK45 (01/10/2026)

`geojson_ctk45/` tải từ nhánh `Backup` của `github.com/NgocSongNe/IPS` (`assets/geojson/`, CRS84).
`ve_tinh_gps_rp_ctk45.png`: 40 POI (vàng; RP01–03 đỏ) cùng các lớp Wall/Room/Stair/Hallways/Doors
chấm lên ảnh vệ tinh. Hàng y = 0 (RP01 TV3,4 · RP02 Cửa ra vào · RP03 Hội trường) nằm ở mép Đông
phần mái cam (sảnh dưới, phía quảng trường), hàng y = 52 lọt sâu trong khối giữa. Đám điểm GPS dãn
~0,42 m/đơn vị (thước Hình 7 cho 0,3508), sai số GPS trong nhà vài mét.
