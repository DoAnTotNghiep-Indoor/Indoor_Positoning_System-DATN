import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ips_dlu/data/anh_khu_vuc.dart';
import 'package:ips_dlu/l10n/app_localizations.dart';
import 'package:ips_dlu/screens/area_detail_screen.dart';
import 'package:ips_dlu/data/khu_vuc.dart';
import 'package:ips_dlu/services/theo_doi_vi_tri.dart';

/// Kiểm thử ảnh thật của khu vực (nhóm 3, mục G).
///
/// Ảnh là asset nên sai đường dẫn KHÔNG làm `flutter analyze` đỏ và cũng không
/// làm app sập — chỉ hiện ô xám im lặng. Vì vậy phải nạp thật từng tệp.

/// Khu vực giả đúng hình dạng `KhuVuc.tuDiem` dựng ra.
KhuVuc _khu(String thuMuc, {String nhom = 'Khu vực đọc'}) => KhuVuc(
      nhom: nhom,
      moTa: 'Khu vực đọc sách tại chỗ.',
      moTaChiTiet: 'Khu vực đọc sách tại chỗ.',
      thuMucAnh: thuMuc,
      icon: Icons.menu_book_outlined,
      diem: const [Offset(-13, 41)],
    );

/// Bọc màn hình trong đúng bộ delegate của app: `L.of(context)` dùng toán tử
/// `!` nên thiếu delegate là ném TypeError ngay lúc dựng, không phải lỗi của
/// màn hình đang thử.
Widget _app(Widget man) => TheoDoiViTriScope(
      theoDoi: TheoDoiViTri(diaChiMayChu: 'http://x'),
      child: _khung(man),
    );

Widget _khung(Widget man) => MaterialApp(
      locale: const Locale('vi'),
      localizationsDelegates: L.localizationsDelegates,
      supportedLocales: L.supportedLocales,
      home: man,
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Mọi ảnh khai trong AnhKhuVuc đều nạp được thật', () async {
    var so = 0;
    for (final thuMuc in AnhKhuVuc.soAnh.keys) {
      for (final d in AnhKhuVuc.duongDan(thuMuc)) {
        final b = await rootBundle.load(d);
        expect(b.lengthInBytes, greaterThan(1000), reason: '$d rỗng');
        so++;
      }
    }
    expect(so, 37);
  });

  test('AnhKhuVuc khớp đúng danh sách asset trong pubspec.yaml', () async {
    // Hai nơi phải khai giống nhau: thiếu ở pubspec thì ảnh không vào gói, thừa
    // ở AnhKhuVuc thì màn Chi tiết hiện ô trống.
    final manifest = await AssetManifest.loadFromAssetBundle(rootBundle);
    final trongGoi = <String, int>{};
    for (final k in manifest.listAssets()) {
      if (!k.startsWith('assets/images/')) continue;
      trongGoi.update(k.split('/')[2], (v) => v + 1, ifAbsent: () => 1);
    }
    expect(trongGoi, AnhKhuVuc.soAnh);
  });

  test('Thư mục lạ trả về danh sách rỗng chứ không ném lỗi', () {
    // `thu_muc_anh` tới từ máy chủ. Thêm một khu vực bên CSDL mà quên chép ảnh
    // sang app là chuyện sẽ xảy ra, và lúc đó app không được sập.
    expect(AnhKhuVuc.duongDan('khu_vuc_chua_co'), isEmpty);
    expect(AnhKhuVuc.duongDan(''), isEmpty);
  });

  testWidgets('Màn Chi tiết hiện ảnh, tên và mô tả thật của khu vực',
      (tester) async {
    await tester.pumpWidget(_app(AreaDetailScreen(khuVuc: _khu('khu_vuc_doc'))));
    await tester.pumpAndSettle();

    expect(find.text('Khu vực đọc'), findsWidgets);
    expect(find.text('Khu vực đọc sách tại chỗ.'), findsOneWidget);
    expect(find.byType(PageView), findsOneWidget);
    expect(find.text('Ảnh khu vực'), findsNothing,
        reason: 'còn ô giữ chỗ nghĩa là ảnh thật chưa được dùng');
  });

  testWidgets('Không biết khu vực thì giữ nguyên ô giữ chỗ demo',
      (tester) async {
    await tester.pumpWidget(_app(AreaDetailScreen(khuVuc: _khu('khong_co', nhom: 'Chưa rõ'))));
    await tester.pumpAndSettle();

    expect(find.text('Ảnh khu vực'), findsOneWidget);
    expect(find.byType(PageView), findsNothing);
  });

  testWidgets('Khu vực chưa có ảnh vẫn hiện được tên và mô tả', (tester) async {
    await tester.pumpWidget(
        _app(AreaDetailScreen(khuVuc: _khu('chua_chup', nhom: 'Phòng máy'))));
    await tester.pumpAndSettle();

    expect(find.text('Phòng máy'), findsWidgets);
    expect(find.byType(PageView), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
