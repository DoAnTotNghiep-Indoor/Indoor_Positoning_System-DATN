import 'package:flutter/material.dart';

/// Tuỳ chọn của người dùng: chế độ sáng/tối, ngôn ngữ và địa chỉ máy chủ.
///
/// `InheritedNotifier` thay vì một gói quản lý trạng thái — cả app chỉ có ba
/// giá trị và chúng nằm ở gốc cây widget.
///
/// CHƯA lưu xuống đĩa: thoát app là mất, cần `shared_preferences`.
class AppSettings extends ChangeNotifier {
  ThemeMode _cheDo = ThemeMode.system;

  /// Mặc định tiếng Việt chứ không theo ngôn ngữ máy: đây là ứng dụng cho thư
  /// viện Đại học Đà Lạt.
  Locale _ngonNgu = const Locale('vi');

  /// 10.0.2.2 là lối tắt máy ảo Android gọi về máy đang chạy nó; điện thoại
  /// thật phải đổi sang IP nội bộ, nên giá trị này sửa được trong Cài đặt chứ
  /// không viết cứng như đồ án CTK45.
  String _diaChiMayChu = 'http://10.0.2.2:8000';

  ThemeMode get cheDo => _cheDo;
  Locale get ngonNgu => _ngonNgu;
  String get diaChiMayChu => _diaChiMayChu;

  void datCheDo(ThemeMode gt) {
    if (gt == _cheDo) return;
    _cheDo = gt;
    notifyListeners();
  }

  void datNgonNgu(Locale gt) {
    if (gt == _ngonNgu) return;
    _ngonNgu = gt;
    notifyListeners();
  }

  void datDiaChiMayChu(String gt) {
    final sach = gt.trim().replaceAll(RegExp(r'/+$'), '');
    if (sach.isEmpty || sach == _diaChiMayChu) return;
    _diaChiMayChu = sach;
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
