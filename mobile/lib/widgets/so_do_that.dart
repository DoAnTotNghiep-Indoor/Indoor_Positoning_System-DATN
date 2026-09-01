import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../data/floor_map.dart';
import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../screens/area_detail_screen.dart';
import 'tap_feedback.dart';
import '../services/api_dinh_vi.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_colors.dart';

/// Sơ đồ mặt bằng thật của tầng 1, kèm chấm vị trí đang đứng.
///
/// Dùng bản số hoá `Map.png` và đúng hệ mét mô hình trả về, nên chấm vị trí rơi
/// vào chỗ thật — khác [FloorPlan] là sơ đồ vẽ tay chỉ để trình bày.
class SoDoMatBang extends StatefulWidget {
  /// Nhóm khu vực đang lọc, null là hiện tất cả. Chấm và nhãn ngoài nhóm bị
  /// làm mờ chứ không ẩn — ẩn đi thì người dùng mất luôn ngữ cảnh xung quanh.
  final String? loc;

  const SoDoMatBang({super.key, this.loc});

  @override
  State<SoDoMatBang> createState() => _SoDoMatBangState();
}

class _SoDoMatBangState extends State<SoDoMatBang> {
  bool _daGoi = false;

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
        final k = _khuVucTaiDiem(e.localPosition, theoDoi.khuVuc, rong);
        if (k != null) _hienTom(context, k);
      },
      child: Stack(
        children: [
        // Chế độ tối đảo RGB chứ không đổi màu cả khối: nét đen thành trắng,
        // chấm lưới thành xám đậm, giữ đúng thứ tự tương phản của bản sáng.
        // Hàng alpha không đổi nên nền vẫn trong suốt.
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

          // Chấm điểm tham chiếu và tuyến đường vẽ trên cùng một canvas: cả
          // hai đều là hình học thuần, tách ra thành widget thì mỗi chấm là
          // một Positioned và 40 chấm thành 40 lớp cho cùng một khung hình.
          Positioned.fill(
            child: CustomPaint(
              painter: _NetSoDo(
                diem: theoDoi.banDo,
                tuyen: theoDoi.tuyen?.duongDi ?? const [],
                loc: widget.loc,
                rong: rong,
                mau: AppColors.accentOf(context),
                muc: toi ? AppColors.inkDark : AppColors.ink,
              ),
            ),
          ),

        for (final n in _viTriNhan(theoDoi.khuVuc, rong))
          _nhan(n.$1.nhom, n.$2, rong, toi, _moNhat(n.$1.nhom)),

          if (vt != null)
            _cham(SoDoThat.sangKhung(vt.xGop, vt.yGop, rong), rong),
        ],
      ),
    );
  }

  /// Chỗ đặt nhãn: MỘT NHÃN MỖI CỤM, đã đẩy ra cho khỏi chồng nhau.
  ///
  /// Mỗi cụm chứ không phải mỗi nhóm — xem [KhuVuc.tamCum]. Trước đây nhãn đặt
  /// ở trọng tâm cả nhóm nên "Hành lang" hạ xuống giữa sảnh, cách cả hai điểm
  /// hành lang thật 42 m.
  ///
  /// Nhãn vẫn có thể trùng chỗ vì trọng tâm của "Bàn thủ thư" và "Cầu thang
  /// tầng 2" chỉ cách nhau vài mét, đọc thành một dòng vô nghĩa. Xếp theo chiều
  /// dọc rồi đẩy nhãn sau xuống dưới nhãn trước nếu quá gần.
  List<(KhuVuc, Offset)> _viTriNhan(List<KhuVuc> khu, double rong) {
    final cao = _caoChu(rong) * 1.6;
    final ra = <(KhuVuc, Offset)>[];

    final sap = [
      for (final k in khu)
        for (final t in k.tamCum)
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

  /// Khu vực gần chỗ vừa chạm nhất, hoặc null nếu chạm ra ngoài toà nhà.
  KhuVuc? _khuVucTaiDiem(Offset cham, List<KhuVuc> khu, double rong) {
    if (khu.isEmpty) return null;

    // Đổi ngược về mét rồi mới so khoảng cách, để ngưỡng "quá xa" tính bằng mét
    // chứ không bằng pixel — pixel đổi theo cỡ màn hình.
    final met = SoDoThat.sangMet(cham, rong);

    var gan = khu.first;
    var min = double.infinity;
    for (final k in khu) {
      final l = k.khoangCach(met.dx, met.dy);
      if (l < min) {
        min = l;
        gan = k;
      }
    }
    // Chạm cách mọi khu vực quá xa thì coi như chạm nhầm, không mở gì cả.
    return min <= 12 ? gan : null;
  }


  /// Nhãn ngoài nhóm đang lọc mờ đi, nhưng không mờ hẳn: vẫn phải đọc được để
  /// biết mình đang ở đâu trên sơ đồ.
  double _moNhat(String nhom) =>
      widget.loc == null || widget.loc == nhom ? 1.0 : 0.28;

  Widget _nhan(String chu, Offset tam, double rong, bool toi, double mo) {
    final co = _caoChu(rong);
    return Positioned(
      left: 0,
      top: tam.dy - co,
      width: tam.dx * 2,
      child: Text(
        chu,
        textAlign: TextAlign.center,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          fontSize: co,
          fontWeight: FontWeight.w600,
          color: (toi ? AppColors.inkDark : AppColors.ink)
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

/// Tấm tóm tắt khi chạm vào một khu vực trên sơ đồ.
///
/// Học theo bottom sheet của CTK45: tên, mô tả, rồi nút mở màn chi tiết. Chạm
/// thẳng vào bản đồ là cách tự nhiên nhất để hỏi "chỗ này là chỗ nào".
void _hienTom(BuildContext context, KhuVuc k) {
  showModalBottomSheet<void>(
    context: context,
    backgroundColor: Theme.of(context).colorScheme.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (sheet) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(k.icon, size: 22, color: AppColors.accentOf(sheet)),
                const SizedBox(width: 10),
                Expanded(
                  child: Semantics(
                    header: true,
                    child: Text(k.nhom,
                        style: Theme.of(sheet).textTheme.titleLarge),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              k.moTa,
              style: TextStyle(
                fontSize: 13.5,
                height: 1.4,
                color: AppColors.inkOf(sheet).withValues(alpha: 0.72),
              ),
            ),
            const SizedBox(height: 18),
            TapFeedback(
              semanticLabel: L.of(sheet).a11yOpenArea,
              onTap: () {
                Navigator.of(sheet).pop();
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => AreaDetailScreen(khuVuc: k),
                  ),
                );
              },
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: Theme.of(sheet).colorScheme.primary,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Text(
                  L.of(sheet).mapOpenDetail,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: Theme.of(sheet).colorScheme.onPrimary,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

/// Chấm 40 điểm tham chiếu và tuyến đường, vẽ thẳng lên canvas.
///
/// Tuyến vẽ bằng chuỗi chấm tròn cách đều theo mét thật, không phải đường liền:
/// khoảng hở giữa các chấm nói rằng đây là tuyến nối các điểm đã đo chứ không
/// phải một lối đi liên tục đã khảo sát từng centimet.
class _NetSoDo extends CustomPainter {
  final List<DiemThamChieu> diem;
  final List<DiemThamChieu> tuyen;
  final String? loc;
  final double rong;
  final Color mau;
  final Color muc;

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
  });

  @override
  void paint(Canvas canvas, Size size) {
    _veQuang(canvas);
    _veDiem(canvas);
    _veTuyen(canvas);
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

  void _veThuoc(Canvas canvas, Size size) {
    const daiM = 10.0;
    final dai = daiM * SoDoThat.pxMoiMetX * (rong / SoDoThat.rongPx);
    final le = rong * 0.03;
    final y = size.height - le;

    canvas.drawLine(
      Offset(le, y),
      Offset(le + dai, y),
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
    chu.paint(canvas, Offset(le + (dai - chu.width) / 2, y - chu.height - 2));
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

    // Đi dọc từng chặng và rải chấm theo mét, mang phần dư sang chặng kế tiếp.
    // Không mang dư thì mỗi đỉnh gãy lại khởi động lại nhịp, và chỗ nối trông
    // như hai chấm dính nhau.
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
      cu.mau != mau;
}
