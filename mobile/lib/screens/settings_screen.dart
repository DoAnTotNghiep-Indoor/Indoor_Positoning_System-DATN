import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';

import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../services/quyen_truy_cap.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_settings.dart';

/// Màn Cài đặt. `GlassGroupedSection` tự chèn đường kẻ giữa các dòng và bo góc
/// đúng cho dòng đầu, dòng cuối.
class SettingsScreen extends StatefulWidget {
  /// Cho tiêm được để kiểm thử không phải đụng kênh nền tảng.
  final QuyenTruyCap quyen;

  const SettingsScreen({super.key, this.quyen = const QuyenTruyCap()});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

/// Thứ tự này phải khớp thứ tự các đoạn trong segmented control bên dưới.
const _cheDoTheoThuTu = <ThemeMode>[
  ThemeMode.system,
  ThemeMode.light,
  ThemeMode.dark,
];

const _maNgonNgu = <String>['vi', 'en'];

class _SettingsScreenState extends State<SettingsScreen> {
  bool _tuDongCapNhat = true;
  bool _giuManHinhSang = false;

  @override
  Widget build(BuildContext context) {
    final chuaCho = AppMetrics.chuaChoThanhTab(context);
    final t = L.of(context);
    final tuyChon = AppSettingsScope.of(context);
    final muc = AppColors.inkOf(context);

    return SafeArea(
      bottom: false,
      child: ListView(
        padding: EdgeInsets.fromLTRB(16, 12, 16, chuaCho),
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 8),
            child: Semantics(
              header: true,
              child: Text(t.settingsTitle,
                  style: Theme.of(context).textTheme.headlineLarge),
            ),
          ),
          const SizedBox(height: 30),
          GlassGroupedSection(
            header: _NhanNhom(t.settingsGroupGeneral),
            children: [
              GlassListTile(
                leading: const Icon(Icons.info_outline),
                title: Text(t.settingsAppInfo),
                trailing: const _GiaTri(DemoData.appVersion),
              ),
              GlassListTile(
                leading: const Icon(Icons.dns_outlined),
                title: Text(t.settingsServer),
                subtitle: Text(t.settingsServerSub),
                trailing: const SizedBox(width: 150, child: _OMayChu()),
              ),
            ],
          ),
          const SizedBox(height: 28),
          GlassGroupedSection(
            header: _NhanNhom(t.settingsGroupAppearance),
            children: [
              // Ba lựa chọn ngắn nên dùng segmented control thay cho dòng bấm
              // mở trang khác — đổi được tại chỗ và thấy kết quả tức thì.
              _DongChon(
                icon: Icons.brightness_6_outlined,
                title: t.settingsTheme,
                // Điều khiển này làm việc theo CHỈ SỐ chứ không theo giá trị.
                // Không dùng .scrollable — bản đó dành cho 6 mục trở lên, nó
                // dồn các mục về trái và để thừa rãnh xám bên phải.
                child: GlassSegmentedControl(
                  selectedIndex: _cheDoTheoThuTu.indexOf(tuyChon.cheDo),
                  segments: [
                    GlassSegment(label: t.settingsThemeSystem),
                    GlassSegment(label: t.settingsThemeLight),
                    GlassSegment(label: t.settingsThemeDark),
                  ],
                  onSegmentSelected: (i) =>
                      tuyChon.datCheDo(_cheDoTheoThuTu[i]),
                ),
              ),
              _DongChon(
                icon: Icons.language_outlined,
                title: t.settingsLanguage,
                child: GlassSegmentedControl(
                  selectedIndex:
                      _maNgonNgu.indexOf(tuyChon.ngonNgu.languageCode),
                  segments: [
                    GlassSegment(label: t.settingsLanguageVi),
                    GlassSegment(label: t.settingsLanguageEn),
                  ],
                  onSegmentSelected: (i) =>
                      tuyChon.datNgonNgu(Locale(_maNgonNgu[i])),
                ),
              ),
            ],
          ),
          const SizedBox(height: 28),
          GlassGroupedSection(
            header: _NhanNhom(t.settingsGroupPositioning),
            children: [
              GlassListTile(
                leading: const Icon(Icons.sync),
                title: Text(t.settingsAutoUpdate),
                // Lấy thẳng từ hằng số chu kỳ, không viết cứng: chuỗi cũ ghi 2 giây
                  // trong khi vòng quét chạy 5 giây, mà 5 giây là mức Android
                  // cho phép — nhanh hơn thì hệ điều hành trả lại kết quả cũ.
                  subtitle:
                      Text(t.settingsAutoUpdateSub(TheoDoiViTri.chuKy.inSeconds)),
                trailing: GlassSwitch(
                  value: _tuDongCapNhat,
                  onChanged: (v) => setState(() => _tuDongCapNhat = v),
                ),
              ),
              GlassListTile(
                leading: const Icon(Icons.brightness_high_outlined),
                title: Text(t.settingsKeepAwake),
                subtitle: Text(t.settingsKeepAwakeSub),
                trailing: GlassSwitch(
                  value: _giuManHinhSang,
                  onChanged: (v) => setState(() => _giuManHinhSang = v),
                ),
              ),
            ],
          ),
          const SizedBox(height: 28),
          GlassGroupedSection(
            header: _NhanNhom(t.settingsGroupPermissions),
            children: [
              _DongQuyen(quyen: widget.quyen),
            ],
          ),
          const SizedBox(height: 20),
          GlassCard(
            padding: const EdgeInsets.all(18),
            shape: const LiquidRoundedSuperellipse(borderRadius: 24),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline,
                    size: 18, color: muc.withValues(alpha: 0.45)),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    t.settingsFootnote,
                    style: TextStyle(
                      fontSize: 12.5,
                      height: 1.45,
                      color: muc.withValues(alpha: 0.55),
                    ),
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

/// Dòng cài đặt có bộ chọn nằm bên dưới: segmented control cần cả chiều ngang,
/// nhét vào ô `trailing` sẽ bị bóp lại và cắt chữ.
class _DongChon extends StatelessWidget {
  final IconData icon;
  final String title;
  final Widget child;

  const _DongChon({
    required this.icon,
    required this.title,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    final muc = AppColors.inkOf(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 22, color: muc.withValues(alpha: 0.8)),
              const SizedBox(width: 16),
              Text(title, style: Theme.of(context).textTheme.bodyLarge),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(width: double.infinity, child: child),
        ],
      ),
    );
  }
}

/// Nhãn nhóm dạng chữ in hoa nhỏ, đặt phía trên mỗi khối cài đặt.
class _NhanNhom extends StatelessWidget {
  final String text;
  const _NhanNhom(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 12, bottom: 8),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 11.5,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.1,
          color: AppColors.inkOf(context).withValues(alpha: 0.45),
        ),
      ),
    );
  }
}

/// Giá trị chỉ đọc ở cuối dòng cài đặt.
/// Ô nhập địa chỉ máy chủ. Chỉ ghi khi rời ô hoặc bấm xong, để mỗi ký tự gõ dở
/// không dựng lại client HTTP.
class _OMayChu extends StatefulWidget {
  const _OMayChu();

  @override
  State<_OMayChu> createState() => _OMayChuState();
}

class _OMayChuState extends State<_OMayChu> {
  final _o = TextEditingController();
  AppSettings? _tuyChon;

  // Đọc InheritedWidget phải ở didChangeDependencies: lúc initState chạy thì
  // widget chưa gắn vào cây nên chưa tra ngược lên được.
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_tuyChon != null) return;
    _tuyChon = AppSettingsScope.of(context);
    _o.text = _tuyChon!.diaChiMayChu;
  }

  @override
  void dispose() {
    _o.dispose();
    super.dispose();
  }

  void _luu() {
    final t = _tuyChon;
    if (t == null) return;
    t.datDiaChiMayChu(_o.text);

    // Chuỗi rỗng bị từ chối; không đồng bộ lại thì ô hiện trống trong khi ứng
    // dụng vẫn gọi địa chỉ cũ.
    if (_o.text.trim() != t.diaChiMayChu) _o.text = t.diaChiMayChu;
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    return TextField(
      controller: _o,
      textAlign: TextAlign.end,
      keyboardType: TextInputType.url,
      autocorrect: false,
      style: TextStyle(
        fontSize: 13,
        color: AppColors.inkOf(context).withValues(alpha: 0.7),
      ),
      decoration: InputDecoration(
        isDense: true,
        border: InputBorder.none,
        hintText: t.settingsServerHint,
        hintStyle: TextStyle(
          fontSize: 13,
          color: AppColors.inkOf(context).withValues(alpha: 0.35),
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

class _GiaTri extends StatelessWidget {
  final String text;
  const _GiaTri(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: TextStyle(
        fontSize: 14,
        color: AppColors.inkOf(context).withValues(alpha: 0.5),
      ),
    );
  }
}


/// Dòng quyền truy cập, đọc trạng thái THẬT thay vì viết cứng "Đã cấp".
///
/// Bản trước luôn hiện "Đã cấp", nên app có thể đồng thời báo "Thiếu quyền truy
/// cập WiFi" ở Trang chủ và "Đã cấp" ở đây — mà đây đúng là nơi người dùng tìm
/// đến sau khi thấy lỗi kia.
class _DongQuyen extends StatefulWidget {
  final QuyenTruyCap quyen;

  const _DongQuyen({required this.quyen});

  @override
  State<_DongQuyen> createState() => _DongQuyenState();
}

class _DongQuyenState extends State<_DongQuyen> with WidgetsBindingObserver {
  TrangThaiQuyen? _trangThai;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _doc();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  /// Đọc lại khi quay về từ màn Cài đặt hệ thống: người dùng vừa cấp quyền ở đó
  /// mà dòng này vẫn hiện trạng thái cũ thì họ tưởng bấm không ăn.
  @override
  void didChangeAppLifecycleState(AppLifecycleState trangThai) {
    if (trangThai == AppLifecycleState.resumed) _doc();
  }

  Future<void> _doc() async {
    try {
      final tt = await widget.quyen.kiemTra();
      if (mounted) setState(() => _trangThai = tt);
    } catch (_) {
      // Kênh nền tảng không có (chạy trên web hoặc trong test) — để trống còn
      // hơn hiện một trạng thái bịa ra.
      if (mounted) setState(() => _trangThai = null);
    }
  }

  Future<void> _cham() async {
    if (_trangThai == TrangThaiQuyen.biChan) {
      await widget.quyen.moCaiDat();
      return;
    }
    try {
      final tt = await widget.quyen.xin();
      if (mounted) setState(() => _trangThai = tt);
    } catch (_) {
      /* không xin được thì giữ nguyên trạng thái đang hiện */
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final (chu, goiY) = switch (_trangThai) {
      TrangThaiQuyen.daCap => (t.settingsPermissionGranted, null),
      TrangThaiQuyen.chuaCap => (
          t.settingsPermissionMissing,
          t.settingsPermissionAsk
        ),
      TrangThaiQuyen.biChan => (
          t.settingsPermissionBlocked,
          t.settingsPermissionOpen
        ),
      null => (t.settingsPermissionChecking, null),
    };

    return GlassListTile(
      leading: Icon(
        _trangThai == TrangThaiQuyen.daCap
            ? Icons.place_outlined
            : Icons.error_outline,
        color: _trangThai == TrangThaiQuyen.daCap
            ? null
            : Theme.of(context).colorScheme.error,
      ),
      title: Text(t.settingsPermission),
      subtitle: Text(goiY ?? t.settingsPermissionSub),
      trailing: _GiaTri(chu),
      onTap: goiY == null ? null : _cham,
    );
  }
}
