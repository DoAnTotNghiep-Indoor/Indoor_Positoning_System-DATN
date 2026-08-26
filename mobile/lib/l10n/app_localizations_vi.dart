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
  String homeAccuracy(String met) {
    return 'Sai số ±$met m';
  }

  @override
  String get homeQuickAccess => 'Truy cập nhanh';

  @override
  String get homeNearby => 'Gần bạn';

  @override
  String get mapTitle => 'Bản đồ';

  @override
  String get mapFloorOne => 'Tầng 1';

  @override
  String get mapRelocateDemo => 'Bản demo — chưa nối API định vị';

  @override
  String get mapRelocate => 'Định vị lại';

  @override
  String mapAreaSummary(int count, int giay) {
    return '$count khu vực · cập nhật $giay giây trước';
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
  String get detailRouteDemo =>
      'Bản demo — chức năng chỉ đường làm ở giai đoạn sau';

  @override
  String get detailImagePlaceholder => 'Ảnh khu vực';

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
  String get settingsAutoUpdate => 'Tự động cập nhật vị trí';

  @override
  String get settingsAutoUpdateSub => 'Quét lại mỗi 2 giây';

  @override
  String get settingsKeepAwake => 'Giữ màn hình sáng';

  @override
  String get settingsKeepAwakeSub => 'Khi đang xem bản đồ';

  @override
  String get settingsPermission => 'Vị trí và WiFi';

  @override
  String get settingsPermissionSub => 'Cần thiết để định vị';

  @override
  String get settingsPermissionGranted => 'Đã cấp';

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
  String a11yAreaRow(String ten, int met) {
    return '$ten, cách $met mét';
  }

  @override
  String get a11yOpenArea => 'Mở chi tiết khu vực';
}
