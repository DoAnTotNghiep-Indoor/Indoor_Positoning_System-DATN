import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

/// DỮ LIỆU DEMO TĨNH.
///
/// Bản này chỉ dựng giao diện, chưa nối API. Khi backend sẵn sàng, thay toàn bộ
/// hằng số dưới đây bằng dữ liệu từ `GET /map`, `POST /predict`, `WS /ws/location`.
/// Toạ độ (x, y) dùng đúng hệ 393x852 của frame thiết kế.

class Area {
  final String id;
  final String nameVi;
  final String nameEn;
  final int distanceM;
  final IconData icon;
  final Rect rect;
  final Color fill;
  final Color stroke;
  final String category;

  const Area({
    required this.id,
    required this.nameVi,
    required this.nameEn,
    required this.distanceM,
    required this.icon,
    required this.rect,
    required this.fill,
    required this.stroke,
    this.category = 'Học tập',
  });
}

class QuickAccess {
  final String label;
  final int distanceM;
  final IconData icon;
  const QuickAccess(this.label, this.distanceM, this.icon);
}

class DemoData {
  DemoData._();

  /// Vị trí hiện tại giả lập (sau này lấy từ WebSocket).
  static const currentAreaName = 'Phòng học nhóm';
  static const currentFloor = 'Tầng 1 · Thư viện Đại học Đà Lạt';
  static const accuracyM = 3.2;

  /// Toạ độ người dùng trên sơ đồ, hệ 393x852.
  static const userX = 150.0;
  static const userY = 585.0;

  static const buildingName = 'Thư viện DLU';
  static const areaCountLabel = '16 khu vực · cập nhật 2 giây trước';
  static const floorLabel = 'Tầng 1';

  static const quickAccess = <QuickAccess>[
    QuickAccess('Không gian đọc', 12, Icons.menu_book_outlined),
    QuickAccess('Phòng học nhóm', 28, Icons.groups_outlined),
    QuickAccess('WC', 15, Icons.wc_outlined),
    QuickAccess('Căng tin', 40, Icons.restaurant_outlined),
  ];

  static const nearby = <Area>[
    Area(
      id: 'info-desk',
      nameVi: 'Quầy hướng dẫn thông tin',
      nameEn: 'Information desk',
      distanceM: 18,
      icon: Icons.place_outlined,
      rect: Rect.fromLTWH(160, 300, 72, 40),
      fill: AppColors.roomBlue,
      stroke: AppColors.strokeGreen,
      category: 'Tiện ích',
    ),
    Area(
      id: 'periodicals',
      nameVi: 'Phòng báo và tạp chí',
      nameEn: 'Periodicals room',
      distanceM: 34,
      icon: Icons.article_outlined,
      rect: Rect.fromLTWH(276, 112, 90, 150),
      fill: AppColors.roomMint,
      stroke: AppColors.strokeBrown,
    ),
    Area(
      id: 'it-centre',
      nameVi: 'Trung tâm Công nghệ thông tin',
      nameEn: 'IT centre',
      distanceM: 52,
      icon: Icons.desktop_windows_outlined,
      rect: Rect.fromLTWH(22, 640, 150, 62),
      fill: AppColors.roomLilac,
      stroke: AppColors.strokeViolet,
      category: 'Nội bộ',
    ),
  ];

  /// Kết quả tìm kiếm demo cho từ khoá "phòng học".
  static const searchResults = <Area>[
    Area(
      id: 'group-study',
      nameVi: 'Phòng học nhóm',
      nameEn: 'Group study room',
      distanceM: 28,
      icon: Icons.groups_outlined,
      rect: Rect.fromLTWH(126, 112, 120, 74),
      fill: AppColors.roomBlue,
      stroke: AppColors.strokeGreen,
    ),
    Area(
      id: 'meeting',
      nameVi: 'Phòng họp',
      nameEn: 'Meeting room',
      distanceM: 34,
      icon: Icons.calendar_month_outlined,
      rect: Rect.fromLTWH(22, 296, 104, 72),
      fill: AppColors.roomSand,
      stroke: AppColors.strokeNavy,
      category: 'Nội bộ',
    ),
    Area(
      id: 'postgrad',
      nameVi: 'Phòng đọc sau đại học',
      nameEn: 'Postgraduate room',
      distanceM: 41,
      icon: Icons.menu_book_outlined,
      rect: Rect.fromLTWH(276, 272, 90, 96),
      fill: AppColors.roomBlue,
      stroke: AppColors.strokeViolet,
    ),
    Area(
      id: 'conference',
      nameVi: 'Phòng hội thảo',
      nameEn: 'Conference room',
      distanceM: 63,
      icon: Icons.co_present_outlined,
      rect: Rect.fromLTWH(214, 672, 152, 30),
      fill: AppColors.roomLilac,
      stroke: AppColors.strokeGrey,
    ),
    Area(
      id: 'periodicals-2',
      nameVi: 'Phòng báo và tạp chí',
      nameEn: 'Periodicals room',
      distanceM: 34,
      icon: Icons.article_outlined,
      rect: Rect.fromLTWH(276, 112, 90, 150),
      fill: AppColors.roomMint,
      stroke: AppColors.strokeBrown,
    ),
  ];

  static const searchFilters = ['Tất cả', 'Học tập', 'Tiện ích', 'Nội bộ'];

  /// Chi tiết khu vực đang xem.
  static const detailTitle = 'Không gian đọc';
  static const detailSubtitle = 'Tầng 1 · Thư viện Đại học Đà Lạt';
  static const detailDescription =
      'Khu vực bàn đọc mở dọc hai bên sảnh chính, có ổ cắm điện tại mỗi dãy '
      'bàn. Mở cửa 7:00 – 21:00 các ngày trong tuần.';

  static const detailChips = <({String label, Color bg, Color fg})>[
    (label: '120 chỗ ngồi', bg: AppColors.roomMint, fg: AppColors.strokeGreen),
    (label: 'Cách 8 m', bg: AppColors.roomBlue, fg: AppColors.strokeNavy),
    (label: 'Yên tĩnh', bg: AppColors.roomLilac, fg: AppColors.strokeViolet),
  ];

  // --- Cài đặt ---
  static const appVersion = 'v0.1';
  static const serverHost = 'api.ips.dlu.edu.vn';
  static const permissionState = 'Đã cấp';
}
