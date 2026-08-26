import 'package:flutter/material.dart';

/// Bọc một vùng chạm để nó *có phản hồi* khi bấm, và để trình đọc màn hình
/// nhận ra đó là nút.
///
/// Tồn tại vì một khoảng trống thật trong app: các thẻ bấm được đang dùng
/// `GestureDetector` trần. Ghi chú cũ trong `glass_card.dart` nói "thư viện đã
/// có phản hồi chạm riêng dạng biến dạng jelly", nhưng `lg.GlassCard` của
/// `liquid_glass_widgets` 0.30.2 KHÔNG có tham số `onTap` — hiệu ứng đó chỉ có ở
/// `GlassButton`/`GlassIconButton`. Hệ quả: chạm vào ô truy cập nhanh, dòng "Gần
/// bạn", thẻ kết quả tìm kiếm hay nút "Đi tới đây" đều không thấy gì xảy ra cho
/// tới khi màn hình mới đã đẩy xong.
///
/// Không dùng `InkWell`: `GlassScaffold` không dựng `Material` nên `InkWell` ném
/// assertion, và gợn mực của Material cũng vẽ đè lên mặt kính.
///
/// Cách làm là thu nhỏ nhẹ khi giữ — cùng ngôn ngữ với `interactionScale` mà
/// `GlassIconButton` của thư viện dùng, nên không phá vẻ ngoài chung.
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

    // Khi đã tự đặt nhãn thì bỏ ngữ nghĩa của các con đi, nếu không trình đọc
    // màn hình đọc hai lần: một lần nhãn tự đặt, một lần từng dòng chữ bên trong.
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

    // Không có nhãn riêng thì gộp chữ bên trong lại thành một mục: nếu không,
    // trình đọc màn hình đọc rời "Phòng họp", "Meeting room", "34 m" thành ba
    // mục thay vì một nút.
    return coNhanRieng ? nut : MergeSemantics(child: nut);
  }
}
