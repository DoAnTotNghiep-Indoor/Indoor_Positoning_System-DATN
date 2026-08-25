import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';
import '../widgets/blob_background.dart';
import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../widgets/floor_plan.dart';
import 'map_screen.dart';

/// Màn chi tiết khu vực: sơ đồ phía trên, bottom sheet thông tin phía dưới.
class AreaDetailScreen extends StatelessWidget {
  const AreaDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
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
      body: const SafeArea(
        bottom: false,
        // fit: expand — nếu không Stack sẽ co theo con không-Positioned.
        child: Stack(
          fit: StackFit.expand,
          children: [
            // Sơ đồ nền
            Positioned.fill(
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

            // Header
            Positioned(
              top: 0,
              left: 16,
              right: 16,
              child: MapHeader(),
            ),

            // Bottom sheet thông tin
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: _DetailSheet(),
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
            color: AppColors.inkOf(context).withValues(alpha: 0.10),
            offset: const Offset(0, -6),
            blurRadius: 22,
          ),
        ],
      ),
      padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
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
              'Ảnh khu vực',
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w500,
                color: Colors.white.withValues(alpha: 0.9),
              ),
            ),
          ),

          const SizedBox(height: 22),
          Text(DemoData.detailTitle,
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 6),
          Text(
            DemoData.detailSubtitle,
            style: TextStyle(
              fontSize: 13.5,
              color: AppColors.inkOf(context).withValues(alpha: 0.6),
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
                    chip.label,
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
            DemoData.detailDescription,
            style: TextStyle(
              fontSize: 13,
              height: 1.45,
              color: AppColors.inkOf(context).withValues(alpha: 0.72),
            ),
          ),

          const SizedBox(height: 22),
          // Nút đi tới đây
          GestureDetector(
            // SnackBar cần một Scaffold của Material, mà GlassScaffold không
            // phải — gọi vào sẽ ném assertion lúc chạm. GlassToast dùng Overlay
            // nên không phụ thuộc Scaffold.
            onTap: () => GlassToast.show(
              context,
              message: t.detailRouteDemo,
              type: GlassToastType.info,
            ),
            child: Container(
              height: 56,
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
              // Màu chữ lấy từ onPrimary chứ không để cứng trắng: ở chế độ tối
              // dải nhấn sáng lên (#6E9BFF → #8FB4FF), chữ trắng đặt lên đó chỉ
              // đạt tương phản 1,05:1 — đo được là không đọc nổi. onPrimary đã
              // khai báo sẵn màu tối cho chế độ tối nên tự đảo đúng chiều.
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.navigation_outlined,
                      size: 19,
                      color: Theme.of(context).colorScheme.onPrimary),
                  const SizedBox(width: 8),
                  Text(
                    t.detailGoHere,
                    style: TextStyle(
                      fontSize: 16.5,
                      fontWeight: FontWeight.w600,
                      color: Theme.of(context).colorScheme.onPrimary,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
