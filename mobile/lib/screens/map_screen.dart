import 'package:flutter/material.dart';
import 'package:intl/intl.dart' as intl;
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;

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
  String? _loc;

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final theoDoi = TheoDoiViTriScope.of(context);
    final nhom = [for (final k in theoDoi.khuVuc) k.nhom]..sort();

    return Stack(
      children: [
        Positioned.fill(
          child: Semantics(
            label: t.mapFloorPlanLabel,
            child: InteractiveViewer(
              maxScale: 5,
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: SoDoMatBang(loc: _loc),
                ),
              ),
            ),
          ),
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
