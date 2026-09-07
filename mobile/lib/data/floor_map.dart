import 'package:flutter/material.dart';

/// Sơ đồ mặt bằng THẬT và phép đổi mét ↔ pixel. Lưới chấm `Map.png` trải
/// 1000 × 605 px, đúng hộp bao 86 × 52 m của bộ điểm tham chiếu, nên lưới
/// chấm chính là hệ toạ độ mét. Trục y hướng LÊN, y = 0 ở cạnh dưới ảnh.
///
/// Số do `tools/trich_ban_do.py` đo; `tests/test_dashboard.py` đối chiếu.
class SoDoThat {
  SoDoThat._();

  static const anh = 'assets/map/Map.png';
  static const rongPx = 1053.0;
  static const caoPx = 651.0;

  static const gocXPx = 24.5;
  static const gocYPx = 625.5;
  static const pxMoiMetX = 11.6279;
  static const pxMoiMetY = 11.6346;

  /// Toạ độ mét của cạnh trái sơ đồ, tức `x` nhỏ nhất trong bộ điểm tham chiếu.
  ///
  /// Có tên riêng để test đối chiếu được: từng nằm trần ở cả ba ngôn ngữ mà
  /// không tệp nào khai, sửa lệch một nơi thì lệch 86 m mà test vẫn xanh.
  static const gocMetX = -43.0;

  /// Bán kính quầng khu vực: nửa trung vị khoảng cách tới điểm gần nhất (7,07 m
  /// trên 44 điểm). Quầng nói "đây là điểm đã đo và vùng quanh nó", không nói
  /// ranh giới phòng — dữ liệu không có ranh giới phòng.
  static const banKinhQuangM = 3.5;

  /// Mét sang toạ độ pixel trong ảnh gốc.
  static Offset sangPixel(double x, double y) =>
      Offset(gocXPx + (x - gocMetX) * pxMoiMetX, gocYPx - y * pxMoiMetY);

  /// Mét sang toạ độ trong khung vẽ rộng [rong] pixel, giữ nguyên tỉ lệ ảnh.
  static Offset sangKhung(double x, double y, double rong) {
    final s = rong / rongPx;
    final p = sangPixel(x, y);
    return Offset(p.dx * s, p.dy * s);
  }

  /// Phép nghịch của [sangKhung]: pixel trong khung rộng [rong] về mét.
  static Offset sangMet(Offset khung, double rong) {
    final s = rong / rongPx;
    return Offset(
      (khung.dx / s - gocXPx) / pxMoiMetX + gocMetX,
      (gocYPx - khung.dy / s) / pxMoiMetY,
    );
  }
}


