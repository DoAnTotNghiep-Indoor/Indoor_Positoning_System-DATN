import 'package:flutter/material.dart';
// Ẩn GlassCard của thư viện: file này dùng bản bọc trong widgets/glass_card.dart
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' hide GlassCard;
import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../widgets/floor_plan.dart';
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
          // Sơ đồ mặt bằng.
          //
          // Lề dưới phải chừa đủ chỗ cho thanh điều hướng, nếu không tường bao
          // và ba phòng cuối toà nhà bị nó cắt mất — đúng lỗi của bản trước, khi
          // lề này để cứng 96 trong khi thanh tab chiếm 84 cộng lề an toàn.
          Positioned.fill(
            child: Padding(
              // Lề trên chỉ 8 chứ không phải 96: header là lớp nổi (Positioned
              // top: 0) nên không chiếm chỗ bố cục, mà 96 đơn vị đầu của sơ đồ
              // vốn là khoảng trống phía trên mái vòm lối vào — header phủ lên
              // đúng chỗ trống đó. Bỏ luôn lề hai bên.
              //
              // Sơ đồ có tỉ lệ 393:852, cao và hẹp hơn vùng hiển thị còn lại,
              // nên khi ép vừa chiều cao vẫn thừa lề hai bên. Cắt lề khung là
              // cách duy nhất làm nó to thêm mà vẫn thấy trọn cả tầng.
              padding: EdgeInsets.only(top: 8, bottom: chuaCho),
              // InteractiveViewer để phóng to bằng hai ngón và kéo xem chi tiết.
              // Mức 1 là toàn cảnh vừa màn hình, kéo lên tới 4 lần.
              //
              // Semantics bao ngoài: sơ đồ vẽ bằng CustomPaint nên trình đọc màn
              // hình chỉ thấy một mớ nhãn phòng rời rạc, không biết đang đứng
              // trước cái gì và cũng không đoán ra là chụm ngón được. Giữ
              // `explicitChildNodes` để tên từng phòng vẫn đọc được.
              child: Semantics(
                container: true,
                explicitChildNodes: true,
                label: t.mapFloorPlanLabel,
                hint: t.mapFloorPlanHint,
                child: InteractiveViewer(
                  minScale: 1,
                  maxScale: 4,
                  child: const Center(child: FloorPlan()),
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

          // Nút định vị lại.
          //
          // Phải nằm HẲN trên thanh điều hướng: nút tìm kiếm của thanh đó cũng
          // ở mép phải, nên đặt thấp là hai nút tròn dính vào nhau. Bản trước để
          // bottom: 96 và chúng chồng lên nhau đúng như vậy.
          Positioned(
            right: 16,
            bottom: chuaCho,
            // GlassIconButton thay cho vòng tròn tự vẽ: nền, viền và bóng
            // trước đây phải tự canh, nay lấy theo lớp kính phía sau.
            child: GlassIconButton(
              icon: Icon(Icons.navigation_outlined,
                  size: 21, color: AppColors.accentOf(context)),
              size: 54,
              // Nút chỉ có mỗi biểu tượng mũi tên: không có nhãn thì trình đọc
              // màn hình đọc thành "nút" trống, người dùng không biết bấm để làm gì.
              semanticLabel: t.mapRelocate,
              onPressed: () => GlassToast.show(
                context,
                message: t.mapRelocateDemo,
                type: GlassToastType.info,
              ),
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
      opacity: 0.6,
      shadow: true,
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
                        DemoData.areaCount, DemoData.updatedSecondsAgo),
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
                // Ở chế độ tối, nền trắng 60% cộng chữ `inkOf` (gần trắng) là
                // chữ sáng trên nền sáng — đo được tương phản khoảng 1,2:1, tức
                // không đọc được. Chế độ sáng giữ nguyên đúng thiết kế gốc, chế
                // độ tối hạ xuống một lớp phủ trắng mỏng để viên nhãn vẫn tách
                // khỏi mặt kính mà chữ sáng vẫn nổi.
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
