import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:ips_dlu/services/api_dinh_vi.dart';
import 'package:ips_dlu/services/dinh_vi_tren_may.dart';
import 'package:ips_dlu/services/quet_wifi.dart';

Map<String, dynamic> _doc(String tep) =>
    jsonDecode(File(tep).readAsStringSync()) as Map<String, dynamic>;

void main() {
  final mo = MoHinhBoBa(_doc('assets/model/bo_ba.json'));

  test('Đoán trùng mô hình Python trên lần quét test', () {
    final dc = _doc('test/du_lieu/doi_chieu_bo_ba.json');
    final quet = dc['quet'] as List;
    final diem = <Float64List>[];
    // Python tính Transformer và KAN bằng float32, Dart bằng float64.
    void gan(String ten, (double, double) kq, List ky, int i) {
      expect(kq.$1, closeTo(ky[0] as num, 1e-3), reason: '$ten, lần quét $i');
      expect(kq.$2, closeTo(ky[1] as num, 1e-3), reason: '$ten, lần quét $i');
    }

    for (var i = 0; i < quet.length; i++) {
      final (d, _) = mo.diem([
        for (final ap in quet[i] as List)
          DiemTruyCap(bssid: ap['bssid'] as String, rssi: ap['rssi'] as int),
      ]);
      final ky = dc['diem'][i] as List;
      for (var c = 0; c < d.length; c++) {
        expect(d[c], closeTo(ky[c] as num, 1e-4), reason: 'điểm $c, lần quét $i');
      }
      diem.add(d);
      gan('một lần quét', mo.gop([d]), dc['toa_do'][i] as List, i);
      gan('gộp 3 lần', mo.gop(diem.sublist(i < 2 ? 0 : i - 2)),
          dc['toa_do_gop'][i] as List, i);
    }
  });

  test('Khớp quá ít AP thì báo như máy chủ', () {
    expect(
      () => mo.diem(const [DiemTruyCap(bssid: 'aa:bb:cc:dd:ee:ff', rssi: -50)]),
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.khongDuAp)
          .having((e) => e.soAp, 'soAp', 0)),
    );
  });

  group('BoGop như backend', () {
    final t0 = DateTime(2026);

    test('chỉ giữ 3 lần gần nhất', () {
      final bo = BoGop<int>();
      late List<int> kq;
      for (final i in [1, 2, 3, 4]) {
        kq = bo.them(i, luc: t0.add(Duration(seconds: i)));
      }
      expect(kq, [2, 3, 4]);
    });

    test('im lặng quá 30 s thì quên lịch sử', () {
      final bo = BoGop<int>()..them(1, luc: t0)..them(2, luc: t0);
      expect(bo.them(3, luc: t0.add(const Duration(seconds: 31))), [3]);
      expect(bo.soMau, 1);
    });
  });
}
