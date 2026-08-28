import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;
import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../widgets/glass_card.dart';
import '../widgets/tap_feedback.dart';
import 'area_detail_screen.dart';

class SearchScreen extends StatefulWidget {
  /// Từ khoá do thanh điều hướng dưới cung cấp.
  ///
  /// Ô nhập nay nằm trong `GlassTabBar.searchable` chứ không nằm trong màn hình,
  /// nên màn hình chỉ nhận kết quả gõ vào chứ không tự giữ TextEditingController
  /// — tránh hai ô tìm kiếm cùng hiện trên một màn.
  final String tuKhoa;

  const SearchScreen({super.key, this.tuKhoa = ''});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  /// Chỉ số trong [AreaCategory.danhSach]; 0 là "Tất cả".
  int _filter = 0;

  bool get _dangLoc => _filter != 0;

  /// Lọc cục bộ trên dữ liệu demo — bản chính thức sẽ gọi API tìm kiếm.
  ///
  /// Khớp theo từng từ thay vì nguyên cụm, để "phòng học" vẫn ra cả "Phòng họp",
  /// "Phòng hội thảo"… đúng như frame thiết kế (5 kết quả).
  List<Area> get _results {
    final tokens = widget.tuKhoa
        .trim()
        .toLowerCase()
        .split(RegExp(r'\s+'))
        .where((t) => t.isNotEmpty)
        .toList();

    final nhom = AreaCategory.danhSach[_filter];

    return DemoData.searchResults.where((a) {
      final haystack = '${a.nameVi} ${a.nameEn}'.toLowerCase();
      final matchQuery =
          tokens.isEmpty || tokens.any((t) => haystack.contains(t));
      // So theo MÃ nhóm, không theo nhãn hiển thị: nhãn đổi theo ngôn ngữ nên
      // bản cũ (so với chuỗi "Học tập") lọc ra rỗng khi giao diện đang tiếng Anh.
      final matchFilter = nhom == AreaCategory.all || a.category == nhom;
      return matchQuery && matchFilter;
    }).toList();
  }

  String _nhanNhom(L t, String ma) => switch (ma) {
        AreaCategory.study => t.searchFilterStudy,
        AreaCategory.facility => t.searchFilterFacility,
        AreaCategory.internal => t.searchFilterInternal,
        _ => t.searchFilterAll,
      };

  @override
  Widget build(BuildContext context) {
    final chuaCho = AppMetrics.chuaChoThanhTab(context);
    final t = L.of(context);
    final results = _results;

    return SafeArea(
      bottom: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 12, 24, 0),
            child: Semantics(
              header: true,
              child: Text(t.searchTitle,
                  style: Theme.of(context).textTheme.headlineLarge),
            ),
          ),
          const SizedBox(height: 16),

          // --- Chip lọc ---
          //
          // Chiều cao 46 chứ không phải 34. Chip nằm trong ListView ngang nên bị
          // ép đúng chiều cao của hộp này, tức vùng chạm cũng chỉ cao 34 — dưới
          // mức tối thiểu 48dp của Material và 44pt của Apple HIG. Đây là hàng
          // điều khiển hay bấm nhất trên màn Tìm kiếm nên đáng để nới.
          SizedBox(
            height: AppMetrics.caoTheoCoChu(context, coBan: 46, phanChu: 18),
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: AreaCategory.danhSach.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, i) {
                final nhan = _nhanNhom(t, AreaCategory.danhSach[i]);
                return lg.GlassChip(
                  label: nhan,
                  selected: i == _filter,
                  semanticLabel: nhan,
                  onTap: () => setState(() => _filter = i),
                );
              },
            ),
          ),

          const SizedBox(height: 18),

          // --- Dòng trạng thái: số kết quả + bộ lọc đang bật ---
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    // Trước đây ghép cứng chuỗi '$n kết quả' trong mã, nên ở
                    // giao diện tiếng Anh vẫn hiện tiếng Việt.
                    t.searchResultCount(results.length),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w500,
                      color: AppColors.inkOf(context).withValues(alpha: 0.6),
                    ),
                  ),
                ),
                // Lối thoát cho bộ lọc: chip đang chọn nằm trong hàng cuộn ngang
                // nên có thể đã trôi khỏi màn hình, người dùng thấy "0 kết quả"
                // mà không biết vì sao. Nút này luôn nhìn thấy khi bộ lọc đang bật.
                if (_dangLoc)
                  _NutBoLoc(onTap: () => setState(() => _filter = 0)),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // --- Danh sách kết quả ---
          Expanded(
            child: results.isEmpty
                ? _KhongCoKetQua(
                    dangLoc: _dangLoc,
                    chuaCho: chuaCho,
                    onBoLoc: () => setState(() => _filter = 0),
                  )
                : ListView.separated(
                    padding: EdgeInsets.fromLTRB(16, 0, 16, chuaCho),
                    itemCount: results.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, i) => _ResultCard(area: results[i]),
                  ),
          ),
        ],
      ),
    );
  }
}

/// Trạng thái "không tìm thấy gì".
///
/// Trước đây chỗ này là một `ListView` rỗng: người dùng gõ sai một chữ là màn
/// hình trắng trơn, chỉ còn dòng "0 kết quả" nhỏ ở trên — không nói vì sao và
/// cũng không gợi ý làm gì tiếp.
class _KhongCoKetQua extends StatelessWidget {
  final bool dangLoc;
  final double chuaCho;
  final VoidCallback onBoLoc;

  const _KhongCoKetQua({
    required this.dangLoc,
    required this.chuaCho,
    required this.onBoLoc,
  });

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);

    // Cuộn được chứ không phải Center cứng: trên màn thấp hoặc khi bàn phím đang
    // bật, khối này cộng phần chừa cho thanh tab vượt quá chiều cao còn lại.
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(32, 24, 32, chuaCho),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Icon(
            Icons.search_off_outlined,
            size: 44,
            color: muc.withValues(alpha: 0.32),
          ),
          const SizedBox(height: 14),
          Text(
            t.searchEmpty,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: muc.withValues(alpha: 0.75),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            t.searchEmptyHint,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 13,
              height: 1.45,
              color: muc.withValues(alpha: 0.5),
            ),
          ),
          if (dangLoc) ...[
            const SizedBox(height: 18),
            _NutBoLoc(onTap: onBoLoc, noiBat: true),
          ],
        ],
      ),
    );
  }
}

/// Nút chữ "Bỏ bộ lọc".
///
/// Vùng chạm cao tối thiểu 48 dù chữ chỉ cao 15 — đây là nút chữ trần, không có
/// nền nên rất dễ bấm trượt nếu chỉ lấy đúng khung chữ làm vùng chạm.
class _NutBoLoc extends StatelessWidget {
  final VoidCallback onTap;
  final bool noiBat;

  const _NutBoLoc({required this.onTap, this.noiBat = false});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final nhan = AppColors.accentOf(context);

    return TapFeedback(
      onTap: onTap,
      semanticLabel: t.searchClearFilter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(
          minHeight: AppMetrics.vungChamToiThieu,
          minWidth: AppMetrics.vungChamToiThieu,
        ),
        child: Container(
          alignment: Alignment.center,
          padding: EdgeInsets.symmetric(horizontal: noiBat ? 18 : 10),
          decoration: noiBat
              ? BoxDecoration(
                  color: nhan.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(16),
                )
              : null,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.filter_alt_off_outlined, size: 15, color: nhan),
              const SizedBox(width: 5),
              Text(
                t.searchClearFilter,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w600,
                  color: nhan,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  final Area area;
  const _ResultCard({required this.area});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);
    final nhan = AppColors.accentOf(context);

    return GlassCard(
      radius: 24,
      semanticLabel: t.a11yAreaRow(area.tenChinh(context), area.distanceM),
      semanticHint: t.a11yOpenArea,
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const AreaDetailScreen()),
      ),
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: nhan.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(15),
            ),
            child: Icon(area.icon, size: 22, color: nhan),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  area.tenChinh(context),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w500,
                    color: muc,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  area.tenPhu(context),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: muc.withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            t.distanceMeters(area.distanceM),
            maxLines: 1,
            style: TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w500,
              color: nhan,
            ),
          ),
        ],
      ),
    );
  }
}
