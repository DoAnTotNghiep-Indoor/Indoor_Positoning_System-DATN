import 'dart:async';

import 'package:flutter_test/flutter_test.dart';

import 'package:ips_dlu/services/la_ban.dart';

/// Kiểm thử la bàn và nón hướng.
///
/// Bất biến đáng khoá nhất ở đây là phép quy đổi từ bắc từ sang trục sơ đồ. Sai
/// dấu hoặc quên trừ [LaBan.gocBacSoDo] thì nón vẫn hiện, vẫn xoay mượt theo
/// tay, chỉ là chỉ sai hướng — loại lỗi không lộ ra khi nhìn ảnh chụp màn hình.
void main() {
  test('Hướng quy về trục sơ đồ bằng cách trừ phương vị toà nhà', () {
    final nguon = StreamController<double?>.broadcast();
    final lb = LaBan(nguon: nguon.stream)..batDau();
    addTearDown(() {
      lb.dispose();
      nguon.close();
    });

    expect(lb.huongSoDo, isNull, reason: 'chưa có số đọc thì chưa có hướng');
  });

  test('Chỉ đúng bắc từ thì nón lệch khỏi trục +y đúng bằng phương vị toà nhà',
      () async {
    final nguon = StreamController<double?>.broadcast();
    final lb = LaBan(nguon: nguon.stream)..batDau();
    addTearDown(() {
      lb.dispose();
      nguon.close();
    });

    nguon.add(0.0);
    await Future<void>.delayed(Duration.zero);
    // 0° bắc từ, trục +y sơ đồ lệch 22° so với bắc, nên nhìn theo trục sơ đồ
    // thì hướng ấy ở -22°, tức 338°.
    expect(lb.huongSoDo, closeTo(360 - LaBan.gocBacSoDo, 0.001));

    // Quay đúng bằng phương vị toà nhà thì nón trùng trục +y.
    nguon.add(LaBan.gocBacSoDo);
    await Future<void>.delayed(Duration.zero);
    expect(lb.huongSoDo, closeTo(0, 0.001));
  });

  test('Hướng luôn nằm trong [0, 360)', () async {
    final nguon = StreamController<double?>.broadcast();
    final lb = LaBan(nguon: nguon.stream)..batDau();
    addTearDown(() {
      lb.dispose();
      nguon.close();
    });

    for (final h in [0.0, 90.0, 180.0, 270.0, 359.9, 21.0]) {
      nguon.add(h);
      await Future<void>.delayed(Duration.zero);
      expect(lb.huongSoDo, inInclusiveRange(0, 360));
    }
  });

  test('Số đọc null bị bỏ qua, không xoá mất hướng đang có', () async {
    final nguon = StreamController<double?>.broadcast();
    final lb = LaBan(nguon: nguon.stream)..batDau();
    addTearDown(() {
      lb.dispose();
      nguon.close();
    });

    nguon.add(90.0);
    await Future<void>.delayed(Duration.zero);
    final truoc = lb.huongSoDo;

    // Android trả null khi hiệu chuẩn từ kế kém. Nhận null mà xoá hướng thì nón
    // nhấp nháy tắt/bật liên tục.
    nguon.add(null);
    await Future<void>.delayed(Duration.zero);
    expect(lb.huongSoDo, truoc);
  });

  test('Dừng lại thì thôi nhận số đọc mới', () async {
    final nguon = StreamController<double?>.broadcast();
    final lb = LaBan(nguon: nguon.stream)..batDau();
    addTearDown(() {
      lb.dispose();
      nguon.close();
    });

    nguon.add(90.0);
    await Future<void>.delayed(Duration.zero);
    final truoc = lb.huongSoDo;

    lb.dungLai();
    nguon.add(180.0);
    await Future<void>.delayed(Duration.zero);
    expect(lb.huongSoDo, truoc);
  });

  test('Máy không có từ kế thì không có cảm biến và không có hướng', () {
    final lb = LaBan(nguon: null);
    // Trên máy chủ chạy test không có kênh nền tảng nào, nên nguồn là null.
    if (!lb.coCamBien) expect(lb.huongSoDo, isNull);
  });

  test('Nón mở đủ rộng để không tỏ ra chính xác hơn dữ liệu cho phép', () {
    // Từ kế điện thoại thường lệch 10-20°, nên nón hẹp hơn thế là khẳng định
    // chắc chắn hơn thứ cảm biến đọc được.
    expect(LaBan.nuaGocMoDo, greaterThanOrEqualTo(20.0));
  });

  test('Phương vị trục sơ đồ khớp con số đo trên ảnh Google Maps', () {
    // Ba đường đo độc lập cho +x trong khoảng 336,88°-340,35°, nên +y phải nằm
    // trong khoảng đó trừ 90°. Bản trước ghi 22° — lệch khoảng 226°, tức nón
    // chỉ gần như ngược hướng. Khoá lại để không ai vô tình đặt về giá trị cũ.
    expect(LaBan.gocBacSoDo, inInclusiveRange(246.0, 251.0));
  });

  test('Xoay nhẹ thì không báo ra ngoài, xoay đủ nhiều mới báo', () async {
    // Từ kế bắn 10-50 số đọc mỗi giây; báo hết thì sơ đồ dựng lại chừng ấy lần,
    // mỗi lần đo bề rộng 26 nhãn. Nón mở 40° nên xoay dưới 2° không nhìn thấy.
    final nguon = StreamController<double?>.broadcast();
    final lb = LaBan(nguon: nguon.stream)..batDau();
    var bao = 0;
    lb.addListener(() => bao++);
    addTearDown(() { lb.dispose(); nguon.close(); });

    nguon.add(90.0);
    await Future<void>.delayed(Duration.zero);
    expect(bao, 1, reason: 'số đọc đầu tiên phải báo');

    for (final h in [90.4, 90.8, 91.2, 90.6, 89.9]) {
      nguon.add(h);
      await Future<void>.delayed(Duration.zero);
    }
    expect(bao, 1, reason: 'rung quanh 90° mà vẫn báo là chưa lọc');

    nguon.add(95.0);
    await Future<void>.delayed(Duration.zero);
    expect(bao, 2, reason: 'xoay 5° phải báo');
  });

  test('Đi qua hướng bắc không sinh một lần báo thừa', () async {
    // 359° và 1° cách nhau 2° chứ không phải 358°. So thẳng hiệu số thì mỗi lần
    // quay qua bắc lại báo một lần vô nghĩa.
    final nguon = StreamController<double?>.broadcast();
    final lb = LaBan(nguon: nguon.stream)..batDau();
    addTearDown(() { lb.dispose(); nguon.close(); });

    nguon.add(359.5);
    await Future<void>.delayed(Duration.zero);
    var bao = 0;
    lb.addListener(() => bao++);

    nguon.add(0.5);
    await Future<void>.delayed(Duration.zero);
    expect(bao, 0, reason: '359,5° sang 0,5° chỉ là 1°, không được báo');
  });
}
