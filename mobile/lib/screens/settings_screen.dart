import 'package:flutter/material.dart';
import '../data/demo_data.dart';
import '../theme/app_colors.dart';
import '../widgets/blob_background.dart';
import '../widgets/glass_card.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlobBackground(
      blobs: BlobBackground.listBlobs,
      child: SafeArea(
        bottom: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 110),
          children: [
            Padding(
              padding: const EdgeInsets.only(left: 8),
              child: Text('Cài đặt',
                  style: Theme.of(context).textTheme.headlineLarge),
            ),
            const SizedBox(height: 30),

            const _SectionLabel('CHUNG'),
            const SizedBox(height: 10),
            GlassCard(
              radius: 26,
              opacity: 0.5,
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Column(
                children: [
                  const _SettingRow(
                    icon: Icons.info_outline,
                    title: 'Thông tin ứng dụng',
                    value: DemoData.appVersion,
                  ),
                  Padding(
                    padding: const EdgeInsets.only(left: 64, right: 16),
                    child: Divider(
                      height: 1,
                      thickness: 1,
                      color: AppColors.ink.withValues(alpha: 0.07),
                    ),
                  ),
                  const _SettingRow(
                    icon: Icons.dns_outlined,
                    title: 'Máy chủ định vị',
                    value: DemoData.serverHost,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),
            const _SectionLabel('QUYỀN TRUY CẬP'),
            const SizedBox(height: 10),
            const GlassCard(
              radius: 26,
              opacity: 0.5,
              padding: EdgeInsets.symmetric(vertical: 6),
              child: _SettingRow(
                icon: Icons.place_outlined,
                title: 'Vị trí và WiFi',
                subtitle: 'Cần thiết để định vị',
                value: DemoData.permissionState,
              ),
            ),

            const SizedBox(height: 20),
            GlassCard(
              radius: 24,
              opacity: 0.38,
              padding: const EdgeInsets.all(18),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline,
                      size: 18, color: AppColors.ink.withValues(alpha: 0.45)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Các tuỳ chọn khác sẽ được bổ sung ở phiên bản tiếp theo.',
                      style: TextStyle(
                        fontSize: 12.5,
                        height: 1.45,
                        color: AppColors.ink.withValues(alpha: 0.55),
                      ),
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

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 12),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          letterSpacing: 0.4,
          color: AppColors.ink.withValues(alpha: 0.45),
        ),
      ),
    );
  }
}

class _SettingRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final String value;

  const _SettingRow({
    required this.icon,
    required this.title,
    required this.value,
    this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppColors.accent.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, size: 19, color: AppColors.accent),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 14,
                    color: AppColors.ink.withValues(alpha: 0.9),
                  ),
                ),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    subtitle!,
                    style: TextStyle(
                      fontSize: 11.5,
                      color: AppColors.ink.withValues(alpha: 0.5),
                    ),
                  ),
                ],
              ],
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 12,
              color: AppColors.ink.withValues(alpha: 0.42),
            ),
          ),
        ],
      ),
    );
  }
}
