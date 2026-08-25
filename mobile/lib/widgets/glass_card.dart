import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;

/// Thẻ kính dùng xuyên suốt app.
///
/// Trước đây đây là thẻ tự vẽ: nền trắng `alpha 0.55` cộng viền sáng, tức là
/// *giả* hiệu ứng kính bằng độ trong suốt. Nay uỷ quyền cho
/// `liquid_glass_widgets`, nơi làm mờ nền bằng fragment shader thật nên thẻ
/// thực sự khúc xạ những gì nằm phía sau, có highlight và sai sắc theo mép.
///
/// Giữ nguyên tên và tham số cũ (`radius`, `padding`, `onTap`) để năm màn hình
/// không phải sửa gì. Riêng `opacity` và `shadow` không còn tác dụng vì độ trong
/// và bóng nay do thư viện tự tính theo nền phía sau — giữ lại để mã cũ vẫn
/// biên dịch được, và đánh dấu deprecated để lần dọn sau gỡ đi.
class GlassCard extends StatelessWidget {
  final Widget child;
  final double radius;
  final EdgeInsetsGeometry? padding;
  final VoidCallback? onTap;

  @Deprecated('Độ trong nay do shader tự tính theo nền phía sau.')
  final double opacity;

  @Deprecated('Bóng nay do thư viện tự tính theo ánh sáng của lớp kính.')
  final bool shadow;

  const GlassCard({
    super.key,
    required this.child,
    this.radius = 24,
    this.padding,
    this.onTap,
    // ignore: deprecated_member_use_from_same_package
    this.opacity = 0.55,
    // ignore: deprecated_member_use_from_same_package
    this.shadow = false,
  });

  @override
  Widget build(BuildContext context) {
    final the = lg.GlassCard(
      padding: padding ?? EdgeInsets.zero,
      shape: lg.LiquidRoundedSuperellipse(borderRadius: radius),
      child: child,
    );

    if (onTap == null) return the;

    // Dùng GestureDetector chứ không dùng InkWell: gợn mực của Material vẽ đè
    // lên mặt kính và làm hỏng highlight, trong khi thư viện đã có phản hồi
    // chạm riêng dạng biến dạng jelly.
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: the,
    );
  }
}
