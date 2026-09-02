import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:ips_dlu/data/khu_vuc.dart';
import 'package:ips_dlu/l10n/app_localizations.dart';
import 'package:ips_dlu/screens/area_detail_screen.dart';
import 'package:ips_dlu/screens/map_screen.dart';
import 'package:ips_dlu/services/api_dinh_vi.dart';
import 'package:ips_dlu/services/quet_wifi.dart';
import 'package:ips_dlu/services/theo_doi_vi_tri.dart';
import 'package:ips_dlu/widgets/so_do_that.dart';

/// Kiểm thử tuyến đường vẽ trên sơ đồ và bộ lọc loại khu vực.
///
/// Hai bất biến chính. Một, tuyến phải vẽ theo `duong_di` — danh sách nút đầy
/// đủ — chứ không theo `chi_dan` vốn đã gộp các chặng đi thẳng; vẽ nhầm thì
/// tuyến cắt góc xuyên qua tường mà nhìn vẫn rất hợp lý. Hai, nhãn chip lấy
/// thẳng từ dữ liệu khảo sát, không từ một bảng loại viết riêng.

/// Bản đồ 4 điểm thuộc 3 nhóm. Thứ tự nhóm ở đây KHÔNG theo bảng chữ cái, để
/// bài test bắt được nếu hàng chip quên sắp xếp.
String _banDo() => jsonEncode({
      'don_vi': 'met',
      'pham_vi': {'x_min': -43, 'x_max': 43, 'y_min': 0, 'y_max': 52},
      'diem_tham_chieu': [
        {'rp_id': 'RP09', 'x': 30.0, 'y': 14.0,
         'ten': 'Căn tin', 'nhom': 'Căn tin'},
        {'rp_id': 'RP39', 'x': 22.0, 'y': 52.0,
         'ten': 'Phòng tạp chí', 'nhom': 'Phòng tạp chí'},
        {'rp_id': 'RP20', 'x': 0.0, 'y': 20.0,
         'ten': 'Bàn thủ thư', 'nhom': 'Bàn thủ thư'},
        {'rp_id': 'RP21', 'x': 4.0, 'y': 20.0,
         'ten': 'Bàn thủ thư', 'nhom': 'Bàn thủ thư'},
      ],
      'do_thi': {'so_diem': 4, 'so_canh': 3, 'canh_ngan_nhat_m': 1.0,
                 'canh_dai_nhat_m': 2.0, 'bac_trung_binh': 1.5},
    });

/// Tuyến 3 chặng mà `chi_dan` chỉ có 2 bước: hai chặng đầu thẳng hàng nên máy
/// chủ gộp lại. Đây đúng là ca phân biệt được hai nguồn dữ liệu.
String _tuyen() => jsonEncode({
      'tu': 'RP09', 'den': 'RP39',
      'quang_duong_m': 41.5,
      'so_chang': 3,
      'duong_di': [
        {'rp_id': 'RP09', 'x': 30.0, 'y': 14.0,
         'ten': 'Căn tin', 'nhom': 'Căn tin'},
        {'rp_id': 'RP10', 'x': 30.0, 'y': 24.0, 'ten': '', 'nhom': ''},
        {'rp_id': 'RP11', 'x': 30.0, 'y': 34.0, 'ten': '', 'nhom': ''},
        {'rp_id': 'RP39', 'x': 22.0, 'y': 52.0,
         'ten': 'Phòng tạp chí', 'nhom': 'Phòng tạp chí'},
      ],
      'chi_dan': [
        {'tu_rp': 'RP09', 'den_rp': 'RP11', 'den_ten': '',
         'huong': 'bat_dau', 'goc_do': 0.0, 'khoang_cach_m': 20.0},
        {'tu_rp': 'RP11', 'den_rp': 'RP39', 'den_ten': 'Phòng tạp chí',
         'huong': 're_trai', 'goc_do': 24.0, 'khoang_cach_m': 21.5},
      ],
    });

String _viTri() => jsonEncode({
      'x': 30.0, 'y': 14.0, 'x_smooth': 30.0, 'y_smooth': 14.0,
      'model': 'fingerprint_knn', 'timestamp': '2026-08-31T10:00:00Z',
      'matched_ap': 12, 'scan_count': 3, 'latency_ms': 0.4,
    });

class _QuetGia extends MayQuetWifi {
  @override
  Future<List<DiemTruyCap>> quet() async =>
      const [DiemTruyCap(bssid: '88:dc:97:12:62:cf', rssi: -57)];
}

TheoDoiViTri _theoDoi() {
  final client = MockClient((yc) async {
    final p = yc.url.path;
    final than = p.endsWith('/map')
        ? _banDo()
        : p.endsWith('/route')
            ? _tuyen()
            : _viTri();
    return http.Response.bytes(utf8.encode(than), 200,
        headers: {'content-type': 'application/json'});
  });
  return TheoDoiViTri(
    diaChiMayChu: 'http://x',
    mayQuet: _QuetGia(),
    api: ApiDinhVi('http://x', client: client),
  );
}

Future<void> _mo(WidgetTester tester, TheoDoiViTri td,
    {double rong = 393}) async {
  tester.view.physicalSize = Size(rong, 852);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);

  // Scope bọc NGOÀI MaterialApp, đúng như `IpsDluApp` dựng. Đặt vào trong
  // `home:` thì nó nằm dưới Navigator, và mọi route đẩy chồng lên — tấm tóm
  // tắt, màn Chi tiết — không còn thấy nó.
  await tester.pumpWidget(TheoDoiViTriScope(
    theoDoi: td,
    child: const MaterialApp(
      localizationsDelegates: L.localizationsDelegates,
      supportedLocales: L.supportedLocales,
      home: MapScreen(),
    ),
  ));
  await tester.pumpAndSettle();
}

KhuVuc _khu(TheoDoiViTri td, String nhom) =>
    KhuVuc.tuDiem(td.banDo).firstWhere((k) => k.nhom == nhom);

/// Chip mang chữ [chu]. Bắt buộc phải lọc trong hàng chip: cùng chuỗi đó còn
/// nằm trên sơ đồ dưới dạng nhãn khu vực, mà mọi nhãn đều đặt `left: 0` nên
/// tìm nhầm sẽ ra bốn widget cùng toạ độ x và phép so thứ tự thành vô nghĩa.
Finder _chip(String chu) => find.descendant(
      of: find.byType(ListView),
      matching: find.text(chu),
    );

void main() {
  test('Tuyến giữ đủ nút trung gian, không rút gọn theo chỉ dẫn', () {
    final kq =
        KetQuaChiDuong.tuJson(jsonDecode(_tuyen()) as Map<String, dynamic>);

    // 3 chặng nên 4 nút; chỉ dẫn chỉ có 2 bước vì đã gộp đoạn thẳng. Vẽ theo
    // chỉ dẫn sẽ mất RP10 và RP11, tuyến cắt thẳng góc qua chỗ có tường.
    expect(kq.duongDi.length, kq.soChang + 1);
    expect(kq.buoc.length, lessThan(kq.duongDi.length - 1));
    expect(kq.duongDi.map((d) => d.rpId).toList(),
        ['RP09', 'RP10', 'RP11', 'RP39']);
  });

  test('Thiếu duong_di thì trả danh sách rỗng chứ không ném lỗi', () {
    // Máy chủ cũ chưa trả trường này; app phải chạy được, chỉ là không vẽ tuyến.
    final j = jsonDecode(_tuyen()) as Map<String, dynamic>;
    j.remove('duong_di');
    expect(KetQuaChiDuong.tuJson(j).duongDi, isEmpty);
  });

  testWidgets('Chỉ đường xong thì tuyến sống sót ngoài màn Chi tiết',
      (tester) async {
    final td = _theoDoi();
    td.batDau();
    await _mo(tester, td);
    expect(td.tuyen, isNull);

    await td.chiDuongToi(_khu(td, 'Phòng tạp chí'));
    await tester.pumpAndSettle();

    // Tuyến nằm ở TheoDoiViTri nên màn Bản đồ thấy được, dù lệnh chỉ đường
    // phát ra từ một màn đã bị pop.
    expect(td.tuyen!.duongDi.length, 4);
    expect(find.byIcon(Icons.turn_right_rounded), findsOneWidget);
    expect(find.textContaining('Phòng tạp chí'), findsWidgets);

    td.dispose();
  });

  testWidgets('Nút xoá gỡ tuyến khỏi sơ đồ', (tester) async {
    final td = _theoDoi();
    td.batDau();
    await _mo(tester, td);
    await td.chiDuongToi(_khu(td, 'Phòng tạp chí'));
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.close_rounded));
    await tester.pumpAndSettle();

    expect(td.tuyen, isNull);
    expect(find.byIcon(Icons.turn_right_rounded), findsNothing);

    td.dispose();
  });

  testWidgets('Chip lọc lấy nhãn từ dữ liệu khảo sát và sắp theo bảng chữ cái',
      (tester) async {
    final td = _theoDoi();
    // BẮT BUỘC bật định vị: chưa có toạ độ thì sapTheoKhoangCach trả nguyên
    // danh sách, mà danh sách đó đã sắp theo tên sẵn từ KhuVuc.tuDiem — bài
    // test sẽ xanh kể cả khi hàng chip quên sắp, tức không kiểm được gì.
    td.batDau();
    // Rộng hơn màn điện thoại: ListView ngang chỉ dựng phần tử trong tầm nhìn,
    // ở 393 px thì chip cuối chưa tồn tại trong cây widget để mà so thứ tự.
    await _mo(tester, td, rong: 900);
    await tester.pumpAndSettle();

    final t = L.of(tester.element(find.byType(MapScreen)));
    final nhom = {for (final d in td.banDo) d.nhom};

    // Mỗi nhóm trong dữ liệu có đúng một chip, không thừa không thiếu. CTK45
    // giữ bảng loại tách rời nên bảng của họ trôi khỏi dữ liệu.
    expect(_chip(t.mapFilterAll), findsOneWidget);
    for (final n in nhom) {
      expect(_chip(n), findsOneWidget, reason: 'thiếu chip cho "$n"');
    }

    // Thứ tự chip phải đứng yên: danh sách khu vực vốn sắp theo khoảng cách nên
    // nó tự đảo chỗ mỗi khi người dùng bước đi.
    final x = {
      for (final n in nhom) n: tester.getTopLeft(_chip(n)).dx,
    };
    final sap = [...nhom]..sort();
    for (var i = 0; i < sap.length - 1; i++) {
      expect(x[sap[i]]!, lessThan(x[sap[i + 1]]!),
          reason: '"${sap[i]}" phải đứng trước "${sap[i + 1]}"');
    }

    td.dispose();
  });

  testWidgets('Bấm chip bật lọc, bấm lại thì bỏ lọc', (tester) async {
    final td = _theoDoi();
    await _mo(tester, td);

    String? loc() => tester.widget<SoDoMatBang>(find.byType(SoDoMatBang)).loc;

    expect(loc(), isNull);

    await tester.tap(_chip('Căn tin'));
    await tester.pumpAndSettle();
    expect(loc(), 'Căn tin');

    await tester.tap(_chip('Căn tin'));
    await tester.pumpAndSettle();
    expect(loc(), isNull);

    td.dispose();
  });

  testWidgets('Chạm sơ đồ mở tấm có cả nút chỉ đường lẫn nút xem chi tiết',
      (tester) async {
    final td = _theoDoi();
    await _mo(tester, td);

    // Chạm giữa sơ đồ: điểm gần nhất là RP20 "Bàn thủ thư" ở (0, 20), cách tâm
    // khoảng 6 m nên lọt ngưỡng 12 m của phép bắt khu vực.
    await tester.tap(find.byType(SoDoMatBang));
    await tester.pumpAndSettle();

    final t = L.of(tester.element(find.byType(MapScreen)));
    expect(find.text('Bàn thủ thư'), findsWidgets);
    expect(find.text(t.mapOpenDetail), findsOneWidget);

    // Chưa định vị thì nút chỉ đường đổi việc thay vì tắt — đoán một điểm xuất
    // phát bất kỳ sẽ cho ra tuyến sai trông rất hợp lý.
    expect(find.text(t.detailNeedPosition), findsOneWidget);
    expect(find.text(t.detailGoHere), findsNothing);

    td.dispose();
  });

  testWidgets('Có vị trí thì nút chỉ đường tìm tuyến rồi đóng tấm lại',
      (tester) async {
    final td = _theoDoi();
    td.batDau();
    await _mo(tester, td);
    await tester.pumpAndSettle();

    await tester.tap(find.byType(SoDoMatBang));
    await tester.pumpAndSettle();

    final t = L.of(tester.element(find.byType(MapScreen)));
    await tester.tap(find.text(t.detailGoHere));
    await tester.pumpAndSettle();

    // Tấm đóng lại để lộ sơ đồ, tuyến nằm sẵn trong TheoDoiViTri nên tự vẽ lên
    // kèm thẻ tổng quãng đường.
    expect(find.text(t.mapOpenDetail), findsNothing);
    expect(td.tuyen, isNotNull);
    expect(find.byIcon(Icons.turn_right_rounded), findsOneWidget);

    td.dispose();
  });

  testWidgets('Vào từ tấm trên sơ đồ thì màn Chi tiết vẫn giữ bản đồ phía sau',
      (tester) async {
    final td = _theoDoi();
    await _mo(tester, td);
    await tester.tap(find.byType(SoDoMatBang));
    await tester.pumpAndSettle();

    final t = L.of(tester.element(find.byType(MapScreen)));
    await tester.tap(find.text(t.mapOpenDetail));
    await tester.pumpAndSettle();

    // Người dùng vừa chạm một chấm nên giữ sơ đồ lại mới thấy đang xem chỗ nào.
    expect(
      find.descendant(
        of: find.byType(AreaDetailScreen),
        matching: find.byType(SoDoMatBang),
      ),
      findsOneWidget,
    );

    td.dispose();
  });
}
