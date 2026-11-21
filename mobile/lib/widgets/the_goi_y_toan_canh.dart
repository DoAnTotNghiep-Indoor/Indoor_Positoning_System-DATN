import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../l10n/app_localizations.dart';
import '../screens/toan_canh_screen.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_theme.dart';

/// Thẻ nhỏ dưới nhãn vị trí khi người dùng tới gần một chỗ có ảnh 360°.
/// Không tự mở toàn màn hình: vị trí còn sai vài mét, bật nhầm khu thì che mất
/// bản đồ. Nền đặc chứ không kính: thẻ nổi trên chữ của Trang chủ, kính trong
/// làm hai lớp chữ chồng nhau. Tự ẩn sau [_hien] nếu không ai chạm.
class TheGoiYToanCanh extends StatefulWidget {
  final TheoDoiViTri theoDoi;
  const TheGoiYToanCanh({super.key, required this.theoDoi});

  @override
  State<TheGoiYToanCanh> createState() => _TheGoiYToanCanhState();
}

class _TheGoiYToanCanhState extends State<TheGoiYToanCanh> {
  static const _hien = Duration(seconds: 20);
  Timer? _hen;
  String? _ma;

  @override
  void dispose() {
    _hen?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final tt = Theme.of(context).textTheme;
    final m = Mau.of(context);
    final tc = widget.theoDoi.goiYToanCanh;

    if (tc?.ma != _ma) {
      _ma = tc?.ma;
      _hen?.cancel();
      if (tc != null) _hen = Timer(_hien, widget.theoDoi.boQuaGoiY);
    }

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 250),
      child: tc == null
          ? const SizedBox.shrink()
          : Padding(
              key: ValueKey(tc.ma),
              padding: const EdgeInsets.only(top: 10),
              child: GestureDetector(
                onTap: () {
                  widget.theoDoi.boQuaGoiY();
                  moToanCanh(context, tc);
                },
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: m.the,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: m.vien),
                    boxShadow: const [
                      BoxShadow(
                          color: Color(0x26000000),
                          blurRadius: 12,
                          offset: Offset(0, 3)),
                    ],
                  ),
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(10, 8, 4, 8),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SvgPicture.asset('assets/images/huong_dan.svg',
                            width: 34, height: 40),
                        const SizedBox(width: 10),
                        Flexible(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(t.panoNearby(tc.ten),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style:
                                      tt.titleMedium?.copyWith(fontSize: 15)),
                              Text(t.panoOpen,
                                  maxLines: 2,
                                  style: tt.bodyMedium?.copyWith(fontSize: 13)),
                            ],
                          ),
                        ),
                        IconButton(
                          tooltip: t.panoDismiss,
                          onPressed: widget.theoDoi.boQuaGoiY,
                          icon: const Icon(Icons.close, size: 20),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
    );
  }
}
