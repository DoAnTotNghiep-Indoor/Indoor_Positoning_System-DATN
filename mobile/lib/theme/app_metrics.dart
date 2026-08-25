import 'package:flutter/material.dart';

/// Các số đo bố cục dùng chung.
///
/// Tồn tại vì thanh điều hướng dưới nổi lên trên nội dung (`GlassScaffold` đặt
/// `extendBody: true` để kính khúc xạ được thứ trôi phía sau), nên mọi màn hình
/// đều phải tự chừa chỗ cho nó. Trước đây mỗi màn ghi một số khác nhau — 96, 110
/// — đều là số đoán, và cả hai đều thiếu: nút định vị ở màn Bản đồ đè lên nút
/// tìm kiếm, còn khung toà nhà bị thanh điều hướng cắt mất phần dưới.
class AppMetrics {
  AppMetrics._();

  /// Khớp `barHeight` mặc định của `GlassTabBar.searchable`.
  static const double chieuCaoThanhTab = 64;

  /// Khớp `verticalPadding` mặc định của `GlassTabBar.searchable`.
  static const double lePhiaDuoiThanhTab = 20;

  /// Khoảng trống tối thiểu giữa nội dung và thanh điều hướng.
  static const double khoangHo = 16;

  /// Chiều cao cần chừa ở đáy màn hình để không bị thanh điều hướng che.
  ///
  /// Cộng cả `viewPadding.bottom` vì `GlassScaffold` dựng thanh này bên trong
  /// vùng an toàn, còn thân màn hình thì dùng `SafeArea(bottom: false)` nên toạ
  /// độ `bottom:` của nó tính từ mép màn hình thật.
  static double chuaChoThanhTab(BuildContext context) =>
      chieuCaoThanhTab +
      lePhiaDuoiThanhTab +
      khoangHo +
      MediaQuery.viewPaddingOf(context).bottom;
}
