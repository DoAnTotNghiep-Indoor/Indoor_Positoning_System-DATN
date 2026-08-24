import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class Blob {
  final double cx, cy, r;
  final Color color;
  final double opacity;
  const Blob(this.cx, this.cy, this.r, this.color, this.opacity);
}

/// Nền gradient kèm các khối màu mờ, tái hiện lớp nền trong frame thiết kế.
/// Toạ độ blob dùng hệ 393x852 rồi được co giãn theo kích thước màn hình thật.
class BlobBackground extends StatelessWidget {
  final List<Blob> blobs;
  final Widget child;

  const BlobBackground({super.key, required this.blobs, required this.child});

  /// Bộ blob của màn Trang chủ.
  static const homeBlobs = <Blob>[
    Blob(30, 20, 140, AppColors.blobA, 0.50),
    Blob(370, 270, 115, AppColors.blobB, 0.35),
    Blob(40, 700, 135, AppColors.blobC, 0.42),
    Blob(330, 820, 120, AppColors.blobD, 0.35),
  ];

  /// Bộ blob của màn Bản đồ và Chi tiết.
  static const mapBlobs = <Blob>[
    Blob(20, 10, 145, AppColors.blobA, 0.45),
    Blob(380, 700, 120, AppColors.blobB, 0.35),
    Blob(30, 500, 110, AppColors.blobC, 0.30),
  ];

  /// Bộ blob của màn Tìm kiếm và Cài đặt.
  static const listBlobs = <Blob>[
    Blob(360, 60, 130, AppColors.blobA, 0.42),
    Blob(20, 380, 130, AppColors.blobB, 0.34),
    Blob(330, 760, 125, AppColors.blobC, 0.40),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, c) {
        final sx = c.maxWidth / 393.0;
        final sy = c.maxHeight / 852.0;
        return DecoratedBox(
          decoration: const BoxDecoration(gradient: AppColors.bgGradient),
          child: Stack(
            children: [
              // Lớp blob mờ
              Positioned.fill(
                child: ClipRect(
                  child: ImageFiltered(
                    imageFilter: ImageFilter.blur(sigmaX: 52, sigmaY: 52),
                    child: Stack(
                      children: [
                        for (final b in blobs)
                          Positioned(
                            left: (b.cx - b.r) * sx,
                            top: (b.cy - b.r) * sy,
                            width: b.r * 2 * sx,
                            height: b.r * 2 * sy,
                            child: DecoratedBox(
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: b.color.withValues(alpha: b.opacity),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
              child,
            ],
          ),
        );
      },
    );
  }
}
