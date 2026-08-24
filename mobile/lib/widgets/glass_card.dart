import 'package:flutter/material.dart';

/// Thẻ nền trắng bán trong suốt có viền sáng — kiểu "glass" dùng xuyên suốt app.
class GlassCard extends StatelessWidget {
  final Widget child;
  final double radius;
  final double opacity;
  final EdgeInsetsGeometry? padding;
  final bool shadow;
  final VoidCallback? onTap;

  const GlassCard({
    super.key,
    required this.child,
    this.radius = 24,
    this.opacity = 0.55,
    this.padding,
    this.shadow = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final content = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: opacity),
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: Colors.white.withValues(alpha: 0.7)),
        boxShadow: shadow
            ? [
                BoxShadow(
                  color: const Color(0xFF0D1A30).withValues(alpha: 0.07),
                  offset: const Offset(0, 8),
                  blurRadius: 18,
                ),
              ]
            : null,
      ),
      child: child,
    );

    if (onTap == null) return content;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(radius),
      child: content,
    );
  }
}
