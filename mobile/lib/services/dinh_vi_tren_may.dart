import 'dart:convert';
import 'dart:isolate';
import 'dart:math';
import 'dart:typed_data';

import 'package:flutter/services.dart';

import 'api_dinh_vi.dart';
import 'quet_wifi.dart';

/// Bộ 3 (HistGB + KAN + Transformer) chạy ngay trên máy, cùng thuật toán với
/// `ml/models/bo_ba.py`. Dữ liệu do `python -m ml.xuat_mo_hinh` sinh;
/// `test/dinh_vi_tren_may_test.dart` kiểm kết quả trùng với Python.
///
/// Mỗi lần quét cho một vector điểm (trung bình log(p + eps) của ba mô hình).
/// [gop] cộng vector điểm của cả cửa sổ rồi lấy trung vị hình học có trọng số
/// trên toạ độ các điểm tham chiếu.
class MoHinhBoBa {
  final Map<String, int> _viTri;
  final double _thieu, _eps;
  final int _soAp, _soLop, _vongTrungVi, soApToiThieu;
  final Float64List _min, _scale, _toaDo;
  final _CayTangCuong _hgb;
  final List<_LopKan> _kan;
  final _ApTransformer _tf;

  MoHinhBoBa(Map<String, dynamic> j)
      : _viTri = {
          for (final (i, b) in (j['ap'] as List).indexed)
            (b as String).toLowerCase(): i
        },
        _thieu = (j['gia_tri_thieu'] as num).toDouble(),
        _eps = (j['eps'] as num).toDouble(),
        _soAp = (j['ap'] as List).length,
        _soLop = (j['toa_do'] as List).length,
        _vongTrungVi = j['vong_trung_vi'] as int,
        soApToiThieu = j['so_ap_toi_thieu'] as int,
        _min = _phang(j['min']),
        _scale = _phang(j['scale']),
        _toaDo = _phang(j['toa_do']),
        _hgb = _CayTangCuong(j['hgb'] as Map<String, dynamic>),
        _kan = [
          for (final l in j['kan'] as List) _LopKan(l as Map<String, dynamic>)
        ],
        _tf = _ApTransformer(j['tf'] as Map<String, dynamic>);

  /// Tệp mô hình vài MB: đọc và dựng trên isolate khác để không giật giao diện.
  static Future<MoHinhBoBa> napTaiSan() async {
    final chuoi = await rootBundle.loadString('assets/model/bo_ba.json');
    return Isolate.run(
        () => MoHinhBoBa(jsonDecode(chuoi) as Map<String, dynamic>));
  }

  /// (vector điểm, số AP khớp). Ném [NgoaiLeApi] `khongDuAp` như máy chủ khi khớp quá ít.
  (Float64List, int) diem(List<DiemTruyCap> quet) {
    final tong = Float64List(_soAp), dem = Int32List(_soAp);
    for (final ap in quet) {
      final i = _viTri[ap.bssid.toLowerCase()];
      // Cùng khoảng RSSI_NHO_NHAT..RSSI_LON_NHAT của ml/config.py.
      if (i != null && ap.rssi >= -100 && ap.rssi < 0) {
        tong[i] += ap.rssi;
        dem[i]++;
      }
    }
    final x = Float64List(_soAp);
    var soKhop = 0;
    for (var a = 0; a < _soAp; a++) {
      final rssi = dem[a] > 0 ? tong[a] / dem[a] : _thieu;
      if (rssi != _thieu) soKhop++;
      // MinMax như scaler.pkl, rồi cắt dưới ở 0 như `bo_ba.BoBa.xac_suat`.
      x[a] = max(rssi * _scale[a] + _min[a], 0.0);
    }
    if (soKhop < soApToiThieu) {
      throw NgoaiLeApi(LoiApi.khongDuAp, soAp: soKhop, toiThieu: soApToiThieu);
    }

    var kan = Float64List.fromList([for (final v in x) 2 * v - 1]);
    for (final l in _kan) {
      kan = l.xuoi(kan);
    }
    final d = Float64List(_soLop);
    for (final logit in [_hgb.xuoi(x, _soLop), kan, _tf.xuoi(x)]) {
      final p = _softmax(logit);
      for (var c = 0; c < _soLop; c++) {
        d[c] += log(p[c] + _eps) / 3;
      }
    }
    return (d, soKhop);
  }

  /// Cửa sổ vector điểm → toạ độ (x, y).
  (double, double) gop(List<Float64List> cuaSo) {
    final l = Float64List(_soLop);
    for (final d in cuaSo) {
      for (var c = 0; c < _soLop; c++) {
        l[c] += d[c];
      }
    }
    final p = _softmax(l);
    var x = 0.0, y = 0.0;
    for (var c = 0; c < _soLop; c++) {
      x += p[c] * _toaDo[2 * c];
      y += p[c] * _toaDo[2 * c + 1];
    }
    // Weiszfeld: trung vị hình học có trọng số.
    for (var v = 0; v < _vongTrungVi; v++) {
      var w = 0.0, nx = 0.0, ny = 0.0;
      for (var c = 0; c < _soLop; c++) {
        final dx = _toaDo[2 * c] - x, dy = _toaDo[2 * c + 1] - y;
        final wc = p[c] / max(sqrt(dx * dx + dy * dy), 1e-9);
        w += wc;
        nx += wc * _toaDo[2 * c];
        ny += wc * _toaDo[2 * c + 1];
      }
      x = nx / w;
      y = ny / w;
    }
    return (x, y);
  }
}

Float64List _phang(Object? v) {
  final ra = <double>[];
  void them(Object? o) {
    if (o is List) {
      o.forEach(them);
    } else {
      ra.add((o as num).toDouble());
    }
  }

  them(v);
  return Float64List.fromList(ra);
}

Float64List _softmax(Float64List z) {
  final m = z.reduce(max);
  final p = Float64List(z.length);
  var s = 0.0;
  for (var i = 0; i < z.length; i++) {
    p[i] = exp(z[i] - m);
    s += p[i];
  }
  for (var i = 0; i < z.length; i++) {
    p[i] /= s;
  }
  return p;
}

/// HistGradientBoostingClassifier: cây thứ i*C + c là vòng i của lớp c, lá có
/// đặc trưng -1. So `x <= ngưỡng` như scikit-learn.
class _CayTangCuong {
  final Float64List _gocLop, _nguong, _giaTri;
  final Int32List _goc, _dacTrung, _trai, _phai;

  _CayTangCuong(Map<String, dynamic> j)
      : _gocLop = _phang(j['goc_lop']),
        _nguong = _phang(j['nguong']),
        _giaTri = _phang(j['gia_tri']),
        _goc = Int32List.fromList((j['goc'] as List).cast<int>()),
        _dacTrung = Int32List.fromList((j['dac_trung'] as List).cast<int>()),
        _trai = Int32List.fromList((j['trai'] as List).cast<int>()),
        _phai = Int32List.fromList((j['phai'] as List).cast<int>());

  Float64List xuoi(Float64List x, int soLop) {
    final z = Float64List.fromList(_gocLop);
    for (var t = 0; t < _goc.length; t++) {
      var n = _goc[t];
      while (_dacTrung[n] >= 0) {
        n = x[_dacTrung[n]] <= _nguong[n] ? _trai[n] : _phai[n];
      }
      z[t % soLop] += _giaTri[n];
    }
    return z;
  }
}

/// Một lớp KAN: mỗi cạnh là w·silu(a) + Σ c·B(a), B là B-spline bậc k trên lưới t.
class _LopKan {
  final int _k, _ra, _soCoSo;
  final double _h;
  final Float64List _t, _wb, _ws, _b;

  _LopKan(Map<String, dynamic> j)
      : _k = j['k'] as int,
        _h = (j['h'] as num).toDouble(),
        _t = _phang(j['t']),
        _wb = _phang(j['Wb']),
        _ws = _phang(j['Ws']),
        _b = _phang(j['b']),
        _ra = (j['b'] as List).length,
        _soCoSo = (j['t'] as List).length - 1 - (j['k'] as int);

  Float64List xuoi(Float64List a) {
    final ra = Float64List.fromList(_b);
    final co = Float64List(_t.length - 1);
    for (var i = 0; i < a.length; i++) {
      final x = a[i];
      final s = x / (1 + exp(-x));
      for (var j = 0; j < _ra; j++) {
        ra[j] += s * _wb[i * _ra + j];
      }
      var m = _t.length - 1;
      for (var q = 0; q < m; q++) {
        co[q] = x >= _t[q] && x < _t[q + 1] ? 1.0 : 0.0;
      }
      for (var p = 1; p <= _k; p++) {
        m--;
        for (var q = 0; q < m; q++) {
          co[q] = (x - _t[q]) / (p * _h) * co[q] +
              (_t[q + p + 1] - x) / (p * _h) * co[q + 1];
        }
      }
      for (var q = 0; q < _soCoSo; q++) {
        if (co[q] == 0) continue;
        final o = (i * _soCoSo + q) * _ra;
        for (var j = 0; j < _ra; j++) {
          ra[j] += co[q] * _ws[o + j];
        }
      }
    }
    return ra;
  }
}

/// Transformer trên tập AP (`ApTransformer` trong bo_ba.py, chuẩn hoá trước mỗi
/// khối). AP không nghe thấy bị che khỏi attention nên bỏ hẳn khỏi dãy token.
class _ApTransformer {
  final int _dau, _dim, _soLop;
  final double _eps;
  final Map<String, Float64List> _w;

  _ApTransformer(Map<String, dynamic> j)
      : _dau = j['dau'] as int,
        _eps = (j['eps'] as num).toDouble(),
        _dim = (j['muc.bias'] as List).length,
        _soLop = j.keys
            .where((k) => k.startsWith('tf.layers.') && k.endsWith('.norm1.weight'))
            .length,
        _w = {
          for (final e in j.entries)
            if (e.value is List) e.key: _phang(e.value)
        };

  /// Lớp tuyến tính tên [ten]; riêng chiếu Q/K/V của PyTorch tên `in_proj_weight`.
  Float64List _tuyenTinh(Float64List x, String ten, [String noi = '.']) {
    final w = _w['$ten${noi}weight']!, b = _w['$ten${noi}bias']!;
    final ra = Float64List.fromList(b);
    for (var o = 0; o < b.length; o++) {
      var s = 0.0;
      for (var i = 0, r = o * x.length; i < x.length; i++, r++) {
        s += w[r] * x[i];
      }
      ra[o] += s;
    }
    return ra;
  }

  Float64List _chuanHoa(Float64List x, String ten) {
    final w = _w['$ten.weight']!, b = _w['$ten.bias']!;
    var tb = 0.0, ps = 0.0;
    for (final v in x) {
      tb += v;
    }
    tb /= x.length;
    for (final v in x) {
      ps += (v - tb) * (v - tb);
    }
    final chia = sqrt(ps / x.length + _eps);
    return Float64List.fromList(
        [for (var i = 0; i < x.length; i++) (x[i] - tb) / chia * w[i] + b[i]]);
  }

  Float64List xuoi(Float64List x) {
    final ap = _w['ap']!, mw = _w['muc.weight']!, mb = _w['muc.bias']!;
    final h = <Float64List>[
      Float64List.fromList(_w['cls']!),
      for (var a = 0; a < x.length; a++)
        if (x[a] > 0)
          Float64List.fromList([
            for (var e = 0; e < _dim; e++) ap[a * _dim + e] + mw[e] * x[a] + mb[e]
          ]),
    ];
    final cd = _dim ~/ _dau, tiLe = 1 / sqrt(cd);
    for (var l = 0; l < _soLop; l++) {
      final ten = 'tf.layers.$l';
      final qkv = [
        for (final v in h)
          _tuyenTinh(_chuanHoa(v, '$ten.norm1'), '$ten.self_attn.in_proj', '_')
      ];
      for (var r = 0; r < h.length; r++) {
        final o = Float64List(_dim);
        for (var d = 0; d < _dau; d++) {
          final s = Float64List(h.length);
          for (var c = 0; c < h.length; c++) {
            var t = 0.0;
            for (var e = d * cd; e < (d + 1) * cd; e++) {
              t += qkv[r][e] * qkv[c][_dim + e];
            }
            s[c] = t * tiLe;
          }
          final p = _softmax(s);
          for (var c = 0; c < h.length; c++) {
            for (var e = d * cd; e < (d + 1) * cd; e++) {
              o[e] += p[c] * qkv[c][2 * _dim + e];
            }
          }
        }
        final sa = _tuyenTinh(o, '$ten.self_attn.out_proj');
        for (var e = 0; e < _dim; e++) {
          h[r][e] += sa[e];
        }
      }
      for (final v in h) {
        final an = _tuyenTinh(_chuanHoa(v, '$ten.norm2'), '$ten.linear1');
        for (var e = 0; e < an.length; e++) {
          an[e] = max(an[e], 0.0);
        }
        final ff = _tuyenTinh(an, '$ten.linear2');
        for (var e = 0; e < _dim; e++) {
          v[e] += ff[e];
        }
      }
    }
    return _tuyenTinh(_chuanHoa(h[0], 'ra.0'), 'ra.1');
  }
}

/// Bản Dart của `BoGop` (backend/services/smoothing_service.py): giữ đầu ra của
/// [cuaSo] lần quét gần nhất, im lặng quá [quenSau] thì quên.
class BoGop<T> {
  static const cuaSo = 3;
  static const quenSau = Duration(seconds: 30);

  final _lich = <T>[];
  DateTime? _lanCuoi;

  int get soMau => _lich.length;

  /// Thêm một đầu ra, trả cả cửa sổ hiện tại (cũ trước, mới sau).
  List<T> them(T dauRa, {DateTime? luc}) {
    final bayGio = luc ?? DateTime.now();
    final truoc = _lanCuoi;
    if (truoc != null && bayGio.difference(truoc) > quenSau) _lich.clear();
    _lanCuoi = bayGio;
    _lich.add(dauRa);
    if (_lich.length > cuaSo) _lich.removeAt(0);
    return List.unmodifiable(_lich);
  }

  void quen() {
    _lich.clear();
    _lanCuoi = null;
  }
}
