import 'package:flutter/material.dart';

/// Bọc một vùng chạm để nó có phản hồi khi bấm, và để trình đọc màn hình nhận
/// ra đó là nút.
///
/// `lg.GlassCard` 0.30.2 KHÔNG nhận `onTap` — hiệu ứng jelly của thư viện chỉ
/// có ở `GlassButton`/`GlassIconButton`. Không dùng `InkWell` thay thế:
/// `GlassScaffold` không dựng `Material` nên `InkWell` ném assertion, và gợn
/// mực của Material vẽ đè lên mặt kính.
class TapFeedback extends StatefulWidget {
  final Widget child;
  final VoidCallback? onTap;

  /// Nhãn đọc lên cho trình đọc màn hình. Bỏ trống thì lấy chữ trong [child].
  final String? semanticLabel;

  /// Câu mô tả điều gì xảy ra khi kích hoạt, ví dụ "Mở chi tiết khu vực".
  final String? semanticHint;

  /// Mức thu nhỏ khi giữ. Mặc định 0.97 — đủ thấy, chưa tới mức giật.
  final double scale;

  const TapFeedback({
    super.key,
    required this.child,
    this.onTap,
    this.semanticLabel,
    this.semanticHint,
    this.scale = 0.97,
  });

  @override
  State<TapFeedback> createState() => _TapFeedbackState();
}

class _TapFeedbackState extends State<TapFeedback> {
  bool _dangGiu = false;

  void _dat(bool gt) {
    if (_dangGiu == gt) return;
    setState(() => _dangGiu = gt);
  }

  @override
  Widget build(BuildContext context) {
    if (widget.onTap == null) return widget.child;

    final coNhanRieng = widget.semanticLabel != null;

    Widget noiDung = AnimatedScale(
      scale: _dangGiu ? widget.scale : 1,
      duration: const Duration(milliseconds: 90),
      curve: Curves.easeOut,
      child: widget.child,
    );

    // Có nhãn riêng thì phải bỏ ngữ nghĩa của các con, không thì trình đọc màn
    // hình đọc hai lần.
    if (coNhanRieng) noiDung = ExcludeSemantics(child: noiDung);

    final nut = Semantics(
      button: true,
      label: widget.semanticLabel,
      hint: widget.semanticHint,
      onTap: widget.onTap,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: widget.onTap,
        onTapDown: (_) => _dat(true),
        onTapUp: (_) => _dat(false),
        onTapCancel: () => _dat(false),
        child: noiDung,
      ),
    );

    // Không có nhãn riêng thì gộp chữ bên trong thành một mục, thay vì đọc rời
    // "Khu vực đọc", "Khu vực cung cấp các thể loại sách", "34 m" thành ba mục.
    return coNhanRieng ? nut : MergeSemantics(child: nut);
  }
}
