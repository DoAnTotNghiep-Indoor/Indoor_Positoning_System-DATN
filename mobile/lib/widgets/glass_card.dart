import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;

import 'tap_feedback.dart';

/// Thẻ kính dùng xuyên suốt app, bọc `lg.GlassCard` của thư viện.
///
/// Không có tham số `opacity` hay `shadow`: shader tự tính hai thứ đó theo nền
/// phía sau, mở ra chỉ khiến chỗ gọi tưởng mình chỉnh được.
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

    // lg.GlassCard không nhận onTap nên tự nó không có phản hồi chạm nào;
    // TapFeedback bù phần đó và khai báo ngữ nghĩa nút.
    return TapFeedback(
      onTap: onTap,
      semanticLabel: semanticLabel,
      semanticHint: semanticHint,
      child: the,
    );
  }
}
