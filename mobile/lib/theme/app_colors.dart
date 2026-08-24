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
}
