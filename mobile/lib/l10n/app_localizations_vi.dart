// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Vietnamese (`vi`).
class LVi extends L {
  LVi([String locale = 'vi']) : super(locale);

  @override
  String get appTitle => 'IPS DLU';

  @override
  String get tabHome => 'Trang chủ';

  @override
  String get tabMap => 'Bản đồ';

  @override
  String get tabSettings => 'Cài đặt';

  @override
  String get searchHint => 'Tìm phòng, khu vực…';

  @override
  String get floorLine => 'Tầng 1 · Thư viện Đại học Đà Lạt';

  @override
  String get homeYouAreAt => 'Bạn đang ở';

  @override
  String get homeQuickAccess => 'Truy cập nhanh';

  @override
  String get homeNearby => 'Gần bạn';

  @override
  String get homeAllAreas => 'Tất cả khu vực';

  @override
  String get liveLocating => 'Đang xác định vị trí…';

  @override
  String liveCoords(String x, String y) {
    return 'x $x · y $y';
  }

  @override
  String liveInfo(int so, String moHinh, String ms) {
    return 'Khớp $so AP · $moHinh · $ms ms';
  }

  @override
  String liveStale(int giay) {
    return 'Vị trí từ $giay giây trước';
  }

  @override
  String get mapFloorOne => 'Tầng 1';

  @override
  String get mapFloorPlanLabel => 'Sơ đồ mặt bằng tầng 1';

  @override
  String get mapFilterAll => 'Tất cả';

  @override
  String mapRouteChip(String met, String noi) {
    return '$met m tới $noi';
  }

  @override
  String mapArrived(String noi) {
    return 'Đã tới $noi';
  }

  @override
  String get mapClearRoute => 'Xoá tuyến đường';

  @override
  String searchResultCount(int count) {
    return '$count kết quả';
  }

  @override
  String get searchEmpty => 'Không tìm thấy khu vực nào phù hợp';

  @override
  String get searchEmptyHint => 'Thử từ khoá khác hoặc chọn \"Tất cả\".';

  @override
  String get searchFilterAll => 'Tất cả';

  @override
  String get searchFilterStudy => 'Học tập';

  @override
  String get searchFilterService => 'Tiện ích';

  @override
  String get searchFilterWays => 'Lối đi';

  @override
  String get placeGo => 'Chỉ đường';

  @override
  String get placeWaiting => 'Đang chờ định vị…';

  @override
  String get placeRouting => 'Đang tìm đường…';

  @override
  String get placeRouteFailed => 'Không tìm được đường tới đây';

  @override
  String get placeHere => 'Bạn đang ở đây';

  @override
  String distanceMeters(int met) {
    return '$met m';
  }

  @override
  String get a11yOpenArea => 'Mở thông tin khu vực';

  @override
  String get settingsTitle => 'Cài đặt';

  @override
  String get settingsGroupGeneral => 'Chung';

  @override
  String get settingsGroupAppearance => 'Giao diện';

  @override
  String get settingsGroupPositioning => 'Định vị';

  @override
  String get settingsAppInfo => 'Phiên bản';

  @override
  String get settingsServer => 'Máy chủ định vị';

  @override
  String get settingsServerSub =>
      'Máy ảo dùng 10.0.2.2, điện thoại thật dùng IP nội bộ';

  @override
  String get settingsServerHint => 'http://<IP>:8000';

  @override
  String get settingsTheme => 'Chế độ màu';

  @override
  String get settingsThemeSystem => 'Hệ thống';

  @override
  String get settingsThemeLight => 'Sáng';

  @override
  String get settingsThemeDark => 'Tối';

  @override
  String get settingsLanguage => 'Ngôn ngữ';

  @override
  String get settingsLanguageVi => 'Tiếng Việt';

  @override
  String get settingsLanguageEn => 'English';

  @override
  String get settingsScanCycle => 'Định vị liên tục';

  @override
  String settingsScanCycleSub(int giay) {
    return 'Quét WiFi mỗi $giay giây khi ứng dụng đang mở';
  }

  @override
  String get settingsPermission => 'Vị trí và WiFi';

  @override
  String get settingsPermissionGranted => 'Đã cấp';

  @override
  String get settingsPermissionMissing => 'Chạm để cấp quyền';

  @override
  String get settingsPermissionBlocked => 'Bị chặn — chạm để mở Cài đặt';

  @override
  String get errWifiPermission =>
      'Cần quyền vị trí để quét WiFi. Chạm để cấp quyền.';

  @override
  String get errWifiBlocked => 'Quyền vị trí đang bị chặn. Chạm để mở Cài đặt.';

  @override
  String get errLocationOff =>
      'Dịch vụ vị trí đang tắt. Hãy bật lên để định vị.';

  @override
  String get errWifiUnsupported => 'Thiết bị không hỗ trợ quét WiFi.';

  @override
  String get errScanFailed => 'Không quét được WiFi, đang thử lại…';

  @override
  String errNotEnoughAp(int so, int can) {
    return 'Chỉ khớp $so/$can access point cần thiết. Bạn có đang ở trong thư viện?';
  }

  @override
  String errBadAddress(String diaChi) {
    return 'Địa chỉ máy chủ không hợp lệ: $diaChi';
  }

  @override
  String errNoConnection(String diaChi) {
    return 'Không kết nối được máy chủ $diaChi';
  }

  @override
  String errServer(int ma) {
    return 'Máy chủ trả lỗi $ma';
  }

  @override
  String get errBadFormat => 'Ứng dụng và máy chủ không hiểu gói tin của nhau.';

  @override
  String get errTimeout => 'Máy chủ không phản hồi kịp.';

  @override
  String get mapFilter => 'Lọc khu vực';

  @override
  String get buildingFull => 'Thư viện Đại học Đà Lạt';
}
