import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart' as intl;
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;

import '../data/floor_map.dart';
import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_theme.dart';
import '../widgets/chung.dart';
import '../widgets/nhan_noi.dart';
import '../widgets/so_do_that.dart';
import '../widgets/the_khu_vuc.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen>
    with SingleTickerProviderStateMixin {
  static const _phongMacDinh = 2.4;
  static const _phongMin = 0.8;
  static const _phongMax = 12.0;
  static const _le = 12.0;

  /// Mức phóng tối thiểu để hiện nhãn cấp 1, 2, 3.
  static const _nguongCap = [0.0, 0.0, 2.0, 4.0];

  String? _loc;
  bool _hienDiem = true;
  bool _hienNhan = true;
  final _bienDoi = TransformationController();
  Size? _khung;

  /// Đã căn theo vị trí thật chưa; người dùng tự kéo/chụm/xoay thì thôi không căn nữa.
  bool _daCanh = false;

  Matrix4 _batDau = Matrix4.identity();
  Offset _tamBatDau = Offset.zero;

  /// Kéo rồi buông thì bản đồ trôi thêm một đoạn ngắn: vận tốc còn 1/e sau [_tau] giây.
  static const _tau = 0.18;

  /// Hai ngón phải xoay quá ~13° mới bắt đầu xoay bản đồ: chụm để phóng không làm bản đồ nghiêng lệch.
  static const _nguongXoay = 0.22;

  /// Bản đồ quay chậm hơn hai ngón, cho dễ chỉnh hướng.
  static const _heSoXoay = 0.7;

  late final _troi = createTicker(_buocTroi);
  Duration _lucTruoc = Duration.zero;
  Offset _vanToc = Offset.zero;
  Offset _tam = Offset.zero;
  bool _dangVeHuongDau = false;

  /// Góc xoay của hai ngón lúc vượt ngưỡng; null khi chưa xoay.
  double? _buXoay;

  /// Góc hai ngón đã gỡ bước nhảy 2π: Flutter trả góc trong (−π, π] nên qua mốc 180° góc nhảy một vòng,
  /// nhân [_heSoXoay] thì thành cú giật thấy được.
  double _gocNgon = 0;

  @override
  void dispose() {
    _troi.dispose();
    _bienDoi.dispose();
    super.dispose();
  }

  /// Dịch [dich], xoay [xoay] và phóng [phong] lần quanh điểm [tam] trên màn hình.
  void _ap(Offset tam, Offset dich, double xoay, double phong) {
    _bienDoi.value =
        Matrix4.translationValues(tam.dx + dich.dx, tam.dy + dich.dy, 0)
          ..multiply(Matrix4.rotationZ(xoay))
          ..multiply(Matrix4.diagonal3Values(phong, phong, 1))
          ..multiply(Matrix4.translationValues(-tam.dx, -tam.dy, 0))
          ..multiply(_bienDoi.value);
  }

  /// Giữ điểm giữa màn hình trong khối thư viện (x ±45,5, y −2 → 76 đơn vị lưới), để kéo hay vuốt mạnh
  /// không đẩy bản đồ ra khỏi màn; chạm biên thì dừng trôi.
  void _kep() {
    final v = _khung;
    if (v == null) return;
    final rong = v.width - 2 * _le;
    final g = _goc(v);
    final hop = Rect.fromPoints(g + SoDoThat.sangKhung(-45.5, 76, rong),
        g + SoDoThat.sangKhung(45.5, -2, rong));
    final giua = Offset(v.width / 2, v.height / 2);
    final m =
        MatrixUtils.transformPoint(Matrix4.inverted(_bienDoi.value), giua);
    final kep = Offset(
        m.dx.clamp(hop.left, hop.right), m.dy.clamp(hop.top, hop.bottom));
    if (kep == m) return;
    final d = giua - MatrixUtils.transformPoint(_bienDoi.value, kep);
    _bienDoi.value = Matrix4.translationValues(d.dx, d.dy, 0)
      ..multiply(_bienDoi.value);
    _vanToc = Offset.zero;
  }

  void _chayTroi() {
    _lucTruoc = Duration.zero;
    if (!_troi.isActive) _troi.start();
  }

  void _buocTroi(Duration troiQua) {
    final dt = (troiQua - _lucTruoc).inMicroseconds / 1e6;
    _lucTruoc = troiQua;
    if (dt <= 0) return;
    if (_dangVeHuongDau) {
      final g = _gocXoay;
      final xong = g.abs() < 0.003;
      _ap(_tam, Offset.zero, xong ? -g : -g * (1 - math.exp(-dt / 0.08)), 1);
      if (xong) {
        _dangVeHuongDau = false;
        _troi.stop();
      }
      return;
    }
    final f = math.exp(-dt / _tau);
    // Quãng đi trong dt của vận tốc giảm theo hàm mũ: v·τ·(1 − e^(−dt/τ)).
    _ap(Offset.zero, _vanToc * _tau * (1 - f), 0, 1);
    _kep();
    _vanToc *= f;
    if (_vanToc.distance < 20) _troi.stop();
  }

  static Offset _goc(Size v) {
    final cao = (v.width - 2 * _le) * SoDoThat.khungCao / SoDoThat.khungRong;
    return Offset(_le, (v.height - cao) / 2);
  }

  /// Phóng [_phongMacDinh] lần quanh vị trí hiện tại (chưa có thì giữa khối thư viện),
  /// kẹp để sơ đồ không trượt khỏi khung nhìn.
  void _canh(Size v, TheoDoiViTri theoDoi) {
    final rong = v.width - 2 * _le;
    final cao = rong * SoDoThat.khungCao / SoDoThat.khungRong;
    final goc = _goc(v);
    final vt = theoDoi.viTri;
    final p = goc +
        (vt == null
            ? SoDoThat.sangKhung(SoDoThat.tamToaX, SoDoThat.tamToaY, rong)
            : SoDoThat.sangKhung(vt.xGop, vt.yGop, rong));
    const s = _phongMacDinh;
    final tx = (v.width / 2 - p.dx * s).clamp(v.width * (1 - s), 0.0);
    // Sơ đồ chỉ là một dải giữa khung nhìn: thấp hơn màn thì căn giữa dải, cao
    // hơn thì kẹp để mép dải không lộ nền trống.
    final ty = cao * s <= v.height
        ? v.height / 2 - (goc.dy + cao / 2) * s
        : (v.height / 2 - p.dy * s)
            .clamp(v.height - (goc.dy + cao) * s, -goc.dy * s);
    _bienDoi.value = Matrix4.diagonal3Values(s, s, 1)
      ..setTranslationRaw(tx, ty, 0);
    _daCanh = vt != null;
  }

  /// Một cử chỉ gộp kéo, chụm và xoay hai ngón, quanh điểm giữa các ngón như Google Maps.
  void _batDauCham(ScaleStartDetails d) {
    _troi.stop();
    _dangVeHuongDau = false;
    _daCanh = true;
    _batDau = _bienDoi.value.clone();
    _tamBatDau = d.localFocalPoint;
    _buXoay = null;
    _gocNgon = 0;
  }

  void _doiCham(ScaleUpdateDetails d) {
    _gocNgon += (d.rotation - _gocNgon + math.pi) % (2 * math.pi) - math.pi;
    if (_buXoay == null && d.pointerCount > 1 && _gocNgon.abs() > _nguongXoay) {
      _buXoay = _gocNgon;
    }
    final xoay = (_gocNgon - (_buXoay ?? _gocNgon)) * _heSoXoay;
    final s0 = _batDau.getMaxScaleOnAxis();
    final s = (s0 * d.scale).clamp(_phongMin, _phongMax) / s0;
    _bienDoi.value = Matrix4.translationValues(
        d.localFocalPoint.dx, d.localFocalPoint.dy, 0)
      ..multiply(Matrix4.rotationZ(xoay))
      ..multiply(Matrix4.diagonal3Values(s, s, 1))
      ..multiply(Matrix4.translationValues(-_tamBatDau.dx, -_tamBatDau.dy, 0))
      ..multiply(_batDau);
    _kep();
  }

  /// Chỉ trôi khi kéo một ngón; xoay hay chụm xong thì dừng ngay.
  void _ketThucCham(ScaleEndDetails d) {
    if (_buXoay != null || d.scaleVelocity.abs() > 0.05) return;
    final v = d.velocity.pixelsPerSecond;
    _vanToc = v.distance > 2500 ? v / v.distance * 2500 : v;
    _chayTroi();
  }

  double get _gocXoay =>
      math.atan2(_bienDoi.value.entry(1, 0), _bienDoi.value.entry(0, 0));

  void _veHuongDau() {
    final v = _khung;
    if (v == null) return;
    _tam = Offset(v.width / 2, v.height / 2);
    _dangVeHuongDau = true;
    _chayTroi();
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final theoDoi = TheoDoiViTriScope.of(context);
    final nhom = [
      for (final k in theoDoi.khuVuc)
        if (!k.theoToaDo) k.nhom
    ]..sort();

    return Stack(
      children: [
        Positioned.fill(
          child: LayoutBuilder(builder: (context, c) {
            final v = c.biggest;
            if (_khung == null || (!_daCanh && theoDoi.viTri != null)) {
              _khung = v;
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (mounted) _canh(v, theoDoi);
              });
            }
            final goc = _goc(v);
            final rong = v.width - 2 * _le;
            final soDo = Stack(children: [
              Positioned(
                left: goc.dx,
                top: goc.dy,
                width: rong,
                height: rong * SoDoThat.khungCao / SoDoThat.khungRong,
                child: SoDoMatBang(
                    loc: _loc, hienDiem: _hienDiem, bienDoi: _bienDoi),
              ),
            ]);
            return Semantics(
              label: t.mapFloorPlanLabel,
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onScaleStart: _batDauCham,
                onScaleUpdate: _doiCham,
                onScaleEnd: _ketThucCham,
                child: ClipRect(
                  child: AnimatedBuilder(
                    animation: _bienDoi,
                    child: soDo,
                    builder: (context, soDo) => Stack(children: [
                      Positioned.fill(
                          child: Transform(
                              transform: _bienDoi.value, child: soDo)),
                      if (_hienNhan)
                        ..._lopNhan(goc, rong, t.localeName, theoDoi),
                    ]),
                  ),
                ),
              ),
            );
          }),
        ),
        SafeArea(
          bottom: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 10, 20, 0),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: PillViTri(theoDoi: theoDoi),
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Menu lớp kiểu Google Maps: nhóm "Hiển thị" bật tắt lớp vẽ, nhóm "Khu vực" lọc.
                    lg.GlassPullDownButton(
                      icon: Icon(Icons.layers_outlined,
                          color: _loc == null && _hienDiem && _hienNhan
                              ? m.chu
                              : m.nhan),
                      semanticLabel: t.mapFilter,
                      menuWidth: 250,
                      items: [
                        lg.GlassMenuLabel(title: t.mapShowSection),
                        _muc(t.mapShowPoints, Icons.scatter_plot_outlined,
                            _hienDiem, () => _hienDiem = !_hienDiem),
                        _muc(t.mapShowLabels, Icons.label_outline_rounded,
                            _hienNhan, () => _hienNhan = !_hienNhan),
                        const lg.GlassMenuDivider(),
                        lg.GlassMenuLabel(title: t.mapAreaSection),
                        for (final n in [null, ...nhom])
                          _muc(n ?? t.mapFilterAll, null, _loc == n,
                              () => _loc = n),
                      ],
                    ),
                  ],
                ),
                if (theoDoi.tuyen != null && theoDoi.dichTuyen != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: _TheTuyen(theoDoi: theoDoi),
                  ),
                // Chỉ hiện khi đã xoay: kim chỉ hướng đầu của sơ đồ, chạm để quay về.
                AnimatedBuilder(
                  animation: _bienDoi,
                  builder: (context, _) => _gocXoay.abs() < 0.02
                      ? const SizedBox.shrink()
                      : Align(
                          alignment: Alignment.centerRight,
                          child: Padding(
                            padding: const EdgeInsets.only(top: 10),
                            child: KinhNoi(
                              padding: EdgeInsets.zero,
                              child: IconButton(
                                tooltip: t.mapResetRotation,
                                onPressed: _veHuongDau,
                                icon: Transform.rotate(
                                  angle: _gocXoay,
                                  child: Icon(Icons.navigation_rounded,
                                      color: m.nhan),
                                ),
                              ),
                            ),
                          ),
                        ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _muc(String ten, IconData? icon, bool chon, VoidCallback doi) {
    final m = Mau.of(context);
    return lg.GlassMenuItem(
      title: ten,
      icon: icon == null ? null : Icon(icon),
      trailing:
          chon ? Icon(Icons.check_rounded, size: 18, color: m.nhan) : null,
      onTap: () => setState(doi),
    );
  }

  /// Nhãn đặt theo toạ độ màn hình sau phép biến đổi, nên không xoay, không phóng theo sơ đồ.
  /// Cấp nhỏ đặt trước; nhãn đè lên nhãn đã đặt thì bỏ, như Google Maps.
  List<Widget> _lopNhan(
      Offset goc, double rong, String ngonNgu, TheoDoiViTri theoDoi) {
    final mt = _bienDoi.value;
    final k = mt.getMaxScaleOnAxis();
    final ds = [
      for (final n in theoDoi.nhan)
        if (k >= _nguongCap[n.cap]) n
    ]..sort((a, b) => a.cap.compareTo(b.cap));
    final daDat = <Rect>[];
    final ra = <Widget>[];
    for (final n in ds) {
      final ten = ngonNgu == 'en' ? n.en ?? n.ten : n.ten;
      final p = MatrixUtils.transformPoint(
          mt, goc + SoDoThat.sangKhung(n.x, n.y, rong));
      final to = n.cap == 1;
      final r = NhanNoi.banKinh(to);
      final o =
          Rect.fromLTWH(p.dx - r, p.dy - r, NhanNoi.rongUoc(ten, to), 2 * r);
      if (daDat.any(o.overlaps)) continue;
      daDat.add(o);
      final kv = _khuVucCua(n, theoDoi);
      const dem = 4.0;
      ra.add(Positioned(
        left: p.dx - r - dem,
        top: p.dy - r - dem,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: kv == null ? null : () => moKhuVuc(context, kv),
          child: Padding(
            padding: const EdgeInsets.all(dem),
            child: NhanNoi(ten: ten, icon: n.icon, to: to),
          ),
        ),
      ));
    }
    return ra;
  }

  static KhuVuc? _khuVucCua(NhanSoDo n, TheoDoiViTri theoDoi) {
    final ten = n.nhom ?? n.ten;
    for (final k in theoDoi.khuVuc) {
      if (k.nhom == ten) return k;
    }
    return null;
  }
}

class _TheTuyen extends StatelessWidget {
  final TheoDoiViTri theoDoi;
  const _TheTuyen({required this.theoDoi});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final dich = theoDoi.dichTuyen!.nhom;
    final met = intl.NumberFormat('#0.#', t.localeName)
        .format(theoDoi.tuyen!.quangDuongM);
    return KinhNoi(
      height: null,
      padding: const EdgeInsets.fromLTRB(16, 4, 4, 4),
      child: Row(
        children: [
          Icon(
              theoDoi.daToi
                  ? Icons.flag_rounded
                  : Icons.directions_walk_rounded,
              color: theoDoi.daToi ? m.dich : m.nhan),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              theoDoi.daToi ? t.mapArrived(dich) : t.mapRouteChip(met, dich),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close_rounded),
            tooltip: t.mapClearRoute,
            onPressed: theoDoi.xoaTuyen,
          ),
        ],
      ),
    );
  }
}
