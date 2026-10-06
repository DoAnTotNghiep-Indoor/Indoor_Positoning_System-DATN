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
  String get searchHint => 'Tìm địa điểm…';

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
    return '$so AP khớp · $moHinh · $ms ms';
  }

  @override
  String liveStale(int giay) {
    return 'Cập nhật $giay giây trước';
  }

  @override
  String get mapFloorOne => 'Tầng 1';

  @override
  String get mapFloorPlanLabel => 'Sơ đồ mặt bằng tầng 1';

  @override
  String get mapFilterAll => 'Tất cả';

  @override
  String mapRouteChip(String met, String noi) {
    return '$noi · còn $met m';
  }

  @override
  String mapArrived(String noi) {
    return 'Đã đến $noi';
  }

  @override
  String get mapClearRoute => 'Huỷ chỉ đường';

  @override
  String get mapResetRotation => 'Đưa bản đồ về hướng ban đầu';

  @override
  String get mapShowSection => 'Hiển thị';

  @override
  String get mapShowPoints => 'Điểm tham chiếu';

  @override
  String get mapShowLabels => 'Tên địa điểm';

  @override
  String get mapAreaSection => 'Lọc theo khu vực';

  @override
  String searchResultCount(int count) {
    return '$count kết quả';
  }

  @override
  String get searchEmpty => 'Không có địa điểm phù hợp';

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
  String get placeWaiting => 'Đang xác định vị trí của bạn…';

  @override
  String get placeRouting => 'Đang tìm đường…';

  @override
  String get placeRouteFailed => 'Không tìm được đường đi tới địa điểm này';

  @override
  String get placeHere => 'Bạn đang ở đây';

  @override
  String distanceMeters(int met) {
    return '$met m';
  }

  @override
  String get a11yOpenArea => 'Mở thông tin địa điểm';

  @override
  String get settingsTitle => 'Cài đặt';

  @override
  String get settingsGroupAppearance => 'Giao diện';

  @override
  String get settingsGroupPositioning => 'Định vị';

  @override
  String get settingsServer => 'Máy chủ định vị';

  @override
  String get settingsServerSub =>
      'Chọn máy chủ của hệ thống hoặc nhập địa chỉ riêng';

  @override
  String get settingsServerHint => 'https://… hoặc http://<IP>:8000';

  @override
  String get settingsServerCustom => 'Tuỳ chỉnh';

  @override
  String get settingsLocalModel => 'Mô hình trên thiết bị';

  @override
  String get settingsLocalModelSub =>
      'Ước lượng vị trí ngay trên thiết bị, không phụ thuộc máy chủ';

  @override
  String get liveOnDevice => 'trên thiết bị';

  @override
  String get settingsTheme => 'Chế độ hiển thị';

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
  String get settingsScanCycleSub =>
      'Quét WiFi liên tục khi ứng dụng đang hoạt động';

  @override
  String settingsScanFresh(String giay, int moi, int tong) {
    return 'Dữ liệu WiFi cập nhật mỗi $giay s ($moi/$tong lượt quét)';
  }

  @override
  String get settingsPermission => 'Quyền vị trí và WiFi';

  @override
  String get settingsPermissionGranted => 'Đã cấp quyền';

  @override
  String get settingsPermissionMissing => 'Chạm để cấp quyền';

  @override
  String get settingsPermissionBlocked =>
      'Đã bị chặn · chạm để mở Cài đặt hệ thống';

  @override
  String get errWifiPermission =>
      'Cần quyền vị trí để quét WiFi. Chạm để cấp quyền.';

  @override
  String get errWifiBlocked =>
      'Quyền vị trí đã bị chặn. Chạm để mở Cài đặt hệ thống.';

  @override
  String get errLocationOff =>
      'Dịch vụ vị trí đang tắt. Vui lòng bật để định vị.';

  @override
  String get errWifiUnsupported => 'Thiết bị không hỗ trợ quét WiFi.';

  @override
  String get errScanFailed => 'Quét WiFi không thành công, đang thử lại…';

  @override
  String errNotEnoughAp(int so, int can) {
    return 'Chỉ nhận diện được $so/$can điểm truy cập cần thiết. Có thể bạn đang ở ngoài thư viện.';
  }

  @override
  String errBadAddress(String diaChi) {
    return 'Địa chỉ máy chủ không hợp lệ: $diaChi';
  }

  @override
  String errNoConnection(String diaChi) {
    return 'Không thể kết nối tới máy chủ $diaChi';
  }

  @override
  String errServer(int ma) {
    return 'Máy chủ báo lỗi (mã $ma)';
  }

  @override
  String get errBadFormat => 'Phản hồi từ máy chủ không đúng định dạng.';

  @override
  String get errTimeout => 'Máy chủ phản hồi quá thời gian chờ.';

  @override
  String get mapFilter => 'Lớp bản đồ';

  @override
  String get buildingFull => 'Thư viện Đại học Đà Lạt';

  @override
  String settingsVersionLine(String app, String phienBan) {
    return '$app · phiên bản $phienBan';
  }
}
