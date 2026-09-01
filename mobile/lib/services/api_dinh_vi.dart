import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'quet_wifi.dart';

/// Toạ độ trả về từ `POST /predict`, đơn vị mét.
class ViTri {
  final double x;
  final double y;

  /// Toạ độ sau khi máy chủ gộp vài lần quét gần nhau. Đây mới là toạ độ nên
  /// hiển thị: gộp 3 lần quét đưa sai số từ 1,92 m xuống 0,38 m trên tập test.
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

  const KetQuaChiDuong({
    required this.quangDuongM,
    required this.soChang,
    required this.buoc,
  });

  factory KetQuaChiDuong.tuJson(Map<String, dynamic> j) => KetQuaChiDuong(
        quangDuongM: (j['quang_duong_m'] as num).toDouble(),
        soChang: j['so_chang'] as int,
        buoc: [
          for (final b in j['chi_dan'] as List)
            BuocChiDan.tuJson(b as Map<String, dynamic>),
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

  /// Dựng URL và chặn sớm địa chỉ không dùng được.
  ///
  /// `http` ném `ArgumentError` khi URI thiếu host — mà `ArgumentError` là
  /// `Error` chứ không phải `Exception`, nên `on Exception` để lọt và vòng quét
  /// bắt nhầm thành "quét WiFi thất bại". Người dùng vừa gõ sai địa chỉ lại đi
  /// kiểm tra quyền và WiFi.
  ///
  /// Bốn cách gõ đều rơi vào đây: `192.168.1.5`, `localhost:8000`, `may-chu`,
  /// `http://`. Chính chú thích trong `AppSettings` bảo người dùng nhập IP nội
  /// bộ, nên thiếu scheme là chuyện sẽ xảy ra thật.
  Uri _url(String duong) {
    final u = Uri.tryParse('$diaChi$duong');
    if (u == null ||
        (u.scheme != 'http' && u.scheme != 'https') ||
        u.host.isEmpty) {
      throw const NgoaiLeApi(LoiApi.diaChiSai);
    }
    return u;
  }

  /// Gửi một lần quét, nhận toạ độ.
  ///
  /// Gửi `[{bssid, rssi}]` kèm cặp chứ KHÔNG gửi mảng số trần như CTK45: mảng
  /// trần sai thứ tự thì mô hình vẫn chạy trơn và trả toạ độ sai không một
  /// cảnh báo nào.
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
    if (tra.statusCode == 422) throw _khongDuAp(tra);

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

  /// Bóc số AP khớp ra khỏi thân 422 để giao diện nói được "khớp 2/6".
  ///
  /// Thân hỏng thì vẫn trả đúng loại lỗi với số đếm rỗng: biết "không đủ AP" đã
  /// hữu ích hơn hẳn một câu lỗi HTTP chung chung.
  NgoaiLeApi _khongDuAp(http.Response tra) {
    try {
      final d = jsonDecode(utf8.decode(tra.bodyBytes))['detail'];
      return NgoaiLeApi(LoiApi.khongDuAp,
          maHttp: 422, soAp: d['so_ap'] as int, toiThieu: d['toi_thieu'] as int);
    } catch (_) {
      return const NgoaiLeApi(LoiApi.khongDuAp, maHttp: 422);
    }
  }

  /// 40 điểm tham chiếu kèm tên, tải một lần rồi giữ lại. Nhờ nó giao diện nói
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

  /// Đường đi từ toạ độ hiện tại tới một điểm tham chiếu.
  ///
  /// Gửi toạ độ mét chứ không gửi rp_id: máy chủ tự neo vào điểm gần nhất, nên
  /// ứng dụng không phải nhân đôi phép tìm điểm gần nhất ở phía mình.
  Future<KetQuaChiDuong> chiDuong({
    required double tuX,
    required double tuY,
    required String denRp,
  }) async {
    final url = _url('/route');

    final http.Response tra;
    try {
      tra = await _client
          .post(
            url,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'tu_x': tuX, 'tu_y': tuY, 'den_rp': denRp}),
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
