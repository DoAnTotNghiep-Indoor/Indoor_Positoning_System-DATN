import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_compass/flutter_compass.dart';

/// Hướng thiết bị đang quay, quy về hệ toạ độ của SƠ ĐỒ chứ không phải của trái
/// đất: từ kế đọc góc so với bắc, còn sơ đồ vẽ theo trục toà nhà.
class LaBan extends ChangeNotifier {
  /// Phương vị trục +y của sơ đồ so với bắc, độ theo chiều kim đồng hồ.
  ///
  /// Đo trên ảnh Google Maps, ba đường độc lập khớp trong 3,5° — cách đo ghi ở
  /// mục 2.5.1 tài liệu thiết kế. Đừng lẫn với góc NGHIÊNG 22° của lưới nhà so
  /// với trục bắc-nam: lẫn hai đại lượng thì nón lệch 226°, gần như ngược hướng.
  static const gocBacSoDo = 248.5;

  /// Nửa góc mở của nón, độ. Rộng vì từ kế điện thoại thường lệch 10-20°, tệ
  /// hơn nữa khi chưa hiệu chuẩn hoặc đứng cạnh kết cấu thép — chứ không phải
  /// vì [gocBacSoDo] còn mơ hồ.
  static const nuaGocMoDo = 20.0;

  /// Đổi ít hơn ngần này độ thì không báo ra ngoài.
  ///
  /// Từ kế Android bắn 10-50 số đọc mỗi giây, mà mỗi lần báo là dựng lại cả sơ đồ
  /// — kể cả đo bề rộng 26 nhãn. Nón mở [nuaGocMoDo] × 2 = 40° nên xoay dưới 2°
  /// không tạo khác biệt nhìn thấy được.
  static const buocBaoDo = 2.0;

  final Stream<double?>? _nguon;
  StreamSubscription<double?>? _dang;

  /// Truyền `nguon` trong kiểm thử để khỏi cần cảm biến thật.
  LaBan({Stream<double?>? nguon})
      : _nguon = nguon ??
            FlutterCompass.events?.map((e) => e.heading);

  double? _huong;

  /// Hướng đã quy về sơ đồ, độ theo chiều kim đồng hồ từ trục +y. Null khi máy
  /// không có từ kế hoặc chưa có số đọc nào.
  double? get huongSoDo =>
      _huong == null ? null : (_huong! - gocBacSoDo) % 360;

  bool get coCamBien => _nguon != null;

  void batDau() {
    if (_dang != null || _nguon == null) return;
    _dang = _nguon.listen((h) {
      if (h == null) return;
      final cu = _huong;
      _huong = h;
      // So theo cung ngắn hơn trên vòng tròn: 359° và 1° cách nhau 2° chứ
      // không phải 358°, quên chỗ này thì mỗi lần đi qua hướng bắc lại báo một
      // lần thừa.
      if (cu != null && _lechVong(cu, h) < buocBaoDo) return;
      notifyListeners();
    });
  }

  static double _lechVong(double a, double b) {
    final d = (a - b).abs() % 360;
    return d > 180 ? 360 - d : d;
  }

  void dungLai() {
    _dang?.cancel();
    _dang = null;
  }

  @override
  void dispose() {
    dungLai();
    super.dispose();
  }
}
