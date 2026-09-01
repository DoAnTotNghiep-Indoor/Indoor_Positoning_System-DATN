import 'package:flutter/material.dart';
import 'package:intl/intl.dart' as intl;

import '../data/demo_data.dart';
import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../services/api_dinh_vi.dart';
import '../services/quet_wifi.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_colors.dart';
import '../theme/app_settings.dart';
import '../theme/app_metrics.dart';
import '../widgets/glass_card.dart';
import '../widgets/tap_feedback.dart';
import 'area_detail_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theoDoi = TheoDoiViTriScope.of(context);
    return AnimatedBuilder(
      animation: theoDoi,
      builder: (context, _) => _noiDung(context, theoDoi),
    );
  }

  Widget _noiDung(BuildContext context, TheoDoiViTri theoDoi) {
    final chuaCho = AppMetrics.chuaChoThanhTab(context);
    final t = L.of(context);
    final muc = AppColors.inkOf(context);

    // Khu vực thật, sắp theo khoảng cách tới chỗ đang đứng. Chưa định vị thì
    // giữ thứ tự bảng chữ cái — bịa ra một điểm quy chiếu để sắp còn tệ hơn.
    final khu = theoDoi.khuVuc;
    final vt = theoDoi.viTri;

    return SafeArea(
      bottom: false,
      child: ListView(
        padding: EdgeInsets.fromLTRB(24, 12, 24, chuaCho),
        children: [
          const _KhoiViTri(),

          const SizedBox(height: 40),
          _TieuDeMuc(t.homeQuickAccess),
          const SizedBox(height: 14),

          // Chiều cao co theo cỡ chữ hệ thống: đóng cứng 104 thì ở mức phóng
          // to 1,6 lần cột chữ bên trong tràn 26 pixel.
          SizedBox(
            height: AppMetrics.caoTheoCoChu(context, coBan: 104, phanChu: 48),
            child: Row(
              children: [
                for (var i = 0; i < khu.length && i < 4; i++) ...[
                  if (i > 0) const SizedBox(width: 11),
                  Expanded(child: _QuickTile(khuVuc: khu[i], viTri: vt)),
                ],
              ],
            ),
          ),

          const SizedBox(height: 34),
          _TieuDeMuc(t.homeNearby),
          const SizedBox(height: 14),

          GlassCard(
            radius: 26,
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Column(
              children: [
                for (var i = 4; i < khu.length && i < 10; i++) ...[
                  if (i > 4)
                    Padding(
                      padding: const EdgeInsets.only(left: 63),
                      child: Divider(
                        height: 1,
                        thickness: 1,
                        color: muc.withValues(alpha: 0.08),
                      ),
                    ),
                  _NearbyRow(khuVuc: khu[i], viTri: vt),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Khối vị trí ở đầu màn hình: toạ độ thật khi đã định vị, nói rõ "chưa xác
/// định" khi chưa có.
///
/// Gộp thành MỘT mục trợ năng — các dòng rời khiến trình đọc màn hình bắt người
/// dùng vuốt nhiều lần cho một mẩu thông tin duy nhất.
class _KhoiViTri extends StatelessWidget {
  const _KhoiViTri();

  @override
  Widget build(BuildContext context) {
    final theoDoi = TheoDoiViTriScope.of(context);
    return AnimatedBuilder(
      animation: theoDoi,
      builder: (context, _) => _noiDung(context, theoDoi),
    );
  }

  Widget _noiDung(BuildContext context, TheoDoiViTri theoDoi) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);
    final nhan = AppColors.accentOf(context);

    // Dấu thập phân khác nhau giữa hai ngôn ngữ; `toString()` luôn cho dấu chấm.
    final so = intl.NumberFormat('#0.0', t.localeName);

    // Đọc vô điều kiện chứ không chỉ khi có lỗi: đăng ký phụ thuộc
    // InheritedWidget theo nhánh thì widget không dựng lại khi địa chỉ đổi.
    final mayChu = AppSettingsScope.of(context).diaChiMayChu;

    final vt = theoDoi.viTri;
    final diemGan = theoDoi.diemGanNhat;
    final khu = (diemGan != null && diemGan.ten.isNotEmpty) ? diemGan : null;
    // Màn Chi tiết nhận KHU VỰC chứ không nhận điểm tham chiếu: người dùng
    // muốn xem "Khu vực đọc", không phải "RP27".
    final khuHienTai = khu == null
        ? null
        : theoDoi.khuVuc.where((k) => k.nhom == khu.nhom).firstOrNull;
    final dangChay = theoDoi.trangThai != TrangThai.dung;
    final coLoi = theoDoi.trangThai == TrangThai.loi;

    final phu = <String>[
      if (coLoi)
        _cauLoi(t, theoDoi, mayChu)
      else if (vt == null)
        dangChay ? t.liveScanning : t.liveIdle
      else ...[
        t.liveMatched(vt.soApKhop),
        // Hiện luôn chứ không chỉ khi cửa sổ chưa đầy: kích thước cửa sổ do
        // máy chủ quyết định, viết cứng ở đây là nhân đôi một hằng số.
        t.liveMerged(vt.soLanQuetDaGop),
        t.liveModel(vt.moHinh, so.format(vt.doTreMs)),
      ],
    ];

    return MergeSemantics(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  t.homeYouAreAt,
                  style: TextStyle(
                      fontSize: 15, color: muc.withValues(alpha: 0.55)),
                ),
              ),
              TapFeedback(
                onTap: dangChay ? theoDoi.dungLai : theoDoi.batDau,
                semanticLabel: dangChay ? t.liveStop : t.liveStart,
                semanticHint: t.a11yToggleTracking,
                child: Container(
                  constraints: const BoxConstraints(
                      minHeight: AppMetrics.vungChamToiThieu),
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: nhan.withValues(alpha: dangChay ? 0.20 : 0.12),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    dangChay ? t.liveStop : t.liveStart,
                    style: TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                        color: nhan),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),

          // Biết khu vực thì tên bấm được, mở màn Chi tiết với đúng ảnh và mô
          // tả. Không biết thì để chữ trơ và lùi về toạ độ mét — nút dẫn tới
          // nội dung demo còn khó hiểu hơn là không có nút.
          if (khu != null && khuHienTai != null)
            TapFeedback(
              semanticLabel: khu.ten,
              semanticHint: t.a11yOpenArea,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => AreaDetailScreen(khuVuc: khuHienTai),
                ),
              ),
              child: Text(khu.ten,
                  style: Theme.of(context).textTheme.displayLarge),
            )
          else
            Text(
              // Chưa có toạ độ thì nói thẳng là chưa biết. Chỗ này từng hiện
              // sẵn một tên phòng, nên ứng dụng trông như đã định vị xong ngay
              // khi vừa mở — đúng lỗi "trả lời tự tin khi không có dữ liệu" mà
              // cả đồ án lấy làm điểm cải tiến.
              vt == null
                  ? t.liveUnknown
                  : t.liveCoords(so.format(vt.xGop), so.format(vt.yGop)),
              style: Theme.of(context).textTheme.displayLarge,
            ),
          const SizedBox(height: 8),
          Text(
            theoNgonNgu(
                context, DemoData.currentFloor, DemoData.currentFloorEn),
            style: TextStyle(fontSize: 15, color: muc.withValues(alpha: 0.7)),
          ),
          for (final dong in phu) ...[
            const SizedBox(height: 4),
            Text(
              dong,
              style: TextStyle(
                fontSize: 13,
                color: coLoi
                    ? Theme.of(context).colorScheme.error
                    : muc.withValues(alpha: 0.5),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _cauLoi(L t, TheoDoiViTri theoDoi, String mayChu) =>
      switch (theoDoi.loiQuet) {
        LoiQuet.thieuQuyen => t.errWifiPermission,
        LoiQuet.quyenBiChan => t.errWifiBlocked,
        LoiQuet.tatDinhVi => t.errLocationOff,
        LoiQuet.khongHoTro => t.errWifiUnsupported,
        LoiQuet.thatBai => t.errScanFailed,
        null => switch (theoDoi.loiApi) {
            LoiApi.mayChuLoi => t.errServer(theoDoi.maHttp ?? 0),
            LoiApi.saiDinhDang => t.errBadFormat,
            LoiApi.quaHan => t.errTimeout,
            LoiApi.diaChiSai => t.errBadAddress(mayChu),
            LoiApi.khongDuAp => t.errNotEnoughAp(
                theoDoi.soApKhop ?? 0, theoDoi.soApToiThieu ?? 0),
            _ => t.errNoConnection(mayChu),
          },
      };
}

/// Tiêu đề một mục. `header: true` để trình đọc màn hình nhảy được giữa các
/// mục thay vì phải vuốt qua từng dòng.
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
  final KhuVuc khuVuc;
  final ViTri? viTri;

  const _QuickTile({required this.khuVuc, required this.viTri});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);

    return GlassCard(
      radius: 24,
      semanticLabel: khuVuc.nhom,
      semanticHint: t.a11yOpenArea,
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => AreaDetailScreen(khuVuc: khuVuc)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(khuVuc.icon, size: 24, color: AppColors.accentOf(context)),
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text(
              khuVuc.nhom,
              textAlign: TextAlign.center,
              maxLines: 2,
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
            _khoangCach(t, khuVuc, viTri),
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

/// Khoảng cách tới khu vực, hoặc số điểm đo khi chưa định vị.
///
/// Bản trước ghi cứng "12 m", "28 m" — những con số không đổi dù người dùng đi
/// khắp toà nhà. Thà nói số điểm đo còn hơn nói một khoảng cách bịa.
String _khoangCach(L t, KhuVuc k, ViTri? vt) {
  if (vt == null) return t.detailPointCount(k.diem.length);
  return t.distanceMeters(k.khoangCach(vt.xGop, vt.yGop).round());
}

class _NearbyRow extends StatelessWidget {
  final KhuVuc khuVuc;
  final ViTri? viTri;

  const _NearbyRow({required this.khuVuc, required this.viTri});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);
    final nhan = AppColors.accentOf(context);

    // TapFeedback chứ không GestureDetector trần: dòng này nằm trong một
    // GlassCard chung nên không có nền riêng để đổi màu khi bấm.
    return TapFeedback(
      semanticLabel: khuVuc.nhom,
      semanticHint: t.a11yOpenArea,
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => AreaDetailScreen(khuVuc: khuVuc)),
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
              child: Icon(khuVuc.icon, size: 20, color: nhan),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    khuVuc.nhom,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 13.5, color: muc),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    khuVuc.moTa,
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
              _khoangCach(t, khuVuc, viTri),
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
