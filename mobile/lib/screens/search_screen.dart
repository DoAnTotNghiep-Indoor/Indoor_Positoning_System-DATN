import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;
import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../widgets/glass_card.dart';
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
  int _filter = 0;

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

    return DemoData.searchResults.where((a) {
      final haystack = '${a.nameVi} ${a.nameEn}'.toLowerCase();
      final matchQuery =
          tokens.isEmpty || tokens.any((t) => haystack.contains(t));
      final matchFilter =
          _filter == 0 || a.category == DemoData.searchFilters[_filter];
      return matchQuery && matchFilter;
    }).toList();
  }

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
            child: Text(t.searchTitle,
                style: Theme.of(context).textTheme.headlineLarge),
          ),
          const SizedBox(height: 16),

          // --- Chip lọc ---
          SizedBox(
            height: 34,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: DemoData.searchFilters.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, i) {
                final active = i == _filter;
                return lg.GlassChip(
                  label: DemoData.searchFilters[i],
                  selected: active,
                  onTap: () => setState(() => _filter = i),
                );
              },
            ),
          ),

          const SizedBox(height: 18),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Text(
              '${results.length} kết quả',
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w500,
                color: AppColors.inkOf(context).withValues(alpha: 0.6),
              ),
            ),
          ),
          const SizedBox(height: 10),

          // --- Danh sách kết quả ---
          Expanded(
            child: ListView.separated(
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

class _ResultCard extends StatelessWidget {
  final Area area;
  const _ResultCard({required this.area});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      radius: 24,
      opacity: 0.5,
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
              color: AppColors.accentOf(context).withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(15),
            ),
            child: Icon(area.icon, size: 22, color: AppColors.accentOf(context)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  area.nameVi,
                  style: TextStyle(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w500,
                    color: AppColors.inkOf(context),
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  area.nameEn,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: AppColors.inkOf(context).withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${area.distanceM} m',
            style: TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w500,
              color: AppColors.accentOf(context),
            ),
          ),
        ],
      ),
    );
  }
}
