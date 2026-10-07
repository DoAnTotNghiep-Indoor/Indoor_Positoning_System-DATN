// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class LEn extends L {
  LEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'WiLoc';

  @override
  String get tabHome => 'Home';

  @override
  String get tabMap => 'Map';

  @override
  String get tabSettings => 'Settings';

  @override
  String get searchHint => 'Search places…';

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
  String get liveLocating => 'Determining your location…';

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
    return 'Updated $giay s ago';
  }

  @override
  String get mapFloorOne => 'Floor 1';

  @override
  String get mapFloorPlanLabel => 'Floor 1 plan';

  @override
  String get mapFilterAll => 'All';

  @override
  String mapRouteChip(String met, String noi) {
    return '$noi · $met m left';
  }

  @override
  String mapArrived(String noi) {
    return 'You have arrived at $noi';
  }

  @override
  String get mapClearRoute => 'End directions';

  @override
  String get mapResetRotation => 'Reset map orientation';

  @override
  String get mapShowSection => 'Show';

  @override
  String get mapShowPoints => 'Reference points';

  @override
  String get mapShowLabels => 'Place names';

  @override
  String get mapAreaSection => 'Filter by area';

  @override
  String searchResultCount(int count) {
    return '$count results';
  }

  @override
  String get searchEmpty => 'No matching places';

  @override
  String get searchEmptyHint => 'Try a different keyword or choose \"All\".';

  @override
  String get searchFilterAll => 'All';

  @override
  String get searchFilterStudy => 'Study';

  @override
  String get searchFilterService => 'Services';

  @override
  String get searchFilterWays => 'Walkways';

  @override
  String get placeGo => 'Directions';

  @override
  String get placeWaiting => 'Determining your location…';

  @override
  String get placeRouting => 'Finding a route…';

  @override
  String get placeRouteFailed => 'No route to this place could be found';

  @override
  String get placeHere => 'You are here';

  @override
  String distanceMeters(int met) {
    return '$met m';
  }

  @override
  String get a11yOpenArea => 'Open place details';

  @override
  String get settingsTitle => 'Settings';

  @override
  String get settingsGroupAppearance => 'Appearance';

  @override
  String get settingsGroupPositioning => 'Positioning';

  @override
  String get settingsServer => 'Positioning server';

  @override
  String get settingsServerSub =>
      'Choose a system server or enter a custom address';

  @override
  String get settingsServerHint => 'https://… or http://<IP>:8000';

  @override
  String get settingsServerCustom => 'Custom';

  @override
  String get settingsLocalModel => 'On-device model';

  @override
  String get settingsLocalModelSub =>
      'Estimates your position on the device, independent of the server';

  @override
  String get liveOnDevice => 'on device';

  @override
  String get settingsTheme => 'Appearance';

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
      'Scans WiFi continuously while the app is in use';

  @override
  String settingsScanFresh(String giay, int moi, int tong) {
    return 'WiFi data refreshes every $giay s ($moi/$tong scans)';
  }

  @override
  String get settingsPermission => 'Location and WiFi access';

  @override
  String get settingsPermissionGranted => 'Granted';

  @override
  String get settingsPermissionMissing => 'Tap to grant access';

  @override
  String get settingsPermissionBlocked =>
      'Blocked · tap to open system settings';

  @override
  String get errWifiPermission =>
      'Location access is required to scan WiFi. Tap to grant.';

  @override
  String get errWifiBlocked =>
      'Location access is blocked. Tap to open system settings.';

  @override
  String get errLocationOff =>
      'Location services are off. Turn them on to enable positioning.';

  @override
  String get errWifiUnsupported =>
      'This device does not support WiFi scanning.';

  @override
  String get errScanFailed => 'WiFi scan failed, retrying…';

  @override
  String errNotEnoughAp(int so, int can) {
    return 'Only $so of $can required access points were recognised. You may be outside the library.';
  }

  @override
  String errBadAddress(String diaChi) {
    return 'Invalid server address: $diaChi';
  }

  @override
  String errNoConnection(String diaChi) {
    return 'Unable to connect to the server at $diaChi';
  }

  @override
  String errServer(int ma) {
    return 'The server returned an error (code $ma)';
  }

  @override
  String get errBadFormat => 'The server response has an unexpected format.';

  @override
  String get errTimeout => 'The server did not respond in time.';

  @override
  String get mapFilter => 'Map layers';

  @override
  String get buildingFull => 'Da Lat University Library';

  @override
  String settingsVersionLine(String app, String phienBan) {
    return '$app · version $phienBan';
  }
}
