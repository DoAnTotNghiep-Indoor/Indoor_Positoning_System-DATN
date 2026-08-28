import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ips_dlu/data/demo_data.dart';
import 'package:ips_dlu/data/floor_map.dart';
import 'package:ips_dlu/main.dart';

/// Kiểm thử sơ đồ mặt bằng sau khi gộp dữ liệu về `data/floor_map.dart`.
///
/// Hai bất biến được khoá ở đây, cả hai đều từng bị vi phạm mà không bài test
/// nào đỏ:
///
/// 1. Sơ đồ phải đổi nhãn theo ngôn ngữ. Bản cũ không gọi `L.of(context)` một
///    lần nào và vẽ cứng "Cầu thang", "Sảnh chính" nên chuyển sang English
///    chúng vẫn là tiếng Việt.
/// 2. Hình học phòng chỉ được khai báo một lần. Bản cũ chép `Rect` và màu của
///    sáu phòng sang cả `demo_data.dart`, đổi sơ đồ là phải sửa tay hai chỗ.

/// Độ sáng tương đối theo WCAG 2.1.
double _doSang(Color c) {
  double kenh(double v) =>
      v <= 0.03928 ? v / 12.92 : math.pow((v + 0.055) / 1.055, 2.4).toDouble();
  return 0.2126 * kenh(c.r) + 0.7152 * kenh(c.g) + 0.0722 * kenh(c.b);
}

/// Tỉ lệ tương phản giữa hai màu đục, theo WCAG 2.1.
double _tuongPhan(Color a, Color b) {
  final la = _doSang(a), lb = _doSang(b);
  return (math.max(la, lb) + 0.05) / (math.min(la, lb) + 0.05);
}

/// Mở màn Bản đồ, tuỳ chọn đổi sang tiếng Anh trước nếu cần.
Future<void> _moBanDo(WidgetTester tester, {bool tiengAnh = false}) async {
  await tester.pumpWidget(const IpsDluApp());
  await tester.pumpAndSettle();

  if (tiengAnh) {
    await tester.tap(find.text('Cài đặt').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();
  }

  await tester.tap(find.text(tiengAnh ? 'Map' : 'Bản đồ').first);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Sơ đồ hiện nhãn tiếng Việt ở chế độ mặc định',
      (WidgetTester tester) async {
    await _moBanDo(tester);

    expect(find.text('Cầu thang'), findsNWidgets(2));
    expect(find.text('Sảnh chính'), findsOneWidget);
    expect(find.text('Phòng hội thảo'), findsOneWidget);

    expect(find.text('Stairs'), findsNothing);
    expect(find.text('Main hall'), findsNothing);
  });

  testWidgets('Đổi sang tiếng Anh thì nhãn trên sơ đồ đổi theo',
      (WidgetTester tester) async {
    await _moBanDo(tester, tiengAnh: true);

    // Bốn nhãn này trước đây KHÔNG có bản tiếng Anh nên vẫn hiện tiếng Việt
    // giữa giao diện English. Đây là bài test bắt đúng lỗi đó.
    expect(find.text('Stairs'), findsNWidgets(2));
    expect(find.text('Main hall'), findsOneWidget);
    expect(find.text('Conference room'), findsOneWidget);
    expect(find.text('Technical'), findsNWidgets(2));

    expect(find.text('Cầu thang'), findsNothing);
    expect(find.text('Sảnh chính'), findsNothing);
    expect(find.text('Phòng hội thảo'), findsNothing);
  });

  test('Mọi phòng đều khai báo đủ hai ngôn ngữ', () {
    for (final p in [...FloorMap.phong, FloorMap.quayHuongDan]) {
      expect(p.vi, isNotEmpty, reason: '${p.id} thiếu nhãn tiếng Việt');
      expect(p.en, isNotEmpty, reason: '${p.id} thiếu nhãn tiếng Anh');
    }
    for (final n in FloorMap.nhan) {
      expect(n.vi, isNotEmpty);
      expect(n.en, isNotEmpty);
    }
  });

  test('Danh sách khu vực dùng chung hình học với sơ đồ, không chép lại', () {
    final trenSoDo = {
      for (final p in [...FloorMap.phong, FloorMap.quayHuongDan]) p.id: p,
    };

    for (final a in [...DemoData.nearby, ...DemoData.searchResults]) {
      final p = trenSoDo[a.phong.id];
      expect(p, isNotNull, reason: '${a.id} trỏ tới phòng không có trên sơ đồ');

      // `same` chứ không phải `equals`: phải là ĐÚNG một đối tượng, không phải
      // hai đối tượng tình cờ bằng nhau. Chép giá trị sẽ qua được `equals`.
      expect(identical(a.phong, p), isTrue,
          reason: '${a.id} không dùng chung đối tượng phòng với sơ đồ');
      expect(a.rect, same(p!.r));
    }
  });

  testWidgets('Sơ đồ không tràn trên màn hình nhỏ, ở cả hai ngôn ngữ',
      (WidgetTester tester) async {
    // 360x640 là máy Android nhỏ phổ biến. Cần kiểm tra riêng cho tiếng Anh vì
    // nhãn tiếng Anh dài hơn hẳn: "INFORMATION DESK" 16 ký tự so với "QUẦY
    // HƯỚNG DẪN" 14, "Conference room" so với "Phòng hội thảo". Từ khi mỗi nhãn
    // chỉ còn một dòng thay vì hai, chiều rộng mới là chiều dễ tràn.
    tester.view.physicalSize = const Size(360, 640);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    for (final tiengAnh in [false, true]) {
      await _moBanDo(tester, tiengAnh: tiengAnh);
      // Tràn bố cục làm bài test đỏ ngay, kèm đúng widget gây ra.
      expect(tester.takeException(), isNull);
    }
  });

  test('Chữ trong ô phòng đủ tương phản khi ô được vẽ đục', () {
    // Sơ đồ ở chế độ tối là "tờ bản đồ giấy" đặt trên nền tối: ô phòng vẽ đục
    // bằng màu pastel, chữ giữ màu `stroke` tối. Bài test khoá đúng điều kiện
    // làm cách đó đứng vững — mỗi cặp (fill, stroke) phải đạt 4,5:1 của WCAG AA
    // cho chữ nhỏ.
    //
    // Bài này khoá phần CHỌN MÀU. Phần vẽ đục do bài kế tiếp khoá — cần cả hai,
    // vì cặp màu đẹp mà vẽ trong suốt thì vẫn mờ.
    for (final p in [...FloorMap.phong, FloorMap.quayHuongDan]) {
      final ty = _tuongPhan(p.fill, p.stroke);
      expect(ty, greaterThanOrEqualTo(4.5),
          reason: '${p.id}: chữ trên nền phòng chỉ đạt ${ty.toStringAsFixed(2)}:1');
    }
  });

  testWidgets('Ô phòng vẽ ĐỤC ở chế độ tối', (WidgetTester tester) async {
    // Đây là bài bắt đúng lỗi đã đo được trên máy thật.
    //
    // Bản trước vẽ ô ở `alpha: 0.55` cho cả hai chế độ. Nền sáng là trắng nên
    // pastel vẫn ra pastel; nền tối là 0xFF1B2942 nên 45% màu navy xuyên qua,
    // kéo pastel xuống xám giữa trong khi chữ giữ màu `stroke` tối — đo trên
    // Xiaomi M2012K11C chỉ còn 2,99–3,42:1, dưới ngưỡng 4,5:1 của WCAG AA.
    //
    // Kiểm tra thẳng alpha của widget đã dựng, không kiểm tra bảng màu: chỉ có
    // cách này mới đỏ khi ai đó hạ alpha xuống lần nữa.
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cài đặt').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tối'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Bản đồ').first);
    await tester.pumpAndSettle();

    final mauPhong = {for (final p in FloorMap.phong) p.fill.toARGB32()};
    var daKiemTra = 0;

    for (final hop in tester.widgetList<Container>(find.byType(Container))) {
      final trangTri = hop.decoration;
      if (trangTri is! BoxDecoration) continue;
      final mau = trangTri.color;
      if (mau == null) continue;
      if (!mauPhong.contains(mau.withValues(alpha: 1).toARGB32())) continue;

      expect(mau.a, 1.0,
          reason: 'Ô phòng ở chế độ tối phải đục hoàn toàn, '
              'đang là alpha ${mau.a.toStringAsFixed(2)}');
      daKiemTra++;
    }

    expect(daKiemTra, FloorMap.phong.length,
        reason: 'Phải soi đủ ${FloorMap.phong.length} ô phòng, '
            'chỉ thấy $daKiemTra — bài test không còn tìm đúng widget nữa');
  });

  test('Không có phòng nào trùng vùng với phòng khác', () {
    final daThay = <Rect, String>{};
    for (final p in FloorMap.phong) {
      final truoc = daThay[p.r];
      expect(truoc, isNull, reason: '${p.id} trùng vùng với $truoc');
      daThay[p.r] = p.id;
    }
  });
}
