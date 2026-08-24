import 'package:flutter/material.dart';
import '../data/demo_data.dart';
import '../theme/app_colors.dart';
import '../widgets/blob_background.dart';
import '../widgets/glass_card.dart';
import 'area_detail_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlobBackground(
      blobs: BlobBackground.homeBlobs,
      child: SafeArea(
        bottom: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 12, 24, 110),
          children: [
            // --- Vị trí hiện tại ---
            Text(
              'Bạn đang ở',
              style: TextStyle(
                fontSize: 15,
                color: AppColors.ink.withValues(alpha: 0.55),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              DemoData.currentAreaName,
              style: Theme.of(context).textTheme.displayLarge,
            ),
            const SizedBox(height: 8),
            Text(
              DemoData.currentFloor,
              style: TextStyle(
                fontSize: 15,
                color: AppColors.ink.withValues(alpha: 0.7),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Sai số ±${DemoData.accuracyM} m',
              style: TextStyle(
                fontSize: 13,
                color: AppColors.ink.withValues(alpha: 0.5),
              ),
            ),

            const SizedBox(height: 40),
            Text('Truy cập nhanh',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 14),

            // --- 4 ô truy cập nhanh ---
            SizedBox(
              height: 104,
              child: Row(
                children: [
                  for (var i = 0; i < DemoData.quickAccess.length; i++) ...[
                    if (i > 0) const SizedBox(width: 11),
                    Expanded(child: _QuickTile(item: DemoData.quickAccess[i])),
                  ],
                ],
              ),
            ),

            const SizedBox(height: 34),
            Text('Gần bạn', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 14),

            // --- Danh sách gần bạn ---
            GlassCard(
              radius: 26,
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Column(
                children: [
                  for (var i = 0; i < DemoData.nearby.length; i++) ...[
                    if (i > 0)
                      Padding(
                        padding: const EdgeInsets.only(left: 63),
                        child: Divider(
                          height: 1,
                          thickness: 1,
                          color: AppColors.ink.withValues(alpha: 0.08),
                        ),
                      ),
                    _NearbyRow(area: DemoData.nearby[i]),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickTile extends StatelessWidget {
  final QuickAccess item;
  const _QuickTile({required this.item});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      radius: 24,
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const AreaDetailScreen()),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(item.icon, size: 24, color: AppColors.accent),
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text(
              item.label,
              textAlign: TextAlign.center,
              maxLines: 2,
              style: TextStyle(
                fontSize: 11,
                height: 1.2,
                color: AppColors.ink.withValues(alpha: 0.75),
              ),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '${item.distanceM} m',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: AppColors.ink.withValues(alpha: 0.42),
            ),
          ),
        ],
      ),
    );
  }
}

class _NearbyRow extends StatelessWidget {
  final Area area;
  const _NearbyRow({required this.area});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const AreaDetailScreen()),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 9.5),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: AppColors.accent.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(13),
              ),
              child: Icon(area.icon, size: 20, color: AppColors.accent),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    area.nameVi,
                    style: const TextStyle(fontSize: 13.5, color: AppColors.ink),
                  ),
                  const SizedBox(height: 2),
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
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: AppColors.accent,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
