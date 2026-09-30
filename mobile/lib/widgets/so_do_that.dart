import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../data/floor_map.dart';
import '../services/api_dinh_vi.dart';
import '../services/la_ban.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_theme.dart';
import 'the_khu_vuc.dart';

/// Hai lớp vẽ tách rời: lớp tĩnh chỉ vẽ lại khi dữ liệu/bộ lọc đổi; lớp động
/// nghe thẳng la bàn và vị trí qua `repaint:` nên số đọc từ kế (10–50 lần/giây)
/// không dựng lại widget nào.
class SoDoMatBang extends StatefulWidget {
  /// Nhóm đang lọc, null là tất cả. Ngoài nhóm thì làm mờ chứ không ẩn.
  final String? loc;

  const SoDoMatBang({super.key, this.loc});

  @override
  State<SoDoMatBang> createState() => _SoDoMatBangState();
}

class _SoDoMatBangState extends State<SoDoMatBang> {
  final _laBan = LaBan()..batDau();

  @override
  void dispose() {
    _laBan.dispose();
    super.dispose();
  }

  void _cham(Offset p, double rong, TheoDoiViTri theoDoi) {
    final ds = theoDoi.banDo;
    if (ds.isEmpty) return;
    final met = SoDoThat.sangMet(p, rong);
    DiemThamChieu? gan;
    var min = 12.0;
    for (final d in ds) {
      final l = (Offset(d.x, d.y) - met).distance;
      if (l < min) {
        min = l;
        gan = d;
      }
    }
    if (gan == null) return;
    for (final k in theoDoi.khuVuc) {
      if (k.nhom == gan.nhom) {
        moKhuVuc(context, k, rpId: gan.rpId);
        return;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theoDoi = TheoDoiViTriScope.of(context);
    final m = Mau.of(context);
    final toi = Theme.of(context).brightness == Brightness.dark;
    final scaler = MediaQuery.textScalerOf(context);

    return AspectRatio(
      aspectRatio: SoDoThat.rongPx / SoDoThat.caoPx,
      child: LayoutBuilder(builder: (context, c) {
        final rong = c.maxWidth;
        return GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapUp: (e) => _cham(e.localPosition, rong, theoDoi),
          child: Stack(
            fit: StackFit.expand,
            children: [
              // Tối: đảo RGB, giữ alpha — nét vẽ sáng trên nền tối.
              toi
                  ? const ColorFiltered(
                      colorFilter: ColorFilter.matrix(<double>[
                        -1, 0, 0, 0, 255, //
                        0, -1, 0, 0, 255, //
                        0, 0, -1, 0, 255, //
                        0, 0, 0, 1, 0, //
                      ]),
                      child: Image(
                          image: AssetImage(SoDoThat.anh), fit: BoxFit.fill),
                    )
                  : const Image(
                      image: AssetImage(SoDoThat.anh), fit: BoxFit.fill),
              RepaintBoundary(
                child: CustomPaint(
                  painter: _LopTinh(
                    diem: theoDoi.banDo,
                    loc: widget.loc,
                    mau: m.nhan,
                    chu: m.chu,
                    scaler: scaler,
                  ),
                ),
              ),
              RepaintBoundary(
                child: CustomPaint(
                  painter: _LopDong(
                    theoDoi: theoDoi,
                    laBan: _laBan,
                    mau: m.nhan,
                    dich: m.dich,
                  ),
                ),
              ),
            ],
          ),
        );
      }),
    );
  }
}

double _tiLe(Size s) => s.width / SoDoThat.rongPx;

class _LopTinh extends CustomPainter {
  final List<DiemThamChieu> diem;
  final String? loc;
  final Color mau;
  final Color chu;
  final TextScaler scaler;

  _LopTinh({
    required this.diem,
    required this.loc,
    required this.mau,
    required this.chu,
    required this.scaler,
  });

  static const _bangMau = [
    Color(0xFF4C78A8),
    Color(0xFFF58518),
    Color(0xFF54A24B),
    Color(0xFFE45756),
    Color(0xFF72B7B2),
    Color(0xFFEECA3B),
    Color(0xFFB279A2),
    Color(0xFFFF9DA6),
    Color(0xFF9D755D),
    Color(0xFFBAB0AC),
    Color(0xFF7970BF),
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final s = _tiLe(size);
    final rong = size.width;
    final ten = ({for (final d in diem) d.nhom}.toList()..sort());
    Color mauNhom(String n) {
      final i = ten.indexOf(n);
      return i < 0 ? mau : _bangMau[i % _bangMau.length];
    }

    final l = loc;
    if (l != null) {
      // Quầng chỉ hiện khi lọc: bật cả 11 nhóm thì sàn phủ kín màu.
      final son = Paint()..color = mauNhom(l).withValues(alpha: 0.3);
      final r = SoDoThat.banKinhQuangM * SoDoThat.pxMoiMetX * s;
      for (final d in diem) {
        if (d.nhom != l) continue;
        canvas.drawCircle(SoDoThat.sangKhung(d.x, d.y, rong), r, son);
      }
    }

    final r = (4.5 * s).clamp(2.0, 4.5);
    for (final d in diem) {
      final chon = l == null || d.nhom == l;
      final c = l == null ? mau : mauNhom(d.nhom);
      canvas.drawCircle(
        SoDoThat.sangKhung(d.x, d.y, rong),
        chon ? r : r * 0.7,
        Paint()..color = (chon ? c : chu).withValues(alpha: chon ? 0.75 : 0.18),
      );
    }

    _veNhan(canvas, rong, s, l);
    _veThuoc(canvas, size, s);
  }

  /// Nhãn đặt trên chấm, bỏ nhãn trùng tên đứng gần nhau (14 điểm "Cầu thang"
  /// không cần 14 nhãn) và dời xuống khi chồng lên nhau. Kẹp trong khung để
  /// cụm sát mép không bị cụt ("Kh…" của CTK45).
  void _veNhan(Canvas canvas, double rong, double s, String? l) {
    final co = (15 * s).clamp(7.0, 12.0);
    final cao = co * 1.6;
    final sap = [
      for (final d in diem)
        if (d.nhom.isNotEmpty) (d.nhom, SoDoThat.sangKhung(d.x, d.y, rong)),
    ]..sort((a, b) => a.$2.dy != b.$2.dy
        ? a.$2.dy.compareTo(b.$2.dy)
        : a.$2.dx.compareTo(b.$2.dx));

    final daDat = <Offset>[];
    final daDatTen = <(String, Offset)>[];
    final cache = <String, TextPainter>{};
    for (final (nhom, tam) in sap) {
      if (daDatTen
          .any((e) => e.$1 == nhom && (e.$2 - tam).distance < rong * 0.2)) {
        continue;
      }
      daDatTen.add((nhom, tam));
      var p = tam;
      for (final q in daDat) {
        if ((p.dx - q.dx).abs() < rong * 0.16 && (p.dy - q.dy).abs() < cao) {
          p = Offset(p.dx, q.dy + cao);
        }
      }
      daDat.add(p);

      final mo = l == null || l == nhom ? 1.0 : 0.3;
      final tp = cache.putIfAbsent(
          '$nhom$mo',
          () => TextPainter(
                text: TextSpan(
                  text: nhom,
                  style: TextStyle(
                    fontSize: co,
                    fontWeight: FontWeight.w600,
                    color: chu.withValues(alpha: 0.85 * mo),
                    shadows: [
                      Shadow(
                          color: chu.computeLuminance() > 0.5
                              ? const Color(0xCC000000)
                              : const Color(0xE6FFFFFF),
                          blurRadius: 3),
                    ],
                  ),
                ),
                textDirection: TextDirection.ltr,
                textScaler: scaler,
                maxLines: 1,
                ellipsis: '…',
              )..layout(maxWidth: rong));
      final x = (p.dx - tp.width / 2)
          .clamp(0.0, math.max(0.0, rong - tp.width))
          .toDouble();
      tp.paint(canvas, Offset(x, p.dy - co - tp.height / 2));
    }
  }

  void _veThuoc(Canvas canvas, Size size, double s) {
    const daiM = 10.0;
    final dai = daiM * SoDoThat.pxMoiMetX * s;
    final trai = size.width * 0.24;
    final y = size.height - size.width * 0.03;
    final c = chu.withValues(alpha: 0.7);
    canvas.drawLine(
        Offset(trai, y),
        Offset(trai + dai, y),
        Paint()
          ..color = c
          ..strokeWidth = (3 * s).clamp(1.4, 3.0));
    final tp = TextPainter(
      text: TextSpan(
        text: '${daiM.toInt()} m',
        style: TextStyle(
            color: c,
            fontSize: (13 * s).clamp(7.0, 12.0),
            fontWeight: FontWeight.w600),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, Offset(trai + (dai - tp.width) / 2, y - tp.height - 2));
  }

  @override
  bool shouldRepaint(_LopTinh cu) =>
      cu.diem != diem ||
      cu.loc != loc ||
      cu.mau != mau ||
      cu.chu != chu ||
      cu.scaler != scaler;
}

class _LopDong extends CustomPainter {
  final TheoDoiViTri theoDoi;
  final LaBan laBan;
  final Color mau;
  final Color dich;

  _LopDong({
    required this.theoDoi,
    required this.laBan,
    required this.mau,
    required this.dich,
  }) : super(repaint: Listenable.merge([theoDoi, laBan]));

  /// Khoảng cách giữa hai chấm của tuyến, tính theo đơn vị sơ đồ để mật độ chấm
  /// giữ nguyên khi phóng to.
  static const _buoc = 1.2;

  @override
  void paint(Canvas canvas, Size size) {
    final s = _tiLe(size);
    final rong = size.width;
    final tuyen = theoDoi.daToi ? null : theoDoi.tuyen?.duongDi;
    if (tuyen != null && tuyen.length >= 2) _veTuyen(canvas, tuyen, rong, s);

    final vt = theoDoi.viTri;
    if (vt == null) return;
    final goc = SoDoThat.sangKhung(vt.xGop, vt.yGop, rong);

    final h = laBan.huongSoDo;
    if (h != null) {
      // Trục y canvas hướng xuống nên 0° (trục +y sơ đồ, hướng lên) là -π/2.
      final ban = (46 * s).clamp(22.0, 46.0);
      final giua = (h - 90) * math.pi / 180;
      const mo = LaBan.nuaGocMoDo * math.pi / 180;
      final vung = Rect.fromCircle(center: goc, radius: ban);
      canvas.drawPath(
        Path()
          ..moveTo(goc.dx, goc.dy)
          ..arcTo(vung, giua - mo, mo * 2, false)
          ..close(),
        Paint()
          ..shader = RadialGradient(
            colors: [mau.withValues(alpha: 0.45), mau.withValues(alpha: 0)],
          ).createShader(vung),
      );
    }

    final r = (11 * s).clamp(6.0, 11.0);
    canvas.drawCircle(goc, r * 2, Paint()..color = mau.withValues(alpha: 0.18));
    canvas.drawCircle(goc, r, Paint()..color = Colors.white);
    canvas.drawCircle(goc, r * 0.68, Paint()..color = mau);
  }

  void _veTuyen(
      Canvas canvas, List<DiemThamChieu> tuyen, double rong, double s) {
    final r = (5 * s).clamp(2.5, 5.0);
    final son = Paint()..color = mau;
    // Mang phần dư sang chặng kế để chỗ gãy không có hai chấm dính nhau.
    var du = 0.0;
    for (var i = 0; i < tuyen.length - 1; i++) {
      final a = tuyen[i], b = tuyen[i + 1];
      final dai =
          math.sqrt((b.x - a.x) * (b.x - a.x) + (b.y - a.y) * (b.y - a.y));
      if (dai == 0) continue;
      for (var t = du; t < dai; t += _buoc) {
        final k = t / dai;
        canvas.drawCircle(
          SoDoThat.sangKhung(
              a.x + (b.x - a.x) * k, a.y + (b.y - a.y) * k, rong),
          r * 0.55,
          son,
        );
      }
      du = (du - dai) % _buoc;
    }
    final cuoi = SoDoThat.sangKhung(tuyen.last.x, tuyen.last.y, rong);
    canvas.drawCircle(cuoi, r * 1.4, Paint()..color = dich);
    canvas.drawCircle(
      cuoi,
      r * 1.4,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = r * 0.5
        ..color = Colors.white,
    );
  }

  @override
  bool shouldRepaint(_LopDong cu) =>
      cu.theoDoi != theoDoi ||
      cu.laBan != laBan ||
      cu.mau != mau ||
      cu.dich != dich;
}
