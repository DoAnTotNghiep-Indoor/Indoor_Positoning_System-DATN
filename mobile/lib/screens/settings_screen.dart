import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';

import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../theme/app_settings.dart';

/// Màn Cài đặt.
///
/// Dùng `GlassGroupedSection` thay cho `GlassCard` bọc `Column`: nó tự chèn
/// đường kẻ giữa các dòng và bo góc đúng cho dòng đầu, dòng cuối — trước đây
/// phần đó phải tự canh bằng `Padding(left: 64)` và `Divider` thủ công.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

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
                trailing: const SizedBox(width: 120, child: _GiaTri(DemoData.serverHost)),
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
                // GlassSegmentedControl làm việc theo CHỈ SỐ chứ không theo
                // giá trị, nên phải tự ánh xạ qua lại với ThemeMode.
                //
                // Hàm dựng mặc định chứ không phải .scrollable: bản scrollable
                // dành cho 6 mục trở lên, nó co từng mục theo độ dài chữ rồi
                // dồn về trái, để thừa một mảng rãnh xám bên phải. Bản mặc
                // định chia đều các mục kín chiều ngang.
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
                subtitle: Text(t.settingsAutoUpdateSub),
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
              GlassListTile(
                leading: const Icon(Icons.place_outlined),
                title: Text(t.settingsPermission),
                subtitle: Text(t.settingsPermissionSub),
                trailing: _GiaTri(t.settingsPermissionGranted),
              ),
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

/// Dòng cài đặt có bộ chọn nằm bên dưới thay vì bên phải.
///
/// Segmented control cần cả chiều ngang; nhét vào ô `trailing` của
/// `GlassListTile` sẽ bị bóp lại và chữ bị cắt.
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
