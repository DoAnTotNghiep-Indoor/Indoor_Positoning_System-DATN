# IPS DLU — Ứng dụng di động

Ứng dụng Android định vị trong nhà cho tầng 1 Thư viện Đại học Đà Lạt. Ứng dụng
quét WiFi, dự đoán toạ độ (qua máy chủ, hoặc ngay trên máy khi bật Mô hình cục bộ),
rồi hiển thị vị trí trên sơ đồ mặt bằng.

Thiết kế giao diện: [Figma](https://www.figma.com/design/3dzSOBhBIhb3e9zkuWOiQS).

## Chức năng

- **Định vị liên tục**: quét xong là quét tiếp khi app mở, dừng khi app
  chạy nền. Máy cần tắt **Điều tiết quét Wi-Fi** trong Tuỳ chọn nhà phát triển; còn bật thì
  Android chỉ cho 4 lần quét mỗi 2 phút và app đọc lại kết quả cũ.
- **Bản đồ**: sơ đồ tầng 1 (sáng/tối), chấm vị trí kèm nón hướng theo la bàn.
- **Tra cứu**: tìm khu vực theo tên hoặc nhóm, popup có ảnh và giới thiệu.
- **Chỉ đường**: vẽ tuyến từ vị trí hiện tại tới khu vực đã chọn.
- **Mô hình cục bộ**: tuỳ chọn trong Cài đặt, mặc định tắt. Bật thì app tự chạy kNN k
  động trên máy, không chờ máy chủ; lần quét vẫn gửi lên máy chủ (không chờ trả lời) để
  Dashboard và CSDL vẫn có dữ liệu. Bản đồ và chỉ đường vẫn lấy từ máy chủ.
- **Cài đặt**: mô hình cục bộ, địa chỉ máy chủ, ngôn ngữ (Việt/Anh), chế độ sáng/tối.
  App nhớ các tuỳ chọn này giữa hai lần mở.

Máy chủ cung cấp `POST /predict`, `GET /map`, `POST /route`.

## Yêu cầu

- Flutter 3.47 stable (Dart 3.13), Android SDK 36.
- Máy Android thật để định vị. Máy ảo chỉ dùng được để xem giao diện.

## Chạy

```bash
cd mobile
flutter pub get
flutter run
flutter analyze
flutter test
```

Bản cài để demo (arm64, khoảng 20,5 MB):

```bash
flutter build apk --release --target-platform android-arm64 --obfuscate --split-debug-info=build/app/symbols
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

Cần chạy máy chủ trước: `uvicorn backend.main:app --host 0.0.0.0` ở thư mục gốc.
Đặt địa chỉ máy chủ trong **Cài đặt** như sau:

| Thiết bị | Địa chỉ |
|---|---|
| Máy ảo | `http://10.0.2.2:8000` (mặc định) |
| Điện thoại cùng mạng | `http://<IP máy chủ>:8000` |
| Điện thoại nối USB, đã chạy `adb reverse tcp:8000 tcp:8000` | `http://127.0.0.1:8000` |
| Khác mạng (WiFi thư viện chặn máy nhìn nhau), chạy `cloudflared tunnel --url http://localhost:8000` | `https://<tên>.trycloudflare.com` |

Khi ở ngoài thư viện, chạy máy chủ với `DEMO=true`. Máy chủ sẽ phát lại các lần
quét thật đã ghi trong thư viện, nên app vẫn có vị trí và hiện nón hướng.

## Cấu trúc

```
lib/
├── main.dart                 khung app, thanh tab, điều hướng
├── theme/                    màu sáng/tối, cấu hình kính, tuỳ chọn người dùng
├── services/
│   ├── theo_doi_vi_tri.dart  vòng quét liên tục, trạng thái định vị và tuyến
│   ├── dinh_vi_tren_may.dart kNN k động và bộ gộp chạy trên máy (Mô hình cục bộ)
│   ├── api_dinh_vi.dart      gọi API, phân loại lỗi
│   ├── quet_wifi.dart        quét WiFi
│   ├── quyen_truy_cap.dart   quyền vị trí / thiết bị WiFi lân cận
│   └── la_ban.dart           hướng la bàn → hướng trên sơ đồ
├── data/                     đổi toạ độ mét ↔ pixel, danh sách khu vực, ảnh
├── widgets/                  sơ đồ, popup khu vực, thành phần dùng chung
├── screens/                  Trang chủ, Bản đồ, Tìm kiếm, Cài đặt
└── l10n/                     chuỗi tiếng Việt/Anh (.arb) và mã sinh tự động
assets/                       font Inter, SVG sơ đồ, ảnh khu vực, mô hình (model/k_dong.json)
```

`data/khu_vuc_thu_vien.dart` được sinh tự động, **không sửa tay**. Sinh lại bằng
`python -m tools.sinh_khu_vuc` từ `data/reference/reference_points.csv`.

## Ghi chú kỹ thuật

- **Nhịp quét**: quét xong là quét tiếp, khoảng 2 giây một lần trên vivo X300. Máy phải
  tắt điều tiết quét Wi-Fi, không thì chỉ được 4 lần mỗi 2 phút và nhận lại kết quả cũ.
- **Mô hình cục bộ**: `assets/model/k_dong.json` sinh bằng `python -m ml.xuat_mo_hinh` ở thư
  mục gốc, chạy lại sau mỗi lần `ml.train` rồi build lại app (`tests/test_xuat_mo_hinh.py`
  báo lỗi nếu quên). `test/dinh_vi_tren_may_test.dart` kiểm bản Dart đoán trùng Python trên
  200 lần quét test (`test/du_lieu/doi_chieu_k_dong.json`, cùng lệnh sinh ra). Một lần đoán
  trên X300 khoảng 0,7 ms; không cần LiteRT hay NPU vì kNN chỉ là tính khoảng cách.
- **Hệ toạ độ**: phép đổi trong `lib/data/floor_map.dart` dùng chung bộ hằng số
  với backend và Dashboard, lấy từ `data/reference/ban_do_tang1.json`.
- **Không đủ AP thì không đoán**: máy chủ trả 422 (mô hình cục bộ báo cùng lỗi), app báo
  "chưa xác định vị trí" thay vì giữ vị trí cũ.
- **Giao diện**: chỉ thanh điều hướng và các nút nổi dùng hiệu ứng kính
  (`liquid_glass_widgets`, khoá ở 0.30.2), nội dung dùng nền đặc.
- **`permission_handler` giữ ở 12.x**: bản 13 cần compileSdk 37 và bản AGP mới hơn.

## Môi trường Android

- Giữ **cmdline-tools 19.0**. Từ bản 20, `sdkmanager` không đọc được tên gói có
  dấu `;` mà Gradle truyền vào, nên build APK bị crash.
- Cảnh báo `SDK XML version 4 ... understands up to 3` là vô hại.

## Hạn chế

- Góc giữa sơ đồ và hướng bắc (`LaBan.gocBacSoDo`, 248,5°) đo trên ảnh vệ tinh.
  Góc này chưa được kiểm tra bằng cách đứng trong thư viện và so nón hướng với
  hướng thật.
