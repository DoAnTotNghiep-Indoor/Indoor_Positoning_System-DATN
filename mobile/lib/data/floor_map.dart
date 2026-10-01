import 'package:flutter/material.dart';

/// Phép đổi toạ độ lưới ↔ pixel. Lưới chấm `Map.png` trải 1000 × 605 px, đúng
/// hộp bao 86 × 52 đơn vị của bộ điểm tham chiếu, nên lưới chấm chính là hệ toạ
/// độ Bảng 4. Trục y hướng LÊN. Một đơn vị lưới là [metMoiDonVi] mét.
///
/// Số do `tools/trich_ban_do.py` đo; dashboard và backend dùng cùng bộ số.
class SoDoThat {
  SoDoThat._();

  /// Sơ đồ vẽ lại từ bản của trường (`tools/ve_so_do_tang1.py`), cùng khung
  /// pixel với `Map.png` nhưng mở rộng lên trên cho các phòng CTK45 khuyết và
  /// xuống dưới cho hai toà CNTT, hội trường. Bốn số dưới là viewBox của hai tệp SVG.
  static const anh = 'assets/map/so_do_tang1.svg';
  static const anhToi = 'assets/map/so_do_tang1_toi.svg';
  static const khungX = -745.6;
  static const khungY = -195.4;
  static const khungRong = 2539.9;
  static const khungCao = 1754.7;

  /// Tâm khối thư viện (đơn vị lưới), để căn khi chưa có vị trí.
  static const tamToaX = 0.0;
  static const tamToaY = 30.0;

  static const gocXPx = 24.5;
  static const gocYPx = 625.5;
  static const pxMoiMetX = 11.6279;
  static const pxMoiMetY = 11.6346;

  /// Toạ độ mét của cạnh trái sơ đồ, tức `x` nhỏ nhất trong bộ điểm tham chiếu.
  ///
  /// Có tên riêng để test đối chiếu được: từng nằm trần ở cả ba ngôn ngữ mà
  /// không tệp nào khai, sửa lệch một nơi thì lệch 86 m mà test vẫn xanh.
  static const gocMetX = -43.0;

  /// Hình 7 báo cáo CTK45: toà nhà cao 19,6 m trên 55,87 đơn vị lưới.
  static const metMoiDonVi = 0.3508;

  /// Bán kính quầng khu vực: nửa trung vị khoảng cách tới điểm gần nhất (7,07 m
  /// trên 44 điểm). Quầng nói "đây là điểm đã đo và vùng quanh nó", không nói
  /// ranh giới phòng — dữ liệu không có ranh giới phòng.
  static const banKinhQuangM = 3.5;

  static Offset sangPixel(double x, double y) =>
      Offset(gocXPx + (x - gocMetX) * pxMoiMetX, gocYPx - y * pxMoiMetY);

  static Offset sangKhung(double x, double y, double rong) {
    final s = rong / khungRong;
    final p = sangPixel(x, y);
    return Offset((p.dx - khungX) * s, (p.dy - khungY) * s);
  }

  static Offset sangMet(Offset khung, double rong) {
    final s = rong / khungRong;
    return Offset(
      (khung.dx / s + khungX - gocXPx) / pxMoiMetX + gocMetX,
      (gocYPx - khung.dy / s - khungY) / pxMoiMetY,
    );
  }
}
