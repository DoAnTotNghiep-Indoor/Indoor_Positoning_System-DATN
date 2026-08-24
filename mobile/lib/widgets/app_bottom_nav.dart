import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

/// Thanh điều hướng dưới: 3 tab trong khối bo tròn + nút tìm kiếm tách riêng.
class AppBottomNav extends StatelessWidget {
  final int currentIndex;
  final bool searchActive;
  final ValueChanged<int> onTap;
  final VoidCallback onSearchTap;

  const AppBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.onSearchTap,
    this.searchActive = false,
  });

  static const _tabs = <({IconData icon, String label})>[
    (icon: Icons.home_outlined, label: 'Trang chủ'),
    (icon: Icons.map_outlined, label: 'Bản đồ'),
    (icon: Icons.settings_outlined, label: 'Cài đặt'),
  ];

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 0, 24, 25),
      child: Row(
        children: [
          Expanded(
            child: Container(
              height: 54,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.6),
                borderRadius: BorderRadius.circular(27),
                border: Border.all(color: Colors.white.withValues(alpha: 0.7)),
              ),
              child: Row(
                children: [
                  for (var i = 0; i < _tabs.length; i++)
                    Expanded(
                      child: _NavTab(
                        icon: _tabs[i].icon,
                        label: _tabs[i].label,
                        active: !searchActive && currentIndex == i,
                        onTap: () => onTap(i),
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 16),
          GestureDetector(
            onTap: onSearchTap,
            child: Container(
              width: 54,
              height: 54,
              decoration: BoxDecoration(
                color: searchActive
                    ? const Color(0xFFEDEDED).withValues(alpha: 0.92)
                    : Colors.white.withValues(alpha: 0.6),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white.withValues(alpha: 0.7)),
              ),
              child: const Icon(Icons.search, size: 21, color: AppColors.navInk),
            ),
          ),
        ],
      ),
    );
  }
}

class _NavTab extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  const _NavTab({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 54,
        decoration: BoxDecoration(
          color: active
              ? const Color(0xFFEDEDED).withValues(alpha: 0.92)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(27),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 19, color: AppColors.navInk),
            const SizedBox(height: 3),
            Text(
              label,
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w500,
                color: AppColors.navInk,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
