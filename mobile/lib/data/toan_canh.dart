import 'dart:math' as math;

/// Ảnh toàn cảnh 360° ngang của một chỗ, nhóm 15 chụp bằng Google Camera 18/11/2026.
///
/// Ảnh giữ độ phân giải gốc, rộng [rong] px nhưng chỉ cao [cao] px: Google Camera cắt
/// mất đỉnh trần và sàn, nên trình xem phải khai vùng cắt thay vì kéo ảnh ra 2:1.
class ToanCanh {
  final String ma;

  /// Tên chỗ chụp, cụ thể hơn [nhom] (khu tự học có hai chỗ).
  final String ten;

  /// Khớp `KhuVuc.nhom` để popup khu vực tìm được ảnh.
  final String nhom;
  final double x, y;

  /// Hướng của tâm ảnh, độ theo chiều kim đồng hồ từ trục +y của sơ đồ — cùng
  /// quy ước với `LaBan.huongSoDo`.
  final double gocTam;
  final int rong, cao;
  final String gioiThieu, huongDan;

  const ToanCanh({
    required this.ma,
    required this.ten,
    required this.nhom,
    required this.x,
    required this.y,
    required this.gocTam,
    required this.rong,
    required this.cao,
    required this.gioiThieu,
    required this.huongDan,
  });

  String get anh => 'assets/panorama/$ma.webp';

  double khoangCach(double px, double py) =>
      math.sqrt((x - px) * (x - px) + (y - py) * (y - py));

  /// Chỗ đứng đếm gạch tại chỗ; lời hướng dẫn soạn từ bảng "Dịch vụ và tiện ích",
  /// "Nguồn tài nguyên" treo ở sảnh và mô tả khu vực sẵn có.
  static const tatCa = <ToanCanh>[
    ToanCanh(
      ma: 'sanh_cua_chinh',
      ten: 'Sảnh cửa chính',
      nhom: 'Cửa chính',
      x: 0,
      y: 2.5,
      gocTam: 0,
      rong: 9216,
      cao: 4082,
      gioiThieu: 'Chào bạn đến Trung tâm Thông tin – Thư viện Trường Đại học '
          'Đà Lạt. Đây là sảnh cửa chính, đi thẳng lên các bậc là tới quầy thủ thư.',
      huongDan: 'Đi qua cổng từ ở giữa sảnh. Muốn mượn tài liệu thì mang tới quầy '
          'thủ thư để quét mã vạch. Hai cầu thang hai bên sảnh lên phòng máy TV3, '
          'TV4 và hội trường.',
    ),
    ToanCanh(
      ma: 'tu_hoc_tap_chi',
      ten: 'Khu tự học phía phòng tạp chí',
      nhom: 'Khu vực tự học',
      x: 21.5,
      y: 32.25,
      gocTam: 0,
      rong: 9728,
      cao: 3890,
      gioiThieu: 'Khu tự học phía phòng tạp chí: bàn đọc rộng dưới mái kính, '
          'dành cho tự học và sinh hoạt nhóm.',
      huongDan: 'Giữ yên lặng khi học. Cầu thang nhỏ trước mặt lên mức quầy, '
          'đi thẳng lên là phòng báo và tạp chí.',
    ),
    ToanCanh(
      ma: 'tu_hoc_loi_ra',
      ten: 'Khu tự học phía lối ra',
      nhom: 'Khu vực tự học',
      x: -21.5,
      y: 32.25,
      gocTam: 0,
      rong: 9728,
      cao: 3930,
      gioiThieu: 'Khu tự học phía lối ra: bàn đọc rộng dưới mái kính, dành cho '
          'tự học và sinh hoạt nhóm.',
      huongDan: 'Giữ yên lặng khi học. Cầu thang nhỏ trước mặt lên mức quầy, '
          'đi thẳng lên là lối ra cửa sau và cầu thang lên tầng 2.',
    ),
    ToanCanh(
      ma: 'quay_thu_thu',
      ten: 'Quầy thủ thư',
      nhom: 'Bàn thủ thư',
      x: 0,
      y: 49.25,
      gocTam: 0,
      rong: 9728,
      cao: 3988,
      gioiThieu: 'Quầy thủ thư (Information Desk) là nơi mượn, trả tài liệu và '
          'hỏi thông tin.',
      huongDan: 'Tài liệu mượn trả bằng mã vạch tại quầy. Cần tìm tài liệu thì '
          'tra mục lục trực tuyến LIBOL ở màn hình trước quầy, hoặc nhờ thủ thư '
          'tìm giúp. Thư viện còn có cơ sở dữ liệu trực tuyến như ProQuest, '
          'MathSciNet.',
    ),
    ToanCanh(
      ma: 'hoc_nhom',
      ten: 'Phòng học nhóm',
      nhom: 'Phòng học nhóm',
      x: -22,
      y: 71.5,
      gocTam: 180,
      rong: 10240,
      cao: 4036,
      gioiThieu: 'Phòng học nhóm dành cho học và thảo luận theo nhóm, cửa phòng '
          'ở ngay sau lưng bạn.',
      huongDan: 'Nói nhỏ để không làm phiền phòng bên cạnh. Hành lang trước mặt '
          'dẫn về lối ra; rẽ phải là thang máy và phòng nghiệp vụ 1.',
    ),
  ];

  static List<ToanCanh> cuaKhu(String nhom) =>
      [for (final t in tatCa) if (t.nhom == nhom) t];

  static ToanCanh ganNhatTrong(List<ToanCanh> ds, double x, double y) =>
      ds.reduce((a, b) => a.khoangCach(x, y) <= b.khoangCach(x, y) ? a : b);
}

/// Quyết định khi nào gợi ý ảnh 360°. Sai số tại chỗ đo ngày 18/11 khoảng 5–6 m
/// nên phải chờ vài lần cập nhật liên tiếp và có vùng đệm, không thì thẻ bật
/// tắt liên tục khi vị trí nhảy qua lại ranh giới.
class GoiYToanCanh {
  /// Đơn vị lưới: 14 ≈ 4,9 m vào vùng, 23 ≈ 8,1 m mới coi là đã rời đi.
  static const banKinhVao = 14.0, banKinhRa = 23.0;
  static const soLanCan = 3;

  final List<ToanCanh> _ds;
  String? _ungVien;
  int _dem = 0;
  final _daGoiY = <String>{};

  GoiYToanCanh([List<ToanCanh>? ds]) : _ds = ds ?? ToanCanh.tatCa;

  /// Gọi sau mỗi lần có vị trí mới; trả về ảnh cần gợi ý NGAY LÚC NÀY, mỗi chỗ
  /// một lần cho mỗi lượt vào.
  ToanCanh? capNhat(double x, double y, {required bool dangChiDuong}) {
    _daGoiY.removeWhere((ma) =>
        _ds.firstWhere((t) => t.ma == ma).khoangCach(x, y) > banKinhRa);

    final gan = ToanCanh.ganNhatTrong(_ds, x, y);
    if (dangChiDuong || gan.khoangCach(x, y) > banKinhVao) {
      _ungVien = null;
      _dem = 0;
      return null;
    }
    _dem = gan.ma == _ungVien ? _dem + 1 : 1;
    _ungVien = gan.ma;
    if (_dem < soLanCan || !_daGoiY.add(gan.ma)) return null;
    return gan;
  }
}
