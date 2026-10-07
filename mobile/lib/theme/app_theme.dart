import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';

/// Token màu của app. Mọi màu chữ là màu đặc (không pha alpha) để giữ tương
/// phản ≥ 4.5:1 trên nền thẻ — bản cũ pha alpha 0.4–0.5 nên chữ phụ chìm hẳn.
@immutable
class Mau extends ThemeExtension<Mau> {
  final Color nenTren, nenDuoi;
  final Color the, vien;
  final Color chu, chuPhu, chuMo;
  final Color nhan, nhanNhat, trenNhan;
  final Color loi, dich;

  const Mau({
    required this.nenTren,
    required this.nenDuoi,
    required this.the,
    required this.vien,
    required this.chu,
    required this.chuPhu,
    required this.chuMo,
    required this.nhan,
    required this.nhanNhat,
    required this.trenNhan,
    required this.loi,
    required this.dich,
  });

  static const sang = Mau(
    nenTren: Color(0xFFEEF4FF),
    nenDuoi: Color(0xFFD9E5FA),
    the: Color(0xFFFFFFFF),
    vien: Color(0x140D1A30),
    chu: Color(0xFF0D1A30),
    chuPhu: Color(0xFF45516A),
    chuMo: Color(0xFF5F6B82),
    nhan: Color(0xFF2C5BD8),
    nhanNhat: Color(0xFFE6EDFD),
    trenNhan: Color(0xFFFFFFFF),
    loi: Color(0xFFB3261E),
    dich: Color(0xFF17A673),
  );

  static const toi = Mau(
    nenTren: Color(0xFF0B1220),
    nenDuoi: Color(0xFF10203A),
    the: Color(0xFF18233A),
    vien: Color(0x1FFFFFFF),
    chu: Color(0xFFEDF1F8),
    chuPhu: Color(0xFFC0C9DA),
    chuMo: Color(0xFF9AA6BD),
    nhan: Color(0xFF8AAEFF),
    nhanNhat: Color(0xFF223457),
    trenNhan: Color(0xFF071430),
    loi: Color(0xFFFF8A80),
    dich: Color(0xFF3FD19B),
  );

  static Mau of(BuildContext context) => Theme.of(context).extension<Mau>()!;

  @override
  Mau copyWith() => this;

  @override
  Mau lerp(Mau? other, double t) => t < 0.5 || other == null ? this : other;
}

/// Nhóm khu vực, quyết định màu biểu tượng và chip lọc trên màn Tìm kiếm.
enum LoaiKhu { hocTap, tienIch, loiDi }

LoaiKhu loaiCua(String nhom) => switch (nhom) {
      'Khu vực tự học' ||
      'Khu vực đọc' ||
      'TV3,4' ||
      'Phòng tạp chí' ||
      'Phòng học nhóm' ||
      'Phòng đọc sau đại học' =>
        LoaiKhu.hocTap,
      'Căn tin' ||
      'Hội trường thư viện' ||
      'Bàn thủ thư' ||
      'WC phía TV3,4' ||
      'WC phía căn tin' ||
      'Phòng nghiệp vụ 1' ||
      'Phòng nghiệp vụ 2' ||
      'Sảnh chờ' ||
      'Ban công' =>
        LoaiKhu.tienIch,
      _ => LoaiKhu.loiDi,
    };

/// (nền, chữ) của ô biểu tượng theo nhóm — bảng màu zone của thiết kế v4.
(Color, Color) mauLoai(BuildContext context, LoaiKhu loai) {
  final toi = Theme.of(context).brightness == Brightness.dark;
  return switch ((loai, toi)) {
    (LoaiKhu.hocTap, false) => (
        const Color(0xFFE6F1FB),
        const Color(0xFF0C447C)
      ),
    (LoaiKhu.tienIch, false) => (
        const Color(0xFFE1F5EE),
        const Color(0xFF085041)
      ),
    (LoaiKhu.loiDi, false) => (
        const Color(0xFFFAEEDA),
        const Color(0xFF633806)
      ),
    (LoaiKhu.hocTap, true) => (
        const Color(0xFF1C3350),
        const Color(0xFF9CC8F5)
      ),
    (LoaiKhu.tienIch, true) => (
        const Color(0xFF16372F),
        const Color(0xFF8FDCC0)
      ),
    (LoaiKhu.loiDi, true) => (const Color(0xFF3A2C16), const Color(0xFFF0C98A)),
  };
}

class AppTheme {
  AppTheme._();

  static final light = _dung(Brightness.light, Mau.sang);
  static final dark = _dung(Brightness.dark, Mau.toi);

  static ThemeData _dung(Brightness doSang, Mau m) => ThemeData(
        useMaterial3: true,
        brightness: doSang,
        fontFamily: 'Inter',
        extensions: [m],
        colorScheme: ColorScheme(
          brightness: doSang,
          primary: m.nhan,
          onPrimary: m.trenNhan,
          secondary: m.nhan,
          onSecondary: m.trenNhan,
          secondaryContainer: m.nhanNhat,
          onSecondaryContainer: m.chu,
          surface: m.the,
          onSurface: m.chu,
          onSurfaceVariant: m.chuPhu,
          outline: m.vien,
          outlineVariant: m.vien,
          error: m.loi,
          onError: m.trenNhan,
        ),
        scaffoldBackgroundColor: m.nenTren,
        textTheme: TextTheme(
          headlineLarge: TextStyle(
              fontSize: 30,
              fontWeight: FontWeight.w700,
              color: m.chu,
              height: 1.15),
          titleLarge: TextStyle(
              fontSize: 22, fontWeight: FontWeight.w700, color: m.chu),
          titleMedium: TextStyle(
              fontSize: 16, fontWeight: FontWeight.w600, color: m.chu),
          bodyLarge: TextStyle(fontSize: 16, color: m.chu, height: 1.4),
          bodyMedium: TextStyle(fontSize: 14, color: m.chuPhu, height: 1.4),
          labelLarge: TextStyle(
              fontSize: 13, fontWeight: FontWeight.w600, color: m.chu),
          labelMedium: TextStyle(fontSize: 12, color: m.chuMo),
        ),
        bottomSheetTheme: BottomSheetThemeData(
          backgroundColor: m.the,
          surfaceTintColor: Colors.transparent,
          dragHandleColor: m.chuMo,
          showDragHandle: true,
        ),
        chipTheme: ChipThemeData(
          backgroundColor: m.the,
          selectedColor: m.nhan,
          side: BorderSide(color: m.vien),
          labelStyle: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: WidgetStateColor.resolveWith(
                (s) => s.contains(WidgetState.selected) ? m.trenNhan : m.chu),
          ),
        ),
        segmentedButtonTheme: SegmentedButtonThemeData(
          style: SegmentedButton.styleFrom(
            selectedBackgroundColor: m.nhan,
            selectedForegroundColor: m.trenNhan,
            foregroundColor: m.chu,
            side: BorderSide(color: m.vien),
            textStyle: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ),
        dividerTheme: DividerThemeData(color: m.vien, thickness: 1, space: 1),
      );
}

/// Chiều cao chừa ở đáy cho thanh tab kính nổi (barHeight 64 + lề 20 của
/// `GlassTabBar.searchable`). Chỉ màn Tìm kiếm cần [banPhim]: đọc `viewInsets`
/// là dựng lại màn theo từng khung hình bàn phím trượt lên.
double chuaThanhTab(BuildContext context, {bool banPhim = false}) {
  final day = MediaQuery.viewPaddingOf(context).bottom;
  final phim = banPhim ? MediaQuery.viewInsetsOf(context).bottom : 0.0;
  return 64 + 20 + 16 + (phim > day ? phim : day);
}

/// Tint chung của mọi chrome kính nổi (thanh tab, pill, nút) để cùng một màu:
/// nền thẻ pha mờ giúp chữ đọc được trên mọi nội dung phía sau.
Color _mauKinh(Mau m) => m.the.withValues(alpha: m == Mau.toi ? 0.55 : 0.65);

LiquidGlassSettings kinhNoi(BuildContext context) =>
    LiquidGlassSettings(glassColor: _mauKinh(Mau.of(context)), blur: 10);

/// Cho thành phần kính tự đọc theme (vd `GlassPullDownButton`); thanh tab và
/// `GlassContainer` nhận [kinhNoi] trực tiếp.
final glassTheme = GlassThemeData(
  light: GlassThemeVariant(
      settings: GlassThemeSettings(glassColor: _mauKinh(Mau.sang), blur: 10)),
  dark: GlassThemeVariant(
      settings: GlassThemeSettings(glassColor: _mauKinh(Mau.toi), blur: 10)),
);
