import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import 'api_dinh_vi.dart';
import 'quet_wifi.dart';

/// Kênh đang ghép dở một yêu cầu khác — không phải lỗi kênh.
class _KenhBan implements Exception {
  const _KenhBan();
}

/// Gửi lần quét qua `WS /ws/location` thay vì mở kết nối HTTP mỗi 5 giây.
///
/// Cùng chữ ký `duDoan` với [ApiDinhVi] nên [TheoDoiViTri] không cần biết đang
/// đi lối nào; **hỏng kênh thì tự rơi về REST**.
///
/// Kênh KHÔNG làm vị trí cập nhật dày hơn: nhịp 5 giây do Android chặn quét
/// quyết định, không phải do đường truyền. Cái được là bỏ bắt tay TCP và phần
/// đầu HTTP mỗi vòng.
class KenhViTri {
  /// Bỏ chờ nếu máy chủ không trả lời trong khoảng này rồi đi lối REST. Nới
  /// rộng hơn một nhịp quét để một lần chậm không kéo theo mở lại kênh.
  static const hanChoLoi = Duration(seconds: 8);

  final ApiDinhVi _api;
  final WebSocketChannel Function(Uri) _mo;

  KenhViTri({required ApiDinhVi api, WebSocketChannel Function(Uri)? moKenh})
      : _api = api,
        _mo = moKenh ?? WebSocketChannel.connect;

  /// Đọc địa chỉ TẠI LÚC MỞ chứ không nhớ sẵn lúc dựng: người dùng đổi máy chủ
  /// trong Cài đặt thì kênh nhớ bản cũ sẽ nối mãi về chỗ không còn dùng.
  ///
  Uri get _diaChi {
    final u = Uri.parse(_api.diaChi);
    return u.replace(
      scheme: u.scheme == 'https' ? 'wss' : 'ws',
      path: '/ws/location',
    );
  }

  WebSocketChannel? _kenh;
  StreamSubscription<dynamic>? _nghe;
  Completer<Map<String, dynamic>>? _dangCho;
  String? _choDeviceId;

  bool get dangMo => _kenh != null;

  Future<ViTri> duDoan({
    required String deviceId,
    required List<DiemTruyCap> quet,
  }) async {
    try {
      return _doc(await _quaKenh(deviceId, quet));
    } on NgoaiLeApi {
      // Lỗi nghiệp vụ — không đủ AP chẳng hạn. Kênh vẫn tốt, REST sẽ trả về
      // đúng lỗi ấy nên gọi lại chỉ tốn thêm một vòng mạng.
      rethrow;
    } on _KenhBan {
      // Kênh tốt, chỉ là đang ghép dở một yêu cầu khác. KHÔNG đóng: đóng ở đây
      // là giật mất kênh của yêu cầu kia, biến một va chạm vô hại thành mất
      // định vị cho cả hai.
      return _api.duDoan(deviceId: deviceId, quet: quet);
    } catch (_) {
      dong();
      return _api.duDoan(deviceId: deviceId, quet: quet);
    }
  }

  Future<Map<String, dynamic>> _quaKenh(
      String deviceId, List<DiemTruyCap> quet) async {
    // Một kênh chỉ ghép được một yêu cầu với một câu trả lời tại mỗi thời điểm:
    // gói trả về không mang mã yêu cầu nào để phân biệt. `TheoDoiViTri` đã chặn
    // gọi chồng bằng cờ riêng của nó, nhưng bất biến này thuộc về kênh nên phải
    // gác ngay tại đây.
    if (_dangCho != null) throw const _KenhBan();

    _batDau();
    final kenh = _kenh!;

    final cho = Completer<Map<String, dynamic>>();
    _dangCho = cho;
    _choDeviceId = deviceId;

    kenh.sink.add(jsonEncode({
      'device_id': deviceId,
      'scan': [for (final d in quet) {'bssid': d.bssid, 'rssi': d.rssi}],
    }));

    return cho.future.timeout(hanChoLoi);
  }

  void _batDau() {
    if (_kenh != null) return;
    final kenh = _mo(_diaChi);
    _kenh = kenh;
    _nghe = kenh.stream.listen(_nhan,
        onError: (_) => dong(), onDone: dong, cancelOnError: true);

    // `connect` trả kênh ngay rồi bắt tay ngầm. Bắt tay hỏng thì `ready` hoàn
    // tất bằng lỗi, và đó là một Future không ai chờ nên nổi lên thành Unhandled
    // Exception — tắt máy chủ rồi đọc logcat thấy nó lặp mỗi vòng quét. Nuốt cả
    // `sink.done` vì mỗi nền tảng lại báo ra một chỗ khác nhau.
    unawaited(kenh.ready.catchError((_) {}));
    unawaited(kenh.sink.done.catchError((_) {}));
  }

  void _nhan(dynamic tho) {
    final cho = _dangCho;
    if (cho == null || cho.isCompleted) return;

    Map<String, dynamic> goi;
    try {
      goi = jsonDecode(tho as String) as Map<String, dynamic>;
    } catch (_) {
      return; // gói hỏng thì bỏ, không được làm đứt kênh
    }

    // Máy chủ phát toạ độ của MỌI thiết bị lên mọi kênh đang mở, nên phải lọc
    // theo device_id — không lọc thì ứng dụng nhận toạ độ của máy khác và hiện
    // nó như vị trí của chính mình. Gói lỗi không kèm device_id, nhưng chỉ yêu
    // cầu của chính mình mới sinh ra lỗi trên kênh này.
    if (goi['loi'] == null && goi['device_id'] != _choDeviceId) return;

    _dangCho = null;
    cho.complete(goi);
  }

  ViTri _doc(Map<String, dynamic> goi) {
    final loi = goi['loi'];
    if (loi == null) return ViTri.tuJson(goi);
    if (loi == 'khong_du_ap') {
      throw NgoaiLeApi(LoiApi.khongDuAp,
          maHttp: 422,
          soAp: goi['so_ap'] as int?,
          toiThieu: goi['toi_thieu'] as int?);
    }
    // Hai mã này nói gói tin hai bên không khớp nhau, không phải máy chủ hỏng.
    if (loi == 'khong_phai_json' || loi == 'goi_sai_dinh_dang') {
      throw const NgoaiLeApi(LoiApi.saiDinhDang);
    }
    // Kênh WS không có mã HTTP: để `maHttp` null thay vì bịa ra một con số,
    // giao diện đã có câu riêng cho trường hợp thiếu mã.
    throw const NgoaiLeApi(LoiApi.mayChuLoi);
  }

  void dong() {
    _nghe?.cancel();
    _nghe = null;
    _kenh?.sink.close();
    _kenh = null;
    _dangCho?.completeError(StateError('kênh đã đóng'));
    _dangCho = null;
  }
}
