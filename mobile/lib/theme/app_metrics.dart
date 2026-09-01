import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Các số đo bố cục dùng chung.
///
/// Thanh điều hướng dưới nổi lên TRÊN nội dung (`GlassScaffold` đặt
/// `extendBody: true` để kính khúc xạ được thứ trôi phía sau), nên mọi màn hình
/// phải tự chừa chỗ cho nó.
class AppMetrics {
  AppMetrics._();

  /// Khớp `barHeight` mặc định của `GlassTabBar.searchable`.
  static const double chieuCaoThanhTab = 64;

  /// Khớp `verticalPadding` mặc định của `GlassTabBar.searchable`.
  static const double lePhiaDuoiThanhTab = 20;

  static const double khoangHo = 16;

  /// Chiều cao cần chừa ở đáy để không bị thanh điều hướng che.
  ///
  /// Lấy MAX của `viewPadding.bottom` và `viewInsets.bottom` chứ không chỉ
  /// `viewPadding`: ô tìm kiếm nằm ngay trong thanh điều hướng nên lúc gõ là
  /// bàn phím luôn bật, mà `viewPadding` theo định nghĩa đã bỏ qua bàn phím.
  /// Không cộng dồn hai giá trị — bàn phím bật thì hệ điều hành đã ẩn thanh cử
  /// chỉ, cộng cả hai sẽ thừa một khoảng.
  static double chuaChoThanhTab(BuildContext context) {
    final mq = MediaQuery.of(context);
    return chieuCaoThanhTab +
        lePhiaDuoiThanhTab +
        khoangHo +
        math.max(mq.viewPadding.bottom, mq.viewInsets.bottom);
  }

  /// Ngưỡng của cả Material (48dp) lẫn Apple HIG (44pt); lấy mức cao hơn.
  static const double vungChamToiThieu = 48;

  /// Co giãn một số đo theo cỡ chữ hệ thống, không bao giờ nhỏ hơn thiết kế.
  ///
  /// Hộp đặt cứng chiều cao mà bên trong là chữ sẽ cắt mất chữ kèm vạch sọc
  /// vàng đen khi người dùng chỉnh cỡ chữ lớn.
  static double caoTheoCoChu(
    BuildContext context, {
    required double coBan,
    required double phanChu,
  }) {
    final tyLe = MediaQuery.textScalerOf(context).scale(phanChu) / phanChu;
    return math.max(coBan, coBan - phanChu + phanChu * tyLe);
  }
}
