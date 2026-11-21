import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:ips_dlu/data/anh_khu_vuc.dart';
import 'package:ips_dlu/data/toan_canh.dart';

void main() {
  const a = ToanCanh(
      ma: 'a', ten: 'A', nhom: 'A', x: 0, y: 0, gocTam: 0, rong: 2, cao: 1, gioiThieu: '', huongDan: '');
  const b = ToanCanh(
      ma: 'b', ten: 'B', nhom: 'B', x: 100, y: 0, gocTam: 0, rong: 2, cao: 1, gioiThieu: '', huongDan: '');

  List<String?> chay(List<double> xs, {bool chiDuong = false}) {
    final g = GoiYToanCanh([a, b]);
    return [for (final x in xs) g.capNhat(x, 0, dangChiDuong: chiDuong)?.ma];
  }

  test('Chỉ gợi ý sau đủ số lần liên tiếp trong vùng, và chỉ một lần', () {
    expect(chay([5, 5, 5, 5, 5]), [null, null, 'a', null, null]);
  });

  test('Nhảy ra ngoài vùng giữa chừng thì đếm lại', () {
    expect(chay([5, 5, 50, 5, 5, 5]), [null, null, null, null, null, 'a']);
  });

  test('Rời hẳn vùng đệm rồi quay lại thì gợi ý lần nữa', () {
    expect(chay([5, 5, 5, 18, 5, 5, 5, 30, 5, 5, 5]),
        [null, null, 'a', null, null, null, null, null, null, null, 'a']);
  });

  test('Không gợi ý khi đang chỉ đường', () {
    expect(chay([5, 5, 5, 5], chiDuong: true), [null, null, null, null]);
  });

  test('Mọi ảnh trong app đều có tệp và được khai trong pubspec', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    expect(pubspec, contains('- assets/panorama/'));
    for (final t in ToanCanh.tatCa) {
      expect(File(t.anh).existsSync(), isTrue, reason: t.anh);
    }
    for (final e in AnhKhuVuc.soAnh.entries) {
      expect(pubspec, contains('- assets/images/${e.key}/'), reason: e.key);
      expect(Directory('assets/images/${e.key}').listSync().length, e.value,
          reason: e.key);
    }
  });
}
