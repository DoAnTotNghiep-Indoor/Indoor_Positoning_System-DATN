import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'quet_wifi.dart';

/// Toạ độ trả về từ `POST /predict`, đơn vị mét.
class ViTri {
  final double x;
  final double y;

  /// Toạ độ sau khi máy chủ gộp vài lần quét gần nhau — toạ độ nên hiển thị.
  final double xGop;
  final double yGop;

  final String moHinh;
  final int soApKhop;
  final int soLanQuetDaGop;
  final double doTreMs;

  const ViTri({
    required this.x,
    required this.y,
    required this.xGop,
    required this.yGop,
    required this.moHinh,
    required this.soApKhop,
    required this.soLanQuetDaGop,
    required this.doTreMs,
  });

  factory ViTri.tuJson(Map<String, dynamic> j) => ViTri(
        x: (j['x'] as num).toDouble(),
        y: (j['y'] as num).toDouble(),
        xGop: (j['x_smooth'] as num).toDouble(),
        yGop: (j['y_smooth'] as num).toDouble(),
        moHinh: j['model'] as String,
        soApKhop: j['matched_ap'] as int,
        soLanQuetDaGop: j['scan_count'] as int,
        doTreMs: (j['latency_ms'] as num).toDouble(),
      );
}

/// Một điểm tham chiếu trên bản đồ, kèm nhãn do `GET /map` trả về.
class DiemThamChieu {
  final String rpId;
  final double x;
  final double y;
  final String ten;
  final String nhom;

  /// Mô tả và tên thư mục ảnh. Chỉ `GET /map` trả hai trường này; `POST /route`
  /// cố tình bỏ chúng nên chặng đường về sẽ có chuỗi rỗng.
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

/// Một bước chỉ đường. `huong` là mã do máy chủ trả về, không phải câu chữ —
/// ứng dụng chạy hai ngôn ngữ nên tự ghép câu lấy.
class BuocChiDan {
  final String tuRp;
  final String denRp;
  final String denTen;
  final String huong;
  final double gocDo;
  final double khoangCachM;

  const BuocChiDan({
    required this.tuRp,
    required this.denRp,
    required this.denTen,
    required this.huong,
    required this.gocDo,
    required this.khoangCachM,
  });

  factory BuocChiDan.tuJson(Map<String, dynamic> j) => BuocChiDan(
        tuRp: j['tu_rp'] as String,
        denRp: j['den_rp'] as String,
        denTen: (j['den_ten'] ?? '') as String,
        huong: j['huong'] as String,
        gocDo: (j['goc_do'] as num).toDouble(),
        khoangCachM: (j['khoang_cach_m'] as num).toDouble(),
      );
}

class KetQuaChiDuong {
  final double quangDuongM;
  final int soChang;
  final List<BuocChiDan> buoc;

  /// Toạ độ mét của từng nút trên tuyến, theo đúng thứ tự đi. Dùng để vẽ tuyến
  /// lên sơ đồ; `chi_dan` không thay thế được vì nó đã gộp các chặng đi thẳng
  /// nên thiếu điểm giữa, vẽ theo nó sẽ ra đường cắt góc xuyên tường.
  final List<DiemThamChieu> duongDi;

  const KetQuaChiDuong({
    required this.quangDuongM,
    required this.soChang,
    required this.buoc,
    this.duongDi = const [],
  });

  factory KetQuaChiDuong.tuJson(Map<String, dynamic> j) => KetQuaChiDuong(
        quangDuongM: (j['quang_duong_m'] as num).toDouble(),
        soChang: j['so_chang'] as int,
        buoc: [
          for (final b in j['chi_dan'] as List)
            BuocChiDan.tuJson(b as Map<String, dynamic>),
        ],
        duongDi: [
          for (final d in (j['duong_di'] ?? const []) as List)
            DiemThamChieu.tuJson(d as Map<String, dynamic>),
        ],
      );
}

enum LoiApi { diaChiSai, khongKetNoi, quaHan, saiDinhDang, khongDuAp, mayChuLoi }

class NgoaiLeApi implements Exception {
  final LoiApi loai;
  final int? maHttp;

  /// Số AP khớp và ngưỡng tối thiểu, chỉ có với [LoiApi.khongDuAp].
  final int? soAp;
  final int? toiThieu;

  const NgoaiLeApi(this.loai, {this.maHttp, this.soAp, this.toiThieu});
}

class ApiDinhVi {
  /// Đổi được lúc chạy: dựng ApiDinhVi mới sẽ phải đóng client cũ, mà lần quét
  /// đang bay dở dùng chính client đó.
  String diaChi;

  final http.Client _client;
  final Duration quaHan;

  ApiDinhVi(this.diaChi,
      {http.Client? client, this.quaHan = const Duration(seconds: 8)})
      : _client = client ?? http.Client();

  /// Dựng URL và chặn sớm địa chỉ không dùng được. `http` ném `ArgumentError`
  /// khi URI thiếu host, mà đó là `Error` chứ không phải `Exception` nên
  /// `on Exception` để lọt và vòng quét báo nhầm thành "quét WiFi thất bại".
  Uri _url(String duong) {
    final u = Uri.tryParse('$diaChi$duong');
    if (u == null ||
        (u.scheme != 'http' && u.scheme != 'https') ||
        u.host.isEmpty) {
      throw const NgoaiLeApi(LoiApi.diaChiSai);
    }
    return u;
  }

  /// Gửi một lần quét, nhận toạ độ. Gửi `[{bssid, rssi}]` kèm cặp chứ KHÔNG
  /// gửi mảng số trần như CTK45: mảng trần sai thứ tự thì mô hình vẫn chạy
  /// trơn và trả toạ độ sai không một cảnh báo nào.
  Future<ViTri> duDoan({
    required String deviceId,
    required List<DiemTruyCap> quet,
  }) async {
    // Dựng URL NGOÀI try: `_url` ném `NgoaiLeApi`, mà nó là `Exception` nên
    // khối `on Exception` bên dưới sẽ nuốt mất và báo nhầm thành mất kết nối.
    final url = _url('/predict');

    final http.Response tra;
    try {
      tra = await _client
          .post(
            url,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'device_id': deviceId,
              'scan': [for (final ap in quet) ap.toJson()],
            }),
          )
          .timeout(quaHan);
    } on TimeoutException {
      // Tách khỏi "không kết nối được": mạng yếu khác hẳn nhập sai địa chỉ.
      throw const NgoaiLeApi(LoiApi.quaHan);
    } on Exception {
      throw const NgoaiLeApi(LoiApi.khongKetNoi);
    }

    // 422 là "quét được nhưng không đủ AP quen để định vị" — khác hẳn lỗi máy
    // chủ. Máy chủ chặn thay vì trả một toạ độ không dựa trên dữ liệu nào.
    if (tra.statusCode == 422) throw _loi422(tra);

    if (tra.statusCode != 200) {
      throw NgoaiLeApi(LoiApi.mayChuLoi, maHttp: tra.statusCode);
    }
    try {
      return ViTri.tuJson(jsonDecode(utf8.decode(tra.bodyBytes)));
    } catch (_) {
      // Bắt cả Error chứ không chỉ Exception: JSON thiếu trường thì phép ép
      // kiểu ném TypeError, mà TypeError là Error nên `on Exception` để lọt.
      throw const NgoaiLeApi(LoiApi.saiDinhDang);
    }
  }

  /// Máy chủ dùng 422 cho HAI chuyện: `detail` là object khi thiếu AP, là danh
  /// sách khi pydantic bắt thân sai schema. Coi mọi 422 là thiếu AP thì ca thứ
  /// hai hiện thành "khớp 0, cần ít nhất 0" — câu vô nghĩa, lại đổ lỗi cho vùng
  /// phủ WiFi trong khi lỗi nằm ở gói tin gửi lên.
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

  /// Điểm tham chiếu kèm tên, tải một lần rồi giữ lại. Nhờ nó giao diện nói
  /// được "Phòng tạp chí" thay vì "x 22,0 m · y 52,0 m".
  Future<List<DiemThamChieu>> layBanDo() async {
    final url = _url('/map');

    final http.Response tra;
    try {
      tra = await _client.get(url).timeout(quaHan);
    } on TimeoutException {
      throw const NgoaiLeApi(LoiApi.quaHan);
    } on Exception {
      throw const NgoaiLeApi(LoiApi.khongKetNoi);
    }

    if (tra.statusCode != 200) {
      throw NgoaiLeApi(LoiApi.mayChuLoi, maHttp: tra.statusCode);
    }
    try {
      final ds =
          jsonDecode(utf8.decode(tra.bodyBytes))['diem_tham_chieu'] as List;
      return [
        for (final m in ds) DiemThamChieu.tuJson(m as Map<String, dynamic>),
      ];
    } catch (_) {
      throw const NgoaiLeApi(LoiApi.saiDinhDang);
    }
  }

  /// Đường đi từ toạ độ hiện tại tới khu vực [denNhom], hoặc đúng điểm [denRp]
  /// khi có. Gửi toạ độ chứ không gửi rp_id: máy chủ tự neo vào điểm gần nhất.
  Future<KetQuaChiDuong> chiDuong({
    required double tuX,
    required double tuY,
    required String denNhom,
    String? denRp,
  }) async {
    final url = _url('/route');

    final http.Response tra;
    try {
      tra = await _client
          .post(
            url,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'tu_x': tuX,
              'tu_y': tuY,
              if (denRp != null) 'den_rp': denRp else 'den_nhom': denNhom,
            }),
          )
          .timeout(quaHan);
    } on TimeoutException {
      throw const NgoaiLeApi(LoiApi.quaHan);
    } on Exception {
      throw const NgoaiLeApi(LoiApi.khongKetNoi);
    }

    if (tra.statusCode != 200) {
      throw NgoaiLeApi(LoiApi.mayChuLoi, maHttp: tra.statusCode);
    }
    try {
      return KetQuaChiDuong.tuJson(jsonDecode(utf8.decode(tra.bodyBytes)));
    } catch (_) {
      throw const NgoaiLeApi(LoiApi.saiDinhDang);
    }
  }

  void dong() => _client.close();
}
