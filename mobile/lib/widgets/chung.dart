import 'package:flutter/material.dart';
import 'package:intl/intl.dart' as intl;
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;

import '../data/floor_map.dart';
import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../services/api_dinh_vi.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_theme.dart';
import 'tap_feedback.dart';
import 'the_khu_vuc.dart';

/// Bề mặt đặc cho nội dung: theo Apple HIG, nội dung đặt trên kính mất tương phản.
class BeMat extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;

  const BeMat({
    super.key,
    required this.child,
    this.padding = EdgeInsets.zero,
    this.radius = 20,
  });

  @override
  Widget build(BuildContext context) {
    final m = Mau.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: m.the,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: m.vien),
      ),
      child: Padding(padding: padding, child: child),
    );
  }
}

class OBieuTuong extends StatelessWidget {
  final KhuVuc khuVuc;
  final double size;

  const OBieuTuong(this.khuVuc, {super.key, this.size = 40});

  @override
  Widget build(BuildContext context) {
    final (nen, chu) = mauLoai(context, loaiCua(khuVuc.nhom));
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(color: nen, shape: BoxShape.circle),
      child: Icon(khuVuc.icon, size: size * 0.5, color: chu),
    );
  }
}

class TieuDeMuc extends StatelessWidget {
  final String text;
  const TieuDeMuc(this.text, {super.key});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(4, 28, 4, 12),
        child: Semantics(
          header: true,
          child: Text(text, style: Theme.of(context).textTheme.titleMedium),
        ),
      );
}

String? khoangCachChu(L t, KhuVuc k, ViTri? vt) => vt == null
    ? null
    : t.distanceMeters(
        (k.khoangCach(vt.xGop, vt.yGop) * SoDoThat.metMoiDonVi).round());

class DongKhuVuc extends StatelessWidget {
  final KhuVuc khuVuc;
  final ViTri? viTri;

  const DongKhuVuc({super.key, required this.khuVuc, this.viTri});

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final m = Mau.of(context);
    final kc = khoangCachChu(L.of(context), khuVuc, viTri);
    return TapFeedback(
      onTap: () => moKhuVuc(context, khuVuc),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Row(
          children: [
            OBieuTuong(khuVuc),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(khuVuc.nhom,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: tt.titleMedium?.copyWith(fontSize: 15)),
                  const SizedBox(height: 2),
                  Text(khuVuc.moTa,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: tt.bodyMedium?.copyWith(fontSize: 13)),
                ],
              ),
            ),
            if (kc != null) ...[
              const SizedBox(width: 8),
              Text(kc, style: tt.labelLarge?.copyWith(color: m.nhan)),
            ],
          ],
        ),
      ),
    );
  }
}

/// Chrome nổi bằng kính, cùng tint với thanh tab.
class KinhNoi extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double? height;

  const KinhNoi(
      {super.key,
      required this.child,
      this.height = 44,
      this.padding = const EdgeInsets.symmetric(horizontal: 16)});

  @override
  Widget build(BuildContext context) => lg.GlassContainer(
        height: height,
        padding: padding,
        settings: kinhNoi(context),
        shape: const lg.LiquidRoundedSuperellipse(borderRadius: 22),
        child: child,
      );
}

class PillViTri extends StatelessWidget {
  final TheoDoiViTri theoDoi;
  const PillViTri({super.key, required this.theoDoi});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final so = intl.NumberFormat('#0.0', t.localeName);
    final vt = theoDoi.viTri;
    final khu = theoDoi.khuHienTai;
    final ten = khu?.nhom ??
        (vt == null
            ? t.liveLocating
            : t.liveCoords(so.format(vt.xGop), so.format(vt.yGop)));

    return TapFeedback(
      onTap: khu == null ? null : () => moKhuVuc(context, khu),
      semanticLabel: '${t.homeYouAreAt} $ten',
      child: KinhNoi(
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            DecoratedBox(
              decoration: BoxDecoration(
                color: vt != null && theoDoi.loi == null ? m.dich : m.loi,
                shape: BoxShape.circle,
              ),
              child: const SizedBox.square(dimension: 10),
            ),
            const SizedBox(width: 10),
            Flexible(
              child: Text(ten,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium),
            ),
          ],
        ),
      ),
    );
  }
}
