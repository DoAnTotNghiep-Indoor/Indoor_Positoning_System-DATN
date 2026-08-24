import 'package:flutter/material.dart';
import '../data/demo_data.dart';
import '../theme/app_colors.dart';
import '../widgets/blob_background.dart';
import '../widgets/floor_plan.dart';
import 'map_screen.dart';

/// Màn chi tiết khu vực: sơ đồ phía trên, bottom sheet thông tin phía dưới.
class AreaDetailScreen extends StatelessWidget {
  const AreaDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BlobBackground(
        blobs: BlobBackground.mapBlobs,
        child: SafeArea(
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

              // Header
              const Positioned(
                top: 0,
                left: 16,
                right: 16,
                child: MapHeader(),
              ),

              // Bottom sheet thông tin
              const Positioned(
                left: 0,
                right: 0,
                bottom: 0,
                child: _DetailSheet(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DetailSheet extends StatelessWidget {
  const _DetailSheet();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(36)),
        boxShadow: [
          BoxShadow(
            color: AppColors.ink.withValues(alpha: 0.10),
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
              color: AppColors.ink.withValues(alpha: 0.6),
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
              color: AppColors.ink.withValues(alpha: 0.72),
            ),
          ),

          const SizedBox(height: 22),
          // Nút đi tới đây
          GestureDetector(
            onTap: () => ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Bản demo — chức năng chỉ đường làm ở giai đoạn sau'),
                duration: Duration(seconds: 2),
              ),
            ),
            child: Container(
              height: 56,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                gradient: AppColors.ctaGradient,
                borderRadius: BorderRadius.circular(22),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.accent.withValues(alpha: 0.35),
                    offset: const Offset(0, 8),
                    blurRadius: 18,
                  ),
                ],
              ),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.navigation_outlined, size: 19, color: Colors.white),
                  SizedBox(width: 8),
                  Text(
                    'Đi tới đây',
                    style: TextStyle(
                      fontSize: 16.5,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
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
