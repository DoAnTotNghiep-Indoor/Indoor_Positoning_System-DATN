import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';

import 'l10n/app_localizations.dart';
import 'services/theo_doi_vi_tri.dart';
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

  // brightnessResolver bắt buộc khi dùng MaterialApp: thiếu nó thì viền và bóng
  // của kính đọc theo sáng/tối của HỆ ĐIỀU HÀNH chứ không theo ThemeMode của
  // app, nên chọn "Sáng" trên máy đang để tối là kính biến mất. Cùng họ lỗi với
  // GlassStatusBarStyle.auto ở AppShell bên dưới.
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
  final _tuyChon = AppSettings(kho: const KhoMacDinh());
  late final _theoDoi = TheoDoiViTri(diaChiMayChu: _tuyChon.diaChiMayChu);

  late final AppLifecycleListener _vongDoi;

  @override
  void initState() {
    super.initState();
    _tuyChon.addListener(_dongBoMayChu);
    _tuyChon.nap();
    _vongDoi = AppLifecycleListener(onStateChange: _theoDoi.doiVongDoi);
  }

  void _dongBoMayChu() => _theoDoi.doiMayChu(_tuyChon.diaChiMayChu);

  @override
  void dispose() {
    _vongDoi.dispose();
    _tuyChon.removeListener(_dongBoMayChu);
    _theoDoi.dispose();
    _tuyChon.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Hai scope bọc NGOÀI MaterialApp, không phải trong `home:`. Route đẩy
    // chồng lên — màn Chi tiết, tấm tóm tắt trên sơ đồ — dựng ở nhánh khác của
    // cây nên chỉ thấy được scope nào nằm trên Navigator. Dời xuống dưới là
    // chúng ném "Thiếu TheoDoiViTriScope" ngay lần chạm đầu tiên.
    return AppSettingsScope(
      settings: _tuyChon,
      child: TheoDoiViTriScope(
        theoDoi: _theoDoi,
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

            // GlassScaffold không phải Material nên không cấp DefaultTextStyle:
            // thiếu lớp này thì mọi Text không ghi rõ `style:` rơi về kiểu dự
            // phòng monospace kèm gạch chân vàng. `transparency` trả lại
            // DefaultTextStyle mà không vẽ nền che mất lớp kính.
            builder: (context, child) => Material(
              type: MaterialType.transparency,
              child: child ?? const SizedBox.shrink(),
            ),
            home: const AppShell(),
          ),
        ),
      ),
    );
  }
}

/// Khung chính: nền blob + thanh điều hướng kính, đổi nội dung theo tab.
///
/// Kính khúc xạ theo thứ nằm phía sau scaffold, nên nền phải do scaffold cấp
/// chứ không để từng màn hình tự dựng.
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

    // GlassTab nhận Widget chứ không IconData.
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
      // KHÔNG dùng GlassStatusBarStyle.auto: nó chọn theo độ sáng của HỆ ĐIỀU
      // HÀNH chứ không theo ThemeMode, nên máy để sáng mà app đang tối thì biểu
      // tượng tối đặt lên nền tối — đo được tương phản 0,3/255.
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
          // Mặc định thư viện là CupertinoIcons, cả app dùng bộ Material.
          searchIcon: const Icon(Icons.search, size: 20),
          onSearchToggle: (dangMo) => setState(() => _searching = dangMo),
          onChanged: (_) => setState(() {}),
        ),
      ),
    );
  }
}
