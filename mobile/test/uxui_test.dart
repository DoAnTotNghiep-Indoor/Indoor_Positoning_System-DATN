import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ips_dlu/data/demo_data.dart';
import 'package:ips_dlu/l10n/app_localizations.dart';
import 'package:ips_dlu/main.dart';
import 'package:ips_dlu/screens/search_screen.dart';

Future<void> _pumpAtSize(WidgetTester tester, Size size) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);

  await tester.pumpWidget(const IpsDluApp());
  await tester.pumpAndSettle();
}

L _searchCopy(WidgetTester tester) =>
    L.of(tester.element(find.byType(SearchScreen)));

Future<void> _openSearch(WidgetTester tester) async {
  await tester.tap(find.byIcon(Icons.search));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Tìm kiếm rỗng giải thích nguyên nhân và cho bỏ bộ lọc',
      (WidgetTester tester) async {
    await _pumpAtSize(tester, const Size(393, 852));
    await _openSearch(tester);

    final t = _searchCopy(tester);
    await tester.enterText(find.byType(EditableText).first, 'meeting');
    await tester.ensureVisible(find.text(t.searchFilterStudy));
    await tester.tap(find.text(t.searchFilterStudy));
    await tester.pumpAndSettle();

    expect(find.text(t.searchResultCount(0)), findsOneWidget);
    expect(find.text(t.searchEmpty), findsOneWidget);
    expect(find.text(t.searchEmptyHint), findsOneWidget);
    expect(find.text(t.searchClearFilter), findsNWidgets(2));

    // Có hai lối bỏ lọc: một ở dòng trạng thái, một trong empty state.
    await tester.tap(find.text(t.searchClearFilter).last);
    await tester.pumpAndSettle();

    expect(find.text(t.searchResultCount(1)), findsOneWidget);
    expect(find.text('Meeting room'), findsOneWidget);
    expect(find.text(t.searchEmpty), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Bộ lọc dùng mã nhóm ổn định khi chuyển sang tiếng Anh',
      (WidgetTester tester) async {
    await _pumpAtSize(tester, const Size(393, 852));
    await tester.tap(find.text('Cài đặt').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();
    await _openSearch(tester);

    final t = _searchCopy(tester);
    final filter = find.text(t.searchFilterInternal);
    // Chip cuối nằm ngoài viewport ban đầu; drag mô phỏng thao tác cuộn ngang.
    await tester.drag(find.byType(ListView).first, const Offset(-240, 0));
    await tester.pumpAndSettle();
    await tester.tap(filter);
    await tester.pumpAndSettle();

    expect(find.text(t.searchResultCount(1)), findsOneWidget);
    expect(find.text('Meeting room'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Màn Chi tiết vẫn cuộn được trên viewport thấp',
      (WidgetTester tester) async {
    await _pumpAtSize(tester, const Size(360, 480));

    await tester.tap(find.text(DemoData.currentAreaName).last);
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.arrow_back), findsOneWidget);
    expect(tester.takeException(), isNull);

    // CTA nằm trong sheet cuộn; ensureVisible mô phỏng thao tác vuốt của người dùng.
    final cta = find.text('Đi tới đây');
    await tester.ensureVisible(cta);
    await tester.pumpAndSettle();
    expect(tester.getRect(cta).bottom, lessThanOrEqualTo(480));
    expect(tester.takeException(), isNull);
  });
}
