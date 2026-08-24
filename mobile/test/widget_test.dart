import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ips_dlu/main.dart';
import 'package:ips_dlu/data/demo_data.dart';

void main() {
  testWidgets('Mở app hiển thị màn Trang chủ với vị trí hiện tại',
      (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    expect(find.text('Bạn đang ở'), findsOneWidget);
    expect(find.text('Truy cập nhanh'), findsOneWidget);
    expect(find.text('Gần bạn'), findsOneWidget);
    // "Phòng học nhóm" xuất hiện 2 lần: tiêu đề hero và nhãn ô truy cập nhanh.
    expect(find.text(DemoData.currentAreaName), findsNWidgets(2));
  });

  testWidgets('Bottom nav chuyển được sang màn Cài đặt',
      (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Cài đặt'));
    await tester.pumpAndSettle();

    expect(find.text('CHUNG'), findsOneWidget);
    expect(find.text('QUYỀN TRUY CẬP'), findsOneWidget);
    expect(find.text(DemoData.serverHost), findsOneWidget);
  });

  testWidgets('Nút tìm kiếm mở màn Tìm kiếm và lọc được kết quả',
      (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.search));
    await tester.pumpAndSettle();

    expect(find.text('Tìm kiếm'), findsOneWidget);
    // Từ khoá mặc định "phòng học" khớp toàn bộ 5 mục demo.
    expect(find.text('5 kết quả'), findsOneWidget);
  });
}
