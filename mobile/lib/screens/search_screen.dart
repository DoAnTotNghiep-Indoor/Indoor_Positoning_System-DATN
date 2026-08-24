import 'package:flutter/material.dart';
import '../data/demo_data.dart';
import '../theme/app_colors.dart';
import '../widgets/blob_background.dart';
import '../widgets/glass_card.dart';
import 'area_detail_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _controller = TextEditingController(text: 'phòng học');
  int _filter = 0;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  /// Lọc cục bộ trên dữ liệu demo — bản chính thức sẽ gọi API tìm kiếm.
  ///
  /// Khớp theo từng từ thay vì nguyên cụm, để "phòng học" vẫn ra cả "Phòng họp",
  /// "Phòng hội thảo"… đúng như frame thiết kế (5 kết quả).
  List<Area> get _results {
    final tokens = _controller.text
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
    final results = _results;

    return BlobBackground(
      blobs: BlobBackground.listBlobs,
      child: SafeArea(
        bottom: false,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 12, 24, 0),
              child: Text('Tìm kiếm',
                  style: Theme.of(context).textTheme.headlineLarge),
            ),
            const SizedBox(height: 16),

            // --- Ô tìm kiếm ---
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: GlassCard(
                radius: 20,
                opacity: 0.6,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: SizedBox(
                  height: 52,
                  child: Row(
                    children: [
                      Icon(Icons.search,
                          size: 20, color: AppColors.ink.withValues(alpha: 0.55)),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          controller: _controller,
                          onChanged: (_) => setState(() {}),
                          style: TextStyle(
                            fontSize: 16,
                            color: AppColors.ink.withValues(alpha: 0.85),
                          ),
                          cursorColor: AppColors.accent,
                          decoration: const InputDecoration(
                            isCollapsed: true,
                            border: InputBorder.none,
                            hintText: 'Tìm phòng, khu vực…',
                          ),
                        ),
                      ),
                      if (_controller.text.isNotEmpty)
                        GestureDetector(
                          onTap: () {
                            _controller.clear();
                            setState(() {});
                          },
                          child: Container(
                            width: 22,
                            height: 22,
                            decoration: BoxDecoration(
                              color: AppColors.ink.withValues(alpha: 0.14),
                              shape: BoxShape.circle,
                            ),
                            child: Icon(Icons.close,
                                size: 13,
                                color: AppColors.ink.withValues(alpha: 0.8)),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(height: 14),

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
                  return GestureDetector(
                    onTap: () => setState(() => _filter = i),
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      decoration: BoxDecoration(
                        color: active
                            ? AppColors.accent
                            : Colors.white.withValues(alpha: 0.45),
                        borderRadius: BorderRadius.circular(17),
                        border: active
                            ? null
                            : Border.all(
                                color: Colors.white.withValues(alpha: 0.7)),
                      ),
                      child: Text(
                        DemoData.searchFilters[i],
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: active
                              ? Colors.white
                              : AppColors.ink.withValues(alpha: 0.8),
                        ),
                      ),
                    ),
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
                  color: AppColors.ink.withValues(alpha: 0.6),
                ),
              ),
            ),
            const SizedBox(height: 10),

            // --- Danh sách kết quả ---
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 110),
                itemCount: results.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (context, i) => _ResultCard(area: results[i]),
              ),
            ),
          ],
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
              color: AppColors.accent.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(15),
            ),
            child: Icon(area.icon, size: 22, color: AppColors.accent),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  area.nameVi,
                  style: const TextStyle(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w500,
                    color: AppColors.ink,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  area.nameEn,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: AppColors.ink.withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${area.distanceM} m',
            style: const TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w500,
              color: AppColors.accent,
            ),
          ),
        ],
      ),
    );
  }
}
