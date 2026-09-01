import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ips_dlu/main.dart';

void main() {
  testWidgets('Mở app hiển thị màn Trang chủ với vị trí hiện tại',
      (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    expect(find.text('Bạn đang ở'), findsOneWidget);
    expect(find.text('Truy cập nhanh'), findsOneWidget);
    expect(find.text('Gần bạn'), findsOneWidget);
    // Bốn ô truy cập nhanh và sáu dòng "Gần bạn" nay là khu vực THẬT, lấy từ
    // bản nhúng sẵn khi chưa nối được máy chủ.
    expect(find.text('Bàn thủ thư'), findsOneWidget);
    expect(find.text('Khu vực đọc'), findsOneWidget);
  });

  testWidgets('Bottom nav chuyển được sang màn Cài đặt',
      (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    // Thanh tab dựng cả nhãn lúc chọn và lúc chưa chọn nên phải lấy cái đầu.
    await tester.tap(find.text('Cài đặt').first);
    await tester.pumpAndSettle();

    expect(find.text('CHUNG'), findsOneWidget);

    // Địa chỉ máy chủ nay là ô nhập sửa được, không còn là chữ tĩnh lấy từ
    // DemoData — kiểm nhãn dòng thay vì kiểm giá trị.
    expect(find.text('Máy chủ định vị'), findsOneWidget);

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
          .descendant(
              of: find.byType(ListView), matching: find.byType(Scrollable))
          .first,
    );
    expect(find.text('QUYỀN TRUY CẬP'), findsOneWidget);
  });

  testWidgets('Chưa định vị thì nói chưa biết, không bịa tên phòng',
      (WidgetTester tester) async {
    // Không có máy chủ trong test nên ứng dụng chưa hề có toạ độ. Chỗ tiêu đề
    // này từng hiện sẵn "Phòng học nhóm" — một cái tên không có trong dữ liệu
    // khảo sát lẫn mã nguồn CTK45 — nên app trông như đã định vị xong ngay khi
    // vừa mở. Đúng lỗi "trả lời tự tin khi không có dữ liệu" mà cả đồ án lấy
    // làm điểm cải tiến.
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    expect(find.text('Chưa xác định vị trí'), findsOneWidget);
    expect(find.text('Phòng học nhóm'), findsNothing);
    expect(find.text('Chưa bật định vị'), findsOneWidget);
  });

  testWidgets('Header Bản đồ không nói "cập nhật" khi chưa có toạ độ nào',
      (WidgetTester tester) async {
    // Dòng phụ từng lấy một hằng số viết cứng nên luôn ghi "cập nhật 2 giây
    // trước", kể cả lúc định vị đang tắt và chưa quét lần nào.
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Bản đồ').first);
    await tester.pumpAndSettle();

    expect(find.textContaining('cập nhật'), findsNothing);
    // Vẫn phải hiện số khu vực — bỏ vế thời gian chứ không bỏ cả dòng. Dùng
    // chuỗi chính xác vì ô tìm kiếm cũng có chữ "khu vực" trong gợi ý.
    expect(find.text('11 khu vực'), findsOneWidget);
  });

  testWidgets('Nút tìm kiếm mở màn Tìm kiếm', (WidgetTester tester) async {
    await tester.pumpWidget(const IpsDluApp());
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.search));
    await tester.pumpAndSettle();

    expect(find.text('Tìm kiếm'), findsOneWidget);
  });
}
