import 'package:flutter/material.dart';
// Ẩn GlassCard của thư viện: file này dùng bản bọc trong widgets/glass_card.dart
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' hide GlassCard;
import 'package:intl/intl.dart' as intl;

import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../widgets/so_do_that.dart';
import '../services/theo_doi_vi_tri.dart';
import '../widgets/glass_card.dart';
import '../widgets/tap_feedback.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  /// Nhóm đang lọc, null là hiện tất cả. Trạng thái thuần giao diện nên giữ ở
  /// màn này, không đẩy xuống TheoDoiViTri cùng chỗ với dữ liệu định vị.
  String? _loc;

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
                  child: Center(child: SoDoMatBang(loc: _loc)),
                ),
              ),
            ),
          ),

          // Header, hàng chip lọc và thẻ tuyến xếp chồng thành một cột nổi.
          // Chúng nằm NGOÀI InteractiveViewer: phóng to sơ đồ mà chip cũng to
          // theo thì bấm không trúng, và thẻ quãng đường sẽ trôi khỏi màn hình.
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: MapHeader(),
                ),
                const SizedBox(height: 8),
                _HangChip(
                  chon: _loc,
                  doi: (v) => setState(() => _loc = v),
                ),
                const _TheTuyen(),
              ],
            ),
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

  /// Dòng phụ của thẻ header: số khu vực, kèm mốc cập nhật nếu đã định vị.
  ///
  /// Chưa có toạ độ nào thì bỏ hẳn vế thời gian thay vì điền một con số cho có
  /// — chuỗi cũ viết cứng "cập nhật 2 giây trước" nên nó đúng hai giây trong cả
  /// vòng đời ứng dụng, kể cả lúc định vị đang tắt.
  String _tomTat(BuildContext context) {
    final theoDoi = TheoDoiViTriScope.of(context);
    final so = theoDoi.khuVuc.length;
    final giay = theoDoi.giayTuCapNhat;
    final t = L.of(context);
    return giay == null ? t.mapAreaCount(so) : t.mapAreaSummary(so, giay);
  }

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
                    _tomTat(context),
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

/// Hàng chip lọc loại khu vực, cuộn ngang.
///
/// Nhãn chip lấy thẳng từ `nhom` của dữ liệu khảo sát, không có bảng loại viết
/// riêng. CTK45 giữ một `CategoryModel` tách rời nên chuỗi trong bảng đó trôi
/// khỏi chuỗi trong dữ liệu — có mục thừa một dấu cách ở cuối và không bao giờ
/// khớp được cái gì. Ở đây chỉ có một nguồn nên không có gì để lệch.
class _HangChip extends StatelessWidget {
  final String? chon;
  final ValueChanged<String?> doi;

  const _HangChip({required this.chon, required this.doi});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final theoDoi = TheoDoiViTriScope.of(context);

    return AnimatedBuilder(
      animation: theoDoi,
      builder: (context, _) {
        // Sắp theo tên để thứ tự chip đứng yên; danh sách khu vực vốn sắp theo
        // khoảng cách nên nó đảo chỗ mỗi lần người dùng bước đi.
        final nhom = [for (final k in theoDoi.khuVuc) k.nhom]..sort();

        return Semantics(
          label: t.mapFilterHint,
          child: SizedBox(
            height: 40,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              children: [
                _chip(context, t.mapFilterAll, chon == null, () => doi(null)),
                for (final n in nhom)
                  _chip(context, n, chon == n, () => doi(chon == n ? null : n)),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _chip(BuildContext context, String chu, bool bat, VoidCallback cham) {
    final mau = AppColors.accentOf(context);
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: TapFeedback(
        semanticLabel: chu,
        onTap: cham,
        child: Container(
          alignment: Alignment.center,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          decoration: BoxDecoration(
            color: bat
                ? mau
                : Theme.of(context).colorScheme.surface.withValues(alpha: 0.72),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: mau.withValues(alpha: bat ? 1 : 0.28)),
          ),
          child: Text(
            chu,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: bat ? Colors.white : AppColors.inkOf(context),
            ),
          ),
        ),
      ),
    );
  }
}

/// Thẻ tổng quãng đường của tuyến đang hiện, kèm nút xoá.
///
/// Số mét ở đây là quãng đường Dijkstra cộng dồn trên các cạnh ĐÃ LỌC TƯỜNG,
/// tính trong hệ mét đo thực địa — khác với thẻ "Tổng khoảng cách" của CTK45
/// vốn cộng trên hình học GeoJSON vẽ tay, nơi một cặp điểm cách nhau 12,8 m
/// thật được ghi thành 7,3 m.
class _TheTuyen extends StatelessWidget {
  const _TheTuyen();

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final theoDoi = TheoDoiViTriScope.of(context);

    return AnimatedBuilder(
      animation: theoDoi,
      builder: (context, _) {
        final tuyen = theoDoi.tuyen;
        final dich = theoDoi.dichTuyen;
        if (tuyen == null || dich == null) return const SizedBox.shrink();

        final so = intl.NumberFormat('#0.#', t.localeName);
        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: GlassCard(
            radius: 20,
            padding: const EdgeInsets.fromLTRB(14, 8, 6, 8),
            child: MergeSemantics(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.turn_right_rounded,
                      size: 18, color: AppColors.accentOf(context)),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      t.mapRouteChip(so.format(tuyen.quangDuongM), dich.nhom),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          fontSize: 13, fontWeight: FontWeight.w600),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close_rounded, size: 18),
                    tooltip: t.mapClearRoute,
                    onPressed: theoDoi.xoaTuyen,
                    visualDensity: VisualDensity.compact,
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
