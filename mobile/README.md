# IPS DLU — Ứng dụng di động (bản demo giao diện)

Ứng dụng Flutter dựng lại 5 màn hình trong frame thiết kế `ips-dlu-screens-v4.svg`,
giữ nguyên bố cục, bảng màu và toạ độ gốc.

> **Bản demo giao diện — chưa nối API.** Toàn bộ dữ liệu là hằng số tĩnh trong
> `lib/data/demo_data.dart`. Phần backend (`POST /predict`, `WS /ws/location`,
> `GET /map`) sẽ làm ở giai đoạn sau theo đúng kế hoạch trong đề cương.

## Yêu cầu

- Flutter **>= 3.27** (Dart >= 3.6) — vì mã dùng `Color.withValues()`.
  Nếu dùng bản cũ hơn, thay toàn bộ `.withValues(alpha: x)` thành `.withOpacity(x)`.

Máy đang cài **Flutter 3.47.1 stable** tại `D:\flutter` (Dart 3.13.1).

## Chạy

Khung nền tảng `web/` và `android/` đã được sinh sẵn.

```bash
cd D:\Nam5\DATN\System_Indoor\mobile
flutter pub get
flutter run -d chrome        # chạy nhanh trên trình duyệt
flutter run                  # chọn thiết bị Android
```

Kiểm tra chất lượng mã:

```bash
flutter analyze
flutter test
```

## Cấu trúc

```
lib/
├── main.dart                     # điểm vào, khung AppShell + bottom nav
├── theme/
│   ├── app_colors.dart           # bảng màu lấy trực tiếp từ frame thiết kế
│   └── app_theme.dart            # ThemeData, thang chữ
├── data/
│   └── demo_data.dart            # DỮ LIỆU TĨNH — thay bằng API ở giai đoạn sau
├── widgets/
│   ├── blob_background.dart      # nền gradient + khối blob mờ
│   ├── glass_card.dart           # thẻ trắng bán trong suốt dùng chung
│   ├── app_bottom_nav.dart       # thanh điều hướng 3 tab + nút tìm kiếm
│   └── floor_plan.dart           # sơ đồ mặt bằng tầng 1 (toạ độ hệ 393x852)
└── screens/
    ├── home_screen.dart          # Trang chủ
    ├── map_screen.dart           # Bản đồ
    ├── area_detail_screen.dart   # Chi tiết khu vực
    ├── search_screen.dart        # Tìm kiếm
    └── settings_screen.dart      # Cài đặt
```

## Ghi chú kỹ thuật

**Hệ toạ độ.** Sơ đồ mặt bằng và các blob dùng đúng hệ **393 × 852** của frame
thiết kế, rồi co giãn theo bề rộng màn hình thật qua hệ số `s = maxWidth / 393`.
Nhờ vậy khi thay số đo thực tế chỉ cần sửa toạ độ, không phải tính lại layout.

**Điểm nối API sau này.** Ba chỗ cần thay khi backend sẵn sàng:

| Vị trí | Hiện tại | Sẽ thành |
|---|---|---|
| `DemoData.userX/userY` | hằng số `(150, 585)` | toạ độ từ `WS /ws/location` |
| `DemoData.nearby`, `searchResults` | danh sách tĩnh | `GET /map`, API tìm kiếm |
| `FloorPlan._rooms` | danh sách tĩnh | `GET /map/{floor_id}` |

**Chưa làm.** Chỉ đường (Dijkstra/A*), quét WiFi thật, kết nối WebSocket — đúng
phạm vi "bản demo giao diện" đã thống nhất.

## Trạng thái kiểm thử

Đã kiểm chứng trên Flutter 3.47.1:

| Lệnh | Kết quả |
|---|---|
| `flutter analyze` | `No issues found!` |
| `flutter test` | `All tests passed!` (3/3) |

`test/widget_test.dart` kiểm tra: màn Trang chủ hiển thị đúng vị trí hiện tại,
bottom nav chuyển được sang Cài đặt, và nút tìm kiếm mở màn Tìm kiếm ra đủ 5 kết quả.

**Chưa chạy thử trực quan trên thiết bị** — mới dừng ở mức test widget.

Đã build thật ra APK:

```
✓ Built build\app\outputs\flutter-apk\app-debug.apk   (143.6 MB, bản debug)
```

### Môi trường

| Hạng mục | Trạng thái |
|---|---|
| Flutter SDK | ✅ 3.47.1 tại `D:\flutter` |
| Android toolchain | ✅ SDK 36.0.0, license đã chấp nhận |
| Chrome (chạy web) | ✅ |
| Thiết bị kết nối | ✅ 3 thiết bị |
| Visual Studio C++ | ⚠️ thiếu workload "Desktop development with C++" — **chỉ cần nếu build app Windows desktop**, không ảnh hưởng Android/web |

### ⚠️ Lưu ý quan trọng về `cmdline-tools`

SDK đang dùng **cmdline-tools 19.0**, không phải bản mới nhất (23.0).

Lý do: từ bản 20 trở đi Google thay `sdkmanager` cũ bằng "Android CLI" mới, và
wrapper mới **tách tên gói ở dấu `;`** — nên khi Gradle gọi
`sdkmanager "ndk;28.2.13676358"` thì nó hiểu nhầm thành hai gói rời rồi crash
(`0xC0000409`), làm build APK thất bại.

Bản 23.0 vẫn được giữ tại `...\Android\Sdk\cmdline-tools\23.0` để dùng sau khi
Gradle/Flutter hỗ trợ CLI mới. **Đừng đổi `cmdline-tools\latest` sang 23.0** cho
tới lúc đó, sẽ hỏng build Android.

Cảnh báo `SDK XML version 4 ... understands up to 3` khi chạy sdkmanager là hệ quả
của việc này — vô hại, build vẫn chạy đúng.
