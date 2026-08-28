import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

/// HÌNH HỌC VÀ NHÃN CỦA SƠ ĐỒ MẶT BẰNG TẦNG 1.
///
/// Nguồn sự thật duy nhất về vị trí các phòng. Trước đây cùng một phòng được
/// khai báo ở hai nơi: `widgets/floor_plan.dart` để vẽ, và `data/demo_data.dart`
/// để hiện trong danh sách "Gần bạn" và kết quả tìm kiếm. Sáu phòng có cùng
/// `Rect` và cùng màu chép làm hai bản, nên đổi sơ đồ là phải sửa tay hai chỗ
/// và không có gì cảnh báo nếu quên một chỗ.
///
/// Toạ độ theo hệ thiết kế [rong] x [cao]. Đây KHÔNG phải mét: mô hình định vị
/// trả về x trong khoảng -43..43 và y trong 0..52 mét, nên khi nối backend ở
/// giai đoạn 3 sẽ cần một phép đổi mét sang hệ này. Phép đổi đó thuộc về dữ liệu
/// toà nhà nên chỗ của nó là tệp này, không phải widget vẽ.
class FloorMap {
  FloorMap._();

  /// Kích thước hệ toạ độ thiết kế.
  static const double rong = 393;
  static const double cao = 852;

  /// Quầy hướng dẫn — có vùng và có tên, nhưng KHÔNG nằm trong [phong] nên sơ
  /// đồ không vẽ nó thành ô: nó nằm giữa sảnh và chỉ hiện dưới dạng nhãn chữ.
  /// Vẫn khai báo đầy đủ ở đây để danh sách "Gần bạn" có chỗ trỏ tới, và để mọi
  /// vùng của toà nhà nằm chung một tệp.
  static const quayHuongDan = PhongSoDo(
    id: 'info-desk',
    r: Rect.fromLTWH(160, 300, 72, 40),
    fill: AppColors.roomBlue,
    stroke: AppColors.strokeGreen,
    vi: ['Quầy hướng dẫn'],
    en: ['Information desk'],
  );

  static const nghiepVu1 = PhongSoDo(
    id: 'technical-1',
    r: Rect.fromLTWH(22, 112, 96, 150),
    fill: AppColors.roomSand,
    stroke: AppColors.strokeNavy,
    vi: ['Phòng', 'nghiệp vụ 1'],
    en: ['Technical', 'dept. 1'],
  );

  static const phongHocNhom = PhongSoDo(
    id: 'group-study',
    r: Rect.fromLTWH(126, 112, 120, 74),
    fill: AppColors.roomBlue,
    stroke: AppColors.strokeGreen,
    vi: ['Phòng học nhóm'],
    en: ['Group study'],
  );

  static const baoTapChi = PhongSoDo(
    id: 'periodicals',
    r: Rect.fromLTWH(276, 112, 90, 150),
    fill: AppColors.roomMint,
    stroke: AppColors.strokeBrown,
    vi: ['Phòng báo', '& tạp chí'],
    en: ['Periodicals'],
  );

  static const nghiepVu2 = PhongSoDo(
    id: 'technical-2',
    r: Rect.fromLTWH(172, 196, 96, 66),
    fill: AppColors.roomSand,
    stroke: AppColors.strokeBrown,
    vi: ['Phòng', 'nghiệp vụ 2'],
    en: ['Technical', 'dept. 2'],
  );

  static const phongHop = PhongSoDo(
    id: 'meeting',
    r: Rect.fromLTWH(22, 296, 104, 72),
    fill: AppColors.roomSand,
    stroke: AppColors.strokeNavy,
    vi: ['Phòng họp'],
    en: ['Meeting room'],
  );

  static const docSauDaiHoc = PhongSoDo(
    id: 'postgrad',
    r: Rect.fromLTWH(276, 272, 90, 96),
    fill: AppColors.roomBlue,
    stroke: AppColors.strokeViolet,
    vi: ['Phòng đọc', 'sau đại học'],
    en: ['Postgraduate', 'reading'],
  );

  /// Giữ nguyên chữ viết tắt trên bản vẽ gốc ở cả hai ngôn ngữ: đây là ký hiệu
  /// in trên sơ đồ mặt bằng của thư viện, không phải tên đầy đủ để dịch.
  static const tm = PhongSoDo(
    id: 'tm',
    r: Rect.fromLTWH(90, 266, 30, 28),
    fill: AppColors.roomStone,
    stroke: AppColors.strokeGreen,
    vi: ['TM'],
    en: ['TM'],
    fs: 9,
  );

  /// "WC" là ký hiệu quốc tế, giữ nguyên ở cả hai ngôn ngữ.
  static const wcTrai = PhongSoDo(
    id: 'wc-left',
    r: Rect.fromLTWH(22, 608, 52, 26),
    fill: AppColors.roomMint,
    stroke: AppColors.strokeGreen,
    vi: ['WC'],
    en: ['WC'],
    fs: 9,
  );

  static const wcPhai = PhongSoDo(
    id: 'wc-right',
    r: Rect.fromLTWH(314, 608, 52, 26),
    fill: AppColors.roomMint,
    stroke: AppColors.strokeGreen,
    vi: ['WC'],
    en: ['WC'],
    fs: 9,
  );

  static const trungTamCntt = PhongSoDo(
    id: 'it-centre',
    r: Rect.fromLTWH(22, 640, 150, 62),
    fill: AppColors.roomLilac,
    stroke: AppColors.strokeViolet,
    vi: ['Trung tâm', 'Công nghệ thông tin'],
    en: ['IT centre'],
  );

  /// Bản cũ nhồi cả hai ngôn ngữ vào một dòng `'Căng tin · Canteen'` nên không
  /// tách ra được khi đổi ngôn ngữ. Nay là hai bản riêng.
  static const cangTin = PhongSoDo(
    id: 'canteen',
    r: Rect.fromLTWH(214, 640, 152, 30),
    fill: AppColors.roomMint,
    stroke: AppColors.strokeBrown,
    vi: ['Căng tin'],
    en: ['Canteen'],
  );

  static const hoiThao = PhongSoDo(
    id: 'conference',
    r: Rect.fromLTWH(214, 672, 152, 30),
    fill: AppColors.roomLilac,
    stroke: AppColors.strokeGrey,
    vi: ['Phòng hội thảo'],
    en: ['Conference room'],
  );

  /// Thứ tự vẽ. Sơ đồ lặp đúng danh sách này.
  static const phong = <PhongSoDo>[
    nghiepVu1,
    phongHocNhom,
    baoTapChi,
    nghiepVu2,
    phongHop,
    docSauDaiHoc,
    tm,
    wcTrai,
    wcPhai,
    trungTamCntt,
    cangTin,
    hoiThao,
  ];

  /// Nhãn không thuộc ô phòng nào — không gian mở, quầy, cầu thang, sảnh.
  ///
  /// Bản cũ vẽ mỗi khu hai dòng chồng nhau, một tiếng Việt một tiếng Anh, và
  /// hai nhãn cầu thang cùng nhãn sảnh chính thì chỉ có tiếng Việt. Nay mỗi
  /// nhãn giữ đủ hai bản và sơ đồ chọn theo ngôn ngữ đang bật, nên `top` dịch
  /// xuống để một dòng nằm đúng giữa chỗ khối hai dòng cũ chiếm.
  static const nhan = <NhanSoDo>[
    NhanSoDo(
      vi: 'KHÔNG GIAN ĐỌC',
      en: 'READING SPACE',
      cx: 112,
      top: 500,
      size: 9.5,
      color: AppColors.strokeNavy,
      bold: true,
    ),
    NhanSoDo(
      vi: 'KHÔNG GIAN ĐỌC',
      en: 'READING SPACE',
      cx: 280,
      top: 500,
      size: 9.5,
      color: AppColors.strokeNavy,
      bold: true,
    ),
    NhanSoDo(
      vi: 'QUẦY HƯỚNG DẪN',
      en: 'INFORMATION DESK',
      cx: 196,
      top: 325,
      size: 8.5,
      color: AppColors.strokeGreen,
      bold: true,
      trenNen: true,
    ),
    NhanSoDo(
      vi: 'Cầu thang',
      en: 'Stairs',
      cx: 74,
      top: 373,
      size: 8,
      color: AppColors.strokeGrey,
      opacity: 0.8,
      trenNen: true,
    ),
    NhanSoDo(
      vi: 'Cầu thang',
      en: 'Stairs',
      cx: 314,
      top: 373,
      size: 8,
      color: AppColors.strokeGrey,
      opacity: 0.8,
      trenNen: true,
    ),
    NhanSoDo(
      vi: 'Sảnh chính',
      en: 'Main hall',
      cx: 196,
      top: 413,
      size: 8.5,
      color: AppColors.strokeGrey,
      opacity: 0.75,
      trenNen: true,
    ),
  ];
}

/// Một ô phòng trên sơ đồ.
class PhongSoDo {
  final String id;
  final Rect r;
  final Color fill;
  final Color stroke;

  /// Nhãn tiếng Việt, mỗi phần tử một dòng.
  final List<String> vi;

  /// Nhãn tiếng Anh, mỗi phần tử một dòng.
  final List<String> en;

  final double fs;

  const PhongSoDo({
    required this.id,
    required this.r,
    required this.fill,
    required this.stroke,
    required this.vi,
    required this.en,
    this.fs = 9.5,
  });

  /// Nhãn theo ngôn ngữ giao diện đang bật.
  List<String> nhan(BuildContext context) =>
      Localizations.localeOf(context).languageCode == 'en' ? en : vi;
}

/// Nhãn chữ đặt tự do trên sơ đồ, không gắn với ô phòng nào.
class NhanSoDo {
  final String vi;
  final String en;

  /// Nhãn được căn giữa trong dải rộng `cx * 2`, tính từ mép trái sơ đồ.
  final double cx;
  final double top;
  final double size;
  final Color color;
  final bool bold;
  final double opacity;

  /// Nhãn nằm thẳng trên nền sơ đồ (cần đổi màu ở chế độ tối) chứ không nằm
  /// trên ô phòng — các ô phòng giữ màu pastel sáng ở cả hai chế độ.
  final bool trenNen;

  const NhanSoDo({
    required this.vi,
    required this.en,
    required this.cx,
    required this.top,
    required this.size,
    required this.color,
    this.bold = false,
    this.opacity = 1,
    this.trenNen = false,
  });

  String chu(BuildContext context) =>
      Localizations.localeOf(context).languageCode == 'en' ? en : vi;
}
