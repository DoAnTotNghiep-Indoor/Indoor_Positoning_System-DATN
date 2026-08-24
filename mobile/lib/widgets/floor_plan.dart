import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../data/demo_data.dart';

/// Sơ đồ mặt bằng tầng 1, dựng theo đúng toạ độ trong frame thiết kế (hệ 393x852)
/// rồi co giãn theo bề rộng màn hình thật.
class FloorPlan extends StatelessWidget {
  final bool showUser;
  const FloorPlan({super.key, this.showUser = true});

  static const _rooms = <({
    Rect r,
    Color fill,
    Color stroke,
    List<String> vi,
    String? en,
    double fs
  })>[
    (r: Rect.fromLTWH(22, 112, 96, 150), fill: AppColors.roomSand, stroke: AppColors.strokeNavy, vi: ['Phòng', 'nghiệp vụ 1'], en: 'Technical dept. 1', fs: 9.5),
    (r: Rect.fromLTWH(126, 112, 120, 74), fill: AppColors.roomBlue, stroke: AppColors.strokeGreen, vi: ['Phòng học nhóm'], en: 'Group study', fs: 9.5),
    (r: Rect.fromLTWH(276, 112, 90, 150), fill: AppColors.roomMint, stroke: AppColors.strokeBrown, vi: ['Phòng báo', '& tạp chí'], en: 'Periodicals', fs: 9.5),
    (r: Rect.fromLTWH(172, 196, 96, 66), fill: AppColors.roomSand, stroke: AppColors.strokeBrown, vi: ['Phòng', 'nghiệp vụ 2'], en: null, fs: 9.5),
    (r: Rect.fromLTWH(22, 296, 104, 72), fill: AppColors.roomSand, stroke: AppColors.strokeNavy, vi: ['Phòng họp'], en: 'Meeting room', fs: 9.5),
    (r: Rect.fromLTWH(276, 272, 90, 96), fill: AppColors.roomBlue, stroke: AppColors.strokeViolet, vi: ['Phòng đọc', 'sau đại học'], en: 'Postgraduate', fs: 9.5),
    (r: Rect.fromLTWH(90, 266, 30, 28), fill: AppColors.roomStone, stroke: AppColors.strokeGreen, vi: ['TM'], en: null, fs: 9),
    (r: Rect.fromLTWH(22, 608, 52, 26), fill: AppColors.roomMint, stroke: AppColors.strokeGreen, vi: ['WC'], en: null, fs: 9),
    (r: Rect.fromLTWH(314, 608, 52, 26), fill: AppColors.roomMint, stroke: AppColors.strokeGreen, vi: ['WC'], en: null, fs: 9),
    (r: Rect.fromLTWH(22, 640, 150, 62), fill: AppColors.roomLilac, stroke: AppColors.strokeViolet, vi: ['Trung tâm', 'Công nghệ thông tin'], en: 'IT centre', fs: 9.5),
    (r: Rect.fromLTWH(214, 640, 152, 30), fill: AppColors.roomMint, stroke: AppColors.strokeBrown, vi: ['Căng tin · Canteen'], en: null, fs: 9.5),
    (r: Rect.fromLTWH(214, 672, 152, 30), fill: AppColors.roomLilac, stroke: AppColors.strokeGrey, vi: ['Phòng hội thảo'], en: null, fs: 9.5),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, c) {
        final s = c.maxWidth / 393.0;
        return SizedBox(
          width: c.maxWidth,
          height: 852 * s,
          child: Stack(
            children: [
              // Đường bao toà nhà + sảnh chính
              Positioned.fill(child: CustomPaint(painter: _ShellPainter(s))),

              // Các phòng
              for (final room in _rooms)
                Positioned(
                  left: room.r.left * s,
                  top: room.r.top * s,
                  width: room.r.width * s,
                  height: room.r.height * s,
                  child: _RoomBox(
                    fill: room.fill,
                    stroke: room.stroke,
                    vi: room.vi,
                    en: room.en,
                    fs: room.fs * s,
                    scale: s,
                  ),
                ),

              // Nhãn không thuộc phòng cụ thể
              _label('KHÔNG GIAN ĐỌC', 112, 494, 9.5, AppColors.strokeNavy, s, bold: true),
              _label('Reading space', 112, 506, 8.5, AppColors.strokeNavy, s, opacity: .75),
              _label('KHÔNG GIAN ĐỌC', 280, 494, 9.5, AppColors.strokeNavy, s, bold: true),
              _label('Reading space', 280, 506, 8.5, AppColors.strokeNavy, s, opacity: .75),
              _label('QUẦY HƯỚNG DẪN', 196, 320, 8.5, AppColors.strokeGreen, s, bold: true),
              _label('Information desk', 196, 331, 7.5, AppColors.strokeBrown, s, opacity: .8),
              _label('Cầu thang', 74, 373, 8, AppColors.strokeGrey, s, opacity: .8),
              _label('Cầu thang', 314, 373, 8, AppColors.strokeGrey, s, opacity: .8),
              _label('Sảnh chính', 196, 413, 8.5, AppColors.strokeGrey, s, opacity: .75),

              // Marker vị trí người dùng
              if (showUser) ...[
                Positioned(
                  left: (DemoData.userX - 26) * s,
                  top: (DemoData.userY - 44) * s,
                  width: 52 * s,
                  height: 44 * s,
                  child: CustomPaint(painter: _ConePainter()),
                ),
                Positioned(
                  left: (DemoData.userX - 9.5) * s,
                  top: (DemoData.userY - 9.5) * s,
                  width: 19 * s,
                  height: 19 * s,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppColors.accent,
                      border: Border.all(color: Colors.white, width: 3.5 * s),
                    ),
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  static Widget _label(
    String text,
    double cx,
    double top,
    double size,
    Color color,
    double s, {
    bool bold = false,
    double opacity = 1,
  }) {
    return Positioned(
      left: 0,
      top: top * s,
      width: cx * 2 * s,
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: TextStyle(
          fontSize: size * s,
          height: 1.15,
          fontWeight: bold ? FontWeight.w600 : FontWeight.w400,
          color: color.withValues(alpha: opacity),
        ),
      ),
    );
  }
}

class _RoomBox extends StatelessWidget {
  final Color fill, stroke;
  final List<String> vi;
  final String? en;
  final double fs, scale;

  const _RoomBox({
    required this.fill,
    required this.stroke,
    required this.vi,
    required this.en,
    required this.fs,
    required this.scale,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: fill.withValues(alpha: 0.55),
        border: Border.all(color: stroke.withValues(alpha: 0.85), width: 1.2),
      ),
      alignment: Alignment.center,
      padding: EdgeInsets.symmetric(horizontal: 2 * scale),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (final line in vi)
            Text(
              line,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: fs,
                height: 1.25,
                fontWeight: FontWeight.w600,
                color: stroke,
              ),
            ),
          if (en != null)
            Text(
              en!,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: fs * 0.79,
                height: 1.3,
                color: stroke.withValues(alpha: 0.75),
              ),
            ),
        ],
      ),
    );
  }
}

/// Vẽ đường bao toà nhà, sảnh chính và hai khu cầu thang.
class _ShellPainter extends CustomPainter {
  final double s;
  _ShellPainter(this.s);

  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(14 * s, 136 * s)
      ..lineTo(48 * s, 104 * s)
      ..lineTo(190 * s, 104 * s)
      ..lineTo(190 * s, 96 * s)
      ..arcToPoint(Offset(232 * s, 96 * s), radius: Radius.circular(28 * s), clockwise: true)
      ..lineTo(232 * s, 104 * s)
      ..lineTo(344 * s, 104 * s)
      ..lineTo(374 * s, 136 * s)
      ..lineTo(374 * s, 700 * s)
      ..arcToPoint(Offset(368 * s, 706 * s), radius: Radius.circular(6 * s), clockwise: true)
      ..lineTo(20 * s, 706 * s)
      ..arcToPoint(Offset(14 * s, 700 * s), radius: Radius.circular(6 * s), clockwise: true)
      ..close();

    canvas.drawPath(path, Paint()..color = Colors.white.withValues(alpha: 0.62));
    canvas.drawPath(
      path,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5 * s
        ..strokeJoin = StrokeJoin.round
        ..color = AppColors.ink.withValues(alpha: 0.42),
    );

    // Sảnh chính
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(22 * s, 430 * s, 344 * s, 170 * s),
        Radius.circular(4 * s),
      ),
      Paint()..color = AppColors.roomBlue.withValues(alpha: 0.9),
    );

    // Cầu thang: 13 bậc mỗi bên
    final step = Paint()..color = AppColors.stairGrey.withValues(alpha: 0.75);
    for (var i = 0; i < 13; i++) {
      canvas.drawRect(Rect.fromLTWH((22 + i * 8) * s, 388 * s, 4.4 * s, 34 * s), step);
      canvas.drawRect(Rect.fromLTWH((262 + i * 8) * s, 388 * s, 4.4 * s, 34 * s), step);
    }
    final line = Paint()..color = Colors.white;
    canvas.drawRect(Rect.fromLTWH(36 * s, 404 * s, 76 * s, 1.6 * s), line);
    canvas.drawRect(Rect.fromLTWH(276 * s, 404 * s, 76 * s, 1.6 * s), line);
  }

  @override
  bool shouldRepaint(covariant _ShellPainter old) => old.s != s;
}

/// Nón hướng nhìn của người dùng.
class _ConePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    final path = Path()
      ..moveTo(w / 2, h)
      ..lineTo(0, 0)
      ..arcToPoint(Offset(w, 0), radius: Radius.circular(w), clockwise: true)
      ..close();
    canvas.drawPath(path, Paint()..color = AppColors.accent.withValues(alpha: 0.2));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
