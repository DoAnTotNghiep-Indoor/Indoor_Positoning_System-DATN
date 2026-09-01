import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Nơi cất tuỳ chọn giữa hai lần mở ứng dụng.
///
/// Có mặt giao diện này để bài kiểm thử thay được bằng bản trong bộ nhớ —
/// `SharedPreferences` đi qua kênh nền tảng, gọi trong `flutter test` sẽ ném
/// `MissingPluginException`.
abstract class KhoTuyChon {
  Future<String?> doc(String khoa);
  Future<void> ghi(String khoa, String gt);
}

class KhoMacDinh implements KhoTuyChon {
  const KhoMacDinh();

  @override
  Future<String?> doc(String khoa) async =>
      (await SharedPreferences.getInstance()).getString(khoa);

  @override
  Future<void> ghi(String khoa, String gt) async =>
      (await SharedPreferences.getInstance()).setString(khoa, gt);
}

/// Tuỳ chọn của người dùng: chế độ sáng/tối, ngôn ngữ và địa chỉ máy chủ.
///
/// `InheritedNotifier` thay vì một gói quản lý trạng thái — cả app chỉ có ba
/// giá trị và chúng nằm ở gốc cây widget. Cả ba lưu xuống đĩa: địa chỉ máy chủ
/// là IP nội bộ của máy chạy backend, bắt gõ lại mỗi lần mở app là hỏng buổi
/// demo. [kho] để null thì không lưu gì, đó là chế độ kiểm thử dùng.
class AppSettings extends ChangeNotifier {
  static const _khoaCheDo = 'che_do';
  static const _khoaNgonNgu = 'ngon_ngu';
  static const _khoaMayChu = 'dia_chi_may_chu';

  final KhoTuyChon? _kho;

  AppSettings({KhoTuyChon? kho}) : _kho = kho;

  ThemeMode _cheDo = ThemeMode.system;

  /// Mặc định tiếng Việt chứ không theo ngôn ngữ máy: đây là ứng dụng cho thư
  /// viện Đại học Đà Lạt.
  Locale _ngonNgu = const Locale('vi');

  /// 10.0.2.2 là lối tắt máy ảo Android gọi về máy đang chạy nó; điện thoại
  /// thật phải đổi sang IP nội bộ, nên giá trị này sửa được trong Cài đặt chứ
  /// không viết cứng như đồ án CTK45.
  String _diaChiMayChu = 'http://10.0.2.2:8000';

  /// Đọc lại tuỳ chọn đã lưu. Hỏng thì bỏ qua và giữ giá trị mặc định — không
  /// mở được ứng dụng vì một tuỳ chọn giao diện là cái giá quá đắt.
  Future<void> nap() async {
    final kho = _kho;
    if (kho == null) return;
    try {
      final cheDo = await kho.doc(_khoaCheDo);
      final ngonNgu = await kho.doc(_khoaNgonNgu);
      final mayChu = await kho.doc(_khoaMayChu);

      if (cheDo != null) {
        _cheDo = ThemeMode.values.firstWhere((m) => m.name == cheDo,
            orElse: () => _cheDo);
      }
      if (ngonNgu != null && ngonNgu.isNotEmpty) _ngonNgu = Locale(ngonNgu);
      if (mayChu != null && mayChu.isNotEmpty) _diaChiMayChu = mayChu;
    } catch (_) {
      return;
    }
    notifyListeners();
  }

  // Không await: người dùng vừa bấm xong thì giao diện phải đổi ngay, còn việc
  // ghi đĩa hỏng hay không cũng không đổi được gì trong phiên này.
  void _luu(String khoa, String gt) => _kho?.ghi(khoa, gt).catchError((_) {});

  ThemeMode get cheDo => _cheDo;
  Locale get ngonNgu => _ngonNgu;
  String get diaChiMayChu => _diaChiMayChu;

  void datCheDo(ThemeMode gt) {
    if (gt == _cheDo) return;
    _cheDo = gt;
    _luu(_khoaCheDo, gt.name);
    notifyListeners();
  }

  void datNgonNgu(Locale gt) {
    if (gt == _ngonNgu) return;
    _ngonNgu = gt;
    _luu(_khoaNgonNgu, gt.languageCode);
    notifyListeners();
  }

  void datDiaChiMayChu(String gt) {
    final sach = gt.trim().replaceAll(RegExp(r'/+$'), '');
    if (sach.isEmpty || sach == _diaChiMayChu) return;
    _diaChiMayChu = sach;
    _luu(_khoaMayChu, sach);
    notifyListeners();
  }
}

/// Cấp [AppSettings] cho cả cây widget và dựng lại khi nó đổi.
class AppSettingsScope extends InheritedNotifier<AppSettings> {
  const AppSettingsScope({
    super.key,
    required AppSettings settings,
    required super.child,
  }) : super(notifier: settings);

  static AppSettings of(BuildContext context) {
    final scope =
        context.dependOnInheritedWidgetOfExactType<AppSettingsScope>();
    assert(scope != null, 'Thiếu AppSettingsScope phía trên cây widget');
    return scope!.notifier!;
  }
}
