import 'package:flutter/material.dart';
import 'app_colors.dart';

class AppTheme {
  AppTheme._();

  static ThemeData get light => _dung(Brightness.light);
  static ThemeData get dark => _dung(Brightness.dark);

  /// Dựng theme cho một độ sáng.
  ///
  /// Hai chế độ dùng chung một thang chữ và một bố cục, chỉ khác bảng màu —
  /// tách thành hàm để cỡ chữ và độ đậm không bị lệch nhau khi sửa một bên.
  static ThemeData _dung(Brightness doSang) {
    final toi = doSang == Brightness.dark;
    final muc = toi ? AppColors.inkDark : AppColors.ink;
    final nhan = toi ? AppColors.accentDark : AppColors.accent;
    final nhanNhat = toi ? AppColors.accentLightDark : AppColors.accentLight;

    return ThemeData(
      useMaterial3: true,
      brightness: doSang,
      colorScheme: ColorScheme(
        brightness: doSang,
        primary: nhan,
        onPrimary: toi ? const Color(0xFF04101F) : Colors.white,
        secondary: nhanNhat,
        onSecondary: toi ? const Color(0xFF04101F) : Colors.white,
        surface: toi ? AppColors.bgMidDark : Colors.white,
        onSurface: muc,
        error: const Color(0xFFB3261E),
        onError: Colors.white,
      ),
      scaffoldBackgroundColor: toi ? AppColors.bgTopDark : AppColors.bgTop,
      fontFamily: 'Roboto',
      textTheme: TextTheme(
        displayLarge: TextStyle(
          fontSize: 34,
          fontWeight: FontWeight.w600,
          color: muc,
          height: 1.1,
        ),
        headlineLarge: TextStyle(
          fontSize: 30,
          fontWeight: FontWeight.w600,
          color: muc,
        ),
        headlineMedium: TextStyle(
          fontSize: 25,
          fontWeight: FontWeight.w600,
          color: muc,
        ),
        titleMedium: TextStyle(
          fontSize: 17,
          fontWeight: FontWeight.w600,
          color: muc,
        ),
        bodyLarge: TextStyle(fontSize: 15, color: muc),
        bodyMedium: TextStyle(fontSize: 13.5, color: muc),
        bodySmall: TextStyle(fontSize: 11.5, color: muc),
      ),
    );
  }
}
