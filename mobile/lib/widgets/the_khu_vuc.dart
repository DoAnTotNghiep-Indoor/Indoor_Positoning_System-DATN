import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../data/anh_khu_vuc.dart';
import '../data/floor_map.dart';
import '../data/khu_vuc.dart';
import '../l10n/app_localizations.dart';
import '../services/api_dinh_vi.dart';
import '../services/theo_doi_vi_tri.dart';
import '../theme/app_theme.dart';
import 'chung.dart';

/// AppShell nghe để chuyển sang tab Bản đồ sau khi tìm được tuyến.
final yeuCauMoBanDo = ValueNotifier<int>(0);

/// Popup duy nhất cho mọi lối chạm vào một khu vực (Trang chủ, Tìm kiếm, sơ
/// đồ): ảnh, giới thiệu ngắn và nút chỉ đường. [rpId] là điểm vừa chạm trên sơ
/// đồ — chỉ đường tới đúng điểm đó thay vì điểm gần nhất của cả khu.
Future<void> moKhuVuc(BuildContext context, KhuVuc k, {String? rpId}) {
  FocusManager.instance.primaryFocus?.unfocus();
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    builder: (_) => _TheKhuVuc(khuVuc: k, rpId: rpId),
  );
}

class _TheKhuVuc extends StatefulWidget {
  final KhuVuc khuVuc;
  final String? rpId;

  const _TheKhuVuc({required this.khuVuc, this.rpId});

  @override
  State<_TheKhuVuc> createState() => _TheKhuVucState();
}

class _TheKhuVucState extends State<_TheKhuVuc> {
  bool _dangTim = false;
  bool _loi = false;

  Future<void> _chiDuong(TheoDoiViTri theoDoi) async {
    setState(() {
      _dangTim = true;
      _loi = false;
    });
    try {
      await theoDoi.chiDuongToi(widget.khuVuc, rpId: widget.rpId);
      if (!mounted) return;
      Navigator.pop(context);
      yeuCauMoBanDo.value++;
    } on NgoaiLeApi {
      if (mounted) setState(() => _loi = true);
    } finally {
      if (mounted) setState(() => _dangTim = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = L.of(context);
    final m = Mau.of(context);
    final tt = Theme.of(context).textTheme;
    final k = widget.khuVuc;
    final theoDoi = TheoDoiViTriScope.of(context);
    final vt = theoDoi.viTri;
    final oDay = widget.rpId != null
        ? theoDoi.diemGanNhat?.rpId == widget.rpId
        : theoDoi.khuHienTai?.nhom == k.nhom;

    final String nhanNut;
    VoidCallback? bam;
    if (_dangTim) {
      nhanNut = t.placeRouting;
    } else if (vt == null) {
      nhanNut = t.placeWaiting;
    } else if (oDay) {
      nhanNut = t.placeHere;
    } else {
      nhanNut = t.placeGo;
      bam = () => _chiDuong(theoDoi);
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _DaiAnh(khuVuc: k),
          const SizedBox(height: 18),
          Row(
            children: [
              OBieuTuong(k, size: 44),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Semantics(
                        header: true,
                        child: Text(k.nhom, style: tt.titleLarge)),
                    const SizedBox(height: 2),
                    Text(t.floorLine, style: tt.bodyMedium),
                  ],
                ),
              ),
              if (vt != null && !oDay)
                Text(
                  t.distanceMeters(
                      (k.khoangCach(vt.xGop, vt.yGop) * SoDoThat.metMoiDonVi)
                          .round()),
                  style: tt.titleMedium?.copyWith(color: m.nhan),
                ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            k.moTaChiTiet.isNotEmpty ? k.moTaChiTiet : k.moTa,
            style: tt.bodyLarge?.copyWith(color: m.chuPhu, fontSize: 15),
          ),
          const SizedBox(height: 22),
          SizedBox(
            width: double.infinity,
            height: 52,
            child: FilledButton.icon(
              onPressed: bam,
              style: FilledButton.styleFrom(
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
                textStyle:
                    const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                disabledBackgroundColor: m.nhanNhat,
                disabledForegroundColor: m.chuPhu,
              ),
              icon: _dangTim
                  ? SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: m.chuPhu))
                  : Icon(oDay ? Icons.place : Icons.directions, size: 20),
              label: Text(nhanNut),
            ),
          ),
          if (_loi) ...[
            const SizedBox(height: 10),
            Text(t.placeRouteFailed,
                style: tt.bodyMedium?.copyWith(color: m.loi)),
          ],
        ],
      ),
    );
  }
}

class _DaiAnh extends StatefulWidget {
  final KhuVuc khuVuc;
  const _DaiAnh({required this.khuVuc});

  @override
  State<_DaiAnh> createState() => _DaiAnhState();
}

class _DaiAnhState extends State<_DaiAnh> {
  int _trang = 0;

  @override
  Widget build(BuildContext context) {
    final anh = AnhKhuVuc.duongDan(widget.khuVuc.thuMucAnh);
    const cao = 200.0;

    if (anh.isEmpty) {
      final (nen, chu) = mauLoai(context, loaiCua(widget.khuVuc.nhom));
      return Container(
        height: cao,
        decoration:
            BoxDecoration(color: nen, borderRadius: BorderRadius.circular(20)),
        child: Center(child: Icon(widget.khuVuc.icon, size: 48, color: chu)),
      );
    }

    // Giải mã đúng bề rộng hiển thị thay vì nguyên ảnh 1024 px.
    final rongPx = (MediaQuery.sizeOf(context).width *
            MediaQuery.devicePixelRatioOf(context))
        .round();

    return SizedBox(
      height: cao,
      child: Stack(
        children: [
          Positioned.fill(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: PageView.builder(
                itemCount: anh.length,
                onPageChanged: (i) => setState(() => _trang = i),
                itemBuilder: (_, i) => Image.asset(
                  anh[i],
                  fit: BoxFit.cover,
                  cacheWidth: math.min(rongPx, 1024),
                ),
              ),
            ),
          ),
          if (anh.length > 1)
            Positioned(
              bottom: 10,
              left: 0,
              right: 0,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  for (var i = 0; i < anh.length; i++)
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      width: i == _trang ? 16 : 6,
                      height: 6,
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(3),
                        color: Colors.white
                            .withValues(alpha: i == _trang ? 1 : 0.6),
                        boxShadow: const [
                          BoxShadow(color: Color(0x40000000), blurRadius: 3),
                        ],
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
