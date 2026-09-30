import 'package:flutter/widgets.dart';

/// Co nhẹ khi giữ thay cho gợn mực Material — cùng cách `clickableScale` bên
/// bản Compose. Gộp chữ bên trong thành một mục cho trình đọc màn hình.
class TapFeedback extends StatefulWidget {
  final Widget child;
  final VoidCallback? onTap;
  final String? semanticLabel;

  const TapFeedback({
    super.key,
    required this.child,
    this.onTap,
    this.semanticLabel,
  });

  @override
  State<TapFeedback> createState() => _TapFeedbackState();
}

class _TapFeedbackState extends State<TapFeedback> {
  bool _giu = false;

  void _dat(bool gt) {
    if (_giu != gt) setState(() => _giu = gt);
  }

  @override
  Widget build(BuildContext context) {
    if (widget.onTap == null) return widget.child;
    return MergeSemantics(
      child: Semantics(
        button: true,
        label: widget.semanticLabel,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: widget.onTap,
          onTapDown: (_) => _dat(true),
          onTapUp: (_) => _dat(false),
          onTapCancel: () => _dat(false),
          child: AnimatedScale(
            scale: _giu ? 0.96 : 1,
            duration: const Duration(milliseconds: 90),
            child: widget.child,
          ),
        ),
      ),
    );
  }
}
