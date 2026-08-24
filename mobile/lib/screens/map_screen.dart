import 'package:flutter/material.dart';
import '../data/demo_data.dart';
import '../theme/app_colors.dart';
import '../widgets/blob_background.dart';
import '../widgets/floor_plan.dart';
import '../widgets/glass_card.dart';

class MapScreen extends StatelessWidget {
  const MapScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlobBackground(
      blobs: BlobBackground.mapBlobs,
      child: SafeArea(
        bottom: false,
        // fit: expand — bắt buộc, nếu không Stack sẽ co theo con không-Positioned
        // (header) và làm sơ đồ mặt bằng bị ép mất.
        child: Stack(
          fit: StackFit.expand,
          children: [
            // Sơ đồ mặt bằng
            const Positioned.fill(
              child: SingleChildScrollView(
                padding: EdgeInsets.only(top: 116, bottom: 96),
                child: FloorPlan(),
              ),
            ),

            // Header
            const Positioned(
              top: 0,
              left: 16,
              right: 16,
              child: MapHeader(),
            ),

            // Nút định vị lại
            Positioned(
              right: 16,
              bottom: 96,
              child: GestureDetector(
                onTap: () => ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Bản demo — chưa nối API định vị'),
                    duration: Duration(seconds: 2),
                  ),
                ),
                child: Container(
                  width: 54,
                  height: 54,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.62),
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white.withValues(alpha: 0.7)),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.ink.withValues(alpha: 0.07),
                        offset: const Offset(0, 8),
                        blurRadius: 18,
                      ),
                    ],
                  ),
                  child: const Icon(Icons.navigation_outlined,
                      size: 21, color: AppColors.accent),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Thẻ header hiển thị tên toà nhà và tầng đang xem.
class MapHeader extends StatelessWidget {
  const MapHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      radius: 26,
      opacity: 0.6,
      shadow: true,
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  DemoData.buildingName,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: AppColors.ink,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  DemoData.areaCountLabel,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: AppColors.ink.withValues(alpha: 0.55),
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.6),
              borderRadius: BorderRadius.circular(15),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.place_outlined,
                    size: 13, color: AppColors.ink.withValues(alpha: 0.7)),
                const SizedBox(width: 4),
                Text(
                  DemoData.floorLabel,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w500,
                    color: AppColors.ink.withValues(alpha: 0.85),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
