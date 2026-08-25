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
  testWidgets('Nút định vị lại trên màn Bản đồ hiện được thông báo',
      (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    // Thanh tab dựng cả nhãn lúc chọn và lúc chưa chọn nên phải lấy cái đầu.
    await tester.tap(find.text('Bản đồ').first);
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.navigation_outlined).first);
    await tester.pumpAndSettle();

    expect(find.textContaining('chưa nối API định vị'), findsOneWidget);
  });

  testWidgets('Nút "đi tới đây" ở màn Chi tiết hiện được thông báo',
      (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    // Mở chi tiết khu vực từ danh sách "Gần bạn" ở màn Trang chủ.
    await tester.tap(find.text('Không gian đọc').last);
    await tester.pumpAndSettle();

    await tester.tap(find.text('Đi tới đây'));
    await tester.pumpAndSettle();

    expect(find.textContaining('chỉ đường'), findsOneWidget);
  });
}
