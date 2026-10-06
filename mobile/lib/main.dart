import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';

import 'l10n/app_localizations.dart';
import 'screens/home_screen.dart';
import 'screens/map_screen.dart';
import 'screens/search_screen.dart';
import 'screens/settings_screen.dart';
import 'services/api_dinh_vi.dart';
import 'services/theo_doi_vi_tri.dart';
import 'theme/app_settings.dart';
import 'theme/app_theme.dart';
import 'widgets/the_khu_vuc.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await LiquidGlassWidgets.initialize(enablePerformanceMonitor: false);

  // brightnessResolver: thiếu nó kính đọc sáng/tối của HỆ ĐIỀU HÀNH chứ không
  // theo ThemeMode của app, chọn "Sáng" trên máy để tối là viền kính biến mất.
  runApp(LiquidGlassWidgets.wrap(
    child: const IpsDluApp(),
    brightnessResolver: Theme.maybeBrightnessOf,
    theme: glassTheme,
  ));
}

class IpsDluApp extends StatefulWidget {
  const IpsDluApp({super.key});

  @override
  State<IpsDluApp> createState() => _IpsDluAppState();
}

class _IpsDluAppState extends State<IpsDluApp> {
  final _tuyChon = AppSettings();
  late final _theoDoi = TheoDoiViTri(api: ApiDinhVi(_tuyChon.diaChiMayChu));
  late final AppLifecycleListener _vongDoi;

  @override
  void initState() {
    super.initState();
    _vongDoi = AppLifecycleListener(onStateChange: _theoDoi.doiVongDoi);
    _theoDoi.taiNhan();
    // Nạp tuỳ chọn đã lưu TRƯỚC khi quét, không thì vòng đầu gọi nhầm
    // địa chỉ mặc định.
    _tuyChon.nap().whenComplete(() {
      _dongBo();
      _tuyChon.addListener(_dongBo);
      _theoDoi.batDau();
    });
  }

  void _dongBo() => _theoDoi
    ..doiMayChu(_tuyChon.diaChiMayChu)
    ..doiCheDo(cucBo: _tuyChon.moHinhCucBo);

  @override
  void dispose() {
    _vongDoi.dispose();
    _tuyChon.removeListener(_dongBo);
    _theoDoi.dispose();
    _tuyChon.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Scope bọc NGOÀI MaterialApp để popup (route khác) cũng thấy được.
    return AppSettingsScope(
      settings: _tuyChon,
      child: TheoDoiViTriScope(
        theoDoi: _theoDoi,
        child: ListenableBuilder(
          listenable: _tuyChon,
          builder: (context, _) => MaterialApp(
            onGenerateTitle: (context) => L.of(context).appTitle,
            debugShowCheckedModeBanner: false,
            theme: AppTheme.light,
            darkTheme: AppTheme.dark,
            themeMode: _tuyChon.cheDo,
            locale: _tuyChon.ngonNgu,
            localizationsDelegates: L.localizationsDelegates,
            supportedLocales: L.supportedLocales,
            // GlassScaffold không dựng Material nên thiếu DefaultTextStyle.
            builder: (context, child) =>
                Material(type: MaterialType.transparency, child: child),
            home: const AppShell(),
          ),
        ),
      ),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _tab = 0;
  bool _dangTim = false;
  final _tuKhoa = TextEditingController();

  @override
  void initState() {
    super.initState();
    yeuCauMoBanDo.addListener(_moBanDo);
  }

  void _moBanDo() => setState(() {
        _tab = 1;
        _dangTim = false;
      });

  @override
  void dispose() {
    yeuCauMoBanDo.removeListener(_moBanDo);
    _tuKhoa.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final toi = Theme.of(context).brightness == Brightness.dark;

    // Giữ Trang chủ khi mở tìm kiếm: dựng lại lúc đóng tốn ~16 ms trên X300.
    final trangChu = !_dangTim && _tab == 0;
    final noiDung = Stack(
      fit: StackFit.expand,
      children: [
        Offstage(
          offstage: !trangChu,
          child: TickerMode(enabled: trangChu, child: const HomeScreen()),
        ),
        if (_dangTim)
          SearchScreen(tuKhoa: _tuKhoa)
        else if (_tab == 1)
          const MapScreen()
        else if (_tab == 2)
          const SettingsScreen(),
      ],
    );

    return PopScope(
      canPop: !_dangTim && _tab == 0,
      onPopInvokedWithResult: (daPop, _) {
        if (daPop) return;
        setState(() => _dangTim ? _dangTim = false : _tab = 0);
      },
      child: GlassScaffold(
        background: DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [m.nenTren, m.nenDuoi],
            ),
          ),
        ),
        // edgeFade vẽ một dải nền đè lên nội dung dưới thanh tab (thành "mảng"
        // mà thanh nổi lên trên) và thêm một lớp ShaderMask mỗi khung hình.
        edgeFade: false,
        statusBarStyle:
            toi ? GlassStatusBarStyle.light : GlassStatusBarStyle.dark,
        body: noiDung,
        bottomBar: GlassTabBar.searchable(
          tabs: [
            GlassTab(
              icon: const Icon(Icons.home_outlined),
              activeIcon: const Icon(Icons.home_rounded),
              label: t.tabHome,
            ),
            GlassTab(
              icon: const Icon(Icons.map_outlined),
              activeIcon: const Icon(Icons.map_rounded),
              label: t.tabMap,
            ),
            GlassTab(
              icon: const Icon(Icons.settings_outlined),
              activeIcon: const Icon(Icons.settings_rounded),
              label: t.tabSettings,
            ),
          ],
          settings: kinhNoi(context),
          selectedIndex: _tab,
          isSearchActive: _dangTim,
          onTabSelected: (i) => setState(() {
            _tab = i;
            _dangTim = false;
          }),
          searchConfig: GlassSearchBarConfig(
            hintText: t.searchHint,
            controller: _tuKhoa,
            searchIcon: const Icon(Icons.search, size: 20),
            onSearchToggle: (mo) => setState(() => _dangTim = mo),
          ),
        ),
      ),
    );
  }
}
