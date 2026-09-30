import 'package:flutter/material.dart';
import 'package:intl/intl.dart' as intl;

import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../services/api_dinh_vi.dart';
import '../services/quet_wifi.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_settings.dart';
import '../theme/app_theme.dart';
import '../widgets/chung.dart';
import '../widgets/tap_feedback.dart';
import '../widgets/the_khu_vuc.dart';

const _truyCapNhanh = ['Khu vực đọc', 'Khu vực tự học', 'WC', 'Căn tin'];

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final theoDoi = TheoDoiViTriScope.of(context);
    final vt = theoDoi.viTri;
    final ds = theoDoi.khuVuc;
    final hienTai = theoDoi.khuHienTai;

    final nhanh = [
      for (final ten in _truyCapNhanh) ...ds.where((k) => k.nhom == ten),
    ];
    final ganBan =
        vt == null ? ds : ds.where((k) => k != hienTai).take(6).toList();

    final tren = MediaQuery.paddingOf(context).top;
    return Stack(
      children: [
        ListView(
          padding:
              EdgeInsets.fromLTRB(20, tren + 72, 20, chuaThanhTab(context)),
          children: [
            _KhoiViTri(theoDoi: theoDoi),
            TieuDeMuc(t.homeQuickAccess),
            SizedBox(
              height: MediaQuery.textScalerOf(context).scale(112),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (var i = 0; i < nhanh.length; i++) ...[
                    if (i > 0) const SizedBox(width: 10),
                    Expanded(child: _OTruyCap(khuVuc: nhanh[i], viTri: vt)),
                  ],
                ],
              ),
            ),
            TieuDeMuc(vt == null ? t.homeAllAreas : t.homeNearby),
            BeMat(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Column(
                children: [
                  for (var i = 0; i < ganBan.length; i++) ...[
                    if (i > 0) const Divider(indent: 68, endIndent: 16),
                    DongKhuVuc(khuVuc: ganBan[i], viTri: vt),
                  ],
                ],
              ),
            ),
          ],
        ),
        Positioned(
          top: tren + 10,
          left: 20,
          right: 20,
          child: Align(
            alignment: Alignment.centerLeft,
            child: PillViTri(theoDoi: theoDoi),
          ),
        ),
      ],
    );
  }
}

class _KhoiViTri extends StatelessWidget {
  final TheoDoiViTri theoDoi;
  const _KhoiViTri({required this.theoDoi});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final tt = Theme.of(context).textTheme;
    final so = intl.NumberFormat('#0.0', t.localeName);
    final vt = theoDoi.viTri;
    final loi = theoDoi.loi;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text.rich(TextSpan(children: [
          TextSpan(
            text: '${t.mapFloorOne}  ',
            style: tt.bodyMedium?.copyWith(
                fontWeight: FontWeight.w700, color: Mau.of(context).chu),
          ),
          TextSpan(text: t.buildingFull, style: tt.bodyMedium),
        ])),
        const SizedBox(height: 6),
        if (loi != null)
          _TrangThai(
            chu: _cauLoi(t, loi, AppSettingsScope.of(context).diaChiMayChu),
            phu: vt != null && theoDoi.giayTuCapNhat != null
                ? t.liveStale(theoDoi.giayTuCapNhat!)
                : null,
            onTap: loi is NgoaiLeQuet &&
                    (loi.loai == LoiQuet.thieuQuyen ||
                        loi.loai == LoiQuet.quyenBiChan)
                ? theoDoi.xuLyQuyen
                : null,
          )
        else if (vt != null)
          Text(t.liveInfo(vt.soApKhop, vt.moHinh, so.format(vt.doTreMs)),
              style: tt.labelMedium),
      ],
    );
  }

  String _cauLoi(L t, Exception loi, String mayChu) => switch (loi) {
        NgoaiLeQuet(loai: LoiQuet.thieuQuyen) => t.errWifiPermission,
        NgoaiLeQuet(loai: LoiQuet.quyenBiChan) => t.errWifiBlocked,
        NgoaiLeQuet(loai: LoiQuet.tatDinhVi) => t.errLocationOff,
        NgoaiLeQuet(loai: LoiQuet.khongHoTro) => t.errWifiUnsupported,
        NgoaiLeApi(loai: LoiApi.khongDuAp, :final soAp, :final toiThieu) =>
          t.errNotEnoughAp(soAp ?? 0, toiThieu ?? 0),
        NgoaiLeApi(loai: LoiApi.diaChiSai) => t.errBadAddress(mayChu),
        NgoaiLeApi(loai: LoiApi.quaHan) => t.errTimeout,
        NgoaiLeApi(loai: LoiApi.saiDinhDang) => t.errBadFormat,
        NgoaiLeApi(loai: LoiApi.mayChuLoi, :final maHttp?) =>
          t.errServer(maHttp),
        NgoaiLeApi() => t.errNoConnection(mayChu),
        _ => t.errScanFailed,
      };
}

class _TrangThai extends StatelessWidget {
  final String chu;
  final String? phu;
  final VoidCallback? onTap;

  const _TrangThai({required this.chu, this.phu, this.onTap});

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final m = Mau.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: TapFeedback(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: m.loi.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(chu,
                        style: tt.bodyMedium
                            ?.copyWith(fontSize: 13.5, color: m.chu)),
                    if (phu != null) Text(phu!, style: tt.labelMedium),
                  ],
                ),
              ),
              if (onTap != null)
                Icon(Icons.chevron_right_rounded, size: 20, color: m.loi),
            ],
          ),
        ),
      ),
    );
  }
}

class _OTruyCap extends StatelessWidget {
  final KhuVuc khuVuc;
  final ViTri? viTri;

  const _OTruyCap({required this.khuVuc, required this.viTri});

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final kc = khoangCachChu(L.of(context), khuVuc, viTri);
    return TapFeedback(
      onTap: () => moKhuVuc(context, khuVuc),
      child: BeMat(
        padding: const EdgeInsets.fromLTRB(6, 14, 6, 12),
        child: Column(
          children: [
            OBieuTuong(khuVuc, size: 40),
            const SizedBox(height: 8),
            Text(
              khuVuc.nhom,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: tt.labelLarge?.copyWith(fontSize: 12, height: 1.25),
            ),
            if (kc != null) ...[
              const SizedBox(height: 2),
              Text(kc, style: tt.labelMedium),
            ],
          ],
        ),
      ),
    );
  }
}
