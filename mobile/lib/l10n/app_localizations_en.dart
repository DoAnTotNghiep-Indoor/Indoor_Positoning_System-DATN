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
  String get floorLine => 'Floor 1 · Da Lat University Library';

  @override
  String get homeYouAreAt => 'You are at';

  @override
  String get homeQuickAccess => 'Quick access';

  @override
  String get homeNearby => 'Nearby';

  @override
  String get homeAllAreas => 'All areas';

  @override
  String get liveLocating => 'Locating you…';

  @override
  String liveCoords(String x, String y) {
    return 'x $x · y $y';
  }

  @override
  String liveInfo(int so, String moHinh, String ms) {
    return '$so APs matched · $moHinh · $ms ms';
  }

  @override
  String liveStale(int giay) {
    return 'Location from $giay s ago';
  }

  @override
  String get mapFloorOne => 'Floor 1';

  @override
  String get mapFloorPlanLabel => 'Floor 1 plan';

  @override
  String get mapFilterAll => 'All';

  @override
  String mapRouteChip(String met, String noi) {
    return '$met m to $noi';
  }

  @override
  String mapArrived(String noi) {
    return 'Arrived at $noi';
  }

  @override
  String get mapClearRoute => 'Clear route';

  @override
  String get mapResetRotation => 'Reset map rotation';

  @override
  String get mapShowSection => 'Show';

  @override
  String get mapShowPoints => 'Reference points';

  @override
  String get mapShowLabels => 'Area names';

  @override
  String get mapAreaSection => 'Areas';

  @override
  String searchResultCount(int count) {
    return '$count results';
  }

  @override
  String get searchEmpty => 'No matching areas found';

  @override
  String get searchEmptyHint => 'Try another keyword or pick \"All\".';

  @override
  String get searchFilterAll => 'All';

  @override
  String get searchFilterStudy => 'Study';

  @override
  String get searchFilterService => 'Services';

  @override
  String get searchFilterWays => 'Ways';

  @override
  String get placeGo => 'Directions';

  @override
  String get placeWaiting => 'Waiting for your location…';

  @override
  String get placeRouting => 'Finding a route…';

  @override
  String get placeRouteFailed => 'Could not find a route here';

  @override
  String get placeHere => 'You are here';

  @override
  String distanceMeters(int met) {
    return '$met m';
  }

  @override
  String get a11yOpenArea => 'Open area info';

  @override
  String get settingsTitle => 'Settings';

  @override
  String get settingsGroupGeneral => 'General';

  @override
  String get settingsGroupAppearance => 'Appearance';

  @override
  String get settingsGroupPositioning => 'Positioning';

  @override
  String get settingsAppInfo => 'Version';

  @override
  String get settingsServer => 'Positioning server';

  @override
  String get settingsServerSub =>
      'Emulator uses 10.0.2.2, a real phone needs the LAN IP';

  @override
  String get settingsServerHint => 'http://<IP>:8000';

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
  String get settingsScanCycle => 'Continuous positioning';

  @override
  String get settingsScanCycleSub =>
      'Scans WiFi continuously while the app is open';

  @override
  String get settingsPermission => 'Location and WiFi';

  @override
  String get settingsPermissionGranted => 'Granted';

  @override
  String get settingsPermissionMissing => 'Tap to grant';

  @override
  String get settingsPermissionBlocked => 'Blocked — tap to open Settings';

  @override
  String get errWifiPermission =>
      'Location permission is needed to scan WiFi. Tap to grant.';

  @override
  String get errWifiBlocked =>
      'Location permission is blocked. Tap to open Settings.';

  @override
  String get errLocationOff =>
      'Location services are off. Turn them on to locate you.';

  @override
  String get errWifiUnsupported => 'This device cannot scan WiFi.';

  @override
  String get errScanFailed => 'WiFi scan failed, retrying…';

  @override
  String errNotEnoughAp(int so, int can) {
    return 'Only $so of the $can required access points matched. Are you inside the library?';
  }

  @override
  String errBadAddress(String diaChi) {
    return 'Invalid server address: $diaChi';
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
  String get errBadFormat =>
      'The app and the server could not parse each other\'s packets.';

  @override
  String get errTimeout => 'The server did not respond in time.';

  @override
  String get mapFilter => 'Map layers';

  @override
  String get buildingFull => 'Da Lat University Library';
}
