import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:ips_dlu/services/api_dinh_vi.dart';
import 'package:ips_dlu/services/dinh_vi_tren_may.dart';
import 'package:ips_dlu/services/quet_wifi.dart';

Map<String, dynamic> _doc(String tep) =>
    jsonDecode(File(tep).readAsStringSync()) as Map<String, dynamic>;

void main() {
  final mo = MoHinhKDong(_doc('assets/model/k_dong.json'));

  test('Đoán trùng mô hình Python trên lần quét test', () {
    final dc = _doc('test/du_lieu/doi_chieu_k_dong.json');
    final quet = dc['quet'] as List,
        toaDo = dc['toa_do'] as List,
        doTrai = dc['do_trai'] as List;
    for (var i = 0; i < quet.length; i++) {
      final (x, y, trai, _) = mo.doan([
        for (final ap in quet[i] as List)
          DiemTruyCap(bssid: ap['bssid'] as String, rssi: ap['rssi'] as int),
      ]);
      expect(x, closeTo(toaDo[i][0] as num, 1e-6), reason: 'lần quét $i');
      expect(y, closeTo(toaDo[i][1] as num, 1e-6), reason: 'lần quét $i');
      // Vân tay trong app làm tròn 7 chữ số; độ trải khuếch đại phần lệch đó hơn toạ độ.
      expect(trai, closeTo(doTrai[i] as num, 1e-5), reason: 'lần quét $i');
    }
  });

  test('Khớp quá ít AP thì báo như máy chủ', () {
    expect(
      () => mo.doan(const [DiemTruyCap(bssid: 'aa:bb:cc:dd:ee:ff', rssi: -50)]),
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.khongDuAp)
          .having((e) => e.soAp, 'soAp', 0)),
    );
  });

  group('BoGop như backend', () {
    final t0 = DateTime(2026);
    for (final (ten, diem, ky) in [
      ('một điểm lạc bị loại', [(0.0, 0.0), (10.0, 0.0), (0.5, 0.0)], (0.5, 0.0)),
      ('hoà thì lấy cái mới', [(0.0, 0.0), (2.0, 0.0)], (2.0, 0.0)),
      ('chỉ giữ 3 lần gần nhất', [(9.0, 9.0), (0.0, 0.0), (1.0, 0.0), (2.0, 0.0)], (1.0, 0.0)),
    ]) {
      test(ten, () {
        final bo = BoGop();
        late (double, double) kq;
        for (final (i, (x, y)) in diem.indexed) {
          kq = bo.them(x, y, luc: t0.add(Duration(seconds: i)));
        }
        expect(kq, ky);
      });
    }

    test('im lặng quá 30 s thì quên lịch sử', () {
      final bo = BoGop()..them(0, 0, luc: t0)..them(0, 0, luc: t0);
      expect(bo.them(5, 5, luc: t0.add(const Duration(seconds: 31))), (5.0, 5.0));
      expect(bo.soMau, 1);
    });
  });
}
