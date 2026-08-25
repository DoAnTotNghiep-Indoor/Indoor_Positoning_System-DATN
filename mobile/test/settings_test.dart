import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ips_dlu/main.dart';

/// Kiểm thử hai tuỳ chọn mới: chế độ sáng/tối và ngôn ngữ giao diện.
///
/// Cả hai đổi trạng thái ở gốc cây widget rồi lan xuống, nên bài test đi hết
/// đường đó: chạm vào bộ chọn trong màn Cài đặt và kiểm tra kết quả ở nơi khác.
Future<void> _moCaiDat(WidgetTester tester) async {
  await tester.pumpWidget(const IpsDluApp());
  await tester.pumpAndSettle();
  await tester.tap(find.text('Cài đặt').first);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Chuyển sang chế độ tối thì theme của app đổi theo',
      (WidgetTester tester) async {
    await _moCaiDat(tester);

    final truoc = Theme.of(tester.element(find.text('CHUNG'))).brightness;
    expect(truoc, Brightness.light, reason: 'mặc định phải là chế độ sáng');

    await tester.tap(find.text('Tối'));
    await tester.pumpAndSettle();

    final sau = Theme.of(tester.element(find.text('CHUNG'))).brightness;
    expect(sau, Brightness.dark);
  });

  testWidgets('Mặc định là tiếng Việt', (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    // Không phụ thuộc ngôn ngữ của máy chạy test: đây là ứng dụng cho thư viện
    // Đại học Đà Lạt nên tiếng Việt phải là mặc định dù máy cài tiếng Anh.
    expect(find.text('Bạn đang ở'), findsOneWidget);
  });

  testWidgets('Chuyển sang tiếng Anh thì giao diện đổi ngôn ngữ',
      (WidgetTester tester) async {
    await _moCaiDat(tester);

    expect(find.text('CHUNG'), findsOneWidget);

    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();

    expect(find.text('GENERAL'), findsOneWidget);
    expect(find.text('CHUNG'), findsNothing);

    // Đổi ngôn ngữ phải lan cả sang thanh điều hướng, không chỉ màn đang mở.
    expect(find.text('Home').first, findsOneWidget);
  });
}
