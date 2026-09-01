import 'package:flutter/material.dart';

import '../data/floor_map.dart';
import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../screens/area_detail_screen.dart';
import 'tap_feedback.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_colors.dart';

/// Sơ đồ mặt bằng thật của tầng 1, kèm chấm vị trí đang đứng.
///
/// Dùng bản số hoá `Map.png` và đúng hệ mét mô hình trả về, nên chấm vị trí rơi
/// vào chỗ thật — khác [FloorPlan] là sơ đồ vẽ tay chỉ để trình bày.
class SoDoMatBang extends StatefulWidget {
  const SoDoMatBang({super.key});

  @override
  State<SoDoMatBang> createState() => _SoDoMatBangState();
}

class _SoDoMatBangState extends State<SoDoMatBang> {
  bool _daGoi = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Nạp ngay khi mở tab, không đợi bật định vị: nhãn khu vực là thứ đáng xem
    // nhất trên màn hình này.
    if (_daGoi) return;
    _daGoi = true;
    TheoDoiViTriScope.of(context).taiBanDo();
  }

  @override
  Widget build(BuildContext context) {
    final theoDoi = TheoDoiViTriScope.of(context);
    return AnimatedBuilder(
      animation: theoDoi,
      builder: (context, _) => AspectRatio(
        aspectRatio: SoDoThat.rongPx / SoDoThat.caoPx,
        child: LayoutBuilder(
          builder: (context, c) => _ve(context, theoDoi, c.maxWidth),
        ),
      ),
    );
  }

  Widget _ve(BuildContext context, TheoDoiViTri theoDoi, double rong) {
    final toi = Theme.of(context).brightness == Brightness.dark;
    final vt = theoDoi.viTri;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapUp: (e) {
        final k = _khuVucTaiDiem(e.localPosition, theoDoi.khuVuc, rong);
        if (k != null) _hienTom(context, k);
      },
      child: Stack(
        children: [
        // Chế độ tối đảo RGB chứ không đổi màu cả khối: nét đen thành trắng,
        // chấm lưới thành xám đậm, giữ đúng thứ tự tương phản của bản sáng.
        // Hàng alpha không đổi nên nền vẫn trong suốt.
        Positioned.fill(
          child: ColorFiltered(
            colorFilter: toi
                ? const ColorFilter.matrix(<double>[
                    -1, 0, 0, 0, 255, //
                    0, -1, 0, 0, 255, //
                    0, 0, -1, 0, 255, //
                    0, 0, 0, 1, 0, //
                  ])
                : const ColorFilter.mode(Colors.transparent, BlendMode.dst),
            child: Image.asset(SoDoThat.anh, fit: BoxFit.fill),
          ),
        ),

        for (final n in _viTriNhan(theoDoi.khuVuc, rong))
          _nhan(n.$1.nhom, n.$2, rong, toi),

          if (vt != null)
            _cham(SoDoThat.sangKhung(vt.xGop, vt.yGop, rong), rong),
        ],
      ),
    );
  }

  /// Chỗ đặt nhãn cho từng khu vực, đã đẩy ra cho khỏi chồng nhau.
  ///
  /// Trọng tâm của "Bàn thủ thư" và "Cầu thang tầng 2" chỉ cách nhau vài mét
  /// nên hai nhãn đè lên nhau, đọc thành một dòng vô nghĩa. Xếp theo chiều dọc
  /// rồi đẩy nhãn sau xuống dưới nhãn trước nếu quá gần.
  List<(KhuVuc, Offset)> _viTriNhan(List<KhuVuc> khu, double rong) {
    final cao = _caoChu(rong) * 1.6;
    final ra = <(KhuVuc, Offset)>[];

    final sap = [...khu]..sort((a, b) {
        final pa = SoDoThat.sangKhung(a.trongTam.dx, a.trongTam.dy, rong);
        final pb = SoDoThat.sangKhung(b.trongTam.dx, b.trongTam.dy, rong);
        return pa.dy != pb.dy ? pa.dy.compareTo(pb.dy) : pa.dx.compareTo(pb.dx);
      });

    for (final k in sap) {
      var p = SoDoThat.sangKhung(k.trongTam.dx, k.trongTam.dy, rong);
      for (final (_, q) in ra) {
        final chongNgang = (p.dx - q.dx).abs() < rong * 0.16;
        if (chongNgang && (p.dy - q.dy).abs() < cao) {
          p = Offset(p.dx, q.dy + cao);
        }
      }
      ra.add((k, p));
    }
    return ra;
  }

  double _caoChu(double rong) =>
      (rong / SoDoThat.rongPx * 15).clamp(7.0, 12.0);

  /// Khu vực gần chỗ vừa chạm nhất, hoặc null nếu chạm ra ngoài toà nhà.
  KhuVuc? _khuVucTaiDiem(Offset cham, List<KhuVuc> khu, double rong) {
    if (khu.isEmpty) return null;

    // Đổi ngược từ pixel khung về mét rồi mới so khoảng cách, để ngưỡng "quá
    // xa" tính bằng mét chứ không bằng pixel — pixel đổi theo cỡ màn hình.
    final s = rong / SoDoThat.rongPx;
    final x = (cham.dx / s - SoDoThat.gocXPx) / SoDoThat.pxMoiMetX - 43.0;
    final y = (SoDoThat.gocYPx - cham.dy / s) / SoDoThat.pxMoiMetY;

    var gan = khu.first;
    var min = double.infinity;
    for (final k in khu) {
      final l = k.khoangCach(x, y);
      if (l < min) {
        min = l;
        gan = k;
      }
    }
    // Chạm cách mọi khu vực quá xa thì coi như chạm nhầm, không mở gì cả.
    return min <= 12 ? gan : null;
  }


  Widget _nhan(String chu, Offset tam, double rong, bool toi) {
    final co = _caoChu(rong);
    return Positioned(
      left: 0,
      top: tam.dy - co,
      width: tam.dx * 2,
      child: Text(
        chu,
        textAlign: TextAlign.center,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          fontSize: co,
          fontWeight: FontWeight.w600,
          color: (toi ? AppColors.inkDark : AppColors.ink).withValues(alpha: 0.7),
        ),
      ),
    );
  }

  Widget _cham(Offset tam, double rong) {
    final r = (rong / SoDoThat.rongPx * 11).clamp(6.0, 11.0);
    return Positioned(
      left: tam.dx - r,
      top: tam.dy - r,
      width: r * 2,
      height: r * 2,
      child: DecoratedBox(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: AppColors.accent,
          border: Border.all(color: Colors.white, width: r * 0.35),
          boxShadow: [
            BoxShadow(
              color: AppColors.accent.withValues(alpha: 0.35),
              blurRadius: r * 1.6,
            ),
          ],
        ),
      ),
    );
  }
}

/// Tấm tóm tắt khi chạm vào một khu vực trên sơ đồ.
///
/// Học theo bottom sheet của CTK45: tên, mô tả, rồi nút mở màn chi tiết. Chạm
/// thẳng vào bản đồ là cách tự nhiên nhất để hỏi "chỗ này là chỗ nào".
void _hienTom(BuildContext context, KhuVuc k) {
  showModalBottomSheet<void>(
    context: context,
    backgroundColor: Theme.of(context).colorScheme.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (sheet) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(k.icon, size: 22, color: AppColors.accentOf(sheet)),
                const SizedBox(width: 10),
                Expanded(
                  child: Semantics(
                    header: true,
                    child: Text(k.nhom,
                        style: Theme.of(sheet).textTheme.titleLarge),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              k.moTa,
              style: TextStyle(
                fontSize: 13.5,
                height: 1.4,
                color: AppColors.inkOf(sheet).withValues(alpha: 0.72),
              ),
            ),
            const SizedBox(height: 18),
            TapFeedback(
              semanticLabel: L.of(sheet).a11yOpenArea,
              onTap: () {
                Navigator.of(sheet).pop();
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => AreaDetailScreen(khuVuc: k),
                  ),
                );
              },
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: Theme.of(sheet).colorScheme.primary,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Text(
                  L.of(sheet).mapOpenDetail,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: Theme.of(sheet).colorScheme.onPrimary,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
