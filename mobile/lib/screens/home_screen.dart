import 'package:flutter/material.dart';
import 'package:intl/intl.dart' as intl;

import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../widgets/glass_card.dart';
import '../widgets/tap_feedback.dart';
import 'area_detail_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final chuaCho = AppMetrics.chuaChoThanhTab(context);
    final t = L.of(context);
    final muc = AppColors.inkOf(context);

    // Dấu thập phân khác nhau giữa hai ngôn ngữ: tiếng Việt viết "3,2" còn tiếng
    // Anh viết "3.2". `toString()` của Dart luôn cho dấu chấm nên bản tiếng Việt
    // trước đây hiện "Sai số ±3.2 m" — sai quy ước chính tả.
    final saiSo = intl.NumberFormat.decimalPattern(t.localeName)
        .format(DemoData.accuracyM);

    return SafeArea(
      bottom: false,
      child: ListView(
        padding: EdgeInsets.fromLTRB(24, 12, 24, chuaCho),
        children: [
          // --- Vị trí hiện tại ---
          //
          // Gộp cả khối thành một mục trợ năng: bốn dòng rời khiến trình đọc màn
          // hình đọc "Bạn đang ở" / "Phòng học nhóm" / "Tầng 1…" / "Sai số…"
          // thành bốn lần vuốt, trong khi chúng là một mẩu thông tin duy nhất và
          // là thứ quan trọng nhất trên màn hình.
          MergeSemantics(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  t.homeYouAreAt,
                  style: TextStyle(
                    fontSize: 15,
                    color: muc.withValues(alpha: 0.55),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  theoNgonNgu(context, DemoData.currentAreaName,
                      DemoData.currentAreaNameEn),
                  style: Theme.of(context).textTheme.displayLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  theoNgonNgu(
                      context, DemoData.currentFloor, DemoData.currentFloorEn),
                  style: TextStyle(
                    fontSize: 15,
                    color: muc.withValues(alpha: 0.7),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  t.homeAccuracy(saiSo),
                  style: TextStyle(
                    fontSize: 13,
                    color: muc.withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 40),
          _TieuDeMuc(t.homeQuickAccess),
          const SizedBox(height: 14),

          // --- 4 ô truy cập nhanh ---
          //
          // Chiều cao co theo cỡ chữ hệ thống thay vì đóng cứng 104: ở mức phóng
          // to 1,6 lần, cột chữ bên trong tràn 26 pixel và Flutter vẽ vạch sọc
          // vàng đen đè lên thẻ (đo được bằng test widget).
          SizedBox(
            height: AppMetrics.caoTheoCoChu(context, coBan: 104, phanChu: 48),
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
          _TieuDeMuc(t.homeNearby),
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
                        color: muc.withValues(alpha: 0.08),
                      ),
                    ),
                  _NearbyRow(area: DemoData.nearby[i]),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Tiêu đề của một mục trên trang.
///
/// Đánh dấu `header: true` để trình đọc màn hình nhảy được giữa các mục bằng
/// thao tác "chuyển tiêu đề" thay vì phải vuốt qua từng dòng.
class _TieuDeMuc extends StatelessWidget {
  final String text;
  const _TieuDeMuc(this.text);

  @override
  Widget build(BuildContext context) {
    return Semantics(
      header: true,
      child: Text(text, style: Theme.of(context).textTheme.titleMedium),
    );
  }
}

class _QuickTile extends StatelessWidget {
  final QuickAccess item;
  const _QuickTile({required this.item});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final nhan = item.nhan(context);

    return GlassCard(
      radius: 24,
      semanticLabel: t.a11yAreaRow(nhan, item.distanceM),
      semanticHint: t.a11yOpenArea,
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const AreaDetailScreen()),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(item.icon, size: 24, color: AppColors.accentOf(context)),
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text(
              nhan,
              textAlign: TextAlign.center,
              maxLines: 2,
              // Chốt chặn cuối cho tên dài: "Reading space" ở cỡ chữ lớn trên
              // màn hẹp vẫn có thể vượt hai dòng.
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 11,
                height: 1.2,
                color: AppColors.inkOf(context).withValues(alpha: 0.75),
              ),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            t.distanceMeters(item.distanceM),
            maxLines: 1,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: AppColors.inkOf(context).withValues(alpha: 0.42),
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
    final t = L.of(context);
    final muc = AppColors.inkOf(context);
    final nhan = AppColors.accentOf(context);

    // TapFeedback chứ không GestureDetector trần: dòng này nằm trong một
    // GlassCard chung nên không có nền riêng để đổi màu khi bấm, trước đây chạm
    // vào hoàn toàn không thấy gì.
    return TapFeedback(
      semanticLabel: t.a11yAreaRow(area.tenChinh(context), area.distanceM),
      semanticHint: t.a11yOpenArea,
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
                color: nhan.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(13),
              ),
              child: Icon(area.icon, size: 20, color: nhan),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    area.tenChinh(context),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 13.5, color: muc),
                  ),
                  const SizedBox(height: 2),
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
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: nhan,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
