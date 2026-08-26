import 'dart:math' as math;

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
  ///
  /// Lấy giá trị LỚN HƠN giữa `viewPadding.bottom` và `viewInsets.bottom`, chứ
  /// không chỉ `viewPadding`. `viewInsets.bottom` là chiều cao bàn phím ảo, còn
  /// `viewPadding` theo định nghĩa của Flutter đã bỏ qua bàn phím. Ô tìm kiếm
  /// nằm ngay trong thanh điều hướng nên lúc gõ là bàn phím luôn bật: nếu chỉ
  /// chừa theo `viewPadding` thì mấy kết quả cuối nằm khuất sau bàn phím, cuộn
  /// hết cỡ cũng không thấy. Dùng `max` chứ không cộng dồn vì khi bàn phím bật,
  /// hệ điều hành đã ẩn thanh cử chỉ dưới đáy — cộng cả hai sẽ thừa một khoảng.
  static double chuaChoThanhTab(BuildContext context) {
    final mq = MediaQuery.of(context);
    return chieuCaoThanhTab +
        lePhiaDuoiThanhTab +
        khoangHo +
        math.max(mq.viewPadding.bottom, mq.viewInsets.bottom);
  }

  /// Chiều cao tối thiểu của một vùng chạm, theo hướng dẫn của cả Material
  /// (48dp) và Apple HIG (44pt). Lấy mức 48 cho chắc.
  static const double vungChamToiThieu = 48;

  /// Co giãn một số đo theo cỡ chữ hệ thống, nhưng không bao giờ nhỏ hơn số đo
  /// gốc của thiết kế.
  ///
  /// Dùng cho các hộp có chiều cao đặt cứng mà bên trong là chữ: để nguyên số
  /// cứng thì người dùng chỉnh cỡ chữ lớn trong Cài đặt hệ thống sẽ thấy chữ bị
  /// cắt kèm vạch sọc vàng đen của Flutter.
  static double caoTheoCoChu(
    BuildContext context, {
    required double coBan,
    required double phanChu,
  }) {
    final tyLe = MediaQuery.textScalerOf(context).scale(phanChu) / phanChu;
    return math.max(coBan, coBan - phanChu + phanChu * tyLe);
  }
}
