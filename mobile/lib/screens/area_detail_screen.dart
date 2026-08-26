import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';
import '../widgets/blob_background.dart';
import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../widgets/floor_plan.dart';
import '../widgets/tap_feedback.dart';
import 'map_screen.dart';

/// Màn chi tiết khu vực: sơ đồ phía trên, bottom sheet thông tin phía dưới.
class AreaDetailScreen extends StatelessWidget {
  const AreaDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);

    // Chiều cao tối đa của tấm thông tin.
    //
    // Trước đây tấm này là `Positioned(bottom: 0)` không giới hạn, cao bao nhiêu
    // tuỳ nội dung. Trên máy thấp phần dôi ra tràn lên khỏi mép trên và bị Stack
    // cắt IM LẶNG — đo trên khung 360x480 thì ô ảnh nằm ở y = -66, tức mất hẳn,
    // và không có cách nào cuộn tới. Chặn ở 78% chiều cao rồi cho cuộn bên trong
    // vừa giữ được sơ đồ phía sau vẫn nhìn thấy, vừa không giấu mất nội dung.
    final caoToiDa = MediaQuery.sizeOf(context).height * 0.78;

    // Màn này được đẩy chồng lên nên phải tự cấp nền: kính khúc xạ theo thứ
    // nằm sau nó, thiếu nền thì thẻ kính trông phẳng và bạc màu.
    return GlassScaffold(
      background: const BlobBackground(blobs: BlobBackground.mapBlobs),
      // KHÔNG dùng GlassStatusBarStyle.auto: tài liệu thư viện ghi rõ nó chọn
      // theo MediaQuery platform brightness, tức độ sáng của HỆ ĐIỀU HÀNH chứ
      // không phải ThemeMode của app. Máy để chế độ sáng mà app đang tối thì
      // auto chọn biểu tượng tối, đặt lên nền tối thành vô hình — đo được tương
      // phản chỉ 0,3/255. Cùng một họ lỗi với brightnessResolver ở main().
      statusBarStyle: Theme.of(context).brightness == Brightness.dark
          ? GlassStatusBarStyle.light
          : GlassStatusBarStyle.dark,
      body: SafeArea(
        bottom: false,
        // fit: expand — nếu không Stack sẽ co theo con không-Positioned.
        child: Stack(
          fit: StackFit.expand,
          children: [
            // Sơ đồ nền
            const Positioned.fill(
              child: ClipRect(
                child: OverflowBox(
                  alignment: Alignment.topCenter,
                  maxHeight: 1400,
                  child: Padding(
                    padding: EdgeInsets.only(top: 116),
                    child: FloorPlan(showUser: false),
                  ),
                ),
              ),
            ),

            // Header + nút quay lại.
            //
            // Nút quay lại là bắt buộc, không phải trang trí: màn này đẩy bằng
            // MaterialPageRoute lên trên một GlassScaffold — không phải Scaffold
            // của Material nên KHÔNG có AppBar nào tự sinh mũi tên quay lại. Trên
            // Android và trên web, MaterialPageRoute cũng không có cử chỉ vuốt
            // mép để lùi. Kết quả là màn Chi tiết trước đây là ngõ cụt: vào rồi
            // chỉ thoát được bằng phím back cứng của hệ điều hành.
            Positioned(
              top: 0,
              left: 16,
              right: 16,
              child: Row(
                children: [
                  GlassIconButton(
                    icon: const Icon(Icons.arrow_back, size: 20),
                    size: AppMetrics.vungChamToiThieu,
                    semanticLabel: t.commonBack,
                    onPressed: () => Navigator.maybePop(context),
                  ),
                  const SizedBox(width: 10),
                  const Expanded(child: MapHeader()),
                ],
              ),
            ),

            // Bottom sheet thông tin
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: ConstrainedBox(
                constraints: BoxConstraints(maxHeight: caoToiDa),
                child: const _DetailSheet(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DetailSheet extends StatelessWidget {
  const _DetailSheet();

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        // Nền phải theo theme, không để cứng Colors.white: chữ trong tấm này
        // dùng inkOf(context) nên ở chế độ tối là chữ sáng — đặt trên nền trắng
        // thành trắng trên trắng, không đọc được.
        color: Theme.of(context).colorScheme.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(36)),
        boxShadow: [
          BoxShadow(
            color: muc.withValues(alpha: 0.10),
            offset: const Offset(0, -6),
            blurRadius: 22,
          ),
        ],
      ),
      child: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(
          24,
          32,
          24,
          // Cộng vùng an toàn dưới: lề cứng 24 đo từ MÉP MÀN HÌNH, mà trên máy
          // dùng cử chỉ điều hướng thì thanh gạch ngang chiếm khoảng 34 đơn vị
          // ở đúng chỗ đó — nút "Đi tới đây" nằm lọt dưới nó.
          24 + MediaQuery.viewPaddingOf(context).bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Ảnh khu vực (placeholder gradient)
            Container(
              height: 164,
              width: double.infinity,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(24),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF9FB9F7), Color(0xFFC3D3F6)],
                ),
              ),
              child: Text(
                t.detailImagePlaceholder,
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w500,
                  // Chữ trắng trên dải xanh nhạt này chỉ đạt khoảng 2:1, dưới
                  // ngưỡng 4.5:1 của WCAG AA. Dải màu cố định ở cả hai chế độ nên
                  // đổi sang mực xanh đậm là đọc được ở cả hai.
                  color: AppColors.strokeNavy.withValues(alpha: 0.75),
                ),
              ),
            ),

            const SizedBox(height: 22),
            Semantics(
              header: true,
              child: Text(
                theoNgonNgu(
                    context, DemoData.detailTitle, DemoData.detailTitleEn),
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              theoNgonNgu(
                  context, DemoData.currentFloor, DemoData.currentFloorEn),
              style: TextStyle(
                fontSize: 13.5,
                color: muc.withValues(alpha: 0.6),
              ),
            ),

            const SizedBox(height: 18),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final chip in DemoData.detailChips)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: chip.bg,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      theoNgonNgu(context, chip.label, chip.labelEn),
                      style: TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w500,
                        color: chip.fg,
                      ),
                    ),
                  ),
              ],
            ),

            const SizedBox(height: 20),
            Text(
              theoNgonNgu(context, DemoData.detailDescription,
                  DemoData.detailDescriptionEn),
              style: TextStyle(
                fontSize: 13,
                height: 1.45,
                color: muc.withValues(alpha: 0.72),
              ),
            ),

            const SizedBox(height: 22),
            const _NutDiToi(),
          ],
        ),
      ),
    );
  }
}

/// Nút hành động chính của màn Chi tiết.
class _NutDiToi extends StatelessWidget {
  const _NutDiToi();

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final onPrimary = Theme.of(context).colorScheme.onPrimary;

    return TapFeedback(
      semanticLabel: t.detailGoHere,
      // SnackBar cần một Scaffold của Material, mà GlassScaffold không phải —
      // gọi vào sẽ ném assertion lúc chạm. GlassToast dùng Overlay nên không
      // phụ thuộc Scaffold.
      onTap: () => GlassToast.show(
        context,
        message: t.detailRouteDemo,
        type: GlassToastType.info,
      ),
      child: Container(
        // Cao theo cỡ chữ hệ thống: 56 cứng cộng chữ 16.5 ở mức phóng to lớn là
        // tràn, mà đây lại là nút hành động chính của màn hình.
        constraints: BoxConstraints(
          minHeight: AppMetrics.caoTheoCoChu(context, coBan: 56, phanChu: 22),
        ),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          gradient: AppColors.ctaGradientOf(context),
          borderRadius: BorderRadius.circular(22),
          boxShadow: [
            BoxShadow(
              color: AppColors.accentOf(context).withValues(alpha: 0.35),
              offset: const Offset(0, 8),
              blurRadius: 18,
            ),
          ],
        ),
        // Màu chữ lấy từ onPrimary chứ không để cứng trắng: ở chế độ tối dải
        // nhấn sáng lên (#6E9BFF → #8FB4FF), chữ trắng đặt lên đó chỉ đạt tương
        // phản 1,05:1 — đo được là không đọc nổi. onPrimary đã khai báo sẵn màu
        // tối cho chế độ tối nên tự đảo đúng chiều.
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.navigation_outlined, size: 19, color: onPrimary),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                t.detailGoHere,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 16.5,
                  fontWeight: FontWeight.w600,
                  color: onPrimary,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
