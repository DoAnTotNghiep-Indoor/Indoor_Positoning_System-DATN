import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:ips_dlu/data/floor_map.dart';
import 'package:ips_dlu/data/khu_vuc.dart';
import 'package:ips_dlu/data/khu_vuc_thu_vien.dart';
import 'package:ips_dlu/services/api_dinh_vi.dart';
import 'package:ips_dlu/services/quet_wifi.dart';
import 'package:ips_dlu/services/theo_doi_vi_tri.dart';
import 'package:ips_dlu/widgets/so_do_that.dart';

/// Kiểm thử sơ đồ mặt bằng thật (nhóm 3, mục E).
///
/// Bất biến cần khoá: chấm vị trí phải đặt theo ĐÚNG phép biến đổi mét↔pixel đo
/// được từ Map.png. Sai phép đổi thì chấm vẫn hiện, vẫn di chuyển, chỉ là chỉ
/// sai phòng — loại lỗi không lộ ra khi nhìn ảnh chụp màn hình.

String _traLoi(double x, double y) => jsonEncode({
      'x': x, 'y': y, 'x_smooth': x, 'y_smooth': y,
      'model': 'fingerprint_knn', 'timestamp': '2026-08-31T10:00:00Z',
      'matched_ap': 12, 'scan_count': 3, 'latency_ms': 0.4,
    });

String _banDo() => jsonEncode({
      'don_vi': 'met',
      'pham_vi': {'x_min': -43, 'x_max': 43, 'y_min': 0, 'y_max': 52},
      'diem_tham_chieu': [
        {'rp_id': 'RP39', 'x': 22.0, 'y': 52.0,
         'ten': 'Phòng tạp chí', 'nhom': 'Phòng tạp chí'},
        {'rp_id': 'RP09', 'x': 30.0, 'y': 14.0,
         'ten': 'Căn tin', 'nhom': 'Căn tin'},
      ],
      'do_thi': {'so_diem': 2, 'so_canh': 1, 'canh_ngan_nhat_m': 1.0,
                 'canh_dai_nhat_m': 2.0, 'bac_trung_binh': 1.0},
    });

class _QuetGia extends MayQuetWifi {
  @override
  Future<List<DiemTruyCap>> quet() async =>
      const [DiemTruyCap(bssid: '88:dc:97:12:62:cf', rssi: -57)];
}

/// Máy chủ giả trả về một toạ độ cố định cho /predict và bản đồ hai điểm.
TheoDoiViTri _theoDoi({double x = 0, double y = 0}) {
  final client = MockClient((yc) async {
    final than = yc.url.path.endsWith('/map') ? _banDo() : _traLoi(x, y);
    return http.Response.bytes(utf8.encode(than), 200,
        headers: {'content-type': 'application/json'});
  });
  return TheoDoiViTri(
    diaChiMayChu: 'http://x',
    mayQuet: _QuetGia(),
    api: ApiDinhVi('http://x', client: client),
  );
}

Future<void> _mo(WidgetTester tester, TheoDoiViTri td) async {
  await tester.pumpWidget(MaterialApp(
    home: TheoDoiViTriScope(
      theoDoi: td,
      child: const Center(child: SoDoMatBang()),
    ),
  ));
  await tester.pumpAndSettle();
}

void main() {
  test('Bốn góc hộp toạ độ rơi đúng bốn góc lưới chấm trong ảnh', () {
    // Lưới chấm trải x 24,5..1024,5 và y 20,5..625,5 px, ứng với hộp bao
    // x ∈ [-43, 43] m và y ∈ [0, 52] m của 40 điểm tham chiếu.
    expect(SoDoThat.sangPixel(-43, 0).dx, closeTo(24.5, 0.01));
    expect(SoDoThat.sangPixel(-43, 0).dy, closeTo(625.5, 0.01));
    expect(SoDoThat.sangPixel(43, 52).dx, closeTo(1024.5, 0.01));
    expect(SoDoThat.sangPixel(43, 52).dy, closeTo(20.5, 0.01));
  });

  test('Trục y hướng LÊN: y lớn hơn cho pixel cao hơn trên ảnh', () {
    // Chiều này là kết luận từ hình dạng toà nhà chứ không phải quy ước tuỳ
    // chọn — lật nó thì cả 40 điểm sai phòng. Xem tools/trich_ban_do.py.
    expect(SoDoThat.sangPixel(0, 52).dy, lessThan(SoDoThat.sangPixel(0, 0).dy));
  });

  test('Tỉ lệ hai trục lệch nhau dưới 0,1%', () {
    // Đây là bằng chứng lưới chấm chính là hệ mét: 1000/86 và 605/52 độc lập
    // nhau mà vẫn cho cùng một tỉ lệ.
    final lech = (SoDoThat.pxMoiMetX - SoDoThat.pxMoiMetY).abs() /
        SoDoThat.pxMoiMetX;
    expect(lech, lessThan(0.001));
  });

  testWidgets('Chấm vị trí đặt đúng chỗ toạ độ mét chỉ tới', (tester) async {
    final td = _theoDoi(x: 22, y: 52); // RP39 "Phòng tạp chí"
    td.batDau();
    await _mo(tester, td);

    final cham = find.byType(DecoratedBox);
    expect(cham, findsOneWidget);

    // Số mong đợi viết thẳng bằng TỈ LỆ đo trên ảnh gốc, KHÔNG gọi lại
    // SoDoThat.sangKhung: gọi lại thì hàm tự so với chính nó, có lật ngược trục
    // hay đổi tỉ lệ bài test vẫn xanh.
    //
    //   x = 22 m  ->  24,5 + (22+43)·11,6279 = 780,31 px  ->  780,31/1053
    //   y = 52 m  ->  625,5 - 52·11,6346     =  20,50 px  ->   20,50/651
    final khung = find.byType(SoDoMatBang);
    final kt = tester.getSize(khung);
    final o = tester.getCenter(cham) - tester.getTopLeft(khung);
    expect(o.dx / kt.width, closeTo(780.31 / 1053, 0.002));
    expect(o.dy / kt.height, closeTo(20.50 / 651, 0.002));

    td.dispose();
  });

  testWidgets('Chưa định vị thì chưa có chấm nào', (tester) async {
    final td = _theoDoi();
    await _mo(tester, td);
    expect(find.byType(DecoratedBox), findsNothing);
    td.dispose();
  });

  testWidgets('Mở tab Bản đồ là tự tải nhãn khu vực, không đợi bật định vị',
      (tester) async {
    final td = _theoDoi();
    await _mo(tester, td);

    expect(td.trangThai, TrangThai.dung, reason: 'không được tự bật quét');
    expect(find.text('Phòng tạp chí'), findsOneWidget);
    expect(find.text('Căn tin'), findsOneWidget);

    td.dispose();
  });

  test('Mọi tâm cụm đều nằm sát một điểm thật của chính nhóm đó', () {
    // Bất biến của nhãn trên sơ đồ: nhãn phải chỉ vào chỗ có thật. Đặt nhãn ở
    // trọng tâm cả nhóm thì 5 trong 11 nhóm vi phạm điều này.
    for (final k in KhuVucThuVien.tatCa) {
      for (final t in k.tamCum) {
        expect(k.khoangCach(t.dx, t.dy), lessThanOrEqualTo(KhuVuc.nguongCumM),
            reason: 'nhãn "${k.nhom}" tại $t rơi ra chỗ trống');
      }
    }
  });

  test('Hành lang tách thành hai cụm ở hai đầu nhà', () {
    final k = KhuVucThuVien.tatCa.firstWhere((k) => k.nhom == 'Hành lang');

    // Hai điểm cách nhau 84 m, tức gần trọn bề ngang 86 m của khu khảo sát.
    expect(k.diem.length, 2);
    expect((k.diem[0] - k.diem[1]).distance, closeTo(84, 0.5));

    // Mỗi điểm một cụm; trung bình của chúng cách CẢ HAI điểm 42 m nên nhãn cũ
    // hạ đúng giữa sảnh, chỗ không có hành lang nào.
    expect(k.tamCum.length, 2);
    final tb = (k.diem[0] + k.diem[1]) / 2;
    expect(k.khoangCach(tb.dx, tb.dy), closeTo(42, 0.5));
  });

  test('Bán kính quầng bằng nửa trung vị khoảng cách tới điểm gần nhất', () {
    // Chốt 3,5 m vào chính dữ liệu khảo sát chứ không để nó là số chọn cho đẹp.
    // Đo lại từ 40 điểm nhúng sẵn: trung vị khoảng cách tới điểm gần nhất là
    // 7,0 m, nên quầng vừa chạm nhau chứ không nuốt điểm bên cạnh.
    final diem = [for (final k in KhuVucThuVien.tatCa) ...k.diem];
    expect(diem.length, 40);

    final gan = [
      for (final a in diem)
        diem
            .where((b) => b != a)
            .map((b) => (a - b).distance)
            .reduce((x, y) => x < y ? x : y),
    ]..sort();
    final trungVi = (gan[diem.length ~/ 2 - 1] + gan[diem.length ~/ 2]) / 2;

    expect(trungVi, closeTo(7.0, 0.01));
    expect(SoDoThat.banKinhQuangM, closeTo(trungVi / 2, 0.01));
  });
}
