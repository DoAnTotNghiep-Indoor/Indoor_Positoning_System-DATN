import 'package:flutter/material.dart';

import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_theme.dart';
import '../widgets/chung.dart';

class SearchScreen extends StatefulWidget {
  /// Ô nhập nằm trong thanh tab kính; màn chỉ nghe từ khoá.
  final TextEditingController tuKhoa;

  const SearchScreen({super.key, required this.tuKhoa});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  LoaiKhu? _loai;

  /// Bỏ dấu tiếng Việt để "khu doc" vẫn ra "Khu vực đọc".
  static String _khongDau(String s) {
    const co = 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ'
        'òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ';
    const khong = 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiii'
        'ooooooooooooooooouuuuuuuuuuuyyyyyd';
    final b = StringBuffer();
    for (final c in s.toLowerCase().split('')) {
      final i = co.indexOf(c);
      b.write(i < 0 ? c : khong[i]);
    }
    return b.toString();
  }

  List<KhuVuc> _loc(List<KhuVuc> ds, String tuKhoa) {
    final tu = _khongDau(tuKhoa).split(RegExp(r'\s+'))
      ..removeWhere((t) => t.isEmpty);
    return [
      for (final k in ds)
        if ((_loai == null || loaiCua(k.nhom) == _loai) &&
            tu.every(_khongDau('${k.nhom} ${k.moTa}').contains))
          k,
    ];
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final tt = Theme.of(context).textTheme;
    final theoDoi = TheoDoiViTriScope.of(context);
    final boLoc = {
      null: t.searchFilterAll,
      LoaiKhu.hocTap: t.searchFilterStudy,
      LoaiKhu.tienIch: t.searchFilterService,
      LoaiKhu.loiDi: t.searchFilterWays,
    };

    return ListenableBuilder(
      listenable: widget.tuKhoa,
      builder: (context, _) {
        final kq = _loc(theoDoi.khuVuc, widget.tuKhoa.text);
        return ListView(
          padding: EdgeInsets.fromLTRB(
              20,
              MediaQuery.paddingOf(context).top + 16,
              20,
              chuaThanhTab(context, banPhim: true)),
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final e in boLoc.entries)
                  ChoiceChip(
                    label: Text(e.value),
                    selected: _loai == e.key,
                    showCheckmark: false,
                    onSelected: (_) => setState(() => _loai = e.key),
                  ),
              ],
            ),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 10),
              child:
                  Text(t.searchResultCount(kq.length), style: tt.labelMedium),
            ),
            if (kq.isEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 48),
                child: Column(
                  children: [
                    Icon(Icons.search_off_rounded,
                        size: 44, color: Mau.of(context).chuMo),
                    const SizedBox(height: 12),
                    Text(t.searchEmpty, style: tt.titleMedium),
                    const SizedBox(height: 6),
                    Text(t.searchEmptyHint, style: tt.bodyMedium),
                  ],
                ),
              )
            else
              BeMat(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Column(
                  children: [
                    for (var i = 0; i < kq.length; i++) ...[
                      if (i > 0) const Divider(indent: 68, endIndent: 16),
                      DongKhuVuc(khuVuc: kq[i], viTri: theoDoi.viTri),
                    ],
                  ],
                ),
              ),
          ],
        );
      },
    );
  }
}
