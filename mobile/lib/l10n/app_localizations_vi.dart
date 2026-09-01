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
  String get homeYouAreAt => 'Bạn đang ở';

  @override
  String get homeQuickAccess => 'Truy cập nhanh';

  @override
  String get homeNearby => 'Gần bạn';

  @override
  String get mapFloorOne => 'Tầng 1';

  @override
  String get mapRelocate => 'Định vị lại';

  @override
  String mapAreaSummary(int count, int giay) {
    return '$count khu vực · cập nhật $giay giây trước';
  }

  @override
  String mapAreaCount(int count) {
    return '$count khu vực';
  }

  @override
  String get mapFloorPlanLabel => 'Sơ đồ mặt bằng tầng 1';

  @override
  String get mapFloorPlanHint =>
      'Chụm hai ngón để phóng to, kéo để xem chi tiết';

  @override
  String get searchTitle => 'Tìm kiếm';

  @override
  String searchResultCount(int count) {
    return '$count kết quả';
  }

  @override
  String get searchEmpty => 'Không tìm thấy khu vực nào phù hợp';

  @override
  String get searchEmptyHint =>
      'Thử một từ khoá khác, hoặc bỏ bộ lọc đang bật.';

  @override
  String get searchClearFilter => 'Bỏ bộ lọc';

  @override
  String get searchFilterAll => 'Tất cả';

  @override
  String get searchFilterStudy => 'Học tập';

  @override
  String get searchFilterFacility => 'Tiện ích';

  @override
  String get searchFilterInternal => 'Nội bộ';

  @override
  String get detailGoHere => 'Đi tới đây';

  @override
  String get detailImagePlaceholder => 'Ảnh khu vực';

  @override
  String detailPhotos(int so) {
    String _temp0 = intl.Intl.pluralLogic(
      so,
      locale: localeName,
      other: '$so ảnh của khu vực, vuốt ngang để xem',
    );
    return '$_temp0';
  }

  @override
  String get settingsTitle => 'Cài đặt';

  @override
  String get settingsGroupGeneral => 'CHUNG';

  @override
  String get settingsGroupAppearance => 'GIAO DIỆN';

  @override
  String get settingsGroupPositioning => 'ĐỊNH VỊ';

  @override
  String get settingsGroupPermissions => 'QUYỀN TRUY CẬP';

  @override
  String get settingsAppInfo => 'Thông tin ứng dụng';

  @override
  String get settingsServer => 'Máy chủ định vị';

  @override
  String get settingsTheme => 'Giao diện';

  @override
  String get settingsThemeSystem => 'Theo hệ thống';

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
  String get settingsScanCycle => 'Chu kỳ quét';

  @override
  String settingsScanCycleSub(int giay) {
    return 'Mỗi $giay giây — mức Android cho phép';
  }

  @override
  String get settingsPermission => 'Vị trí và WiFi';

  @override
  String get settingsPermissionSub => 'Cần thiết để định vị';

  @override
  String get settingsPermissionGranted => 'Đã cấp';

  @override
  String get settingsPermissionMissing => 'Chưa cấp';

  @override
  String get settingsPermissionBlocked => 'Bị chặn';

  @override
  String get settingsPermissionChecking => 'Đang kiểm tra…';

  @override
  String get settingsPermissionAsk => 'Chạm để cấp quyền';

  @override
  String get settingsPermissionOpen => 'Chạm để mở Cài đặt hệ thống';

  @override
  String get settingsFootnote =>
      'Các tuỳ chọn khác sẽ được bổ sung ở phiên bản tiếp theo.';

  @override
  String distanceMeters(int met) {
    return '$met m';
  }

  @override
  String get commonBack => 'Quay lại';

  @override
  String get a11yOpenArea => 'Mở chi tiết khu vực';

  @override
  String get liveStart => 'Bắt đầu định vị';

  @override
  String get liveStop => 'Dừng định vị';

  @override
  String get liveScanning => 'Đang quét WiFi…';

  @override
  String get liveIdle => 'Chưa bật định vị';

  @override
  String get liveUnknown => 'Chưa xác định vị trí';

  @override
  String liveCoords(String x, String y) {
    return 'x $x m · y $y m';
  }

  @override
  String liveMatched(int so) {
    return 'Khớp $so access point';
  }

  @override
  String liveModel(String ten, String ms) {
    return 'Mô hình $ten · $ms ms';
  }

  @override
  String liveMerged(int so) {
    return 'Đã gộp $so lần quét';
  }

  @override
  String get errWifiPermission =>
      'Chưa được cấp quyền vị trí. Ứng dụng sẽ hỏi lại khi bạn bấm bắt đầu.';

  @override
  String get errWifiBlocked =>
      'Quyền vị trí đang bị chặn. Mở Cài đặt hệ thống để cấp lại.';

  @override
  String get errLocationOff => 'Dịch vụ vị trí đang tắt. Bật lên rồi thử lại.';

  @override
  String get errWifiUnsupported => 'Thiết bị không hỗ trợ quét WiFi.';

  @override
  String get errScanFailed => 'Không quét được WiFi. Thử lại sau ít giây.';

  @override
  String errNotEnoughAp(int so, int can) {
    return 'Không đủ dữ liệu để định vị — chỉ khớp $so/$can access point của thư viện. Bạn có đang ở trong thư viện không?';
  }

  @override
  String errBadAddress(String diaChi) {
    return 'Địa chỉ máy chủ không hợp lệ: $diaChi. Cần đủ dạng http://<IP>:<cổng>';
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
  String get errBadFormat => 'Máy chủ trả dữ liệu không đúng định dạng.';

  @override
  String get settingsServerHint => 'Nhập địa chỉ máy chủ';

  @override
  String get settingsServerSub =>
      'Máy ảo dùng 10.0.2.2, điện thoại thật dùng IP nội bộ';

  @override
  String get a11yToggleTracking => 'Bật hoặc tắt định vị theo thời gian thực';

  @override
  String get errTimeout =>
      'Máy chủ không phản hồi kịp. Kiểm tra lại chất lượng mạng.';

  @override
  String detailPointCount(int so) {
    return '$so điểm đo';
  }

  @override
  String detailPhotoCount(int so) {
    return '$so ảnh';
  }

  @override
  String get detailNeedPosition => 'Bật định vị để chỉ đường';

  @override
  String get detailRouteLoading => 'Đang tìm đường…';

  @override
  String get detailRouteFailed => 'Không tìm được đường tới đây';

  @override
  String routeSummary(String met, int buoc) {
    return '$met m · $buoc bước';
  }

  @override
  String routeStep(String huong, String met, String noi) {
    return '$huong $met m tới $noi';
  }

  @override
  String get stepStraight => 'Đi thẳng';

  @override
  String get stepSlightLeft => 'Chếch trái';

  @override
  String get stepSlightRight => 'Chếch phải';

  @override
  String get stepLeft => 'Rẽ trái';

  @override
  String get stepRight => 'Rẽ phải';

  @override
  String get stepUTurn => 'Quay đầu';

  @override
  String get mapOpenDetail => 'Mở chi tiết khu vực';

  @override
  String get mapFilterAll => 'Tất cả';

  @override
  String get mapFilterHint => 'Lọc sơ đồ theo loại khu vực';

  @override
  String mapRouteChip(String met, String noi) {
    return '$met m tới $noi';
  }

  @override
  String get mapClearRoute => 'Xoá tuyến đường';
}
