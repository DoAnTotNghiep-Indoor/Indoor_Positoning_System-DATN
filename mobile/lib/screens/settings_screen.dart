import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../services/quyen_truy_cap.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_settings.dart';
import '../theme/app_theme.dart';
import '../widgets/chung.dart';
import '../widgets/tap_feedback.dart';

const _phienBan = 'v0.2';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final tuyChon = AppSettingsScope.of(context);

    return ListView(
      padding: EdgeInsets.fromLTRB(20, MediaQuery.paddingOf(context).top + 16,
          20, chuaThanhTab(context)),
      children: [
        Text(t.settingsTitle, style: Theme.of(context).textTheme.headlineLarge),
        TieuDeMuc(t.settingsGroupPositioning),
        BeMat(
          child: Column(
            children: [
              const _DongQuyen(),
              const Divider(indent: 56),
              _Dong(
                icon: Icons.sync_rounded,
                tieuDe: t.settingsScanCycle,
                phu: t.settingsScanCycleSub,
              ),
              const Divider(indent: 56),
              _Dong(
                icon: Icons.memory_rounded,
                tieuDe: t.settingsLocalModel,
                phu: t.settingsLocalModelSub,
                cuoi: Switch(
                  value: tuyChon.moHinhCucBo,
                  onChanged: tuyChon.datMoHinhCucBo,
                ),
                onTap: () => tuyChon.datMoHinhCucBo(!tuyChon.moHinhCucBo),
              ),
              const Divider(indent: 56),
              _Dong(
                icon: Icons.dns_outlined,
                tieuDe: t.settingsServer,
                phu: t.settingsServerSub,
                duoi: const _OMayChu(),
              ),
            ],
          ),
        ),
        TieuDeMuc(t.settingsGroupAppearance),
        BeMat(
          child: Column(
            children: [
              _Dong(
                icon: Icons.contrast_rounded,
                tieuDe: t.settingsTheme,
                duoi: SegmentedButton<ThemeMode>(
                  showSelectedIcon: false,
                  segments: [
                    ButtonSegment(
                        value: ThemeMode.system,
                        label: Text(t.settingsThemeSystem)),
                    ButtonSegment(
                        value: ThemeMode.light,
                        label: Text(t.settingsThemeLight)),
                    ButtonSegment(
                        value: ThemeMode.dark,
                        label: Text(t.settingsThemeDark)),
                  ],
                  selected: {tuyChon.cheDo},
                  onSelectionChanged: (s) => tuyChon.datCheDo(s.first),
                ),
              ),
              const Divider(indent: 56),
              _Dong(
                icon: Icons.translate_rounded,
                tieuDe: t.settingsLanguage,
                duoi: SegmentedButton<String>(
                  showSelectedIcon: false,
                  segments: [
                    ButtonSegment(
                        value: 'vi', label: Text(t.settingsLanguageVi)),
                    ButtonSegment(
                        value: 'en', label: Text(t.settingsLanguageEn)),
                  ],
                  selected: {tuyChon.ngonNgu.languageCode},
                  onSelectionChanged: (s) =>
                      tuyChon.datNgonNgu(Locale(s.first)),
                ),
              ),
            ],
          ),
        ),
        TieuDeMuc(t.settingsGroupGeneral),
        BeMat(
          child: _Dong(
            icon: Icons.info_outline_rounded,
            tieuDe: t.settingsAppInfo,
            cuoi: Text('${t.appTitle} $_phienBan',
                style: Theme.of(context).textTheme.bodyMedium),
          ),
        ),
      ],
    );
  }
}

class _Dong extends StatelessWidget {
  final IconData icon;
  final String tieuDe;
  final String? phu;
  final Widget? cuoi;
  final Widget? duoi;
  final VoidCallback? onTap;

  const _Dong({
    required this.icon,
    required this.tieuDe,
    this.phu,
    this.cuoi,
    this.duoi,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final noiDung = Padding(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: Mau.of(context).nhan),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(tieuDe,
                    style:
                        tt.titleMedium?.copyWith(fontWeight: FontWeight.w500)),
                if (phu != null)
                  Text(phu!, style: tt.bodyMedium?.copyWith(fontSize: 13)),
                if (duoi != null) ...[
                  const SizedBox(height: 12),
                  SizedBox(width: double.infinity, child: duoi),
                ],
              ],
            ),
          ),
          if (cuoi != null) ...[const SizedBox(width: 12), cuoi!],
        ],
      ),
    );
    return TapFeedback(onTap: onTap, child: noiDung);
  }
}

/// Ghi khi rời ô hoặc bấm xong để mỗi ký tự gõ dở không đổi máy chủ.
class _OMayChu extends StatefulWidget {
  const _OMayChu();

  @override
  State<_OMayChu> createState() => _OMayChuState();
}

class _OMayChuState extends State<_OMayChu> {
  late final _tuyChon = AppSettingsScope.of(context);
  late final _o = TextEditingController(text: _tuyChon.diaChiMayChu);

  @override
  void dispose() {
    _o.dispose();
    super.dispose();
  }

  void _luu() {
    _tuyChon.datDiaChiMayChu(_o.text);
    _o.text = _tuyChon.diaChiMayChu;
  }

  @override
  Widget build(BuildContext context) {
    final m = Mau.of(context);
    return TextField(
      controller: _o,
      keyboardType: TextInputType.url,
      autocorrect: false,
      style: TextStyle(fontSize: 15, color: m.chu),
      decoration: InputDecoration(
        isDense: true,
        filled: true,
        fillColor: m.nhanNhat,
        hintText: L.of(context).settingsServerHint,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
      onTapOutside: (_) {
        _luu();
        FocusScope.of(context).unfocus();
      },
      onSubmitted: (_) => _luu(),
    );
  }
}

class _DongQuyen extends StatefulWidget {
  const _DongQuyen();

  @override
  State<_DongQuyen> createState() => _DongQuyenState();
}

class _DongQuyenState extends State<_DongQuyen> {
  static const _quyen = QuyenTruyCap();
  TrangThaiQuyen? _tt;
  late final AppLifecycleListener _vongDoi;

  @override
  void initState() {
    super.initState();
    // Đọc lại khi quay về từ Cài đặt hệ thống, nơi người dùng vừa cấp quyền.
    _vongDoi = AppLifecycleListener(onResume: _doc);
    _doc();
  }

  @override
  void dispose() {
    _vongDoi.dispose();
    super.dispose();
  }

  Future<void> _doc() async {
    final tt = await _quyen.kiemTra().catchError((_) => TrangThaiQuyen.chuaCap);
    if (mounted) setState(() => _tt = tt);
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final daCap = _tt == TrangThaiQuyen.daCap;
    return _Dong(
      icon: daCap ? Icons.location_on_outlined : Icons.location_off_outlined,
      tieuDe: t.settingsPermission,
      phu: switch (_tt) {
        TrangThaiQuyen.daCap => t.settingsPermissionGranted,
        TrangThaiQuyen.biChan => t.settingsPermissionBlocked,
        _ => t.settingsPermissionMissing,
      },
      cuoi: Icon(daCap ? Icons.check_circle_rounded : Icons.error_rounded,
          color: daCap ? m.dich : m.loi),
      onTap: daCap || _tt == null
          ? null
          : () async {
              await TheoDoiViTriScope.doc(context).xuLyQuyen();
              _doc();
            },
    );
  }
}
