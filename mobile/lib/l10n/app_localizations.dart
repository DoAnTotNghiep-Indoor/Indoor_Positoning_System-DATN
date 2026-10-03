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

  /// No description provided for @appTitle.
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

  /// No description provided for @floorLine.
  ///
  /// In vi, this message translates to:
  /// **'Tầng 1 · Thư viện Đại học Đà Lạt'**
  String get floorLine;

  /// No description provided for @homeYouAreAt.
  ///
  /// In vi, this message translates to:
  /// **'Bạn đang ở'**
  String get homeYouAreAt;

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

  /// No description provided for @homeAllAreas.
  ///
  /// In vi, this message translates to:
  /// **'Tất cả khu vực'**
  String get homeAllAreas;

  /// No description provided for @liveLocating.
  ///
  /// In vi, this message translates to:
  /// **'Đang xác định vị trí…'**
  String get liveLocating;

  /// No description provided for @liveCoords.
  ///
  /// In vi, this message translates to:
  /// **'x {x} · y {y}'**
  String liveCoords(String x, String y);

  /// No description provided for @liveInfo.
  ///
  /// In vi, this message translates to:
  /// **'Khớp {so} AP · {moHinh} · {ms} ms'**
  String liveInfo(int so, String moHinh, String ms);

  /// No description provided for @liveStale.
  ///
  /// In vi, this message translates to:
  /// **'Vị trí từ {giay} giây trước'**
  String liveStale(int giay);

  /// No description provided for @mapFloorOne.
  ///
  /// In vi, this message translates to:
  /// **'Tầng 1'**
  String get mapFloorOne;

  /// No description provided for @mapFloorPlanLabel.
  ///
  /// In vi, this message translates to:
  /// **'Sơ đồ mặt bằng tầng 1'**
  String get mapFloorPlanLabel;

  /// No description provided for @mapFilterAll.
  ///
  /// In vi, this message translates to:
  /// **'Tất cả'**
  String get mapFilterAll;

  /// No description provided for @mapRouteChip.
  ///
  /// In vi, this message translates to:
  /// **'{met} m tới {noi}'**
  String mapRouteChip(String met, String noi);

  /// No description provided for @mapArrived.
  ///
  /// In vi, this message translates to:
  /// **'Đã tới {noi}'**
  String mapArrived(String noi);

  /// No description provided for @mapClearRoute.
  ///
  /// In vi, this message translates to:
  /// **'Xoá tuyến đường'**
  String get mapClearRoute;

  /// No description provided for @mapResetRotation.
  ///
  /// In vi, this message translates to:
  /// **'Đưa sơ đồ về hướng ban đầu'**
  String get mapResetRotation;

  /// No description provided for @mapShowSection.
  ///
  /// In vi, this message translates to:
  /// **'Hiển thị'**
  String get mapShowSection;

  /// No description provided for @mapShowPoints.
  ///
  /// In vi, this message translates to:
  /// **'Điểm tham chiếu'**
  String get mapShowPoints;

  /// No description provided for @mapShowLabels.
  ///
  /// In vi, this message translates to:
  /// **'Tên khu vực'**
  String get mapShowLabels;

  /// No description provided for @mapAreaSection.
  ///
  /// In vi, this message translates to:
  /// **'Khu vực'**
  String get mapAreaSection;

  /// No description provided for @searchResultCount.
  ///
  /// In vi, this message translates to:
  /// **'{count} kết quả'**
  String searchResultCount(int count);

  /// No description provided for @searchEmpty.
  ///
  /// In vi, this message translates to:
  /// **'Không tìm thấy khu vực nào phù hợp'**
  String get searchEmpty;

  /// No description provided for @searchEmptyHint.
  ///
  /// In vi, this message translates to:
  /// **'Thử từ khoá khác hoặc chọn \"Tất cả\".'**
  String get searchEmptyHint;

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

  /// No description provided for @searchFilterService.
  ///
  /// In vi, this message translates to:
  /// **'Tiện ích'**
  String get searchFilterService;

  /// No description provided for @searchFilterWays.
  ///
  /// In vi, this message translates to:
  /// **'Lối đi'**
  String get searchFilterWays;

  /// No description provided for @placeGo.
  ///
  /// In vi, this message translates to:
  /// **'Chỉ đường'**
  String get placeGo;

  /// No description provided for @placeWaiting.
  ///
  /// In vi, this message translates to:
  /// **'Đang chờ định vị…'**
  String get placeWaiting;

  /// No description provided for @placeRouting.
  ///
  /// In vi, this message translates to:
  /// **'Đang tìm đường…'**
  String get placeRouting;

  /// No description provided for @placeRouteFailed.
  ///
  /// In vi, this message translates to:
  /// **'Không tìm được đường tới đây'**
  String get placeRouteFailed;

  /// No description provided for @placeHere.
  ///
  /// In vi, this message translates to:
  /// **'Bạn đang ở đây'**
  String get placeHere;

  /// No description provided for @distanceMeters.
  ///
  /// In vi, this message translates to:
  /// **'{met} m'**
  String distanceMeters(int met);

  /// No description provided for @a11yOpenArea.
  ///
  /// In vi, this message translates to:
  /// **'Mở thông tin khu vực'**
  String get a11yOpenArea;

  /// No description provided for @settingsTitle.
  ///
  /// In vi, this message translates to:
  /// **'Cài đặt'**
  String get settingsTitle;

  /// No description provided for @settingsGroupGeneral.
  ///
  /// In vi, this message translates to:
  /// **'Chung'**
  String get settingsGroupGeneral;

  /// No description provided for @settingsGroupAppearance.
  ///
  /// In vi, this message translates to:
  /// **'Giao diện'**
  String get settingsGroupAppearance;

  /// No description provided for @settingsGroupPositioning.
  ///
  /// In vi, this message translates to:
  /// **'Định vị'**
  String get settingsGroupPositioning;

  /// No description provided for @settingsAppInfo.
  ///
  /// In vi, this message translates to:
  /// **'Phiên bản'**
  String get settingsAppInfo;

  /// No description provided for @settingsServer.
  ///
  /// In vi, this message translates to:
  /// **'Máy chủ định vị'**
  String get settingsServer;

  /// No description provided for @settingsServerSub.
  ///
  /// In vi, this message translates to:
  /// **'Máy ảo dùng 10.0.2.2, điện thoại thật dùng IP nội bộ'**
  String get settingsServerSub;

  /// No description provided for @settingsServerHint.
  ///
  /// In vi, this message translates to:
  /// **'http://<IP>:8000'**
  String get settingsServerHint;

  /// No description provided for @settingsLocalModel.
  ///
  /// In vi, this message translates to:
  /// **'Mô hình cục bộ'**
  String get settingsLocalModel;

  /// No description provided for @settingsLocalModelSub.
  ///
  /// In vi, this message translates to:
  /// **'Định vị ngay trên điện thoại, không cần máy chủ'**
  String get settingsLocalModelSub;

  /// No description provided for @liveOnDevice.
  ///
  /// In vi, this message translates to:
  /// **'trên máy'**
  String get liveOnDevice;

  /// No description provided for @settingsTheme.
  ///
  /// In vi, this message translates to:
  /// **'Chế độ màu'**
  String get settingsTheme;

  /// No description provided for @settingsThemeSystem.
  ///
  /// In vi, this message translates to:
  /// **'Hệ thống'**
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

  /// No description provided for @settingsScanCycle.
  ///
  /// In vi, this message translates to:
  /// **'Định vị liên tục'**
  String get settingsScanCycle;

  /// No description provided for @settingsScanCycleSub.
  ///
  /// In vi, this message translates to:
  /// **'Quét WiFi liên tục khi ứng dụng đang mở'**
  String get settingsScanCycleSub;

  /// No description provided for @settingsPermission.
  ///
  /// In vi, this message translates to:
  /// **'Vị trí và WiFi'**
  String get settingsPermission;

  /// No description provided for @settingsPermissionGranted.
  ///
  /// In vi, this message translates to:
  /// **'Đã cấp'**
  String get settingsPermissionGranted;

  /// No description provided for @settingsPermissionMissing.
  ///
  /// In vi, this message translates to:
  /// **'Chạm để cấp quyền'**
  String get settingsPermissionMissing;

  /// No description provided for @settingsPermissionBlocked.
  ///
  /// In vi, this message translates to:
  /// **'Bị chặn — chạm để mở Cài đặt'**
  String get settingsPermissionBlocked;

  /// No description provided for @errWifiPermission.
  ///
  /// In vi, this message translates to:
  /// **'Cần quyền vị trí để quét WiFi. Chạm để cấp quyền.'**
  String get errWifiPermission;

  /// No description provided for @errWifiBlocked.
  ///
  /// In vi, this message translates to:
  /// **'Quyền vị trí đang bị chặn. Chạm để mở Cài đặt.'**
  String get errWifiBlocked;

  /// No description provided for @errLocationOff.
  ///
  /// In vi, this message translates to:
  /// **'Dịch vụ vị trí đang tắt. Hãy bật lên để định vị.'**
  String get errLocationOff;

  /// No description provided for @errWifiUnsupported.
  ///
  /// In vi, this message translates to:
  /// **'Thiết bị không hỗ trợ quét WiFi.'**
  String get errWifiUnsupported;

  /// No description provided for @errScanFailed.
  ///
  /// In vi, this message translates to:
  /// **'Không quét được WiFi, đang thử lại…'**
  String get errScanFailed;

  /// No description provided for @errNotEnoughAp.
  ///
  /// In vi, this message translates to:
  /// **'Chỉ khớp {so}/{can} access point cần thiết. Bạn có đang ở trong thư viện?'**
  String errNotEnoughAp(int so, int can);

  /// No description provided for @errBadAddress.
  ///
  /// In vi, this message translates to:
  /// **'Địa chỉ máy chủ không hợp lệ: {diaChi}'**
  String errBadAddress(String diaChi);

  /// No description provided for @errNoConnection.
  ///
  /// In vi, this message translates to:
  /// **'Không kết nối được máy chủ {diaChi}'**
  String errNoConnection(String diaChi);

  /// No description provided for @errServer.
  ///
  /// In vi, this message translates to:
  /// **'Máy chủ trả lỗi {ma}'**
  String errServer(int ma);

  /// No description provided for @errBadFormat.
  ///
  /// In vi, this message translates to:
  /// **'Ứng dụng và máy chủ không hiểu gói tin của nhau.'**
  String get errBadFormat;

  /// No description provided for @errTimeout.
  ///
  /// In vi, this message translates to:
  /// **'Máy chủ không phản hồi kịp.'**
  String get errTimeout;

  /// No description provided for @mapFilter.
  ///
  /// In vi, this message translates to:
  /// **'Lớp bản đồ'**
  String get mapFilter;

  /// No description provided for @buildingFull.
  ///
  /// In vi, this message translates to:
  /// **'Thư viện Đại học Đà Lạt'**
  String get buildingFull;
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
