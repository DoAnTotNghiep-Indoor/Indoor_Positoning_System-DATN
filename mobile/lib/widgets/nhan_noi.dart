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

/// Nhãn kiểu Google Maps: biểu tượng tô màu theo loại rồi tên; viền chữ mảnh cùng màu nền để đọc được
/// trên mọi màu sàn.
class NhanNoi extends StatelessWidget {
  final String ten;
  final String icon;

  /// Nhãn cấp 1 (toà, khu lớn) chữ to hơn.
  final bool to;

  const NhanNoi({super.key, required this.ten, required this.icon, this.to = false});

  @override
  Widget build(BuildContext context) {
    final m = Mau.of(context);
    final (hinh, mau) = _kieu[icon] ?? _kieu['diem']!;
    final kieu = TextStyle(fontSize: to ? 13 : 11.5, height: 1.1);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(hinh, size: to ? 17 : 15, color: mau),
        const SizedBox(width: 3),
        Stack(children: [
          Text(ten,
              style: kieu.copyWith(
                  foreground: Paint()
                    ..style = PaintingStyle.stroke
                    ..strokeWidth = 1.6
                    ..color = m.the)),
          Text(ten, style: kieu.copyWith(color: m.chu)),
        ]),
      ],
    );
  }
}
