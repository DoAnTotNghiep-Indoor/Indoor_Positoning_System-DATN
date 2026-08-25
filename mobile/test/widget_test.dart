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

    // Thanh tab dựng cả nhãn lúc chọn và lúc chưa chọn nên phải lấy cái đầu.
    await tester.tap(find.text('Cài đặt').first);
    await tester.pumpAndSettle();

    expect(find.text('CHUNG'), findsOneWidget);
    expect(find.text(DemoData.serverHost), findsOneWidget);

    // Màn Cài đặt nay có 4 nhóm nên nhóm cuối nằm ngoài vùng nhìn; ListView
    // chưa dựng widget chưa hiển thị, phải cuộn tới thì mới tìm thấy.
    //
    // Phải chỉ rõ cuộn cái nào: trong cây còn nhiều Scrollable khác — hai
    // segmented control ở nhóm GIAO DIỆN cũng cuộn ngang được — nên để mặc
    // định thì scrollUntilVisible báo "Too many elements".
    await tester.scrollUntilVisible(
      find.text('QUYỀN TRUY CẬP'),
      200,
      scrollable: find
          .descendant(of: find.byType(ListView), matching: find.byType(Scrollable))
          .first,
    );
    expect(find.text('QUYỀN TRUY CẬP'), findsOneWidget);
  });

  testWidgets('Nút tìm kiếm mở màn Tìm kiếm', (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.search));
    await tester.pumpAndSettle();

    expect(find.text('Tìm kiếm'), findsOneWidget);
  });
}
