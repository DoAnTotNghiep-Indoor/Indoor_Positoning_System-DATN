// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class LEn extends L {
  LEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'IPS DLU';

  @override
  String get tabHome => 'Home';

  @override
  String get tabMap => 'Map';

  @override
  String get tabSettings => 'Settings';

  @override
  String get searchHint => 'Search rooms, areas…';

  @override
  String get homeYouAreAt => 'You are at';

  @override
  String get homeQuickAccess => 'Quick access';

  @override
  String get homeNearby => 'Near you';

  @override
  String get mapFloorOne => 'Floor 1';

  @override
  String get mapRelocate => 'Recentre on me';

  @override
  String mapAreaSummary(int count, int giay) {
    return '$count areas · updated ${giay}s ago';
  }

  @override
  String mapAreaCount(int count) {
    return '$count areas';
  }

  @override
  String get mapFloorPlanLabel => 'Floor 1 plan';

  @override
  String get mapFloorPlanHint => 'Pinch to zoom, drag to pan';

  @override
  String get searchTitle => 'Search';

  @override
  String searchResultCount(int count) {
    return '$count results';
  }

  @override
  String get searchEmpty => 'No matching areas found';

  @override
  String get searchEmptyHint =>
      'Try a different keyword, or clear the active filter.';

  @override
  String get searchClearFilter => 'Clear filter';

  @override
  String get searchFilterAll => 'All';

  @override
  String get searchFilterStudy => 'Study';

  @override
  String get searchFilterFacility => 'Facilities';

  @override
  String get searchFilterInternal => 'Staff only';

  @override
  String get detailGoHere => 'Go here';

  @override
  String get detailImagePlaceholder => 'Area photo';

  @override
  String detailPhotos(int so) {
    String _temp0 = intl.Intl.pluralLogic(
      so,
      locale: localeName,
      other: '$so photos of this area, swipe to browse',
      one: '1 photo of this area, swipe to browse',
    );
    return '$_temp0';
  }

  @override
  String get settingsTitle => 'Settings';

  @override
  String get settingsGroupGeneral => 'GENERAL';

  @override
  String get settingsGroupAppearance => 'APPEARANCE';

  @override
  String get settingsGroupPositioning => 'POSITIONING';

  @override
  String get settingsGroupPermissions => 'PERMISSIONS';

  @override
  String get settingsAppInfo => 'App version';

  @override
  String get settingsServer => 'Positioning server';

  @override
  String get settingsTheme => 'Theme';

  @override
  String get settingsThemeSystem => 'System';

  @override
  String get settingsThemeLight => 'Light';

  @override
  String get settingsThemeDark => 'Dark';

  @override
  String get settingsLanguage => 'Language';

  @override
  String get settingsLanguageVi => 'Tiếng Việt';

  @override
  String get settingsLanguageEn => 'English';

  @override
  String get settingsScanCycle => 'Scan interval';

  @override
  String settingsScanCycleSub(int giay) {
    return 'Every $giay seconds — the rate Android allows';
  }

  @override
  String get settingsPermission => 'Location and WiFi';

  @override
  String get settingsPermissionSub => 'Required for positioning';

  @override
  String get settingsPermissionGranted => 'Granted';

  @override
  String get settingsPermissionMissing => 'Not granted';

  @override
  String get settingsPermissionBlocked => 'Blocked';

  @override
  String get settingsPermissionChecking => 'Checking…';

  @override
  String get settingsPermissionAsk => 'Tap to grant';

  @override
  String get settingsPermissionOpen => 'Tap to open system settings';

  @override
  String get settingsFootnote =>
      'More options will be added in the next version.';

  @override
  String distanceMeters(int met) {
    return '$met m';
  }

  @override
  String get commonBack => 'Back';

  @override
  String get a11yOpenArea => 'Open area details';

  @override
  String get liveStart => 'Start positioning';

  @override
  String get liveStop => 'Stop positioning';

  @override
  String get liveScanning => 'Scanning WiFi…';

  @override
  String get liveIdle => 'Tracking is off';

  @override
  String get liveUnknown => 'Location unknown';

  @override
  String liveCoords(String x, String y) {
    return 'x $x m · y $y m';
  }

  @override
  String liveMatched(int so) {
    return 'Matched $so access points';
  }

  @override
  String liveModel(String ten, String ms) {
    return 'Model $ten · $ms ms';
  }

  @override
  String liveMerged(int so) {
    return 'Merged $so scans';
  }

  @override
  String get errWifiPermission =>
      'Location permission not granted. The app will ask again when you start.';

  @override
  String get errWifiBlocked =>
      'Location permission is blocked. Open system Settings to grant it.';

  @override
  String get errLocationOff =>
      'Location services are off. Turn them on and try again.';

  @override
  String get errWifiUnsupported => 'This device cannot scan WiFi.';

  @override
  String get errScanFailed => 'WiFi scan failed. Try again in a few seconds.';

  @override
  String errNotEnoughAp(int so, int can) {
    return 'Not enough data to locate you — only $so of $can library access points matched. Are you inside the library?';
  }

  @override
  String errBadAddress(String diaChi) {
    return 'Invalid server address: $diaChi. It must look like http://<IP>:<port>';
  }

  @override
  String errNoConnection(String diaChi) {
    return 'Cannot reach the server at $diaChi';
  }

  @override
  String errServer(int ma) {
    return 'Server returned error $ma';
  }

  @override
  String get errBadFormat => 'The server returned malformed data.';

  @override
  String get settingsServerHint => 'Enter server address';

  @override
  String get settingsServerSub =>
      'Emulator uses 10.0.2.2, a real phone needs the LAN IP';

  @override
  String get a11yToggleTracking => 'Turn realtime positioning on or off';

  @override
  String get errTimeout =>
      'The server did not respond in time. Check your network.';

  @override
  String detailPointCount(int so) {
    return '$so survey points';
  }

  @override
  String detailPhotoCount(int so) {
    return '$so photos';
  }

  @override
  String get detailNeedPosition => 'Turn on positioning to get directions';

  @override
  String get detailRouteLoading => 'Finding a route…';

  @override
  String get detailRouteFailed => 'No route to this area';

  @override
  String routeSummary(String met, int buoc) {
    return '$met m · $buoc steps';
  }

  @override
  String routeStep(String huong, String met, String noi) {
    return '$huong $met m to $noi';
  }

  @override
  String get stepStraight => 'Go straight';

  @override
  String get stepSlightLeft => 'Bear left';

  @override
  String get stepSlightRight => 'Bear right';

  @override
  String get stepLeft => 'Turn left';

  @override
  String get stepRight => 'Turn right';

  @override
  String get stepUTurn => 'Turn around';

  @override
  String get mapOpenDetail => 'Open area detail';

  @override
  String get mapFilterAll => 'All';

  @override
  String get mapFilterHint => 'Filter the floor plan by area type';

  @override
  String mapRouteChip(String met, String noi) {
    return '$met m to $noi';
  }

  @override
  String get mapClearRoute => 'Clear route';
}
