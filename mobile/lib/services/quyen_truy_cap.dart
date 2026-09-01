import 'package:permission_handler/permission_handler.dart';

/// Trạng thái quyền quét WiFi, theo đúng ba cách xử lý khác nhau.
enum TrangThaiQuyen {
  /// Chưa hỏi lần nào, hoặc người dùng đã từ chối nhưng còn hỏi lại được.
  chuaCap,

  daCap,

  /// Người dùng chọn "Không hỏi lại", hoặc thiết bị bị chính sách chặn. Hỏi
  /// tiếp không có tác dụng — chỉ mở được màn Cài đặt của hệ điều hành.
  biChan,
}

/// Đọc và xin quyền quét WiFi.
///
/// Android coi danh sách AP xung quanh là dữ liệu suy ra được vị trí, nên quét
/// WiFi cần quyền vị trí. Từ Android 13 có thêm `NEARBY_WIFI_DEVICES` dùng thay,
/// và máy mới trả `denied` vĩnh viễn cho quyền vị trí — vì vậy phải coi là ĐÃ
/// CẤP khi một trong hai quyền được cấp, chứ không phải cả hai.
///
/// Tách thành lớp riêng và cho tiêm được để màn Cài đặt kiểm thử được: gọi
/// thẳng `permission_handler` thì mọi bài test widget đều đụng kênh nền tảng.
class QuyenTruyCap {
  const QuyenTruyCap();

  Future<TrangThaiQuyen> kiemTra() async =>
      _gop(await Permission.locationWhenInUse.status,
          await Permission.nearbyWifiDevices.status);

  /// Hỏi người dùng. Trả về trạng thái sau khi họ trả lời.
  Future<TrangThaiQuyen> xin() async {
    final ds = await [
      Permission.locationWhenInUse,
      Permission.nearbyWifiDevices,
    ].request();
    return _gop(ds[Permission.locationWhenInUse]!,
        ds[Permission.nearbyWifiDevices]!);
  }

  /// Mở màn Cài đặt của hệ điều hành — lối duy nhất khi quyền đã bị chặn hẳn.
  Future<void> moCaiDat() => openAppSettings();

  TrangThaiQuyen _gop(PermissionStatus a, PermissionStatus b) {
    if (a.isGranted || b.isGranted) return TrangThaiQuyen.daCap;
    // `restricted` là chính sách thiết bị chặn, `permanentlyDenied` là người
    // dùng chọn không hỏi lại. Cả hai đều không xin thêm được.
    if (a.isPermanentlyDenied || a.isRestricted) return TrangThaiQuyen.biChan;
    return TrangThaiQuyen.chuaCap;
  }
}
