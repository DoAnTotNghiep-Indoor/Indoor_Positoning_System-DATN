import 'package:flutter/material.dart';

/// Tuỳ chọn giao diện của người dùng: chế độ sáng/tối và ngôn ngữ.
///
/// Dùng `InheritedNotifier` thay vì một gói quản lý trạng thái: cả app chỉ có
/// đúng hai giá trị này, và chúng nằm ở gốc cây widget nên không cần cơ chế nào
/// phức tạp hơn. Màn Cài đặt nằm sâu ba tầng nên vẫn cần một cách đọc/ghi từ xa,
/// đó là lý do không để state ngay trong `IpsDluApp`.
///
/// Chưa lưu xuống đĩa — chọn xong thoát app là mất. Việc đó cần `shared_preferences`
/// và sẽ làm cùng lúc với phần lưu cấu hình máy chủ ở giai đoạn nối API.
class AppSettings extends ChangeNotifier {
  ThemeMode _cheDo = ThemeMode.system;

  /// Mặc định tiếng Việt, không theo ngôn ngữ máy.
  ///
  /// Đây là ứng dụng cho thư viện Đại học Đà Lạt nên tiếng Việt là ngôn ngữ
  /// chính; máy cài tiếng Anh vẫn nên mở ra thấy tiếng Việt trước.
  Locale _ngonNgu = const Locale('vi');

  ThemeMode get cheDo => _cheDo;
  Locale get ngonNgu => _ngonNgu;

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
