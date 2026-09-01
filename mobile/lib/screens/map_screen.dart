import 'package:flutter/material.dart';
// Ẩn GlassCard của thư viện: file này dùng bản bọc trong widgets/glass_card.dart
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' hide GlassCard;
import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../widgets/so_do_that.dart';
import '../services/theo_doi_vi_tri.dart';
import '../widgets/glass_card.dart';

class MapScreen extends StatelessWidget {
  const MapScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final chuaCho = AppMetrics.chuaChoThanhTab(context);

    return SafeArea(
      bottom: false,
      // fit: expand — bắt buộc, nếu không Stack sẽ co theo con không-Positioned
      // (header) và làm sơ đồ mặt bằng bị ép mất.
      child: Stack(
        fit: StackFit.expand,
        children: [
          // Sơ đồ mặt bằng. Lề dưới phải chừa chỗ cho thanh điều hướng nổi;
          // lề trên chỉ 8 vì header là lớp nổi, không chiếm chỗ bố cục.
          Positioned.fill(
            child: Padding(
              padding: EdgeInsets.only(top: 8, bottom: chuaCho),
              // Semantics bao ngoài: sơ đồ vẽ bằng canvas nên trình đọc màn hình
              // không biết đang đứng trước cái gì, cũng không đoán ra là chụm
              // ngón được. `explicitChildNodes` giữ cho nhãn từng khu vẫn đọc.
              child: Semantics(
                container: true,
                explicitChildNodes: true,
                label: t.mapFloorPlanLabel,
                hint: t.mapFloorPlanHint,
                child: InteractiveViewer(
                  minScale: 1,
                  maxScale: 5,
                  child: const Center(child: SoDoMatBang()),
                ),
              ),
            ),
          ),

          // Header
          const Positioned(
            top: 0,
            left: 16,
            right: 16,
            child: MapHeader(),
          ),

          // Nút định vị phải nằm HẲN trên thanh điều hướng: nút tìm kiếm của
          // thanh đó cũng ở mép phải, đặt thấp là hai nút tròn dính vào nhau.
          Positioned(
            right: 16,
            bottom: chuaCho,
            // GlassIconButton lấy nền, viền và bóng theo lớp kính phía sau.
            child: GlassIconButton(
              icon: Icon(Icons.navigation_outlined,
                  size: 21, color: AppColors.accentOf(context)),
              size: 54,
              // Nút chỉ có biểu tượng: thiếu nhãn thì trình đọc màn hình đọc
              // thành "nút" trống.
              semanticLabel: t.mapRelocate,
              onPressed: () {
                final theoDoi = TheoDoiViTriScope.of(context);
                if (theoDoi.trangThai == TrangThai.dung) theoDoi.batDau();
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// Thẻ header hiển thị tên toà nhà và tầng đang xem.
class MapHeader extends StatelessWidget {
  const MapHeader({super.key});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);
    final toi = Theme.of(context).brightness == Brightness.dark;

    return GlassCard(
      radius: 26,
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
      child: MergeSemantics(
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    theoNgonNgu(context, DemoData.buildingName,
                        DemoData.buildingNameEn),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: muc,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    t.mapAreaSummary(
                        TheoDoiViTriScope.of(context).khuVuc.length,
                        DemoData.updatedSecondsAgo),
                    // Thẻ này nằm đè lên sơ đồ nên chiều cao phải đoán trước
                    // được; để dòng phụ tự xuống hàng trên máy hẹp sẽ đẩy thẻ
                    // cao thêm và che mất hàng phòng đầu tiên.
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 11.5,
                      color: muc.withValues(alpha: 0.55),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                // Chế độ tối phải hạ nền xuống lớp phủ mỏng: nền trắng 60%
                // cộng chữ `inkOf` gần trắng chỉ cho tương phản 1,2:1.
                color: Colors.white.withValues(alpha: toi ? 0.12 : 0.6),
                borderRadius: BorderRadius.circular(15),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.place_outlined,
                      size: 13, color: muc.withValues(alpha: 0.7)),
                  const SizedBox(width: 4),
                  Text(
                    t.mapFloorOne,
                    maxLines: 1,
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w500,
                      color: muc.withValues(alpha: 0.85),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
