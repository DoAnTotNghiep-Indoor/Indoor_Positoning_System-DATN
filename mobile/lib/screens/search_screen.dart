import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart' as lg;
import '../data/demo_data.dart';
import '../data/floor_map.dart';
import '../data/khu_vuc.dart';
import '../services/api_dinh_vi.dart';
import '../services/theo_doi_vi_tri.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../theme/app_metrics.dart';
import '../widgets/glass_card.dart';
import '../widgets/tap_feedback.dart';
import 'area_detail_screen.dart';

class SearchScreen extends StatefulWidget {
  /// Từ khoá do thanh điều hướng dưới cung cấp. Ô nhập nằm trong
  /// `GlassTabBar.searchable` nên màn hình không tự giữ TextEditingController —
  /// tránh hai ô tìm kiếm cùng hiện trên một màn.
  final String tuKhoa;

  const SearchScreen({super.key, this.tuKhoa = ''});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  /// Chỉ số trong [AreaCategory.danhSach]; 0 là "Tất cả".
  int _filter = 0;

  bool get _dangLoc => _filter != 0;

  /// Lọc cục bộ trên các khu vực thật, không gọi API: cả thư viện chỉ hơn chục
  /// khu vực. Khớp theo từng từ và bỏ dấu trước khi so, để "khu doc" vẫn ra
  /// "Khu vực đọc".
  List<KhuVuc> _ketQua(List<KhuVuc> tatCa) {
    final tokens = _khongDau(widget.tuKhoa)
        .split(RegExp(r'\s+'))
        .where((t) => t.isNotEmpty)
        .toList();

    final nhom = AreaCategory.danhSach[_filter];

    return tatCa.where((k) {
      final kho = _khongDau('${k.nhom} ${k.moTa}');
      final khopTu = tokens.isEmpty || tokens.every((t) => kho.contains(t));
      // So theo MÃ nhóm, không theo nhãn hiển thị: nhãn đổi theo ngôn ngữ nên
      // bản cũ (so với chuỗi "Học tập") lọc ra rỗng khi giao diện đang tiếng Anh.
      final khopLoc = nhom == AreaCategory.all || _nhomCua(k) == nhom;
      return khopTu && khopLoc;
    }).toList();
  }

  /// Xếp khu vực vào ba nhóm lọc sẵn có của màn này.
  static String _nhomCua(KhuVuc k) => switch (k.nhom) {
        'Khu vực tự học' || 'Khu vực đọc' || 'TV3,4' || 'Phòng tạp chí' =>
          AreaCategory.study,
        'Căn tin' || 'Hội trường thư viện' || 'Bàn thủ thư' =>
          AreaCategory.facility,
        _ => AreaCategory.internal,
      };

  /// Bỏ dấu tiếng Việt để so chuỗi. Chỉ cần đủ cho 11 tên khu vực nên tra bảng
  /// thay vì kéo cả một gói chuẩn hoá Unicode vào.
  static String _khongDau(String s) {
    const co = 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ'
        'òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ';
    const khong = 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiii'
        'ooooooooooooooooouuuuuuuuuuuyyyyyd';
    final b = StringBuffer();
    for (final c in s.trim().toLowerCase().runes) {
      final k = co.indexOf(String.fromCharCode(c));
      b.write(k < 0 ? String.fromCharCode(c) : khong[k]);
    }
    return b.toString();
  }

  String _nhanNhom(L t, String ma) => switch (ma) {
        AreaCategory.study => t.searchFilterStudy,
        AreaCategory.facility => t.searchFilterFacility,
        AreaCategory.internal => t.searchFilterInternal,
        _ => t.searchFilterAll,
      };

  @override
  Widget build(BuildContext context) {
    final chuaCho = AppMetrics.chuaChoThanhTab(context);
    final t = L.of(context);
    final theoDoi = TheoDoiViTriScope.of(context);
    final results = _ketQua(theoDoi.khuVuc);

    return SafeArea(
      bottom: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 12, 24, 0),
            child: Semantics(
              header: true,
              child: Text(t.searchTitle,
                  style: Theme.of(context).textTheme.headlineLarge),
            ),
          ),
          const SizedBox(height: 16),

          // Chiều cao 46 chứ không phải 34: chip nằm trong ListView ngang nên vùng
          // chạm bị ép theo hộp này, dưới mức tối thiểu 48dp Material / 44pt HIG.
          SizedBox(
            height: AppMetrics.caoTheoCoChu(context, coBan: 46, phanChu: 18),
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: AreaCategory.danhSach.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, i) {
                final nhan = _nhanNhom(t, AreaCategory.danhSach[i]);
                return lg.GlassChip(
                  label: nhan,
                  selected: i == _filter,
                  semanticLabel: nhan,
                  onTap: () => setState(() => _filter = i),
                );
              },
            ),
          ),

          const SizedBox(height: 18),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    // Trước đây ghép cứng chuỗi '$n kết quả' trong mã, nên ở
                    // giao diện tiếng Anh vẫn hiện tiếng Việt.
                    t.searchResultCount(results.length),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w500,
                      color: AppColors.inkOf(context).withValues(alpha: 0.6),
                    ),
                  ),
                ),
                // Lối thoát cho bộ lọc: chip đang chọn nằm trong hàng cuộn ngang
                // nên có thể đã trôi khỏi màn hình, người dùng thấy "0 kết quả"
                // mà không biết vì sao. Nút này luôn nhìn thấy khi bộ lọc đang bật.
                if (_dangLoc)
                  _NutBoLoc(onTap: () => setState(() => _filter = 0)),
              ],
            ),
          ),
          const SizedBox(height: 10),

          Expanded(
            child: results.isEmpty
                ? _KhongCoKetQua(
                    dangLoc: _dangLoc,
                    chuaCho: chuaCho,
                    onBoLoc: () => setState(() => _filter = 0),
                  )
                : ListView.separated(
                    padding: EdgeInsets.fromLTRB(16, 0, 16, chuaCho),
                    itemCount: results.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, i) => _ResultCard(
                      khuVuc: results[i],
                      viTri: theoDoi.viTri,
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

/// Trạng thái "không tìm thấy gì". Trước đây là `ListView` rỗng: gõ sai một
/// chữ là màn hình trắng trơn, không nói vì sao và không gợi ý gì.
class _KhongCoKetQua extends StatelessWidget {
  final bool dangLoc;
  final double chuaCho;
  final VoidCallback onBoLoc;

  const _KhongCoKetQua({
    required this.dangLoc,
    required this.chuaCho,
    required this.onBoLoc,
  });

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);

    // Cuộn được chứ không phải Center cứng: trên màn thấp hoặc khi bàn phím đang
    // bật, khối này cộng phần chừa cho thanh tab vượt quá chiều cao còn lại.
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(32, 24, 32, chuaCho),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Icon(
            Icons.search_off_outlined,
            size: 44,
            color: muc.withValues(alpha: 0.32),
          ),
          const SizedBox(height: 14),
          Text(
            t.searchEmpty,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: muc.withValues(alpha: 0.75),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            t.searchEmptyHint,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 13,
              height: 1.45,
              color: muc.withValues(alpha: 0.5),
            ),
          ),
          if (dangLoc) ...[
            const SizedBox(height: 18),
            _NutBoLoc(onTap: onBoLoc, noiBat: true),
          ],
        ],
      ),
    );
  }
}

/// Nút chữ "Bỏ bộ lọc".
///
/// Vùng chạm cao tối thiểu 48 dù chữ chỉ cao 15 — đây là nút chữ trần, không có
/// nền nên rất dễ bấm trượt nếu chỉ lấy đúng khung chữ làm vùng chạm.
class _NutBoLoc extends StatelessWidget {
  final VoidCallback onTap;
  final bool noiBat;

  const _NutBoLoc({required this.onTap, this.noiBat = false});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final nhan = AppColors.accentOf(context);

    return TapFeedback(
      onTap: onTap,
      semanticLabel: t.searchClearFilter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(
          minHeight: AppMetrics.vungChamToiThieu,
          minWidth: AppMetrics.vungChamToiThieu,
        ),
        child: Container(
          alignment: Alignment.center,
          padding: EdgeInsets.symmetric(horizontal: noiBat ? 18 : 10),
          decoration: noiBat
              ? BoxDecoration(
                  color: nhan.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(16),
                )
              : null,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.filter_alt_off_outlined, size: 15, color: nhan),
              const SizedBox(width: 5),
              Text(
                t.searchClearFilter,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w600,
                  color: nhan,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  final KhuVuc khuVuc;
  final ViTri? viTri;

  const _ResultCard({required this.khuVuc, required this.viTri});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);
    final nhan = AppColors.accentOf(context);

    return GlassCard(
      radius: 24,
      semanticLabel: khuVuc.nhom,
      semanticHint: t.a11yOpenArea,
      onTap: () {
        // Ô tìm kiếm còn giữ focus thì con trỏ mờ dần liên tục, kính vẽ lại mỗi khung.
        FocusManager.instance.primaryFocus?.unfocus();
        moChiTietKhuVuc(context, khuVuc);
      },
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: nhan.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(15),
            ),
            child: Icon(khuVuc.icon, size: 22, color: nhan),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  khuVuc.nhom,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w500,
                    color: muc,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  khuVuc.moTa,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: muc.withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ),
          // Chưa định vị thì không hiện gì: số điểm đo là chi tiết khảo sát.
          if (viTri != null) ...[
            const SizedBox(width: 8),
            Text(
              t.distanceMeters((khuVuc.khoangCach(viTri!.xGop, viTri!.yGop) *
                      SoDoThat.metMoiDonVi)
                  .round()),
              maxLines: 1,
              // Thiếu overflow thì Text cắt ngang không để lại dấu gì.
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w500,
                color: nhan,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
