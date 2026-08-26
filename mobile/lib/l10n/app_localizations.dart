import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_vi.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of L
/// returned by `L.of(context)`.
///
/// Applications need to include `L.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: L.localizationsDelegates,
///   supportedLocales: L.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the L.supportedLocales
/// property.
abstract class L {
  L(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static L of(BuildContext context) {
    return Localizations.of<L>(context, L)!;
  }

  static const LocalizationsDelegate<L> delegate = _LDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('vi')
  ];

  /// Tên ứng dụng hiện trên trình quản lý tác vụ
  ///
  /// In vi, this message translates to:
  /// **'IPS DLU'**
  String get appTitle;

  /// No description provided for @tabHome.
  ///
  /// In vi, this message translates to:
  /// **'Trang chủ'**
  String get tabHome;

  /// No description provided for @tabMap.
  ///
  /// In vi, this message translates to:
  /// **'Bản đồ'**
  String get tabMap;

  /// No description provided for @tabSettings.
  ///
  /// In vi, this message translates to:
  /// **'Cài đặt'**
  String get tabSettings;

  /// No description provided for @searchHint.
  ///
  /// In vi, this message translates to:
  /// **'Tìm phòng, khu vực…'**
  String get searchHint;

  /// Nhãn phía trên tên khu vực hiện tại
  ///
  /// In vi, this message translates to:
  /// **'Bạn đang ở'**
  String get homeYouAreAt;

  /// Sai số định vị hiện tại
  ///
  /// In vi, this message translates to:
  /// **'Sai số ±{met} m'**
  String homeAccuracy(String met);

  /// No description provided for @homeQuickAccess.
  ///
  /// In vi, this message translates to:
  /// **'Truy cập nhanh'**
  String get homeQuickAccess;

  /// No description provided for @homeNearby.
  ///
  /// In vi, this message translates to:
  /// **'Gần bạn'**
  String get homeNearby;

  /// No description provided for @mapTitle.
  ///
  /// In vi, this message translates to:
  /// **'Bản đồ'**
  String get mapTitle;

  /// No description provided for @mapFloorOne.
  ///
  /// In vi, this message translates to:
  /// **'Tầng 1'**
  String get mapFloorOne;

  /// No description provided for @mapRelocateDemo.
  ///
  /// In vi, this message translates to:
  /// **'Bản demo — chưa nối API định vị'**
  String get mapRelocateDemo;

  /// Nhãn trợ năng của nút định vị lại trên màn Bản đồ
  ///
  /// In vi, this message translates to:
  /// **'Định vị lại'**
  String get mapRelocate;

  /// Dòng phụ trên thẻ header của màn Bản đồ
  ///
  /// In vi, this message translates to:
  /// **'{count} khu vực · cập nhật {giay} giây trước'**
  String mapAreaSummary(int count, int giay);

  /// Nhãn trợ năng cho cả sơ đồ mặt bằng
  ///
  /// In vi, this message translates to:
  /// **'Sơ đồ mặt bằng tầng 1'**
  String get mapFloorPlanLabel;

  /// Gợi ý trợ năng cho thao tác trên sơ đồ
  ///
  /// In vi, this message translates to:
  /// **'Chụm hai ngón để phóng to, kéo để xem chi tiết'**
  String get mapFloorPlanHint;

  /// No description provided for @searchTitle.
  ///
  /// In vi, this message translates to:
  /// **'Tìm kiếm'**
  String get searchTitle;

  /// Số kết quả tìm được
  ///
  /// In vi, this message translates to:
  /// **'{count} kết quả'**
  String searchResultCount(int count);

  /// No description provided for @searchEmpty.
  ///
  /// In vi, this message translates to:
  /// **'Không tìm thấy khu vực nào phù hợp'**
  String get searchEmpty;

  /// Câu gợi ý cách xử lý khi không có kết quả
  ///
  /// In vi, this message translates to:
  /// **'Thử một từ khoá khác, hoặc bỏ bộ lọc đang bật.'**
  String get searchEmptyHint;

  /// Nút đưa bộ lọc về "Tất cả"
  ///
  /// In vi, this message translates to:
  /// **'Bỏ bộ lọc'**
  String get searchClearFilter;

  /// No description provided for @searchFilterAll.
  ///
  /// In vi, this message translates to:
  /// **'Tất cả'**
  String get searchFilterAll;

  /// No description provided for @searchFilterStudy.
  ///
  /// In vi, this message translates to:
  /// **'Học tập'**
  String get searchFilterStudy;

  /// No description provided for @searchFilterFacility.
  ///
  /// In vi, this message translates to:
  /// **'Tiện ích'**
  String get searchFilterFacility;

  /// No description provided for @searchFilterInternal.
  ///
  /// In vi, this message translates to:
  /// **'Nội bộ'**
  String get searchFilterInternal;

  /// No description provided for @detailGoHere.
  ///
  /// In vi, this message translates to:
  /// **'Đi tới đây'**
  String get detailGoHere;

  /// No description provided for @detailRouteDemo.
  ///
  /// In vi, this message translates to:
  /// **'Bản demo — chức năng chỉ đường làm ở giai đoạn sau'**
  String get detailRouteDemo;

  /// Chữ trong ô ảnh giữ chỗ ở màn Chi tiết
  ///
  /// In vi, this message translates to:
  /// **'Ảnh khu vực'**
  String get detailImagePlaceholder;

  /// No description provided for @settingsTitle.
  ///
  /// In vi, this message translates to:
  /// **'Cài đặt'**
  String get settingsTitle;

  /// No description provided for @settingsGroupGeneral.
  ///
  /// In vi, this message translates to:
  /// **'CHUNG'**
  String get settingsGroupGeneral;

  /// No description provided for @settingsGroupAppearance.
  ///
  /// In vi, this message translates to:
  /// **'GIAO DIỆN'**
  String get settingsGroupAppearance;

  /// No description provided for @settingsGroupPositioning.
  ///
  /// In vi, this message translates to:
  /// **'ĐỊNH VỊ'**
  String get settingsGroupPositioning;

  /// No description provided for @settingsGroupPermissions.
  ///
  /// In vi, this message translates to:
  /// **'QUYỀN TRUY CẬP'**
  String get settingsGroupPermissions;

  /// No description provided for @settingsAppInfo.
  ///
  /// In vi, this message translates to:
  /// **'Thông tin ứng dụng'**
  String get settingsAppInfo;

  /// No description provided for @settingsServer.
  ///
  /// In vi, this message translates to:
  /// **'Máy chủ định vị'**
  String get settingsServer;

  /// No description provided for @settingsTheme.
  ///
  /// In vi, this message translates to:
  /// **'Giao diện'**
  String get settingsTheme;

  /// No description provided for @settingsThemeSystem.
  ///
  /// In vi, this message translates to:
  /// **'Theo hệ thống'**
  String get settingsThemeSystem;

  /// No description provided for @settingsThemeLight.
  ///
  /// In vi, this message translates to:
  /// **'Sáng'**
  String get settingsThemeLight;

  /// No description provided for @settingsThemeDark.
  ///
  /// In vi, this message translates to:
  /// **'Tối'**
  String get settingsThemeDark;

  /// No description provided for @settingsLanguage.
  ///
  /// In vi, this message translates to:
  /// **'Ngôn ngữ'**
  String get settingsLanguage;

  /// No description provided for @settingsLanguageVi.
  ///
  /// In vi, this message translates to:
  /// **'Tiếng Việt'**
  String get settingsLanguageVi;

  /// No description provided for @settingsLanguageEn.
  ///
  /// In vi, this message translates to:
  /// **'English'**
  String get settingsLanguageEn;

  /// No description provided for @settingsAutoUpdate.
  ///
  /// In vi, this message translates to:
  /// **'Tự động cập nhật vị trí'**
  String get settingsAutoUpdate;

  /// No description provided for @settingsAutoUpdateSub.
  ///
  /// In vi, this message translates to:
  /// **'Quét lại mỗi 2 giây'**
  String get settingsAutoUpdateSub;

  /// No description provided for @settingsKeepAwake.
  ///
  /// In vi, this message translates to:
  /// **'Giữ màn hình sáng'**
  String get settingsKeepAwake;

  /// No description provided for @settingsKeepAwakeSub.
  ///
  /// In vi, this message translates to:
  /// **'Khi đang xem bản đồ'**
  String get settingsKeepAwakeSub;

  /// No description provided for @settingsPermission.
  ///
  /// In vi, this message translates to:
  /// **'Vị trí và WiFi'**
  String get settingsPermission;

  /// No description provided for @settingsPermissionSub.
  ///
  /// In vi, this message translates to:
  /// **'Cần thiết để định vị'**
  String get settingsPermissionSub;

  /// No description provided for @settingsPermissionGranted.
  ///
  /// In vi, this message translates to:
  /// **'Đã cấp'**
  String get settingsPermissionGranted;

  /// No description provided for @settingsFootnote.
  ///
  /// In vi, this message translates to:
  /// **'Các tuỳ chọn khác sẽ được bổ sung ở phiên bản tiếp theo.'**
  String get settingsFootnote;

  /// Khoảng cách tính bằng mét
  ///
  /// In vi, this message translates to:
  /// **'{met} m'**
  String distanceMeters(int met);

  /// Nhãn trợ năng của nút quay lại
  ///
  /// In vi, this message translates to:
  /// **'Quay lại'**
  String get commonBack;

  /// Nhãn trợ năng cho một dòng khu vực trong danh sách
  ///
  /// In vi, this message translates to:
  /// **'{ten}, cách {met} mét'**
  String a11yAreaRow(String ten, int met);

  /// Gợi ý trợ năng khi chạm vào một khu vực
  ///
  /// In vi, this message translates to:
  /// **'Mở chi tiết khu vực'**
  String get a11yOpenArea;
}

class _LDelegate extends LocalizationsDelegate<L> {
  const _LDelegate();

  @override
  Future<L> load(Locale locale) {
    return SynchronousFuture<L>(lookupL(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'vi'].contains(locale.languageCode);

  @override
  bool shouldReload(_LDelegate old) => false;
}

L lookupL(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return LEn();
    case 'vi':
      return LVi();
  }

  throw FlutterError(
      'L.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
