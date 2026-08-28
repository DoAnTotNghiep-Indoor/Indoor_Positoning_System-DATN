import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;

import 'tap_feedback.dart';

/// Thẻ kính dùng xuyên suốt app.
///
/// Trước đây đây là thẻ tự vẽ: nền trắng `alpha 0.55` cộng viền sáng, tức là
/// *giả* hiệu ứng kính bằng độ trong suốt. Nay uỷ quyền cho
/// `liquid_glass_widgets`, nơi làm mờ nền bằng fragment shader thật nên thẻ
/// thực sự khúc xạ những gì nằm phía sau, có highlight và sai sắc theo mép.
///
/// Giữ nguyên tên và tham số cũ (`radius`, `padding`, `onTap`) để năm màn hình
/// không phải sửa gì. Hai tham số `opacity` và `shadow` đã được gỡ hẳn: độ trong
/// và bóng nay do shader tự tính theo nền phía sau, nên `build()` không đọc tới
/// chúng — để lại chỉ khiến chỗ gọi tưởng mình đang chỉnh được thứ gì đó.
class GlassCard extends StatelessWidget {
  final Widget child;
  final double radius;
  final EdgeInsetsGeometry? padding;
  final VoidCallback? onTap;

  /// Nhãn và gợi ý cho trình đọc màn hình, chỉ dùng khi có [onTap].
  final String? semanticLabel;
  final String? semanticHint;

  const GlassCard({
    super.key,
    required this.child,
    this.radius = 24,
    this.padding,
    this.onTap,
    this.semanticLabel,
    this.semanticHint,
  });

  @override
  Widget build(BuildContext context) {
    final the = lg.GlassCard(
      padding: padding ?? EdgeInsets.zero,
      shape: lg.LiquidRoundedSuperellipse(borderRadius: radius),
      child: child,
    );

    if (onTap == null) return the;

    // Trước đây chỗ này là `GestureDetector` trần, kèm ghi chú rằng thư viện đã
    // tự lo phản hồi chạm. Ghi chú đó sai: `lg.GlassCard` 0.30.2 không nhận
    // `onTap` nên cũng không có trạng thái "đang bấm" nào để hiển thị — chạm vào
    // thẻ không thấy gì đổi. `TapFeedback` bù đúng phần thiếu đó, đồng thời khai
    // báo ngữ nghĩa nút cho trình đọc màn hình.
    return TapFeedback(
      onTap: onTap,
      semanticLabel: semanticLabel,
      semanticHint: semanticHint,
      child: the,
    );
  }
}
