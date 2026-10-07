import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:flutter/services.dart';

import 'api_dinh_vi.dart';
import 'quet_wifi.dart';

/// kNN k động chạy ngay trên máy, cùng thuật toán với `ml/models/fingerprint_knn_dong.py`.
/// Dữ liệu do `python -m ml.xuat_mo_hinh` sinh; `test/dinh_vi_tren_may_test.dart`
/// kiểm kết quả trùng với Python.
class MoHinhKDong {
  final Map<String, int> _viTri;
  final double _thieu, _beta, _nguong;
  final int _kLon, _soAp, soApToiThieu;
  final List<double> _min, _scale;
  final Float64List _vanTay, _tongHang;
  final List<int> _nhan;
  final List<List<double>> _toaDo;

  MoHinhKDong(Map<String, dynamic> j)
      : _viTri = {
          for (final (i, b) in (j['ap'] as List).indexed)
            (b as String).toLowerCase(): i
        },
        _thieu = (j['gia_tri_thieu'] as num).toDouble(),
        _beta = (j['beta'] as num).toDouble(),
        _nguong = (j['nguong'] as num).toDouble(),
        _kLon = j['k_lon'] as int,
        _soAp = (j['ap'] as List).length,
        soApToiThieu = j['so_ap_toi_thieu'] as int,
        _min = _soThuc(j['min']),
        _scale = _soThuc(j['scale']),
        _vanTay = Float64List.fromList(
            [for (final h in j['van_tay'] as List) ..._soThuc(h)]),
        _tongHang = Float64List((j['van_tay'] as List).length),
        _nhan = (j['nhan'] as List).cast<int>(),
        _toaDo = [for (final t in j['toa_do'] as List) _soThuc(t)] {
    for (var i = 0; i < _tongHang.length; i++) {
      for (var a = 0; a < _soAp; a++) {
        _tongHang[i] += _vanTay[i * _soAp + a];
      }
    }
  }

  static List<double> _soThuc(Object? ds) =>
      [for (final v in ds as List) (v as num).toDouble()];

  static Future<MoHinhKDong> napTaiSan() async => MoHinhKDong(
      jsonDecode(await rootBundle.loadString('assets/model/k_dong.json'))
          as Map<String, dynamic>);

  /// (x, y, độ trải, số AP khớp); độ trải như `DinhViKDong.do_trai`, đơn vị lưới. Ném
  /// [NgoaiLeApi] `khongDuAp` như máy chủ khi khớp quá ít.
  (double, double, double, int) doan(List<DiemTruyCap> quet) {
    final tong = Float64List(_soAp), dem = Int32List(_soAp);
    for (final ap in quet) {
      final i = _viTri[ap.bssid.toLowerCase()];
      // Cùng khoảng RSSI_NHO_NHAT..RSSI_LON_NHAT của ml/config.py.
      if (i != null && ap.rssi >= -100 && ap.rssi < 0) {
        tong[i] += ap.rssi;
        dem[i]++;
      }
    }
    final q = Float64List(_soAp);
    var tongQ = 0.0, soKhop = 0;
    for (var a = 0; a < _soAp; a++) {
      final rssi = dem[a] > 0 ? tong[a] / dem[a] : _thieu;
      if (rssi != _thieu) soKhop++;
      final v = rssi * _scale[a] + _min[a];
      q[a] = pow(max(v, 0.0), _beta).toDouble();
      tongQ += q[a];
    }
    if (soKhop < soApToiThieu) {
      throw NgoaiLeApi(LoiApi.khongDuAp, soAp: soKhop, toiThieu: soApToiThieu);
    }

    // Khoảng cách Bray-Curtis tới từng vân tay.
    final n = _tongHang.length;
    final d = Float64List(n);
    for (var i = 0; i < n; i++) {
      var s = 0.0;
      for (var a = 0, o = i * _soAp; a < _soAp; a++, o++) {
        s += (q[a] - _vanTay[o]).abs();
      }
      d[i] = s / (tongQ + _tongHang[i]);
    }
    final thuTu = List<int>.generate(n, (i) => i)
      ..sort((a, b) => d[a].compareTo(d[b]));

    // Độ trải luôn tính bằng k lớn láng giềng, kể cả khi đoán bằng k = 1.
    final lon = thuTu.take(_kLon);
    var w = 0.0, x = 0.0, y = 0.0;
    for (final i in lon) {
      final wi = 1 / (d[i] + 1e-12);
      final t = _toaDo[_nhan[i]];
      w += wi;
      x += wi * t[0];
      y += wi * t[1];
    }
    x /= w;
    y /= w;
    var v = 0.0;
    for (final i in lon) {
      final t = _toaDo[_nhan[i]];
      v += (1 / (d[i] + 1e-12)) *
          ((t[0] - x) * (t[0] - x) + (t[1] - y) * (t[1] - y));
    }
    final doTrai = sqrt(v / w);

    if (d[thuTu[0]] < _nguong) {
      final t = _toaDo[_nhan[thuTu[0]]];
      return (t[0], t[1], doTrai, soKhop);
    }
    return (x, y, doTrai, soKhop);
  }
}

/// Bản Dart của `BoGop` (backend/services/smoothing_service.py): trả dự đoán có
/// tổng khoảng cách tới các dự đoán còn lại nhỏ nhất trong cửa sổ, hoà thì lấy cái mới.
class BoGop {
  static const cuaSo = 3;
  static const quenSau = Duration(seconds: 30);

  final _lich = <(double, double)>[];
  DateTime? _lanCuoi;

  int get soMau => _lich.length;

  (double, double) them(double x, double y, {DateTime? luc}) {
    final bayGio = luc ?? DateTime.now();
    final truoc = _lanCuoi;
    if (truoc != null && bayGio.difference(truoc) > quenSau) _lich.clear();
    _lanCuoi = bayGio;
    _lich.add((x, y));
    if (_lich.length > cuaSo) _lich.removeAt(0);

    var tot = _lich.last;
    var totTong = double.infinity;
    for (final p in _lich.reversed) {
      var tong = 0.0;
      for (final o in _lich) {
        tong += sqrt(pow(p.$1 - o.$1, 2) + pow(p.$2 - o.$2, 2));
      }
      if (tong < totTong) {
        tot = p;
        totTong = tong;
      }
    }
    return tot;
  }

  void quen() {
    _lich.clear();
    _lanCuoi = null;
  }
}
