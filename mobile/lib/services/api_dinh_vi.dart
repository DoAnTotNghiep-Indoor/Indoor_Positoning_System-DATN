import 'dart:async';
import 'dart:convert';
import 'dart:ui' show Offset;

import 'package:http/http.dart' as http;

import 'quet_wifi.dart';

/// Toạ độ đơn vị lưới của sơ đồ, từ `POST /predict` hoặc tính trên máy.
class ViTri {
  final double x;
  final double y;

  /// Toạ độ sau khi gộp vài lần quét gần nhau — toạ độ nên hiển thị.
  final double xGop;
  final double yGop;

  /// Độ trải toạ độ các láng giềng, đơn vị lưới: chỉ báo tương đối (lớn là kém tin),
  /// không phải bán kính sai số có độ phủ cố định.
  final double doTrai;

  final String moHinh;
  final int soApKhop;
  final int soLanQuetDaGop;
  final double doTreMs;

  /// Tính ngay trên điện thoại (tuỳ chọn "Mô hình cục bộ"), không qua máy chủ.
  final bool cucBo;

  const ViTri({
    required this.x,
    required this.y,
    required this.xGop,
    required this.yGop,
    required this.doTrai,
    required this.moHinh,
    required this.soApKhop,
    required this.soLanQuetDaGop,
    required this.doTreMs,
    this.cucBo = false,
  });

  factory ViTri.tuJson(Map<String, dynamic> j) => ViTri(
        x: (j['x'] as num).toDouble(),
        y: (j['y'] as num).toDouble(),
        xGop: (j['x_smooth'] as num).toDouble(),
        yGop: (j['y_smooth'] as num).toDouble(),
        // Máy chủ của nhóm hợp tác có thể không trả trường này: 0 là không vẽ quầng.
        doTrai: (j['do_trai'] as num?)?.toDouble() ?? 0,
        moHinh: j['model'] as String,
        soApKhop: j['matched_ap'] as int,
        soLanQuetDaGop: j['scan_count'] as int,
        doTreMs: (j['latency_ms'] as num).toDouble(),
      );
}

class DiemThamChieu {
  final String rpId;
  final double x;
  final double y;
  final String ten;
  final String nhom;

  /// Chỉ `GET /map` trả ba trường này; nút trên tuyến của `POST /route` để rỗng.
  final String moTa;
  final String moTaChiTiet;
  final String thuMucAnh;

  const DiemThamChieu({
    required this.rpId,
    required this.x,
    required this.y,
    required this.ten,
    required this.nhom,
    this.moTa = '',
    this.moTaChiTiet = '',
    this.thuMucAnh = '',
  });

  factory DiemThamChieu.tuJson(Map<String, dynamic> j) => DiemThamChieu(
        rpId: j['rp_id'] as String,
        x: (j['x'] as num).toDouble(),
        y: (j['y'] as num).toDouble(),
        ten: (j['ten'] ?? '') as String,
        nhom: (j['nhom'] ?? '') as String,
        moTa: (j['mo_ta'] ?? '') as String,
        moTaChiTiet: (j['mo_ta_chi_tiet'] ?? '') as String,
        thuMucAnh: (j['thu_muc_anh'] ?? '') as String,
      );
}

class KetQuaChiDuong {
  final double quangDuongM;
  final int soChang;

  /// Mọi nút trên tuyến theo thứ tự đi. Không vẽ theo `chi_dan`: nó đã gộp các
  /// chặng thẳng hàng nên thiếu điểm giữa, vẽ ra sẽ cắt góc xuyên tường.
  final List<DiemThamChieu> duongDi;

  const KetQuaChiDuong({
    required this.quangDuongM,
    required this.soChang,
    this.duongDi = const [],
  });

  factory KetQuaChiDuong.tuJson(Map<String, dynamic> j) => KetQuaChiDuong(
        quangDuongM: (j['quang_duong_m'] as num).toDouble(),
        soChang: j['so_chang'] as int,
        duongDi: [
          for (final d in (j['duong_di'] ?? const []) as List)
            DiemThamChieu.tuJson(d as Map<String, dynamic>),
        ],
      );
}

enum LoiApi {
  diaChiSai,
  khongKetNoi,
  quaHan,
  saiDinhDang,
  khongDuAp,
  mayChuLoi
}

class NgoaiLeApi implements Exception {
  final LoiApi loai;
  final int? maHttp;

  final int? soAp;
  final int? toiThieu;

  const NgoaiLeApi(this.loai, {this.maHttp, this.soAp, this.toiThieu});
}

class ApiDinhVi {
  /// Đổi tại chỗ thay vì dựng lại: lần quét đang bay dở dùng chính client này.
  String diaChi;

  final http.Client _client;
  final Duration quaHan;

  ApiDinhVi(this.diaChi,
      {http.Client? client, this.quaHan = const Duration(seconds: 8)})
      : _client = client ?? http.Client();

  /// `http` ném `ArgumentError` (một `Error`, không phải `Exception`) khi URI
  /// thiếu host, nên phải chặn trước — gọi ngoài khối try của nơi dùng.
  Uri _url(String duong) {
    final u = Uri.tryParse('$diaChi$duong');
    if (u == null ||
        (u.scheme != 'http' && u.scheme != 'https') ||
        u.host.isEmpty) {
      throw const NgoaiLeApi(LoiApi.diaChiSai);
    }
    return u;
  }

  Future<http.Response> _gui(Future<http.Response> yeuCau) async {
    try {
      return await yeuCau.timeout(quaHan);
    } on TimeoutException {
      throw const NgoaiLeApi(LoiApi.quaHan);
    } on Exception {
      throw const NgoaiLeApi(LoiApi.khongKetNoi);
    }
  }

  /// Bắt cả `Error`: JSON thiếu trường thì phép ép kiểu ném `TypeError`.
  T _doc<T>(http.Response tra, T Function(dynamic) doi) {
    if (tra.statusCode != 200) {
      throw NgoaiLeApi(LoiApi.mayChuLoi, maHttp: tra.statusCode);
    }
    try {
      return doi(jsonDecode(utf8.decode(tra.bodyBytes)));
    } catch (_) {
      throw const NgoaiLeApi(LoiApi.saiDinhDang);
    }
  }

  /// Gửi `[{bssid, rssi}]` chứ không gửi mảng số trần như CTK45: mảng trần sai
  /// thứ tự thì mô hình vẫn trả toạ độ sai mà không cảnh báo gì.
  Future<ViTri> duDoan({
    required String deviceId,
    required List<DiemTruyCap> quet,
  }) async {
    final url = _url('/predict');
    final tra = await _gui(_client.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'device_id': deviceId,
        'scan': [for (final ap in quet) ap.toJson()],
      }),
    ));
    if (tra.statusCode == 422) throw _loi422(tra);
    return _doc(tra, (j) => ViTri.tuJson(j as Map<String, dynamic>));
  }

  /// 422 mang hai nghĩa: `detail` là object khi thiếu AP, là danh sách khi
  /// pydantic bắt thân sai schema. Gộp làm một sẽ đổ lỗi nhầm cho vùng phủ WiFi.
  NgoaiLeApi _loi422(http.Response tra) {
    Object? d;
    try {
      d = (jsonDecode(utf8.decode(tra.bodyBytes)) as Map)['detail'];
    } catch (_) {
      return const NgoaiLeApi(LoiApi.saiDinhDang, maHttp: 422);
    }
    if (d is! Map || d['loi'] != 'khong_du_ap') {
      return const NgoaiLeApi(LoiApi.saiDinhDang, maHttp: 422);
    }
    return NgoaiLeApi(LoiApi.khongDuAp,
        maHttp: 422,
        soAp: (d['so_ap'] as num?)?.toInt(),
        toiThieu: (d['toi_thieu'] as num?)?.toInt());
  }

  Future<List<DiemThamChieu>> layBanDo() async {
    final url = _url('/map');
    final tra = await _gui(_client.get(url));
    return _doc(
        tra,
        (j) => [
              for (final m in j['diem_tham_chieu'] as List)
                DiemThamChieu.tuJson(m as Map<String, dynamic>),
            ]);
  }

  Future<KetQuaChiDuong> chiDuong({
    required double tuX,
    required double tuY,
    required String denNhom,
    String? denRp,
    Offset? den,
  }) async {
    final url = _url('/route');
    final tra = await _gui(_client.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'tu_x': tuX,
        'tu_y': tuY,
        if (den != null) ...{'den_x': den.dx, 'den_y': den.dy}
        else if (denRp != null) 'den_rp': denRp
        else 'den_nhom': denNhom,
      }),
    ));
    return _doc(tra, (j) => KetQuaChiDuong.tuJson(j as Map<String, dynamic>));
  }

  void dong() => _client.close();
}
