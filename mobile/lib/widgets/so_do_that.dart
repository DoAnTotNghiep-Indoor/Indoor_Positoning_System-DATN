import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../data/floor_map.dart';
import '../data/khu_vuc.dart';
import 'tom_tat_khu_vuc.dart';
import '../services/api_dinh_vi.dart';
import '../services/la_ban.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_colors.dart';

/// Sơ đồ mặt bằng thật của tầng 1, kèm chấm vị trí đang đứng. Dùng `Map.png`
/// và đúng hệ mét mô hình trả về — khác [FloorPlan] là sơ đồ vẽ tay.
class SoDoMatBang extends StatefulWidget {
  /// Nhóm khu vực đang lọc, null là hiện tất cả. Chấm và nhãn ngoài nhóm bị
  /// làm mờ chứ không ẩn — ẩn đi thì người dùng mất luôn ngữ cảnh xung quanh.
  final String? loc;

  /// Truyền vào trong kiểm thử để khỏi cần từ kế thật.
  final LaBan? laBan;

  const SoDoMatBang({super.key, this.loc, this.laBan});

  @override
  State<SoDoMatBang> createState() => _SoDoMatBangState();
}

class _SoDoMatBangState extends State<SoDoMatBang> {
  bool _daGoi = false;
  late final LaBan _laBan = widget.laBan ?? LaBan();

  // Bề rộng nhãn đã đo, khoá theo (chữ, cỡ, hệ số phóng chữ). Không có bộ nhớ
  // đệm này thì mỗi khung hình phải `TextPainter.layout()` cho cả 44 nhãn.
  final _demRongChu = <String, double>{};

  @override
  void initState() {
    super.initState();
    // KHÔNG addListener ở đây: từ kế chỉ đổi nón hướng, mà nón nằm trong
    // `_NetSoDo`. Nghe ở cấp State thì mỗi số đọc dựng lại cả Stack — kể cả 44
    // nhãn và phép đo bề rộng của chúng. Nay chỉ `CustomPaint` nghe, xem `_ve`.
    _laBan.batDau();
  }

  @override
  void dispose() {
    // Chỉ dọn cái tự dựng. La bàn truyền từ ngoài vào là của bên gọi.
    if (widget.laBan == null) _laBan.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Nạp ngay khi mở tab, không đợi bật định vị: nhãn khu vực là thứ đáng xem
    // nhất trên màn hình này.
    if (_daGoi) return;
    _daGoi = true;
    TheoDoiViTriScope.of(context).taiBanDo();
  }

  @override
  Widget build(BuildContext context) {
    final theoDoi = TheoDoiViTriScope.of(context);
    return AnimatedBuilder(
      animation: theoDoi,
      builder: (context, _) => AspectRatio(
        aspectRatio: SoDoThat.rongPx / SoDoThat.caoPx,
        child: LayoutBuilder(
          builder: (context, c) => _ve(context, theoDoi, c.maxWidth),
        ),
      ),
    );
  }

  Widget _ve(BuildContext context, TheoDoiViTri theoDoi, double rong) {
    final toi = Theme.of(context).brightness == Brightness.dark;
    final vt = theoDoi.viTri;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapUp: (e) {
        final d = _diemTaiCham(e.localPosition, theoDoi.banDo, rong);
        if (d == null) return;
        final k = theoDoi.khuVuc.where((k) => k.nhom == d.nhom).firstOrNull;
        if (k != null) hienTomTatKhuVuc(context, k, rpId: d.rpId);
      },
      child: Stack(
        children: [
        // Chế độ tối đảo RGB chứ không đổi màu cả khối, giữ đúng thứ tự tương
        // phản của bản sáng. Hàng alpha không đổi nên nền vẫn trong suốt.
        Positioned.fill(
          child: ColorFiltered(
            colorFilter: toi
                ? const ColorFilter.matrix(<double>[
                    -1, 0, 0, 0, 255, //
                    0, -1, 0, 0, 255, //
                    0, 0, -1, 0, 255, //
                    0, 0, 0, 1, 0, //
                  ])
                : const ColorFilter.mode(Colors.transparent, BlendMode.dst),
            child: Image.asset(SoDoThat.anh, fit: BoxFit.fill),
          ),
        ),

          // Chấm và tuyến chung một canvas: tách thành widget thì 40 chấm hoá 40
          // lớp Positioned cho cùng một khung hình.
          //
          // Chỉ riêng lớp này nghe từ kế, nên số đọc mới chỉ vẽ lại canvas chứ
          // không dựng lại nhãn. RepaintBoundary tách hẳn lớp vẽ để phần còn lại
          // của Stack không phải sơn lại theo.
          Positioned.fill(
            child: RepaintBoundary(
              child: AnimatedBuilder(
                animation: _laBan,
                builder: (context, _) => CustomPaint(
                  painter: _NetSoDo(
                    diem: theoDoi.banDo,
                    tuyen: theoDoi.daToi
                        ? const []
                        : theoDoi.tuyen?.duongDi ?? const [],
                    loc: widget.loc,
                    rong: rong,
                    mau: AppColors.accentOf(context),
                    muc: toi ? AppColors.inkDark : AppColors.ink,
                    viTri: vt,
                    huong: _laBan.huongSoDo,
                  ),
                ),
              ),
            ),
          ),

        for (final n in _viTriNhan(theoDoi.khuVuc, rong))
          _nhan(context, n.$1.nhom, n.$2, rong, toi, _moNhat(n.$1.nhom)),

          if (vt != null)
            _cham(SoDoThat.sangKhung(vt.xGop, vt.yGop, rong), rong),
        ],
      ),
    );
  }

  /// Mỗi điểm tham chiếu một nhãn ngay trên chấm; nhãn chồng nhau thì xếp dọc.
  List<(KhuVuc, Offset)> _viTriNhan(List<KhuVuc> khu, double rong) {
    final cao = _caoChu(rong) * 1.6;
    final ra = <(KhuVuc, Offset)>[];

    final sap = [
      for (final k in khu)
        for (final t in k.diem)
          (k, SoDoThat.sangKhung(t.dx, t.dy, rong)),
    ]..sort((a, b) =>
        a.$2.dy != b.$2.dy ? a.$2.dy.compareTo(b.$2.dy)
                           : a.$2.dx.compareTo(b.$2.dx));

    for (final (k, tam) in sap) {
      var p = tam;
      for (final (_, q) in ra) {
        final chongNgang = (p.dx - q.dx).abs() < rong * 0.16;
        if (chongNgang && (p.dy - q.dy).abs() < cao) {
          p = Offset(p.dx, q.dy + cao);
        }
      }
      ra.add((k, p));
    }
    return ra;
  }

  double _caoChu(double rong) =>
      (rong / SoDoThat.rongPx * 15).clamp(7.0, 12.0);

  /// Điểm tham chiếu gần chỗ vừa chạm nhất, hoặc null nếu chạm ra ngoài toà nhà.
  DiemThamChieu? _diemTaiCham(Offset cham, List<DiemThamChieu> ds, double rong) {
    if (ds.isEmpty) return null;

    // Đổi ngược về đơn vị lưới rồi mới so, để ngưỡng "quá xa" không đổi theo cỡ
    // màn hình.
    final met = SoDoThat.sangMet(cham, rong);

    var gan = ds.first;
    var min = double.infinity;
    for (final d in ds) {
      final l = (Offset(d.x, d.y) - met).distance;
      if (l < min) {
        min = l;
        gan = d;
      }
    }
    // Chạm cách mọi khu vực quá xa thì coi như chạm nhầm, không mở gì cả.
    return min <= 12 ? gan : null;
  }


  /// Nhãn ngoài nhóm đang lọc mờ đi, nhưng không mờ hẳn: vẫn phải đọc được để
  /// biết mình đang ở đâu trên sơ đồ.
  double _moNhat(String nhom) =>
      widget.loc == null || widget.loc == nhom ? 1.0 : 0.28;

  /// Kiểu chữ của nhãn. Tách ra vì phải dựng đúng kiểu này hai lần — một lần
  /// đo bề rộng, một lần vẽ; đo bằng kiểu khác thì nhãn lại cụt như cũ.
  TextStyle _kieuNhan(double co, Color mau) => TextStyle(
        fontSize: co,
        fontWeight: FontWeight.w600,
        color: mau,
      );

  /// Bề rộng thật của nhãn khi vẽ ra. Phải gộp [DefaultTextStyle] và
  /// [MediaQuery.textScalerOf] chứ không đo bằng kiểu trần: `Text` thừa hưởng
  /// phông theme và cỡ chữ hệ thống, đo thiếu là mọi nhãn bị cắt.
  double _rongChu(BuildContext context, String chu, double co) {
    final scaler = MediaQuery.textScalerOf(context);
    final khoa = '$chu|${co.toStringAsFixed(2)}|${scaler.scale(10)}';
    final da = _demRongChu[khoa];
    if (da != null) return da;

    final thuoc = TextPainter(
      text: TextSpan(
        text: chu,
        style: DefaultTextStyle.of(context)
            .style
            .merge(_kieuNhan(co, const Color(0xFF000000))),
      ),
      textDirection: TextDirection.ltr,
      textScaler: scaler,
      maxLines: 1,
    )..layout();
    // Nới một pixel: bề rộng bố cục làm tròn xuống thì chữ cuối chạm mép và
    // ellipsis nhảy vào dù chỉ thiếu phần lẻ.
    return _demRongChu[khoa] = thuoc.width + 1;
  }

  Widget _nhan(BuildContext context, String chu, Offset tam, double rong,
      bool toi, double mo) {
    final co = _caoChu(rong);

    // Căn giữa quanh chấm nhưng phải nằm trọn khung. Cách cũ `left: 0, width:
    // tam.dx * 2` làm cụm sát mép bị cụt thành "Kh..." — lỗi Hình 21 của CTK45.
    final w = math.min(_rongChu(context, chu, co), rong);
    final trai = math.max(0.0, math.min(tam.dx - w / 2, rong - w));

    return Positioned(
      left: trai,
      top: tam.dy - co,
      width: w,
      child: Text(
        chu,
        textAlign: TextAlign.center,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: _kieuNhan(
          co,
          (toi ? AppColors.inkDark : AppColors.ink)
              .withValues(alpha: 0.7 * mo),
        ),
      ),
    );
  }

  Widget _cham(Offset tam, double rong) {
    final r = (rong / SoDoThat.rongPx * 11).clamp(6.0, 11.0);
    return Positioned(
      left: tam.dx - r,
      top: tam.dy - r,
      width: r * 2,
      height: r * 2,
      child: DecoratedBox(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: AppColors.accent,
          border: Border.all(color: Colors.white, width: r * 0.35),
          boxShadow: [
            BoxShadow(
              color: AppColors.accent.withValues(alpha: 0.35),
              blurRadius: r * 1.6,
            ),
          ],
        ),
      ),
    );
  }
}


/// Chấm điểm tham chiếu và tuyến đường, vẽ thẳng lên canvas. Tuyến là chuỗi
/// chấm cách đều chứ không phải đường liền: khoảng hở nói rằng đây là tuyến
/// nối các điểm đã đo, không phải lối đi khảo sát từng centimet.
class _NetSoDo extends CustomPainter {
  final List<DiemThamChieu> diem;
  final List<DiemThamChieu> tuyen;
  final String? loc;
  final double rong;
  final Color mau;
  final Color muc;

  /// Vị trí đang đứng, null khi chưa định vị. Chỉ dùng để đặt gốc nón hướng.
  final ViTri? viTri;

  /// Hướng đã quy về hệ sơ đồ, độ theo chiều kim đồng hồ từ trục +y. Null thì
  /// không vẽ nón — máy không có từ kế, hoặc chưa có số đọc nào.
  final double? huong;

  /// Khoảng cách giữa hai chấm trên tuyến, tính bằng MÉT chứ không bằng pixel —
  /// người dùng phóng to sơ đồ thì mật độ chấm phải giữ nguyên ý nghĩa.
  static const buocChamM = 1.2;

  static const _bangMau = [
    Color(0xFF4C78A8), Color(0xFFF58518), Color(0xFF54A24B),
    Color(0xFFE45756), Color(0xFF72B7B2), Color(0xFFEECA3B),
    Color(0xFFB279A2), Color(0xFFFF9DA6), Color(0xFF9D755D),
    Color(0xFFBAB0AC), Color(0xFF7970BF),
  ];

  const _NetSoDo({
    required this.diem,
    required this.tuyen,
    required this.loc,
    required this.rong,
    required this.mau,
    required this.muc,
    required this.viTri,
    required this.huong,
  });

  @override
  void paint(Canvas canvas, Size size) {
    _veQuang(canvas);
    _veDiem(canvas);
    _veTuyen(canvas);
    _veNonHuong(canvas);
    _veThuoc(canvas, size);
  }

  /// Màu theo thứ tự bảng chữ cái của tên nhóm: ổn định giữa các lần chạy, khác
  /// với băm chuỗi vốn không bảo đảm điều đó.
  Color _mauNhom(String nhom, List<String> ten) {
    final i = ten.indexOf(nhom);
    return i < 0 ? mau : _bangMau[i % _bangMau.length];
  }

  /// Quầng chỉ hiện khi đang lọc: bật cả 11 nhóm cùng lúc thì sàn phủ kín màu
  /// và sơ đồ mất hết ý nghĩa.
  void _veQuang(Canvas canvas) {
    if (loc == null) return;
    final ten = ({for (final d in diem) d.nhom}.toList()..sort());
    final son = Paint()
      ..color = _mauNhom(loc!, ten).withValues(alpha: 0.30);
    final r = SoDoThat.banKinhQuangM * SoDoThat.pxMoiMetX * (rong / SoDoThat.rongPx);

    for (final d in diem) {
      if (d.nhom != loc) continue;
      canvas.drawCircle(SoDoThat.sangKhung(d.x, d.y, rong), r, son);
    }
  }

  /// Nón hướng nhìn, mở từ chấm vị trí. Vẽ RỘNG có chủ ý: [LaBan.gocBacSoDo]
  /// chưa ai đo nên nón lệch đúng bằng sai số đó. Mũi tên nhọn sẽ khẳng định
  /// một độ chính xác mà dữ liệu không đỡ nổi.
  void _veNonHuong(Canvas canvas) {
    final vt = viTri;
    final h = huong;
    if (vt == null || h == null) return;

    final goc = SoDoThat.sangKhung(vt.xGop, vt.yGop, rong);
    final ban = (rong / SoDoThat.rongPx * 46).clamp(22.0, 46.0);

    // Trục +y sơ đồ hướng LÊN nhưng trục y canvas hướng XUỐNG, nên 0° phải là
    // -pi/2 chứ không phải 0. Quên chỗ này là nón chỉ sang phải thay vì lên.
    final giua = (h - 90) * math.pi / 180;
    const mo = LaBan.nuaGocMoDo * math.pi / 180;

    canvas.drawPath(
      Path()
        ..moveTo(goc.dx, goc.dy)
        ..arcTo(Rect.fromCircle(center: goc, radius: ban), giua - mo, mo * 2,
            false)
        ..close(),
      Paint()
        ..shader = RadialGradient(
          colors: [mau.withValues(alpha: 0.42), mau.withValues(alpha: 0.0)],
        ).createShader(Rect.fromCircle(center: goc, radius: ban)),
    );
  }

  void _veThuoc(Canvas canvas, Size size) {
    const daiM = 10.0;
    final dai = daiM * SoDoThat.pxMoiMetX * (rong / SoDoThat.rongPx);
    final le = rong * 0.03;
    // Lùi vào 1/4 bề rộng: góc trái dưới là nhãn TV3,4.
    final trai = rong * 0.24;
    final y = size.height - le;

    canvas.drawLine(
      Offset(trai, y),
      Offset(trai + dai, y),
      Paint()
        ..color = muc.withValues(alpha: 0.65)
        ..strokeWidth = (rong / SoDoThat.rongPx * 3).clamp(1.4, 3.0),
    );

    final chu = TextPainter(
      text: TextSpan(
        text: '${daiM.toInt()} m',
        style: TextStyle(
          color: muc.withValues(alpha: 0.65),
          fontSize: (rong / SoDoThat.rongPx * 13).clamp(7.0, 12.0),
          fontWeight: FontWeight.w600,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    chu.paint(canvas, Offset(trai + (dai - chu.width) / 2, y - chu.height - 2));
  }

  void _veDiem(Canvas canvas) {
    final r = (rong / SoDoThat.rongPx * 4.5).clamp(2.0, 4.5);
    final ten = ({for (final d in diem) d.nhom}.toList()..sort());

    for (final d in diem) {
      final chon = loc == null || d.nhom == loc;
      // Chấm dùng đúng màu của quầng, để mắt nối được hai thứ với nhau.
      final c = loc == null ? mau : _mauNhom(d.nhom, ten);
      canvas.drawCircle(
        SoDoThat.sangKhung(d.x, d.y, rong),
        chon ? r : r * 0.7,
        Paint()..color = (chon ? c : muc).withValues(alpha: chon ? 0.7 : 0.16),
      );
    }
  }

  void _veTuyen(Canvas canvas) {
    if (tuyen.length < 2) return;

    final r = (rong / SoDoThat.rongPx * 5).clamp(2.5, 5.0);
    final son = Paint()..color = mau;

    // Rải chấm theo mét và mang phần dư sang chặng kế: không mang thì mỗi đỉnh
    // gãy khởi động lại nhịp, chỗ nối trông như hai chấm dính nhau.
    var du = 0.0;
    for (var i = 0; i < tuyen.length - 1; i++) {
      final a = tuyen[i], b = tuyen[i + 1];
      final dai = math.sqrt(
          (b.x - a.x) * (b.x - a.x) + (b.y - a.y) * (b.y - a.y));
      if (dai == 0) continue;

      for (var t = du; t < dai; t += buocChamM) {
        final k = t / dai;
        canvas.drawCircle(
          SoDoThat.sangKhung(a.x + (b.x - a.x) * k, a.y + (b.y - a.y) * k, rong),
          r * 0.5,
          son,
        );
      }
      du = (du - dai) % buocChamM;
    }

    _veGhim(canvas, tuyen.first, r, mau.withValues(alpha: 0.9));
    _veGhim(canvas, tuyen.last, r * 1.25, const Color(0xFF17A673));
  }

  void _veGhim(Canvas canvas, DiemThamChieu d, double r, Color c) {
    final p = SoDoThat.sangKhung(d.x, d.y, rong);
    canvas.drawCircle(p, r, Paint()..color = c);
    canvas.drawCircle(
      p,
      r,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = r * 0.4
        ..color = Colors.white,
    );
  }

  @override
  bool shouldRepaint(_NetSoDo cu) =>
      cu.diem != diem ||
      cu.tuyen != tuyen ||
      cu.loc != loc ||
      cu.rong != rong ||
      cu.mau != mau ||
      cu.viTri != viTri ||
      cu.huong != huong;
}
