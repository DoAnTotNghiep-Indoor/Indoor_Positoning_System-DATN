import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';

import 'l10n/app_localizations.dart';
import 'theme/app_settings.dart';
import 'theme/app_theme.dart';
import 'widgets/blob_background.dart';
import 'screens/home_screen.dart';
import 'screens/map_screen.dart';
import 'screens/search_screen.dart';
import 'screens/settings_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Nạp trước shader để khung hình đầu tiên đã có kính thật, không bị nháy.
  await LiquidGlassWidgets.initialize();

  // brightnessResolver là bắt buộc khi dùng MaterialApp: thiếu nó thì viền và
  // bóng của kính đọc theo sáng/tối của HỆ ĐIỀU HÀNH thay vì theo ThemeMode của
  // app, nên người dùng chọn "Sáng" trên máy đang để tối sẽ thấy kính biến mất.
  runApp(LiquidGlassWidgets.wrap(
    child: const IpsDluApp(),
    brightnessResolver: Theme.maybeBrightnessOf,
  ));
}

class IpsDluApp extends StatefulWidget {
  const IpsDluApp({super.key});

  @override
  State<IpsDluApp> createState() => _IpsDluAppState();
}

class _IpsDluAppState extends State<IpsDluApp> {
  final _tuyChon = AppSettings();

  @override
  void dispose() {
    _tuyChon.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppSettingsScope(
      settings: _tuyChon,
      child: AnimatedBuilder(
        animation: _tuyChon,
        builder: (context, _) => MaterialApp(
          onGenerateTitle: (context) => L.of(context).appTitle,
          debugShowCheckedModeBanner: false,

          theme: AppTheme.light,
          darkTheme: AppTheme.dark,
          themeMode: _tuyChon.cheDo,

          locale: _tuyChon.ngonNgu,
          localizationsDelegates: L.localizationsDelegates,
          supportedLocales: L.supportedLocales,

          // Scaffold của Material vốn dựng một Material bên trong, và chính nó
          // cấp DefaultTextStyle cho cả cây widget. GlassScaffold không phải
          // Material nên mất thứ đó: mọi Text dựa vào kế thừa kiểu chữ sẽ rơi về
          // kiểu dự phòng của Flutter — monospace kèm gạch chân vàng. Chỉ chữ
          // nào ghi đủ `style:` mới hiện đúng, nên lỗi lộ ra loang lổ.
          //
          // MaterialType.transparency dựng Material mà KHÔNG vẽ nền, nên vừa
          // trả lại DefaultTextStyle vừa không che mất lớp kính phía sau.
          builder: (context, child) => Material(
            type: MaterialType.transparency,
            child: child ?? const SizedBox.shrink(),
          ),
          home: const AppShell(),
        ),
      ),
    );
  }
}

/// Khung chính: nền blob + thanh điều hướng kính, đổi nội dung theo tab.
///
/// `GlassScaffold` lo phần nền, thứ tự lớp và làm mờ mép. Kính khúc xạ theo thứ
/// nằm phía sau nó, nên nền phải do scaffold cấp chứ không để từng màn hình tự
/// dựng — đó là lý do `BlobBackground` nằm ở đây.
class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;
  bool _searching = false;
  final _timKiem = TextEditingController();

  @override
  void dispose() {
    _timKiem.dispose();
    super.dispose();
  }

  /// Mỗi màn hình có bộ blob riêng để nền không lặp lại khi chuyển tab.
  List<Blob> get _blobs {
    if (_searching) return BlobBackground.listBlobs;
    return switch (_index) {
      0 => BlobBackground.homeBlobs,
      1 => BlobBackground.mapBlobs,
      _ => BlobBackground.listBlobs,
    };
  }

  Widget get _noiDung {
    if (_searching) return SearchScreen(tuKhoa: _timKiem.text);
    return switch (_index) {
      0 => const HomeScreen(),
      1 => const MapScreen(),
      _ => const SettingsScreen(),
    };
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);

    // GlassTab nhận Widget chứ không nhận IconData, nên bọc trong Icon().
    final tabs = <GlassTab>[
      GlassTab(
        icon: const Icon(Icons.home_outlined),
        activeIcon: const Icon(Icons.home),
        label: t.tabHome,
      ),
      GlassTab(
        icon: const Icon(Icons.map_outlined),
        activeIcon: const Icon(Icons.map),
        label: t.tabMap,
      ),
      GlassTab(
        icon: const Icon(Icons.settings_outlined),
        activeIcon: const Icon(Icons.settings),
        label: t.tabSettings,
      ),
    ];

    return GlassScaffold(
      background: BlobBackground(blobs: _blobs),
      // KHÔNG dùng GlassStatusBarStyle.auto: tài liệu thư viện ghi rõ nó chọn
      // theo MediaQuery platform brightness, tức độ sáng của HỆ ĐIỀU HÀNH chứ
      // không phải ThemeMode của app. Máy để chế độ sáng mà app đang tối thì
      // auto chọn biểu tượng tối, đặt lên nền tối thành vô hình — đo được tương
      // phản chỉ 0,3/255. Cùng một họ lỗi với brightnessResolver ở main().
      statusBarStyle: Theme.of(context).brightness == Brightness.dark
          ? GlassStatusBarStyle.light
          : GlassStatusBarStyle.dark,
      body: _noiDung,
      bottomBar: GlassTabBar.searchable(
        tabs: tabs,
        selectedIndex: _index,
        isSearchActive: _searching,
        onTabSelected: (i) => setState(() {
          _index = i;
          _searching = false;
        }),
        searchConfig: GlassSearchBarConfig(
          hintText: t.searchHint,
          controller: _timKiem,
          // Mặc định của thư viện là CupertinoIcons.search, trong khi cả app
          // dùng bộ Material — đặt tường minh để nét icon đồng bộ.
          searchIcon: const Icon(Icons.search, size: 20),
          onSearchToggle: (dangMo) => setState(() => _searching = dangMo),
          onChanged: (_) => setState(() {}),
        ),
      ),
    );
  }
}
