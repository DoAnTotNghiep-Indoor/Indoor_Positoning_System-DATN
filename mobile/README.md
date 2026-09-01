# IPS DLU — Ứng dụng di động

Ứng dụng Flutter quét WiFi thật, gửi lên máy chủ và hiển thị vị trí người dùng
trên sơ đồ mặt bằng tầng 1 Thư viện Đại học Đà Lạt.

Bố cục và bảng màu dựng theo frame thiết kế `ips-dlu-screens-v4.svg`; dữ liệu
hiển thị thì lấy từ `GET /map` và `POST /predict`.

> **Ngoài phạm vi đề cương.** Đề cương (mục I và chương 5) chỉ yêu cầu ứng dụng
> **Web**. Ứng dụng di động là phần làm thêm, dùng làm nguồn quét WiFi cho hệ
> thống và để kiểm thử thực địa — không thay thế Web Dashboard.

## Yêu cầu

- Flutter **>= 3.27** (Dart >= 3.6) vì mã dùng `Color.withValues()`.
- Máy Android thật hoặc máy ảo. Web chỉ dựng được giao diện: `wifi_scan` không
  có bản cho trình duyệt.

Đã kiểm chứng trên **Flutter 3.47.1 stable** (Dart 3.13.1) tại `D:\flutter`,
Android SDK 36.0.0.

## Chạy

```bash
cd D:\Nam5\DATN\System_Indoor\mobile
flutter pub get
flutter run                  # chọn thiết bị Android
flutter analyze
flutter test
```

Máy chủ phải chạy trước (`uvicorn backend.main:app --host 0.0.0.0` ở thư mục
gốc). Địa chỉ sửa trong màn **Cài đặt**, mặc định `http://10.0.2.2:8000` là lối
tắt máy ảo Android gọi về máy đang chạy nó. Điện thoại thật thì đổi sang IP nội
bộ của máy chủ, hoặc nối USB rồi `adb reverse tcp:8000 tcp:8000` để dùng luôn
`http://127.0.0.1:8000`.

Địa chỉ, ngôn ngữ và chế độ sáng/tối được nhớ giữa hai lần mở app.

## Cấu trúc

```
lib/
├── main.dart                     # điểm vào, AppShell + bottom nav + hai Scope
├── theme/
│   ├── app_colors.dart           # bảng màu lấy từ frame thiết kế
│   ├── app_theme.dart            # ThemeData, thang chữ
│   ├── app_metrics.dart          # số đo co giãn theo cỡ chữ hệ thống
│   └── app_settings.dart         # tuỳ chọn người dùng, lưu bằng shared_preferences
├── services/
│   ├── quet_wifi.dart            # gọi wifi_scan, phân loại lý do không quét được
│   ├── quyen_truy_cap.dart       # quyền vị trí / NEARBY_WIFI_DEVICES
│   ├── api_dinh_vi.dart          # POST /predict, GET /map, POST /route
│   └── theo_doi_vi_tri.dart      # vòng lặp quét 5 giây, giữ trạng thái cho UI
├── data/
│   ├── floor_map.dart            # phép đổi mét ↔ pixel của sơ đồ thật
│   ├── khu_vuc.dart              # gộp điểm tham chiếu thành khu vực
│   ├── khu_vuc_thu_vien.dart     # SINH TỰ ĐỘNG — bản offline của khu vực
│   ├── anh_khu_vuc.dart          # số ảnh mỗi thư mục, dựng đường dẫn asset
│   └── demo_data.dart            # vài chuỗi cố định của toà nhà
├── widgets/
│   ├── so_do_that.dart           # vẽ Map.png, nhãn khu vực, chấm vị trí
│   ├── glass_card.dart           # thẻ kính dùng chung
│   ├── blob_background.dart      # nền gradient
│   └── tap_feedback.dart         # phản hồi chạm + nhãn trợ năng
├── screens/                      # Trang chủ, Bản đồ, Chi tiết, Tìm kiếm, Cài đặt
└── l10n/                         # app_vi.arb, app_en.arb và mã sinh từ chúng
```

`khu_vuc_thu_vien.dart` **không sửa tay**: sinh bằng `python -m tools.sinh_khu_vuc`
từ `data/reference/reference_points.csv`, và `tests/test_khu_vuc.py` so từng byte
tệp sinh ra với CSV.

## Ghi chú kỹ thuật

**Chu kỳ quét 5 giây.** Android chặn ứng dụng nền trước ở 4 lần `startScan` mỗi
2 phút. Quét dày hơn chỉ tốn pin để nhận lại kết quả cũ trong bộ đệm, nên con số
này là giới hạn hệ điều hành chứ không phải tuỳ chọn.

**Hệ toạ độ.** Sơ đồ dùng phép đổi mét ↔ pixel trong `lib/data/floor_map.dart`, cùng
một phép với backend và Dashboard web. Ba nơi giữ cùng bộ hằng số và
`tests/test_dashboard.py` đối chiếu cả ba với `data/reference/ban_do_tang1.json`.

**Không đủ AP thì không đoán.** Máy chủ trả 422 khi lần quét khớp ít AP hơn
ngưỡng trong hợp đồng dữ liệu; ứng dụng xoá toạ độ cũ và nói rõ "chưa xác định
vị trí" thay vì giữ tên phòng cũ trên màn hình.

**`kotlin.incremental=false`** trong `android/gradle.properties`: ứng dụng dùng
Kotlin Gradle Plugin 2.4.0 còn `wifi_scan` khai Kotlin 1.8.21, cơ chế biên dịch
tăng dần của Kotlin 2.x làm hỏng build. Gỡ dòng này khi nâng được `wifi_scan`.

## Trạng thái kiểm thử

| Lệnh | Kết quả |
|---|---|
| `flutter analyze` | `No issues found!` |
| `flutter test` | `All tests passed!` (65 bài) |
| `flutter build apk --debug` | `✓ Built app-debug.apk` |

| Tệp test | Nội dung |
|---|---|
| `dinh_vi_test.dart` | Vòng quét, phân loại lỗi API, huỷ giữa chừng, mốc cập nhật |
| `quyen_va_dia_chi_test.dart` | Quyền truy cập, ô địa chỉ máy chủ, ghi nhớ tuỳ chọn |
| `so_do_that_test.dart` | Phép đổi mét ↔ pixel và vị trí chấm trên sơ đồ |
| `anh_khu_vuc_test.dart` | Số ảnh mỗi thư mục khớp `AssetManifest` |
| `widget_test.dart` | Điều hướng, và không bịa vị trí khi chưa định vị |
| `uxui_test.dart`, `interaction_test.dart`, `settings_test.dart` | Trợ năng, cỡ chữ lớn, viewport thấp, song ngữ |

Đã chạy trên máy Android thật (Samsung), gồm cả tình huống đứng ngoài thư viện:
điện thoại thấy 23 access point, khớp 0 với hợp đồng dữ liệu, ứng dụng báo
không đủ dữ liệu thay vì trả một toạ độ trong thư viện.

## Lưu ý về môi trường Android

**Đừng đổi `cmdline-tools\latest` sang 23.0.** SDK đang cố ý dùng
**cmdline-tools 19.0**. Từ bản 20 trở đi Google thay `sdkmanager` cũ bằng
"Android CLI" mới, và wrapper mới tách tên gói ở dấu `;` — Gradle gọi
`sdkmanager "ndk;28.2.13676358"` thì nó hiểu thành hai gói rời rồi crash
(`0xC0000409`), build APK thất bại. Bản 23.0 vẫn giữ ở
`...\Android\Sdk\cmdline-tools\23.0` để dùng khi Gradle hỗ trợ CLI mới.

Cảnh báo `SDK XML version 4 ... understands up to 3` là hệ quả của việc này —
vô hại, build vẫn đúng.

Thiếu workload "Desktop development with C++" của Visual Studio chỉ chặn build
app Windows desktop, không ảnh hưởng Android hay web.

## Chưa làm

- Chỉ đường mới dừng ở danh sách chỉ dẫn từng chặng; chưa vẽ tuyến lên sơ đồ và
  chưa có la bàn theo hướng người dùng đang quay.
- Chưa dùng `WS /ws/location`; ứng dụng gọi REST mỗi 5 giây.
- Chưa chụp ảnh màn hình bộ giao diện mới trên thiết bị thật.
