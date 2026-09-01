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

  /// Nhãn trợ năng cho dải ảnh thật ở màn Chi tiết
  ///
  /// In vi, this message translates to:
  /// **'{so, plural, other{{so} ảnh của khu vực, vuốt ngang để xem}}'**
  String detailPhotos(int so);

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

  /// Chu kỳ quét, lấy từ TheoDoiViTri.chuKy chứ không viết cứng
  ///
  /// In vi, this message translates to:
  /// **'Quét lại mỗi {giay} giây'**
  String settingsAutoUpdateSub(int giay);

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

  /// No description provided for @settingsPermissionMissing.
  ///
  /// In vi, this message translates to:
  /// **'Chưa cấp'**
  String get settingsPermissionMissing;

  /// No description provided for @settingsPermissionBlocked.
  ///
  /// In vi, this message translates to:
  /// **'Bị chặn'**
  String get settingsPermissionBlocked;

  /// No description provided for @settingsPermissionChecking.
  ///
  /// In vi, this message translates to:
  /// **'Đang kiểm tra…'**
  String get settingsPermissionChecking;

  /// No description provided for @settingsPermissionAsk.
  ///
  /// In vi, this message translates to:
  /// **'Chạm để cấp quyền'**
  String get settingsPermissionAsk;

  /// No description provided for @settingsPermissionOpen.
  ///
  /// In vi, this message translates to:
  /// **'Chạm để mở Cài đặt hệ thống'**
  String get settingsPermissionOpen;

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

  /// No description provided for @liveStart.
  ///
  /// In vi, this message translates to:
  /// **'Bắt đầu định vị'**
  String get liveStart;

  /// No description provided for @liveStop.
  ///
  /// In vi, this message translates to:
  /// **'Dừng định vị'**
  String get liveStop;

  /// No description provided for @liveScanning.
  ///
  /// In vi, this message translates to:
  /// **'Đang quét WiFi…'**
  String get liveScanning;

  /// No description provided for @liveDemo.
  ///
  /// In vi, this message translates to:
  /// **'Đang hiển thị dữ liệu demo'**
  String get liveDemo;

  /// No description provided for @liveCoords.
  ///
  /// In vi, this message translates to:
  /// **'x {x} m · y {y} m'**
  String liveCoords(String x, String y);

  /// No description provided for @liveMatched.
  ///
  /// In vi, this message translates to:
  /// **'Khớp {so} access point'**
  String liveMatched(int so);

  /// No description provided for @liveModel.
  ///
  /// In vi, this message translates to:
  /// **'Mô hình {ten} · {ms} ms'**
  String liveModel(String ten, String ms);

  /// No description provided for @liveMerged.
  ///
  /// In vi, this message translates to:
  /// **'Đã gộp {so} lần quét'**
  String liveMerged(int so);

  /// No description provided for @errWifiPermission.
  ///
  /// In vi, this message translates to:
  /// **'Chưa được cấp quyền vị trí. Ứng dụng sẽ hỏi lại khi bạn bấm bắt đầu.'**
  String get errWifiPermission;

  /// No description provided for @errWifiBlocked.
  ///
  /// In vi, this message translates to:
  /// **'Quyền vị trí đang bị chặn. Mở Cài đặt hệ thống để cấp lại.'**
  String get errWifiBlocked;

  /// No description provided for @errLocationOff.
  ///
  /// In vi, this message translates to:
  /// **'Dịch vụ vị trí đang tắt. Bật lên rồi thử lại.'**
  String get errLocationOff;

  /// No description provided for @errWifiUnsupported.
  ///
  /// In vi, this message translates to:
  /// **'Thiết bị không hỗ trợ quét WiFi.'**
  String get errWifiUnsupported;

  /// No description provided for @errScanFailed.
  ///
  /// In vi, this message translates to:
  /// **'Không quét được WiFi. Thử lại sau ít giây.'**
  String get errScanFailed;

  /// Quét được WiFi nhưng không đủ AP quen; máy chủ trả 422
  ///
  /// In vi, this message translates to:
  /// **'Không đủ dữ liệu để định vị — chỉ khớp {so}/{can} access point của thư viện. Bạn có đang ở trong thư viện không?'**
  String errNotEnoughAp(int so, int can);

  /// Địa chỉ trong Cài đặt thiếu http:// hoặc thiếu tên máy
  ///
  /// In vi, this message translates to:
  /// **'Địa chỉ máy chủ không hợp lệ: {diaChi}. Cần đủ dạng http://<IP>:<cổng>'**
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
  /// **'Máy chủ trả dữ liệu không đúng định dạng.'**
  String get errBadFormat;

  /// No description provided for @settingsServerHint.
  ///
  /// In vi, this message translates to:
  /// **'Nhập địa chỉ máy chủ'**
  String get settingsServerHint;

  /// No description provided for @settingsServerSub.
  ///
  /// In vi, this message translates to:
  /// **'Máy ảo dùng 10.0.2.2, điện thoại thật dùng IP nội bộ'**
  String get settingsServerSub;

  /// No description provided for @a11yToggleTracking.
  ///
  /// In vi, this message translates to:
  /// **'Bật hoặc tắt định vị theo thời gian thực'**
  String get a11yToggleTracking;

  /// No description provided for @errTimeout.
  ///
  /// In vi, this message translates to:
  /// **'Máy chủ không phản hồi kịp. Kiểm tra lại chất lượng mạng.'**
  String get errTimeout;

  /// No description provided for @detailPointCount.
  ///
  /// In vi, this message translates to:
  /// **'{so} điểm đo'**
  String detailPointCount(int so);

  /// No description provided for @detailPhotoCount.
  ///
  /// In vi, this message translates to:
  /// **'{so} ảnh'**
  String detailPhotoCount(int so);

  /// No description provided for @detailNeedPosition.
  ///
  /// In vi, this message translates to:
  /// **'Bật định vị để chỉ đường'**
  String get detailNeedPosition;

  /// No description provided for @detailRouteLoading.
  ///
  /// In vi, this message translates to:
  /// **'Đang tìm đường…'**
  String get detailRouteLoading;

  /// No description provided for @detailRouteFailed.
  ///
  /// In vi, this message translates to:
  /// **'Không tìm được đường tới đây'**
  String get detailRouteFailed;

  /// No description provided for @routeSummary.
  ///
  /// In vi, this message translates to:
  /// **'{met} m · {buoc} bước'**
  String routeSummary(String met, int buoc);

  /// No description provided for @routeStep.
  ///
  /// In vi, this message translates to:
  /// **'{huong} {met} m tới {noi}'**
  String routeStep(String huong, String met, String noi);

  /// No description provided for @stepStraight.
  ///
  /// In vi, this message translates to:
  /// **'Đi thẳng'**
  String get stepStraight;

  /// No description provided for @stepSlightLeft.
  ///
  /// In vi, this message translates to:
  /// **'Chếch trái'**
  String get stepSlightLeft;

  /// No description provided for @stepSlightRight.
  ///
  /// In vi, this message translates to:
  /// **'Chếch phải'**
  String get stepSlightRight;

  /// No description provided for @stepLeft.
  ///
  /// In vi, this message translates to:
  /// **'Rẽ trái'**
  String get stepLeft;

  /// No description provided for @stepRight.
  ///
  /// In vi, this message translates to:
  /// **'Rẽ phải'**
  String get stepRight;

  /// No description provided for @stepUTurn.
  ///
  /// In vi, this message translates to:
  /// **'Quay đầu'**
  String get stepUTurn;

  /// No description provided for @mapOpenDetail.
  ///
  /// In vi, this message translates to:
  /// **'Mở chi tiết khu vực'**
  String get mapOpenDetail;
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
