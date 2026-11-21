import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:panorama_viewer/panorama_viewer.dart';

import '../data/toan_canh.dart';
import '../l10n/app_localizations.dart';
import '../services/la_ban.dart';
import '../theme/app_theme.dart';
import '../widgets/chung.dart';

Future<void> moToanCanh(BuildContext context, ToanCanh t) =>
    Navigator.of(context).push(MaterialPageRoute<void>(
        fullscreenDialog: true, builder: (_) => ToanCanhScreen(toanCanh: t)));

/// Ảnh 360° của một chỗ, nhân vật hướng dẫn và bong bóng lời đè lên trên.
///
/// Mặc định kéo ngón tay, mở đúng hướng người dùng đang nhìn theo la bàn. Chế độ
/// xoay máy để trình xem đọc từ kế (kinh độ 0 là hướng bắc), ta dời ảnh một góc
/// bằng phương vị của tâm ảnh để cảnh trên màn khớp cảnh trước mặt.
class ToanCanhScreen extends StatefulWidget {
  final ToanCanh toanCanh;
  const ToanCanhScreen({super.key, required this.toanCanh});

  @override
  State<ToanCanhScreen> createState() => _ToanCanhScreenState();
}

class _ToanCanhScreenState extends State<ToanCanhScreen> {
  final _laBan = LaBan();
  bool _xoayMay = false;
  bool _huongDan = false;

  /// Ảnh gốc khoảng 10.000 px giải mã mất vài giây, trong lúc đó trình xem chỉ có nền xám.
  bool _daTai = false;
  bool _loiTai = false;

  /// Hướng sơ đồ ở số đọc la bàn đầu tiên. Trình xem chỉ đọc kinh độ lúc dựng,
  /// nên có số đọc rồi thì dựng lại đúng một lần để mở đúng hướng đang nhìn.
  double? _huongDau;

  @override
  void initState() {
    super.initState();
    // Trình xem nuốt lỗi giải mã và quay vòng chờ mãi; nghe cùng luồng ảnh để
    // biết mà báo. Bộ nhớ đệm gộp hai lần resolve nên không giải mã hai lần.
    AssetImage(widget.toanCanh.anh)
        .resolve(ImageConfiguration.empty)
        .addListener(ImageStreamListener((_, __) {},
            onError: (_, __) {
          if (mounted) setState(() => _loiTai = true);
        }));
    _laBan
      ..addListener(_coHuong)
      ..batDau();
  }

  void _coHuong() {
    if (_huongDau != null || _laBan.huongSoDo == null) return;
    setState(() => _huongDau = _laBan.huongSoDo);
    _laBan.dungLai();
  }

  @override
  void dispose() {
    _laBan.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final tt = Theme.of(context).textTheme;
    final tc = widget.toanCanh;

    // Phương vị của tâm ảnh so với bắc.
    final phuongVi = (LaBan.gocBacSoDo + tc.gocTam) % 360;
    // Kéo tay: mở đúng hướng đang nhìn nếu có từ kế, không thì mở ở tâm ảnh.
    final huong = _huongDau;
    final kinhDo = _xoayMay ? -phuongVi : (huong == null ? 0.0 : huong - tc.gocTam);
    // Ảnh phủ cao/rong*360° theo chiều dọc; chừa 30° để không nhìn thấy mép cắt.
    final nuaDoc = tc.cao / tc.rong * 180;
    final gioiHan = (nuaDoc - 30).clamp(0.0, 90.0);

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          Positioned.fill(
            child: PanoramaViewer(
              // Đổi chế độ thì dựng lại trình xem để kinh độ ban đầu có hiệu lực.
              key: ValueKey((_xoayMay, _huongDau != null)),
              sensorControl: _xoayMay
                  ? SensorControl.absoluteOrientation
                  : SensorControl.none,
              longitude: kinhDo,
              // Mặc định 1 thì vuốt hết bề ngang màn chỉ quay khoảng 40°.
              sensitivity: 2.2,
              minLatitude: -gioiHan,
              maxLatitude: gioiHan,
              croppedArea: Rect.fromLTWH(0, (tc.rong / 2 - tc.cao) / 2,
                  tc.rong.toDouble(), tc.cao.toDouble()),
              croppedFullWidth: tc.rong.toDouble(),
              croppedFullHeight: tc.rong / 2,
              onImageLoad: () => setState(() => _daTai = true),
              child: Image.asset(tc.anh),
            ),
          ),
          if (_loiTai)
            Center(
              child: Text(t.panoLoadFailed,
                  style: tt.titleMedium?.copyWith(color: Colors.white)),
            )
          else if (!_daTai)
            const Center(child: CircularProgressIndicator(color: Colors.white)),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(18, 8, 18, 16),
              child: Column(
                children: [
                  Row(
                    children: [
                      _NutKinh(
                        icon: Icons.close,
                        nhan: t.panoClose,
                        bam: () => Navigator.pop(context),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        // Cùng cỡ và kiểu chữ với nhãn vị trí ngoài Trang chủ.
                        child: KinhNoi(
                          // GlassContainer đặt con ở góc trên trái, phải tự căn giữa.
                          child: Align(
                            alignment: Alignment.centerLeft,
                            child: Text(tc.ten,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: tt.titleMedium),
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                      _NutKinh(
                        icon: _xoayMay
                            ? Icons.screen_rotation_alt
                            : Icons.pan_tool_alt_outlined,
                        nhan: _xoayMay ? t.panoSensor : t.panoDrag,
                        bam: () => setState(() => _xoayMay = !_xoayMay),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      SvgPicture.asset('assets/images/huong_dan.svg',
                          width: 72, height: 84),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.fromLTRB(16, 14, 16, 6),
                          decoration: BoxDecoration(
                            color: m.the,
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: const [
                              BoxShadow(color: Color(0x40000000), blurRadius: 12),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(_huongDan ? tc.huongDan : tc.gioiThieu,
                                  style: tt.bodyLarge
                                      ?.copyWith(color: m.chu, fontSize: 15)),
                              const SizedBox(height: 6),
                              Align(
                                alignment: Alignment.centerRight,
                                child: FilledButton.tonal(
                                  style: FilledButton.styleFrom(
                                      minimumSize: const Size(0, 48)),
                                  onPressed: () =>
                                      setState(() => _huongDan = !_huongDan),
                                  child: Text(
                                      _huongDan ? t.panoIntro : t.panoTips),
                                ),
                              ),
                              const SizedBox(height: 8),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NutKinh extends StatelessWidget {
  final IconData icon;
  final String nhan;
  final VoidCallback bam;
  const _NutKinh({required this.icon, required this.nhan, required this.bam});

  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        label: nhan,
        child: Tooltip(
          message: nhan,
          // Hình tròn 44 như nhãn vị trí, nhưng vùng chạm 48 × 48 phủ cả viền
          // ngoài: chạm hụt trên ảnh 360° là thành kéo ảnh.
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: bam,
            child: SizedBox.square(
              dimension: 48,
              child: Center(
                child: KinhNoi(
                  padding: EdgeInsets.zero,
                  child: SizedBox(width: 44, child: Icon(icon, size: 22)),
                ),
              ),
            ),
          ),
        ),
      );
}
