import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Biểu tượng và màu theo khoá `icon` của `nhan_tang1.json`; màu khớp màu chữ phòng trong SVG.
const _kieu = {
  'doc': (Icons.menu_book_rounded, Color(0xFF1E4E8C)),
  'van_phong': (Icons.work_outline_rounded, Color(0xFF475569)),
  'may_tinh': (Icons.computer_rounded, Color(0xFF146C43)),
  'hoi_truong': (Icons.stadium_outlined, Color(0xFF4C3A96)),
  'wc': (Icons.wc_rounded, Color(0xFF495057)),
  'thang': (Icons.stairs_rounded, Color(0xFF6B7280)),
  'quay': (Icons.support_agent_rounded, Color(0xFF2C5BD8)),
  'cua': (Icons.door_front_door_outlined, Color(0xFF8A5A2B)),
  'ghe': (Icons.weekend_outlined, Color(0xFFB0602F)),
  'diem': (Icons.place_rounded, Color(0xFF374151)),
};

(IconData, Color) kieuNhan(String icon) => _kieu[icon] ?? _kieu['diem']!;

/// Nhãn kiểu Google Maps: biểu tượng trắng trên nền tròn tô màu theo loại, tên ở bên phải cùng màu,
/// viền chữ cùng màu nền để đọc được trên mọi màu sàn. Nhãn neo vào tâm biểu tượng ([banKinh]), không
/// neo giữa cả nhãn, nên chữ dài không kéo biểu tượng lệch khỏi chỗ của nó.
class NhanNoi extends StatelessWidget {
  final String ten;
  final String icon;

  /// Nhãn cấp 1 (toà, khu lớn) to hơn.
  final bool to;

  const NhanNoi(
      {super.key, required this.ten, required this.icon, this.to = false});

  static double banKinh(bool to) => to ? 12 : 10.5;

  /// Bề rộng ước theo số ký tự, để tránh nhãn đè nhau mà không phải dựng TextPainter mỗi khung.
  static double rongUoc(String ten, bool to) =>
      2 * banKinh(to) + 4 + ten.length * (to ? 7.4 : 6.6);

  @override
  Widget build(BuildContext context) {
    final m = Mau.of(context);
    final toi = Theme.of(context).brightness == Brightness.dark;
    final (hinh, mau) = kieuNhan(icon);
    final r = banKinh(to);
    final kieu = TextStyle(
        fontSize: to ? 13.5 : 12, fontWeight: FontWeight.w500, height: 1.1);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 2 * r,
          height: 2 * r,
          decoration: BoxDecoration(
            color: mau,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 1.2),
            boxShadow: const [
              BoxShadow(
                  color: Color(0x33000000), blurRadius: 2, offset: Offset(0, 1))
            ],
          ),
          child: Icon(hinh, size: r * 1.25, color: Colors.white),
        ),
        const SizedBox(width: 4),
        Stack(children: [
          Text(ten,
              style: kieu.copyWith(
                  foreground: Paint()
                    ..style = PaintingStyle.stroke
                    ..strokeWidth = 2.4
                    ..strokeJoin = StrokeJoin.round
                    ..color = m.the)),
          Text(ten,
              style: kieu.copyWith(
                  color: toi ? Color.lerp(mau, Colors.white, 0.55) : mau)),
        ]),
      ],
    );
  }
}
