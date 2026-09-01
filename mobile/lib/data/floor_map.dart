import 'package:flutter/material.dart';

/// Sơ đồ mặt bằng THẬT và phép đổi mét ↔ pixel của nó.
///
/// Lưới chấm trong `Map.png` trải đúng 1000 px ngang và 605 px dọc, bằng đúng
/// hộp bao 86 m × 52 m của 40 điểm tham chiếu — hai trục cho cùng một tỉ lệ tới
/// 4 chữ số có nghĩa, nên lưới chấm chính là hệ toạ độ mét.
///
/// Trục y hướng LÊN: y = 0 ở cạnh dưới ảnh, nơi có cửa ra vào. Đây là kết luận
/// từ hình dạng toà nhà chứ không phải quy ước tuỳ chọn.
///
/// Số do `tools/trich_ban_do.py` đo và ghi vào `ban_do_tang1.json`; chép sang
/// đây để app khỏi tải thêm một tệp cấu hình chỉ để vẽ, và `tests/
/// test_dashboard.py` đối chiếu hai nơi.
class SoDoThat {
  SoDoThat._();

  static const anh = 'assets/map/Map.png';
  static const rongPx = 1053.0;
  static const caoPx = 651.0;

  static const gocXPx = 24.5;
  static const gocYPx = 625.5;
  static const pxMoiMetX = 11.6279;
  static const pxMoiMetY = 11.6346;

  /// Mét sang toạ độ pixel trong ảnh gốc.
  static Offset sangPixel(double x, double y) =>
      Offset(gocXPx + (x + 43.0) * pxMoiMetX, gocYPx - y * pxMoiMetY);

  /// Mét sang toạ độ trong khung vẽ rộng [rong] pixel, giữ nguyên tỉ lệ ảnh.
  static Offset sangKhung(double x, double y, double rong) {
    final s = rong / rongPx;
    final p = sangPixel(x, y);
    return Offset(p.dx * s, p.dy * s);
  }
}


