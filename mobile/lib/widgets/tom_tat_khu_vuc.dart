import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';

import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../screens/area_detail_screen.dart';
import '../services/api_dinh_vi.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_colors.dart';
import 'tap_feedback.dart';

/// Tấm tóm tắt trượt lên khi chạm một vị trí trên sơ đồ: tên, mô tả, rồi hai
/// lối đi tiếp — xem chi tiết, hoặc chỉ đường từ chỗ đang đứng tới đó.
///
/// Chỉ màn Bản đồ dùng tấm này. Trang chủ vào thẳng màn Chi tiết vì ở đó người
/// dùng đã đọc tên và mô tả ngay trên danh sách rồi, chen thêm một tấm nữa là
/// bắt bấm hai lần cho cùng một việc. Trên sơ đồ thì ngược lại: chạm vào một
/// chấm chưa biết đó là chỗ nào, nên cần một bước trả lời trước khi đi tiếp.
void hienTomTatKhuVuc(BuildContext context, KhuVuc k) {
  showModalBottomSheet<void>(
    context: context,
    backgroundColor: Theme.of(context).colorScheme.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    // Lấy bộ theo dõi TỪ context của màn Bản đồ rồi truyền vào, không để tấm tự
    // tra ngược cây: `showModalBottomSheet` dựng nội dung ở một route khác nên
    // nó chỉ thấy được scope nào nằm trên Navigator.
    builder: (sheet) => _TomTat(
      khuVuc: k,
      ngoai: context,
      theoDoi: TheoDoiViTriScope.of(context),
    ),
  );
}

class _TomTat extends StatefulWidget {
  final KhuVuc khuVuc;

  /// Context của màn Bản đồ, không phải của tấm này. Mở màn Chi tiết phải đẩy
  /// lên Navigator đó — đẩy lên context của tấm thì màn mới bị gỡ ngay cùng lúc
  /// tấm đóng lại.
  final BuildContext ngoai;

  final TheoDoiViTri theoDoi;

  const _TomTat({
    required this.khuVuc,
    required this.ngoai,
    required this.theoDoi,
  });

  @override
  State<_TomTat> createState() => _TomTatState();
}

class _TomTatState extends State<_TomTat> {
  bool _dangTim = false;

  Future<void> _chiDuong(TheoDoiViTri theoDoi) async {
    if (theoDoi.viTri == null) {
      theoDoi.batDau();
      return;
    }

    setState(() => _dangTim = true);
    try {
      await theoDoi.chiDuongToi(widget.khuVuc);
      // Đóng tấm để lộ sơ đồ: tuyến vừa tìm được đã nằm trong TheoDoiViTri nên
      // nó tự vẽ lên, kèm thẻ tổng quãng đường ở đầu màn.
      if (mounted) Navigator.of(context).pop();
    } on NgoaiLeApi catch (e) {
      if (mounted) {
        GlassToast.show(context,
            message: _cauLoi(L.of(context), e.loai),
            type: GlassToastType.error);
        setState(() => _dangTim = false);
      }
    }
  }

  String _cauLoi(L t, LoiApi loai) => switch (loai) {
        LoiApi.diaChiSai => t.errBadAddress(''),
        LoiApi.quaHan => t.errTimeout,
        _ => t.detailRouteFailed,
      };

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final k = widget.khuVuc;
    final theoDoi = widget.theoDoi;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(k.icon, size: 22, color: AppColors.accentOf(context)),
                const SizedBox(width: 10),
                Expanded(
                  child: Semantics(
                    header: true,
                    child: Text(k.nhom,
                        style: Theme.of(context).textTheme.titleLarge),
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
                color: AppColors.inkOf(context).withValues(alpha: 0.72),
              ),
            ),
            const SizedBox(height: 18),
            AnimatedBuilder(
              animation: theoDoi,
              builder: (context, _) => Row(
                children: [
                  Expanded(child: _nutChiDuong(t, theoDoi)),
                  const SizedBox(width: 10),
                  Expanded(child: _nutChiTiet(t)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _nutChiDuong(L t, TheoDoiViTri theoDoi) {
    final coViTri = theoDoi.viTri != null;
    final nhan = _dangTim
        ? t.detailRouteLoading
        : (coViTri ? t.detailGoHere : t.detailNeedPosition);

    return TapFeedback(
      semanticLabel: nhan,
      onTap: _dangTim ? null : () => _chiDuong(theoDoi),
      child: _vo(
        nen: Theme.of(context).colorScheme.primary,
        chu: Theme.of(context).colorScheme.onPrimary,
        icon: coViTri ? Icons.directions : Icons.my_location,
        nhan: nhan,
      ),
    );
  }

  Widget _nutChiTiet(L t) => TapFeedback(
        semanticLabel: t.a11yOpenArea,
        onTap: () {
          Navigator.of(context).pop();
          moChiTietKhuVuc(widget.ngoai, widget.khuVuc,
              toanManHinh: false);
        },
        child: _vo(
          nen: AppColors.accentOf(context).withValues(alpha: 0.12),
          chu: AppColors.accentOf(context),
          icon: Icons.info_outline,
          nhan: t.mapOpenDetail,
        ),
      );

  Widget _vo({
    required Color nen,
    required Color chu,
    required IconData icon,
    required String nhan,
  }) =>
      Container(
        padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 10),
        decoration:
            BoxDecoration(color: nen, borderRadius: BorderRadius.circular(18)),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 18, color: chu),
            const SizedBox(width: 7),
            Flexible(
              child: Text(
                nhan,
                maxLines: 2,
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontSize: 13.5, fontWeight: FontWeight.w600, color: chu),
              ),
            ),
          ],
        ),
      );
}
