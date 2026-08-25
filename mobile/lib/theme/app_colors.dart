import 'package:flutter/material.dart';

/// Bảng màu lấy trực tiếp từ frame thiết kế `ips-dlu-screens-v4.svg`.
class AppColors {
  AppColors._();

  // Nền
  static const bgTop = Color(0xFFEEF4FF);
  static const bgMid = Color(0xFFDDE8FB);
  static const bgBottom = Color(0xFFCFDFF8);

  // Khối blob trang trí
  static const blobA = Color(0xFF3F74FB);
  static const blobB = Color(0xFF2B8AE0);
  static const blobC = Color(0xFF6B9BFF);
  static const blobD = Color(0xFF4A7EF5);

  // Chữ
  static const ink = Color(0xFF0D1A30);
  static const navInk = Color(0xFF1A1A1A);

  // Nhấn
  static const accent = Color(0xFF2C5BD8);
  static const accentLight = Color(0xFF4A7EF5);

  // Màu nền các khu vực trên sơ đồ
  static const roomBlue = Color(0xFFE6F1FB);
  static const roomSand = Color(0xFFFAEEDA);
  static const roomMint = Color(0xFFE1F5EE);
  static const roomLilac = Color(0xFFEEEDFE);
  static const roomStone = Color(0xFFEDEBE4);

  // Màu viền / chữ theo nhóm khu vực
  static const strokeNavy = Color(0xFF0C447C);
  static const strokeBrown = Color(0xFF633806);
  static const strokeGreen = Color(0xFF085041);
  static const strokeViolet = Color(0xFF3C3489);
  static const strokeGrey = Color(0xFF4A4A45);

  static const stairGrey = Color(0xFF8A8A8A);

  static const bgGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [bgTop, bgMid, bgBottom],
    stops: [0.0, 0.55, 1.0],
  );

  static const ctaGradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [accent, accentLight],
  );

  // ===========================================================================
  // Chế độ tối
  // ===========================================================================
  //
  // Không lấy màu sáng rồi đảo ngược. Nền tối phải đủ tối để lớp kính nổi lên
  // được — kính hoạt động bằng cách khúc xạ thứ phía sau, nền xám nhạt sẽ khiến
  // nó trông đục chứ không trong. Blob giữ nguyên tông xanh nhưng hạ độ sáng và
  // giảm độ bão hoà, nếu để nguyên màu sáng chúng sẽ chói gắt trên nền tối.

  static const bgTopDark = Color(0xFF0A1020);
  static const bgMidDark = Color(0xFF0E1830);
  static const bgBottomDark = Color(0xFF122240);

  static const blobADark = Color(0xFF2A4FA8);
  static const blobBDark = Color(0xFF1E5C93);
  static const blobCDark = Color(0xFF3D63B0);
  static const blobDDark = Color(0xFF2F55A6);

  static const inkDark = Color(0xFFE8EDF7);
  static const accentDark = Color(0xFF6E9BFF);
  static const accentLightDark = Color(0xFF8FB4FF);

  static const bgGradientDark = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [bgTopDark, bgMidDark, bgBottomDark],
    stops: [0.0, 0.55, 1.0],
  );

  static const ctaGradientDark = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [accentDark, accentLightDark],
  );

  /// Màu chữ chính, chọn theo sáng/tối của theme đang dùng.
  ///
  /// Các màn hình gọi hàm này thay vì dùng thẳng [ink], vì [ink] là hằng số nên
  /// không tự đổi khi người dùng chuyển chế độ.
  static Color inkOf(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark ? inkDark : ink;

  static Color accentOf(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark ? accentDark : accent;

  static LinearGradient bgGradientOf(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark ? bgGradientDark : bgGradient;

  static LinearGradient ctaGradientOf(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark ? ctaGradientDark : ctaGradient;
}
