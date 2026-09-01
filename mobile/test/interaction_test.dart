import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ips_dlu/main.dart';

/// Kiểm tra các nút có thực sự phản hồi khi chạm.
///
/// Bài test này tồn tại vì một lỗi thật: sau khi chuyển sang `GlassScaffold`,
/// hai nút vẫn gọi `ScaffoldMessenger.showSnackBar`, mà `GlassScaffold` không
/// phải `Scaffold` của Material nên lời gọi ném assertion
/// *"no descendant Scaffolds to present to"* ngay lúc chạm. `flutter analyze`
/// không bắt được vì mã vẫn hợp lệ về kiểu, và ba bài test cũ cũng không bắt
/// được vì chúng chỉ kiểm tra điều hướng chứ không chạm vào nút nào.
void main() {
  testWidgets('Nút định vị lại trên màn Bản đồ bật định vị thật',
      (WidgetTester tester) async {
    // Bản trước nút này chỉ hiện toast "chưa nối API định vị" — câu đó nay sai,
    // API đã nối từ nhóm 2.
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    // Thanh tab dựng cả nhãn lúc chọn và lúc chưa chọn nên phải lấy cái đầu.
    await tester.tap(find.text('Bản đồ').first);
    await tester.pumpAndSettle();

    await tester.tap(find.text('Trang chủ').first);
    await tester.pumpAndSettle();
    expect(find.text('Bắt đầu định vị'), findsOneWidget);

    await tester.tap(find.text('Bản đồ').first);
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.navigation_outlined).first);
    await tester.pumpAndSettle();

    await tester.tap(find.text('Trang chủ').first);
    await tester.pumpAndSettle();
    expect(find.text('Dừng định vị'), findsOneWidget,
        reason: 'nút định vị lại phải bật vòng quét thật');
  });

  testWidgets('Chưa định vị thì nút ở màn Chi tiết mời bật định vị',
      (WidgetTester tester) async {
    // Không có vị trí xuất phát thì không thể chỉ đường, mà đoán một điểm bất
    // kỳ sẽ cho ra tuyến sai trông rất hợp lý — nên nút đổi việc chứ không tắt.
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Bàn thủ thư').first);
    await tester.pumpAndSettle();

    expect(find.text('Bật định vị để chỉ đường'), findsOneWidget);
    expect(find.text('Đi tới đây'), findsNothing);
  });

  testWidgets('Mỗi ô truy cập nhanh mở đúng khu vực của nó',
      (WidgetTester tester) async {
    // Bản trước bốn trong năm lối vào đều mở `const AreaDetailScreen()`, nên
    // mọi ô đều dẫn tới cùng một màn mang tên "Không gian đọc".
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    for (final ten in ['Bàn thủ thư', 'Căn tin']) {
      await tester.tap(find.text(ten).first);
      await tester.pumpAndSettle();
      expect(find.text(ten), findsWidgets, reason: 'mở nhầm khu vực');
      expect(find.text('Không gian đọc'), findsNothing);
      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();
    }
  });
}
