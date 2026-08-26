import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

/// DỮ LIỆU DEMO TĨNH.
///
/// Bản này chỉ dựng giao diện, chưa nối API. Khi backend sẵn sàng, thay toàn bộ
/// hằng số dưới đây bằng dữ liệu từ `GET /map`, `POST /predict`, `WS /ws/location`.
/// Toạ độ (x, y) dùng đúng hệ 393x852 của frame thiết kế.

/// Chọn chuỗi theo ngôn ngữ giao diện đang bật.
///
/// Dữ liệu demo là danh từ riêng của toà nhà nên không nằm trong tệp `.arb` —
/// khi nối API, tên khu vực sẽ do máy chủ trả về theo `Accept-Language` chứ
/// không phải khoá dịch trong app. Trong lúc chờ, mỗi mục giữ sẵn hai bản và
/// hàm này chọn đúng bản theo `Localizations.localeOf`.
String theoNgonNgu(BuildContext context, String vi, String en) =>
    Localizations.localeOf(context).languageCode == 'en' ? en : vi;

/// Mã nhóm khu vực.
///
/// Trước đây `category` giữ thẳng nhãn tiếng Việt ("Học tập") và màn Tìm kiếm so
/// sánh chuỗi đó với nhãn của chip lọc. Cách ấy khiến bộ lọc chỉ chạy đúng khi
/// giao diện đang ở tiếng Việt: đổi sang tiếng Anh là nhãn chip đổi theo còn dữ
/// liệu thì không, không chip nào khớp nữa. Nay `category` là MÃ bất biến, còn
/// nhãn hiển thị do `.arb` cấp.
class AreaCategory {
  AreaCategory._();

  static const all = 'all';
  static const study = 'study';
  static const facility = 'facility';
  static const internal = 'internal';

  /// Thứ tự này quyết định thứ tự chip lọc trên màn Tìm kiếm.
  static const danhSach = <String>[all, study, facility, internal];
}

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
    this.category = AreaCategory.study,
  });

  /// Tên hiển thị ở dòng đầu, theo ngôn ngữ đang bật.
  String tenChinh(BuildContext context) => theoNgonNgu(context, nameVi, nameEn);

  /// Tên ở dòng phụ — luôn là bản còn lại, để người dùng đối chiếu được với
  /// biển chỉ dẫn thật trong thư viện (biển ghi song ngữ).
  String tenPhu(BuildContext context) => theoNgonNgu(context, nameEn, nameVi);
}

class QuickAccess {
  final String label;
  final String labelEn;
  final int distanceM;
  final IconData icon;
  const QuickAccess(this.label, this.labelEn, this.distanceM, this.icon);

  String nhan(BuildContext context) => theoNgonNgu(context, label, labelEn);
}

class DemoData {
  DemoData._();

  /// Vị trí hiện tại giả lập (sau này lấy từ WebSocket).
  static const currentAreaName = 'Phòng học nhóm';
  static const currentAreaNameEn = 'Group study room';
  static const currentFloor = 'Tầng 1 · Thư viện Đại học Đà Lạt';
  static const currentFloorEn = 'Floor 1 · Da Lat University Library';
  static const accuracyM = 3.2;

  /// Toạ độ người dùng trên sơ đồ, hệ 393x852.
  static const userX = 150.0;
  static const userY = 585.0;

  static const buildingName = 'Thư viện DLU';
  static const buildingNameEn = 'DLU Library';

  /// Tách khỏi chuỗi `'16 khu vực · cập nhật 2 giây trước'` cũ: chuỗi ghép sẵn
  /// không dịch được, và trật tự "số + danh từ" mỗi ngôn ngữ một khác.
  static const areaCount = 16;
  static const updatedSecondsAgo = 2;

  static const quickAccess = <QuickAccess>[
    QuickAccess('Không gian đọc', 'Reading space', 12, Icons.menu_book_outlined),
    QuickAccess('Phòng học nhóm', 'Group study', 28, Icons.groups_outlined),
    QuickAccess('WC', 'Restroom', 15, Icons.wc_outlined),
    QuickAccess('Căng tin', 'Canteen', 40, Icons.restaurant_outlined),
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
      category: AreaCategory.facility,
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
      category: AreaCategory.internal,
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
      category: AreaCategory.internal,
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

  /// Chi tiết khu vực đang xem.
  static const detailTitle = 'Không gian đọc';
  static const detailTitleEn = 'Reading space';
  static const detailDescription =
      'Khu vực bàn đọc mở dọc hai bên sảnh chính, có ổ cắm điện tại mỗi dãy '
      'bàn. Mở cửa 7:00 – 21:00 các ngày trong tuần.';
  static const detailDescriptionEn =
      'Open reading desks along both sides of the main hall, with a power '
      'outlet at every row. Open 7:00 – 21:00 on weekdays.';

  static const detailChips = <({String label, String labelEn, Color bg, Color fg})>[
    (
      label: '120 chỗ ngồi',
      labelEn: '120 seats',
      bg: AppColors.roomMint,
      fg: AppColors.strokeGreen
    ),
    (
      label: 'Cách 8 m',
      labelEn: '8 m away',
      bg: AppColors.roomBlue,
      fg: AppColors.strokeNavy
    ),
    (
      label: 'Yên tĩnh',
      labelEn: 'Quiet zone',
      bg: AppColors.roomLilac,
      fg: AppColors.strokeViolet
    ),
  ];

  // --- Cài đặt ---
  static const appVersion = 'v0.1';
  static const serverHost = 'api.ips.dlu.edu.vn';
}
