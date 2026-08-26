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
  String homeAccuracy(String met) {
    return 'Accuracy ±$met m';
  }

  @override
  String get homeQuickAccess => 'Quick access';

  @override
  String get homeNearby => 'Near you';

  @override
  String get mapTitle => 'Map';

  @override
  String get mapFloorOne => 'Floor 1';

  @override
  String get mapRelocateDemo =>
      'Demo build — positioning API not connected yet';

  @override
  String get mapRelocate => 'Recentre on me';

  @override
  String mapAreaSummary(int count, int giay) {
    return '$count areas · updated ${giay}s ago';
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
  String get detailRouteDemo => 'Demo build — routing comes in a later stage';

  @override
  String get detailImagePlaceholder => 'Area photo';

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
  String get settingsAutoUpdate => 'Auto-update position';

  @override
  String get settingsAutoUpdateSub => 'Rescan every 2 seconds';

  @override
  String get settingsKeepAwake => 'Keep screen on';

  @override
  String get settingsKeepAwakeSub => 'While viewing the map';

  @override
  String get settingsPermission => 'Location and WiFi';

  @override
  String get settingsPermissionSub => 'Required for positioning';

  @override
  String get settingsPermissionGranted => 'Granted';

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
  String a11yAreaRow(String ten, int met) {
    return '$ten, $met metres away';
  }

  @override
  String get a11yOpenArea => 'Open area details';
}
