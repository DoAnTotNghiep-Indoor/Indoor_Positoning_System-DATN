import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Tuỳ chọn người dùng, lưu xuống đĩa vì địa chỉ máy chủ là IP nội bộ — gõ lại
/// mỗi lần mở app là hỏng buổi demo.
class AppSettings extends ChangeNotifier {
  final SharedPreferencesAsync? _kho;

  AppSettings({bool luu = true}) : _kho = luu ? SharedPreferencesAsync() : null;

  ThemeMode _cheDo = ThemeMode.system;
  Locale _ngonNgu = const Locale('vi');

  /// Máy chủ của đồ án trên VM, ra ngoài qua Cloudflare Tunnel. DEMO phát lại lần quét
  /// thật ở thư viện để trình diễn ở nơi khác; mỗi bản một CSDL riêng.
  static const mayChuCoSan = {
    'IPS DLU PROD': 'https://dlu-ips.etylix.me',
    'IPS DLU DEMO': 'https://dlu-ips-demo.etylix.me',
  };

  String _diaChiMayChu = mayChuCoSan['IPS DLU PROD']!;
  bool _moHinhCucBo = false;

  ThemeMode get cheDo => _cheDo;
  Locale get ngonNgu => _ngonNgu;
  String get diaChiMayChu => _diaChiMayChu;

  /// Tên máy chủ có sẵn đang dùng; null là địa chỉ tự nhập.
  String? get tenMayChu {
    for (final e in mayChuCoSan.entries) {
      if (e.value == _diaChiMayChu) return e.key;
    }
    return null;
  }
  bool get moHinhCucBo => _moHinhCucBo;

  Future<void> nap() async {
    final kho = _kho;
    if (kho == null) return;
    try {
      final cheDo = await kho.getString('che_do');
      final ngonNgu = await kho.getString('ngon_ngu');
      final mayChu = await kho.getString('dia_chi_may_chu');
      _moHinhCucBo = await kho.getBool('mo_hinh_cuc_bo') ?? _moHinhCucBo;
      _cheDo = ThemeMode.values.asNameMap()[cheDo] ?? _cheDo;
      if (ngonNgu != null && ngonNgu.isNotEmpty) _ngonNgu = Locale(ngonNgu);
      if (mayChu != null && mayChu.isNotEmpty) _diaChiMayChu = mayChu;
      notifyListeners();
    } catch (_) {
      // hỏng tuỳ chọn thì giữ mặc định, không chặn mở app
    }
  }

  void _luu(String khoa, String gt) =>
      _kho?.setString(khoa, gt).catchError((_) {});

  void datCheDo(ThemeMode gt) {
    if (gt == _cheDo) return;
    _cheDo = gt;
    _luu('che_do', gt.name);
    notifyListeners();
  }

  void datNgonNgu(Locale gt) {
    if (gt == _ngonNgu) return;
    _ngonNgu = gt;
    _luu('ngon_ngu', gt.languageCode);
    notifyListeners();
  }

  void datMoHinhCucBo(bool gt) {
    if (gt == _moHinhCucBo) return;
    _moHinhCucBo = gt;
    _kho?.setBool('mo_hinh_cuc_bo', gt).catchError((_) {});
    notifyListeners();
  }

  void datDiaChiMayChu(String gt) {
    final sach = gt.trim().replaceAll(RegExp(r'/+$'), '');
    if (sach.isEmpty || sach == _diaChiMayChu) return;
    _diaChiMayChu = sach;
    _luu('dia_chi_may_chu', sach);
    notifyListeners();
  }
}

class AppSettingsScope extends InheritedNotifier<AppSettings> {
  const AppSettingsScope({
    super.key,
    required AppSettings settings,
    required super.child,
  }) : super(notifier: settings);

  static AppSettings of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AppSettingsScope>()!.notifier!;
}
