import 'dart:async';
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:stream_channel/stream_channel.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'package:ips_dlu/services/api_dinh_vi.dart';
import 'package:ips_dlu/services/kenh_vi_tri.dart';
import 'package:ips_dlu/services/quet_wifi.dart';

/// Kiểm thử kênh WebSocket gửi lần quét. Hai bất biến nguy hiểm nhất:
///
/// 1. Máy chủ phát toạ độ của MỌI thiết bị lên MỌI kênh đang mở. Không lọc theo
///    `device_id` thì ứng dụng hiện toạ độ của máy khác như vị trí của chính
///    mình — sai lặng lẽ, giao diện trông vẫn bình thường.
/// 2. Kênh hỏng phải rơi về REST: mất định vị hẳn tệ hơn mất phần tiết kiệm.

const _quet = [DiemTruyCap(bssid: '88:dc:97:12:62:cf', rssi: -57)];

String _goi({required String deviceId, double x = 12, double y = 34}) =>
    jsonEncode({
      'device_id': deviceId,
      'x': x, 'y': y, 'x_smooth': x, 'y_smooth': y,
      'model': 'fingerprint_knn', 'timestamp': '2026-09-03T10:00:00Z',
      'matched_ap': 12, 'scan_count': 3, 'latency_ms': 0.4,
    });

/// Kênh giả: ghi lại thứ gửi lên, cho bài test tự bơm thứ trả về.
class _KenhGia extends StreamChannelMixin implements WebSocketChannel {
  final _vao = StreamController<dynamic>.broadcast();
  final xong = Completer<void>();
  final sinkXong = Completer<void>();
  final guiDi = <String>[];
  var daDong = false;

  @override
  Stream<dynamic> get stream => _vao.stream;

  @override
  Future<void> get ready => xong.future;

  @override
  WebSocketSink get sink => _SinkGia(this);

  void tra(String s) => _vao.add(s);
  void hong() => _vao.addError(StateError('rớt mạng'));

  /// Bắt tay hỏng: máy chủ tắt thì CHỈ `ready` báo lỗi — stream im lặng và
  /// `sink.done` cũng vậy, đúng như `web_socket_channel` 3.0.3 hành xử trên
  /// máy thật. Bản vá đầu tiên chỉ nuốt `sink.done` nên không đỡ được gì.
  void batTayHong() {
    if (!xong.isCompleted) xong.completeError(StateError('không nối được'));
  }

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

class _SinkGia implements WebSocketSink {
  final _KenhGia _k;
  _SinkGia(this._k);

  @override
  void add(dynamic data) => _k.guiDi.add(data as String);

  @override
  Future<void> get done => _k.sinkXong.future;

  @override
  Future<void> close([int? code, String? reason]) async {
    _k.daDong = true;
    if (!_k.sinkXong.isCompleted) _k.sinkXong.complete();
  }

  @override
  dynamic noSuchMethod(Invocation i) => super.noSuchMethod(i);
}

ApiDinhVi _apiRest({int ma = 200, String? than}) => ApiDinhVi(
      'http://x',
      client: MockClient((_) async => http.Response.bytes(
            utf8.encode(than ?? _goi(deviceId: 'rest', x: 99, y: 99)),
            ma,
            headers: {'content-type': 'application/json'},
          )),
    );

void main() {
  test('Gửi lần quét lên kênh rồi nhận lại đúng toạ độ của mình', () async {
    final gia = _KenhGia();
    final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

    final ket = kenh.duDoan(deviceId: 'may-toi', quet: _quet);
    await Future<void>.delayed(Duration.zero);

    expect(gia.guiDi, hasLength(1));
    final da = jsonDecode(gia.guiDi.single) as Map<String, dynamic>;
    expect(da['device_id'], 'may-toi');
    expect((da['scan'] as List).single, {
      'bssid': '88:dc:97:12:62:cf',
      'rssi': -57,
    });

    gia.tra(_goi(deviceId: 'may-toi', x: 12, y: 34));
    final vt = await ket;
    expect(vt.x, 12);
    expect(vt.y, 34);
    kenh.dong();
  });

  test('Toạ độ của máy KHÁC phát lên kênh thì bỏ qua, không nhận nhầm',
      () async {
    final gia = _KenhGia();
    final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

    final ket = kenh.duDoan(deviceId: 'may-toi', quet: _quet);
    await Future<void>.delayed(Duration.zero);

    // Máy chủ phát toạ độ của một thiết bị khác lên cùng kênh này.
    gia.tra(_goi(deviceId: 'may-khac', x: 1, y: 1));
    await Future<void>.delayed(Duration.zero);

    // Rồi mới tới câu trả lời thật của mình.
    gia.tra(_goi(deviceId: 'may-toi', x: 12, y: 34));
    final vt = await ket;
    expect(vt.x, 12, reason: 'đã nhận nhầm toạ độ của máy khác');
    expect(vt.y, 34);
    kenh.dong();
  });

  test('Không đủ AP trên kênh ném đúng lỗi, kèm cả hai con số', () async {
    final gia = _KenhGia();
    final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

    final ket = kenh.duDoan(deviceId: 'may-toi', quet: _quet);
    await Future<void>.delayed(Duration.zero);
    gia.tra(jsonEncode({'loi': 'khong_du_ap', 'so_ap': 0, 'toi_thieu': 6}));

    await expectLater(
      ket,
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.khongDuAp)
          .having((e) => e.soAp, 'soAp', 0)
          .having((e) => e.toiThieu, 'toiThieu', 6)),
    );
    kenh.dong();
  });

  test('Kênh rớt thì rơi về REST chứ không mất định vị', () async {
    final gia = _KenhGia();
    final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

    final ket = kenh.duDoan(deviceId: 'may-toi', quet: _quet);
    await Future<void>.delayed(Duration.zero);
    gia.hong();

    final vt = await ket;
    expect(vt.x, 99, reason: 'phải là toạ độ do lối REST trả về');
    expect(kenh.dangMo, isFalse, reason: 'kênh hỏng phải được đóng lại');
  });

  test('Gói hỏng không làm đứt kênh', () async {
    final gia = _KenhGia();
    final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

    final ket = kenh.duDoan(deviceId: 'may-toi', quet: _quet);
    await Future<void>.delayed(Duration.zero);

    gia.tra('{ đây không phải JSON');
    await Future<void>.delayed(Duration.zero);
    expect(kenh.dangMo, isTrue);

    gia.tra(_goi(deviceId: 'may-toi'));
    await ket;
    kenh.dong();
  });

  test('Đổi máy chủ thì kênh cũ đóng lại để nối về địa chỉ mới', () async {
    final api = _apiRest();
    final moiLanMo = <Uri>[];
    final kenh = KenhViTri(api: api, moKenh: (u) {
      moiLanMo.add(u);
      return _KenhGia();
    });

    kenh.duDoan(deviceId: 'x', quet: _quet).ignore();
    await Future<void>.delayed(Duration.zero);
    expect(moiLanMo.single.toString(), 'ws://x/ws/location');

    kenh.dong();
    api.diaChi = 'https://vidu.vn';
    kenh.duDoan(deviceId: 'x', quet: _quet).ignore();
    await Future<void>.delayed(Duration.zero);
    expect(moiLanMo.last.toString(), 'wss://vidu.vn/ws/location',
        reason: 'kênh vẫn nhớ địa chỉ cũ');
    kenh.dong();
  });

  test('Yêu cầu thứ hai chồng lên không được giật kênh của yêu cầu đầu',
      () async {
    // Gói trả về không mang mã yêu cầu, nên kênh chỉ ghép được một cặp
    // hỏi-đáp tại mỗi thời điểm. Nếu cái thứ hai đóng kênh để rơi về REST thì
    // cái thứ nhất mất luôn câu trả lời — một va chạm vô hại thành hỏng cả hai.
    final gia = _KenhGia();
    final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

    final mot = kenh.duDoan(deviceId: 'may-toi', quet: _quet);
    await Future<void>.delayed(Duration.zero);

    final hai = await kenh.duDoan(deviceId: 'may-toi', quet: _quet);
    expect(hai.x, 99, reason: 'cái thứ hai phải đi lối REST');
    expect(kenh.dangMo, isTrue, reason: 'kênh bị đóng oan');
    expect(gia.daDong, isFalse);

    gia.tra(_goi(deviceId: 'may-toi', x: 12, y: 34));
    expect((await mot).x, 12, reason: 'cái thứ nhất mất câu trả lời');
    kenh.dong();
  });

  test('Bắt tay hỏng không để lọt ngoại lệ chưa bắt', () async {
    final gia = _KenhGia();
    final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

    final tuong = kenh.duDoan(deviceId: 'may-1', quet: _quet);
    gia.batTayHong();

    // Lỗi bắt tay không đi qua stream nên `onError` của listen không thấy;
    // không ai chờ `ready` thì Flutter báo Unhandled Exception mỗi vòng quét.
    await expectLater(Future.delayed(const Duration(milliseconds: 50)),
        completes);

    gia.tra(_goi(deviceId: 'may-1'));
    expect((await tuong).x, 12);
  });

  test('Gói lỗi định dạng KHÔNG bị quy thành lỗi máy chủ', () async {
    // `khong_phai_json` và `goi_sai_dinh_dang` nói gói tin hai bên lệch nhau.
    // Gộp cả vào `mayChuLoi` thì giao diện đổ lỗi cho máy chủ, kèm mã 0 vô nghĩa.
    for (final ma in ['khong_phai_json', 'goi_sai_dinh_dang']) {
      final gia = _KenhGia();
      final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

      final ket = kenh.duDoan(deviceId: 'may-toi', quet: _quet);
      await Future<void>.delayed(Duration.zero);
      gia.tra(jsonEncode({'loi': ma}));

      await expectLater(
        ket,
        throwsA(isA<NgoaiLeApi>()
            .having((e) => e.loai, 'loai cua $ma', LoiApi.saiDinhDang)),
      );
      kenh.dong();
    }
  });

  test('Lỗi lạ trên kênh để maHttp null, không bịa ra mã HTTP', () async {
    final gia = _KenhGia();
    final kenh = KenhViTri(api: _apiRest(), moKenh: (_) => gia);

    final ket = kenh.duDoan(deviceId: 'may-toi', quet: _quet);
    await Future<void>.delayed(Duration.zero);
    gia.tra(jsonEncode({'loi': 'mot_ma_chua_biet'}));

    await expectLater(
      ket,
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.mayChuLoi)
          .having((e) => e.maHttp, 'maHttp', isNull)),
    );
    kenh.dong();
  });
}
