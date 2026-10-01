import 'package:flutter/material.dart';
import 'package:intl/intl.dart' as intl;
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;

import '../data/floor_map.dart';
import '../l10n/app_localizations.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_theme.dart';
import '../widgets/chung.dart';
import '../widgets/so_do_that.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  static const _phongMacDinh = 2.4;
  static const _le = 12.0;

  String? _loc;
  final _bienDoi = TransformationController();
  Size? _khung;

  /// Đã căn theo vị trí thật chưa; người dùng tự kéo/chụm thì thôi không căn nữa.
  bool _daCanh = false;

  @override
  void dispose() {
    _bienDoi.dispose();
    super.dispose();
  }

  /// Phóng [_phongMacDinh] lần quanh vị trí hiện tại (chưa có thì giữa khối thư viện),
  /// kẹp để sơ đồ không trượt khỏi khung nhìn.
  void _canh(Size v, TheoDoiViTri theoDoi) {
    final rong = v.width - 2 * _le;
    final cao = rong * SoDoThat.khungCao / SoDoThat.khungRong;
    final goc = Offset(_le, (v.height - cao) / 2);
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

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final theoDoi = TheoDoiViTriScope.of(context);
    final nhom = [for (final k in theoDoi.khuVuc) k.nhom]..sort();

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
            return Semantics(
              label: t.mapFloorPlanLabel,
              child: InteractiveViewer(
                transformationController: _bienDoi,
                maxScale: 12,
                onInteractionStart: (_) => _daCanh = true,
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: _le),
                    child: SoDoMatBang(loc: _loc, bienDoi: _bienDoi),
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
                    lg.GlassPullDownButton(
                      icon: Icon(Icons.filter_list_rounded,
                          color: _loc == null ? m.chu : m.nhan),
                      semanticLabel: t.mapFilter,
                      menuWidth: 240,
                      items: [
                        for (final n in [null, ...nhom])
                          lg.GlassMenuItem(
                            title: n ?? t.mapFilterAll,
                            trailing: _loc == n
                                ? Icon(Icons.check_rounded,
                                    size: 18, color: m.nhan)
                                : null,
                            onTap: () => setState(() => _loc = n),
                          ),
                      ],
                    ),
                  ],
                ),
                if (theoDoi.tuyen != null && theoDoi.dichTuyen != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: _TheTuyen(theoDoi: theoDoi),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
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
