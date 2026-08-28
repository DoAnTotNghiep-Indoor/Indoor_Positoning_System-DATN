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

  test('Không có phòng nào trùng vùng với phòng khác', () {
    final daThay = <Rect, String>{};
    for (final p in FloorMap.phong) {
      final truoc = daThay[p.r];
      expect(truoc, isNull, reason: '${p.id} trùng vùng với $truoc');
      daThay[p.r] = p.id;
    }
  });
}
