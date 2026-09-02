import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';
import '../widgets/blob_background.dart';
import 'package:intl/intl.dart' as intl;

import '../data/anh_khu_vuc.dart';
import '../data/khu_vuc.dart';
import '../data/demo_data.dart';
import '../l10n/app_localizations.dart';
import '../theme/app_colors.dart';
import '../services/api_dinh_vi.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_metrics.dart';
import '../widgets/so_do_that.dart';
import '../widgets/tap_feedback.dart';
import 'map_screen.dart';

/// Màn chi tiết khu vực: sơ đồ phía trên, tấm thông tin phía dưới.
///
/// Mọi lối vào đều phải truyền [khuVuc]. Trước đây bốn trong năm lối mở màn này
/// không tham số, nên mười hai mục bấm được trên Trang chủ và Tìm kiếm đều dẫn
/// tới đúng một màn mang tên "Không gian đọc".
/// Mở màn Chi tiết bằng chuyển cảnh TRƯỢT LÊN TỪ ĐÁY.
///
/// Dùng route riêng chứ không `MaterialPageRoute`: mặc định của Android là đẩy
/// ngang, đọc như "sang một chỗ khác". Nội dung ở đây là thông tin của chính
/// chỗ vừa chạm nên trượt lên hợp hơn — cùng hướng với tấm tóm tắt trên sơ đồ,
/// hai lối vào cho ra cùng một cảm giác.
///
/// Tôn trọng thiết lập tắt hiệu ứng của hệ điều hành: lúc đó bỏ luôn phần
/// trượt thay vì rút ngắn nó.
Future<void> moChiTietKhuVuc(
  BuildContext context,
  KhuVuc khuVuc, {
  bool toanManHinh = true,
}) {
  return Navigator.of(context).push(
    PageRouteBuilder<void>(
      transitionDuration: const Duration(milliseconds: 320),
      reverseTransitionDuration: const Duration(milliseconds: 260),
      pageBuilder: (_, __, ___) =>
          AreaDetailScreen(khuVuc: khuVuc, toanManHinh: toanManHinh),
      transitionsBuilder: (context, hoat, __, con) {
        if (MediaQuery.disableAnimationsOf(context)) return con;
        return SlideTransition(
          position: Tween(begin: const Offset(0, 1), end: Offset.zero).animate(
            CurvedAnimation(parent: hoat, curve: Curves.easeOutCubic),
          ),
          child: con,
        );
      },
    ),
  );
}

class AreaDetailScreen extends StatelessWidget {
  final KhuVuc khuVuc;

  /// Thông tin chiếm trọn màn, không chừa nửa dưới cho sơ đồ.
  ///
  /// Bật khi vào từ danh sách — Trang chủ hoặc Tìm kiếm — nơi người dùng chọn
  /// theo tên chứ không theo vị trí, nên nửa sơ đồ phía sau chỉ chiếm chỗ của
  /// chính nội dung họ vừa hỏi. Tắt khi vào từ tấm tóm tắt trên sơ đồ: ở đó
  /// người dùng vừa chạm một chấm nên giữ bản đồ lại mới thấy mình đang xem chỗ
  /// nào.
  final bool toanManHinh;

  const AreaDetailScreen({
    super.key,
    required this.khuVuc,
    this.toanManHinh = true,
  });

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);

    // Chiều cao tối đa của tấm thông tin.
    //
    // Trước đây tấm này là `Positioned(bottom: 0)` không giới hạn, cao bao nhiêu
    // tuỳ nội dung. Trên máy thấp phần dôi ra tràn lên khỏi mép trên và bị Stack
    // cắt IM LẶNG — đo trên khung 360x480 thì ô ảnh nằm ở y = -66, tức mất hẳn,
    // và không có cách nào cuộn tới. Chặn ở 78% chiều cao rồi cho cuộn bên trong
    // vừa giữ được sơ đồ phía sau vẫn nhìn thấy, vừa không giấu mất nội dung.
    final caoToiDa = MediaQuery.sizeOf(context).height * 0.78;

    // Chừa đúng chỗ cho hàng nút quay lại, phần còn lại là của nội dung.
    const caoHeader = 62.0;

    // Màn này được đẩy chồng lên nên phải tự cấp nền: kính khúc xạ theo thứ
    // nằm sau nó, thiếu nền thì thẻ kính trông phẳng và bạc màu.
    return GlassScaffold(
      background: const BlobBackground(blobs: BlobBackground.mapBlobs),
      // Không dùng GlassStatusBarStyle.auto — lý do ở AppShell trong main.dart.
      statusBarStyle: Theme.of(context).brightness == Brightness.dark
          ? GlassStatusBarStyle.light
          : GlassStatusBarStyle.dark,
      body: SafeArea(
        bottom: false,
        // fit: expand — nếu không Stack sẽ co theo con không-Positioned.
        child: Stack(
          fit: StackFit.expand,
          children: [
            // Sơ đồ nền là bản số hoá thật, cùng một sơ đồ với tab Bản đồ.
            // Trước đây là sơ đồ vẽ tay với những phòng không có trong dữ liệu
            // khảo sát, nên màn chi tiết của một khu vực thật lại đứng trên nền
            // một toà nhà không tồn tại.
            if (!toanManHinh)
              const Positioned.fill(
                child: Padding(
                  padding: EdgeInsets.only(top: 116),
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: SoDoMatBang(),
                  ),
                ),
              ),

            // Header + nút quay lại.
            //
            // Nút quay lại là bắt buộc, không phải trang trí: màn này đẩy bằng
            // MaterialPageRoute lên trên một GlassScaffold — không phải Scaffold
            // của Material nên KHÔNG có AppBar nào tự sinh mũi tên quay lại. Trên
            // Android và trên web, MaterialPageRoute cũng không có cử chỉ vuốt
            // mép để lùi. Kết quả là màn Chi tiết trước đây là ngõ cụt: vào rồi
            // chỉ thoát được bằng phím back cứng của hệ điều hành.
            Positioned(
              top: 0,
              left: 16,
              right: 16,
              child: Row(
                children: [
                  GlassIconButton(
                    icon: const Icon(Icons.arrow_back, size: 20),
                    size: AppMetrics.vungChamToiThieu,
                    semanticLabel: t.commonBack,
                    onPressed: () => Navigator.maybePop(context),
                  ),
                  const SizedBox(width: 10),
                  // Toàn màn hình thì bỏ header bản đồ: tấm thông tin ngay dưới
                  // đã ghi "Tầng 1 · Thư viện Đại học Đà Lạt" rồi.
                  if (!toanManHinh) const Expanded(child: MapHeader()),
                ],
              ),
            ),

            Positioned(
              left: 0,
              right: 0,
              top: toanManHinh ? caoHeader : null,
              bottom: 0,
              child: toanManHinh
                  ? _DetailSheet(khuVuc: khuVuc)
                  : ConstrainedBox(
                      constraints: BoxConstraints(maxHeight: caoToiDa),
                      child: _DetailSheet(khuVuc: khuVuc),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DetailSheet extends StatelessWidget {
  final KhuVuc khuVuc;

  const _DetailSheet({required this.khuVuc});

  List<String> get _anh => AnhKhuVuc.duongDan(khuVuc.thuMucAnh);

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final muc = AppColors.inkOf(context);

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        // Nền phải theo theme, không để cứng Colors.white: chữ trong tấm này
        // dùng inkOf(context) nên ở chế độ tối là chữ sáng — đặt trên nền trắng
        // thành trắng trên trắng, không đọc được.
        color: Theme.of(context).colorScheme.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(36)),
        boxShadow: [
          BoxShadow(
            color: muc.withValues(alpha: 0.10),
            offset: const Offset(0, -6),
            blurRadius: 22,
          ),
        ],
      ),
      child: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(
          24,
          32,
          24,
          // Cộng vùng an toàn dưới: lề cứng 24 đo từ MÉP MÀN HÌNH, mà trên máy
          // dùng cử chỉ điều hướng thì thanh gạch ngang chiếm khoảng 34 đơn vị
          // ở đúng chỗ đó — nút "Đi tới đây" nằm lọt dưới nó.
          24 + MediaQuery.viewPaddingOf(context).bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Không có ảnh mặc định cho khu chưa chụp: gán nhầm ảnh còn tệ
            // hơn là không có ảnh.
            if (_anh.isNotEmpty) _DaiAnh(duongDan: _anh) else Container(
              height: 164,
              width: double.infinity,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(24),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF9FB9F7), Color(0xFFC3D3F6)],
                ),
              ),
              child: Text(
                t.detailImagePlaceholder,
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w500,
                  // Chữ trắng trên dải xanh nhạt này chỉ đạt khoảng 2:1, dưới
                  // ngưỡng 4.5:1 của WCAG AA. Dải màu cố định ở cả hai chế độ nên
                  // đổi sang mực xanh đậm là đọc được ở cả hai.
                  color: AppColors.strokeNavy.withValues(alpha: 0.75),
                ),
              ),
            ),

            const SizedBox(height: 22),
            Semantics(
              header: true,
              child: Text(
                khuVuc.nhom,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              theoNgonNgu(
                  context, DemoData.currentFloor, DemoData.currentFloorEn),
              style: TextStyle(
                fontSize: 13.5,
                color: muc.withValues(alpha: 0.6),
              ),
            ),

            const SizedBox(height: 18),
            _ChiSo(khuVuc: khuVuc),

            const SizedBox(height: 20),
            Text(
              // Đoạn dài nếu có; lối đi như cầu thang, hành lang thì CTK45 cố ý
              // không viết mô tả chi tiết nên lùi về câu một dòng.
              khuVuc.moTaChiTiet.isNotEmpty ? khuVuc.moTaChiTiet : khuVuc.moTa,
              style: TextStyle(
                fontSize: 13,
                height: 1.45,
                color: muc.withValues(alpha: 0.72),
              ),
            ),

            const SizedBox(height: 22),
            _NutChiDuong(khuVuc: khuVuc),
          ],
        ),
      ),
    );
  }
}

/// Chip số liệu thật: bao nhiêu điểm đo, bao nhiêu ảnh.
///
/// Thay cho ba chip bịa "120 chỗ ngồi · Cách 8 m · Yên tĩnh" giống hệt nhau ở
/// mọi khu vực. Số điểm đo là thứ đáng nói trong một đồ án định vị: khu vực
/// nhiều điểm thì mô hình đoán chắc hơn.
class _ChiSo extends StatelessWidget {
  final KhuVuc khuVuc;

  const _ChiSo({required this.khuVuc});

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final soAnh = AnhKhuVuc.duongDan(khuVuc.thuMucAnh).length;

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        _chip(context, t.detailPointCount(khuVuc.diem.length),
            AppColors.roomBlue, AppColors.strokeNavy),
        if (soAnh > 0)
          _chip(context, t.detailPhotoCount(soAnh), AppColors.roomMint,
              AppColors.strokeGreen),
      ],
    );
  }

  Widget _chip(BuildContext context, String chu, Color nen, Color chuMau) =>
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: nen.withValues(alpha: 0.55),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(
          chu,
          style: TextStyle(
            fontSize: 11.5,
            fontWeight: FontWeight.w500,
            color: chuMau,
          ),
        ),
      );
}

/// Nút hành động chính: gọi `POST /route` thật thay vì hiện một toast.
///
/// Nhãn đổi theo trạng thái. Chưa định vị thì không có điểm xuất phát, mà đoán
/// một điểm bất kỳ sẽ cho ra tuyến đường sai trông rất hợp lý — nên lúc đó nút
/// bật định vị chứ không tìm đường.
class _NutChiDuong extends StatefulWidget {
  final KhuVuc khuVuc;

  const _NutChiDuong({required this.khuVuc});

  @override
  State<_NutChiDuong> createState() => _NutChiDuongState();
}

class _NutChiDuongState extends State<_NutChiDuong> {
  bool _dangTim = false;

  Future<void> _cham(TheoDoiViTri theoDoi) async {
    if (theoDoi.viTri == null) {
      theoDoi.batDau();
      return;
    }

    setState(() => _dangTim = true);
    try {
      final kq = await theoDoi.chiDuongToi(widget.khuVuc);
      if (mounted) _hienChiDan(context, widget.khuVuc, kq);
    } on NgoaiLeApi catch (e) {
      if (mounted) {
        GlassToast.show(context,
            message: _cauLoi(L.of(context), e.loai),
            type: GlassToastType.error);
      }
    } finally {
      if (mounted) setState(() => _dangTim = false);
    }
  }

  String _cauLoi(L t, LoiApi loai) => switch (loai) {
        LoiApi.diaChiSai => t.errBadAddress(''),
        LoiApi.quaHan => t.errTimeout,
        _ => t.detailRouteFailed,
      };

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final theoDoi = TheoDoiViTriScope.of(context);
    final onPrimary = Theme.of(context).colorScheme.onPrimary;

    return AnimatedBuilder(
      animation: theoDoi,
      builder: (context, _) {
        final coViTri = theoDoi.viTri != null;
        final nhan = _dangTim
            ? t.detailRouteLoading
            : (coViTri ? t.detailGoHere : t.detailNeedPosition);

        return TapFeedback(
          semanticLabel: nhan,
          onTap: _dangTim ? null : () => _cham(theoDoi),
          child: Container(
            constraints: BoxConstraints(
              minHeight: AppMetrics.caoTheoCoChu(context, coBan: 56, phanChu: 22),
            ),
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primary,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(coViTri ? Icons.directions : Icons.my_location,
                    size: 20, color: onPrimary),
                const SizedBox(width: 10),
                Flexible(
                  child: Text(
                    nhan,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 16.5,
                      fontWeight: FontWeight.w600,
                      color: onPrimary,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Câu chữ cho từng mã hướng. Máy chủ trả mã để ứng dụng còn dịch được.
const _cauHuong = <String, String Function(L)>{
  'bat_dau': _diThang,
  'di_thang': _diThang,
  'chech_trai': _chechTrai,
  'chech_phai': _chechPhai,
  're_trai': _reTrai,
  're_phai': _rePhai,
  'quay_dau': _quayDau,
};

String _diThang(L t) => t.stepStraight;
String _chechTrai(L t) => t.stepSlightLeft;
String _chechPhai(L t) => t.stepSlightRight;
String _reTrai(L t) => t.stepLeft;
String _rePhai(L t) => t.stepRight;
String _quayDau(L t) => t.stepUTurn;

void _hienChiDan(BuildContext context, KhuVuc khuVuc, KetQuaChiDuong kq) {
  final t = L.of(context);
  final so = intl.NumberFormat('#0.#', t.localeName);

  showModalBottomSheet<void>(
    context: context,
    backgroundColor: Theme.of(context).colorScheme.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (context) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Semantics(
              header: true,
              child: Text(khuVuc.nhom,
                  style: Theme.of(context).textTheme.titleLarge),
            ),
            const SizedBox(height: 4),
            Text(
              t.routeSummary(so.format(kq.quangDuongM), kq.buoc.length),
              style: TextStyle(
                fontSize: 13,
                color: AppColors.inkOf(context).withValues(alpha: 0.6),
              ),
            ),
            const SizedBox(height: 16),
            Flexible(
              child: ListView.separated(
                shrinkWrap: true,
                itemCount: kq.buoc.length,
                separatorBuilder: (_, __) => const SizedBox(height: 12),
                itemBuilder: (context, i) {
                  final b = kq.buoc[i];
                  final huong = (_cauHuong[b.huong] ?? _diThang)(t);
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${i + 1}.',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppColors.inkOf(context)
                                .withValues(alpha: 0.45),
                          )),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          t.routeStep(huong, so.format(b.khoangCachM),
                              b.denTen.isEmpty ? b.denRp : b.denTen),
                          style: const TextStyle(fontSize: 14, height: 1.35),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

/// Dải ảnh thật của khu vực, vuốt ngang để xem hết.
///
/// `PageView` chứ không `ListView`: ảnh gốc là ảnh dọc, xếp ngang liên tục thì
/// mỗi tấm chỉ hiện được một dải hẹp.
class _DaiAnh extends StatefulWidget {
  final List<String> duongDan;

  const _DaiAnh({required this.duongDan});

  @override
  State<_DaiAnh> createState() => _DaiAnhState();
}

class _DaiAnhState extends State<_DaiAnh> {
  final _dieuKhien = PageController();
  int _trang = 0;

  @override
  void dispose() {
    _dieuKhien.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    return Semantics(
      label: t.detailPhotos(widget.duongDan.length),
      child: SizedBox(
        height: 164,
        child: Stack(
          children: [
            Positioned.fill(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(24),
                child: PageView(
                  controller: _dieuKhien,
                  onPageChanged: (i) => setState(() => _trang = i),
                  children: [
                    for (final d in widget.duongDan)
                      // cover: ảnh dọc trong ô ngang, contain sẽ chừa hai dải
                      // trống rộng hơn cả ảnh.
                      Image.asset(d, fit: BoxFit.cover),
                  ],
                ),
              ),
            ),
            if (widget.duongDan.length > 1)
              Positioned(
                bottom: 10,
                left: 0,
                right: 0,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    for (var i = 0; i < widget.duongDan.length; i++)
                      Container(
                        width: 6,
                        height: 6,
                        margin: const EdgeInsets.symmetric(horizontal: 3),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          // Chấm trên nền ảnh bất kỳ nên phải tự sáng, không
                          // lấy màu theo theme.
                          color: Colors.white
                              .withValues(alpha: i == _trang ? 0.95 : 0.45),
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
