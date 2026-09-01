import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:ips_dlu/services/api_dinh_vi.dart';
import 'package:ips_dlu/services/quet_wifi.dart';
import 'package:ips_dlu/services/theo_doi_vi_tri.dart';

/// Thân JSON mẫu của `POST /predict`, đúng hình dạng backend trả về.
String _traLoiMau({int soApKhop = 12, int soLanQuet = 3}) => jsonEncode({
      'x': 13.0,
      'y': 41.0,
      'x_smooth': 12.5,
      'y_smooth': 40.5,
      'model': 'fingerprint_knn',
      'timestamp': '2026-08-30T10:00:00Z',
      'matched_ap': soApKhop,
      'scan_count': soLanQuet,
      'latency_ms': 0.42,
    });

/// Thân JSON mẫu của `GET /map`, rút gọn còn hai điểm.
String _banDoMau() => jsonEncode({
      'don_vi': 'met',
      'pham_vi': {'x_min': -43, 'x_max': 43, 'y_min': 0, 'y_max': 52},
      'diem_tham_chieu': [
        {
          'rp_id': 'RP39',
          'x': 22.0,
          'y': 52.0,
          'ten': 'Phòng tạp chí',
          'nhom': 'Phòng tạp chí'
        },
        {
          'rp_id': 'RP16',
          'x': -42.0,
          'y': 24.0,
          'ten': 'Hành lang',
          'nhom': 'Hành lang'
        },
      ],
      'do_thi': {
        'so_diem': 2,
        'so_canh': 1,
        'canh_ngan_nhat_m': 1.0,
        'canh_dai_nhat_m': 2.0,
        'bac_trung_binh': 1.0
      },
    });

/// Máy quét giả: trả về kết quả cố định hoặc ném đúng loại lỗi cần thử.
class _QuetGia extends MayQuetWifi {
  final Object? nem;
  _QuetGia({this.nem});

  @override
  Future<List<DiemTruyCap>> quet() async {
    if (nem != null) throw nem!;
    return const [DiemTruyCap(bssid: '88:dc:97:12:62:cf', rssi: -57)];
  }
}

void main() {
  const quetMau = [
    DiemTruyCap(bssid: '88:dc:97:12:62:cf', rssi: -57),
    DiemTruyCap(bssid: '8e:dc:97:12:65:63', rssi: -49),
  ];

  test('Gửi BSSID KÈM CẶP với RSSI, không gửi mảng số trần', () async {
    // Đây là bài test cho cải tiến cốt lõi so với đồ án CTK45. Bản cũ gửi
    // {"rssi": [-57, -49, ...]} theo đúng thứ tự cột: client sai thứ tự thì mô
    // hình vẫn chạy trơn và trả toạ độ sai không một cảnh báo nào.
    late Map<String, dynamic> daGui;
    final api = ApiDinhVi(
      'http://test',
      client: MockClient((yc) async {
        daGui = jsonDecode(yc.body);
        return http.Response(_traLoiMau(), 200);
      }),
    );

    await api.duDoan(deviceId: 'may-1', quet: quetMau);

    expect(daGui['device_id'], 'may-1');
    expect(daGui['scan'], isA<List>());
    expect(daGui['scan'][0], {'bssid': '88:dc:97:12:62:cf', 'rssi': -57});
    expect(daGui['scan'][1], {'bssid': '8e:dc:97:12:65:63', 'rssi': -49});

    // Không được có khoá nào chứa mảng số trần kiểu bản cũ.
    expect(daGui.containsKey('rssi'), isFalse);
  });

  test('Đọc đúng toạ độ đã gộp chứ không phải toạ độ thô', () async {
    final api = ApiDinhVi('http://test',
        client: MockClient((_) async => http.Response(_traLoiMau(), 200)));

    final vt = await api.duDoan(deviceId: 'may-1', quet: quetMau);

    expect(vt.x, 13.0);
    expect(vt.y, 41.0);
    expect(vt.xGop, 12.5);
    expect(vt.yGop, 40.5);
    expect(vt.moHinh, 'fingerprint_knn');
    expect(vt.soApKhop, 12);
  });

  test('Máy chủ trả mã lỗi thì giữ lại mã đó để hiện cho người dùng', () async {
    // KHÔNG dùng 422 làm mã lỗi chung: 422 nay mang nghĩa riêng "quét được
    // nhưng không đủ AP quen", xem bài kế tiếp.
    final api = ApiDinhVi('http://test',
        client: MockClient((_) async => http.Response('{}', 503)));

    await expectLater(
      api.duDoan(deviceId: 'may-1', quet: quetMau),
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.mayChuLoi)
          .having((e) => e.maHttp, 'maHttp', 503)),
    );
  });

  test('Quét được nhưng không đủ AP quen thì báo riêng, kèm số đếm', () async {
    // Đo trên máy thật ngoài thư viện: điện thoại thấy 23 AP, khớp 0, mà mô
    // hình vẫn khẳng định người dùng đứng ở RP01 trong thư viện. Máy chủ nay
    // chặn bằng 422, và ứng dụng phải nói được "khớp 2/6" chứ không gộp chung
    // vào "lỗi máy chủ".
    final api = ApiDinhVi('http://test',
        client: MockClient((_) async => http.Response.bytes(
            utf8.encode(jsonEncode({
              'detail': {'loi': 'khong_du_ap', 'so_ap': 2, 'toi_thieu': 6}
            })),
            422,
            headers: {'content-type': 'application/json'})));

    await expectLater(
      api.duDoan(deviceId: 'may-1', quet: quetMau),
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.khongDuAp)
          .having((e) => e.soAp, 'soAp', 2)
          .having((e) => e.toiThieu, 'toiThieu', 6)),
    );
  });

  test('Thân 422 hỏng thì vẫn báo đúng loại lỗi, chỉ thiếu số đếm', () async {
    final api = ApiDinhVi('http://test',
        client: MockClient((_) async => http.Response('khong-phai-json', 422)));

    await expectLater(
      api.duDoan(deviceId: 'may-1', quet: quetMau),
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.khongDuAp)
          .having((e) => e.soAp, 'soAp', isNull)),
    );
  });

  test('Không đủ AP thì XOÁ toạ độ cũ, không giữ tên phòng cũ trên màn hình',
      () async {
    // Giữ lại toạ độ cũ thì giao diện vẫn hiện tên phòng như thể người dùng
    // còn đứng đó, trong khi lần quét mới nói rõ là không biết ở đâu.
    // Phân nhánh theo đường dẫn: `batDau` gọi /map TRƯỚC /predict, đếm chung
    // thì lần quét đầu đã tiêu mất lượt trả lời thành công.
    var lanDau = true;
    final td = TheoDoiViTri(
      diaChiMayChu: 'http://x',
      mayQuet: _QuetGia(),
      api: ApiDinhVi('http://x', client: MockClient((yc) async {
        if (yc.url.path.endsWith('/map')) {
          return http.Response.bytes(utf8.encode(_banDoMau()), 200,
              headers: {'content-type': 'application/json'});
        }
        if (lanDau) {
          lanDau = false;
          return http.Response.bytes(utf8.encode(_traLoiMau()), 200,
              headers: {'content-type': 'application/json'});
        }
        return http.Response.bytes(
            utf8.encode(jsonEncode({
              'detail': {'loi': 'khong_du_ap', 'so_ap': 0, 'toi_thieu': 6}
            })),
            422,
            headers: {'content-type': 'application/json'});
      })),
    );

    td.batDau();
    await Future.delayed(const Duration(milliseconds: 100));
    expect(td.viTri, isNotNull, reason: 'lần quét đầu phải có toạ độ');

    // Ép một vòng quét nữa qua API công khai: xuống nền rồi quay lên sẽ dừng
    // và bật lại, mà `batDau` quét ngay chứ không đợi hết chu kỳ 5 giây.
    td.doiVongDoi(AppLifecycleState.paused);
    td.doiVongDoi(AppLifecycleState.resumed);
    await Future.delayed(const Duration(milliseconds: 150));

    expect(td.viTri, isNull, reason: 'toạ độ cũ phải bị xoá');
    expect(td.loiApi, LoiApi.khongDuAp);
    td.dispose();
  });

  test('Không nối được máy chủ thì báo đúng loại lỗi', () async {
    final api = ApiDinhVi('http://test',
        client:
            MockClient((_) async => throw http.ClientException('rớt mạng')));

    await expectLater(
      api.duDoan(deviceId: 'may-1', quet: quetMau),
      throwsA(
          isA<NgoaiLeApi>().having((e) => e.loai, 'loai', LoiApi.khongKetNoi)),
    );
  });

  test('Máy chủ trả JSON thiếu trường thì báo sai định dạng', () async {
    final api = ApiDinhVi('http://test',
        client: MockClient((_) async => http.Response('{"x": 1}', 200)));

    await expectLater(
      api.duDoan(deviceId: 'may-1', quet: quetMau),
      throwsA(
          isA<NgoaiLeApi>().having((e) => e.loai, 'loai', LoiApi.saiDinhDang)),
    );
  });

  test('Mã thiết bị giữ nguyên giữa các lần quét', () {
    final theoDoi = TheoDoiViTri(diaChiMayChu: 'http://test');
    addTearDown(theoDoi.dispose);

    // Máy chủ gộp các lần quét theo device_id; mã đổi giữa chừng thì cửa sổ gộp
    // bị cắt và toạ độ mất phần hậu xử lý.
    expect(theoDoi.deviceId, theoDoi.deviceId);
    expect(theoDoi.deviceId, startsWith('dlu-'));
  });

  test('Chưa bật thì không có toạ độ và trạng thái là dừng', () {
    final theoDoi = TheoDoiViTri(diaChiMayChu: 'http://test');
    addTearDown(theoDoi.dispose);

    expect(theoDoi.trangThai, TrangThai.dung);
    expect(theoDoi.viTri, isNull);
  });

  test('Lỗi không lường trước vẫn chuyển sang trạng thái lỗi', () async {
    // wifi_scan ném PlatformException khi kênh nền tảng hỏng — không thuộc hai
    // loại đã bắt riêng. Thiếu nhánh bắt chung thì trạng thái kẹt ở dangChay và
    // người dùng nhìn "Đang quét…" mãi mà không biết vì sao.
    final theoDoi = TheoDoiViTri(
      diaChiMayChu: 'http://test',
      mayQuet: _QuetGia(nem: StateError('kênh nền tảng hỏng')),
    );
    addTearDown(theoDoi.dispose);

    theoDoi.batDau();
    await Future.delayed(const Duration(milliseconds: 100));

    expect(theoDoi.trangThai, TrangThai.loi);
    expect(theoDoi.loiQuet, LoiQuet.thatBai);
    theoDoi.dungLai();
  });

  test('Huỷ giữa lúc đang quét không ném lỗi dùng-sau-dispose', () async {
    // Bắt trực tiếp lỗi Flutter ghi nhận, không dựa vào việc test tự đỏ:
    // notifyListeners() sau dispose ném FlutterError từ trong khối finally của
    // một Future không ai chờ, nên có thể trôi qua mà không ai thấy.
    final daBat = <FlutterErrorDetails>[];
    final cu = FlutterError.onError;
    FlutterError.onError = daBat.add;
    addTearDown(() => FlutterError.onError = cu);

    final theoDoi =
        TheoDoiViTri(diaChiMayChu: 'http://test', mayQuet: _QuetGia());
    theoDoi.batDau();
    theoDoi.dispose(); // lần quét đang bay dở vẫn chạy nốt sau khi đã huỷ
    await Future.delayed(const Duration(milliseconds: 200));

    expect(daBat, isEmpty,
        reason: 'Lỗi ghi nhận được: ${daBat.map((e) => e.exception)}');
  });

  test('Máy chủ trả lời chậm thì báo quá hạn, không báo mất kết nối', () async {
    final api = ApiDinhVi(
      'http://test',
      quaHan: const Duration(milliseconds: 30),
      client: MockClient((_) async {
        await Future.delayed(const Duration(milliseconds: 300));
        return http.Response(_traLoiMau(), 200);
      }),
    );

    await expectLater(
      api.duDoan(deviceId: 'may-1', quet: quetMau),
      throwsA(isA<NgoaiLeApi>().having((e) => e.loai, 'loai', LoiApi.quaHan)),
    );
  });

  test('Đổi địa chỉ máy chủ không đóng client đang dùng dở', () async {
    var soLanGoi = 0;
    final api = ApiDinhVi('http://cu', client: MockClient((yc) async {
      soLanGoi++;
      return http.Response(_traLoiMau(), 200);
    }));
    final theoDoi =
        TheoDoiViTri(diaChiMayChu: 'http://cu', mayQuet: _QuetGia(), api: api);
    addTearDown(theoDoi.dispose);

    theoDoi.doiMayChu('http://moi');
    await api.duDoan(deviceId: 'may-1', quet: quetMau);

    expect(api.diaChi, 'http://moi');
    expect(soLanGoi, 1);
  });

  test('Xuống nền thì dừng quét, quay lên thì quét lại', () async {
    final theoDoi =
        TheoDoiViTri(diaChiMayChu: 'http://test', mayQuet: _QuetGia());
    addTearDown(theoDoi.dispose);

    theoDoi.batDau();
    expect(theoDoi.trangThai, isNot(TrangThai.dung));

    theoDoi.doiVongDoi(AppLifecycleState.paused);
    expect(theoDoi.trangThai, TrangThai.dung);

    theoDoi.doiVongDoi(AppLifecycleState.resumed);
    expect(theoDoi.trangThai, isNot(TrangThai.dung));
    theoDoi.dungLai();
  });

  test('Người dùng tự bấm dừng thì quay lên nền KHÔNG tự quét lại', () async {
    final theoDoi =
        TheoDoiViTri(diaChiMayChu: 'http://test', mayQuet: _QuetGia());
    addTearDown(theoDoi.dispose);

    theoDoi.batDau();
    theoDoi.dungLai();
    theoDoi.doiVongDoi(AppLifecycleState.paused);
    theoDoi.doiVongDoi(AppLifecycleState.resumed);

    expect(theoDoi.trangThai, TrangThai.dung);
  });

  test('Đọc được danh sách điểm tham chiếu kèm tên từ GET /map', () async {
    final api = ApiDinhVi('http://test', client: MockClient((yc) async {
      expect(yc.url.path, '/map');
      return http.Response.bytes(utf8.encode(_banDoMau()), 200);
    }));

    final ds = await api.layBanDo();

    expect(ds, hasLength(2));
    expect(ds[0].rpId, 'RP39');
    expect(ds[0].ten, 'Phòng tạp chí');
    expect(ds[1].nhom, 'Hành lang');
  });

  test('Tên khu vực lấy theo điểm tham chiếu gần toạ độ nhất', () async {
    // Mô hình vân tay luôn trả về đúng toạ độ một điểm tham chiếu, nên phép tìm
    // gần nhất này thường khớp tuyệt đối chứ không phải xấp xỉ.
    final api = ApiDinhVi('http://test', client: MockClient((yc) async {
      return yc.url.path == '/map'
          ? http.Response.bytes(utf8.encode(_banDoMau()), 200)
          : http.Response(_traLoiMau(), 200);
    }));
    final theoDoi = TheoDoiViTri(
        diaChiMayChu: 'http://test', mayQuet: _QuetGia(), api: api);
    addTearDown(theoDoi.dispose);

    theoDoi.batDau();
    await Future.delayed(const Duration(milliseconds: 200));
    theoDoi.dungLai();

    // _traLoiMau trả x_smooth 12,5 · y_smooth 40,5 — gần RP39 (22, 52) hơn hay
    // gần RP16 (-42, 24) hơn thì tên phải theo đúng điểm đó.
    expect(theoDoi.tenKhuVuc, 'Phòng tạp chí');
  });

  test('Chưa tải được bản đồ thì không có tên, giao diện lùi về toạ độ', () {
    final theoDoi = TheoDoiViTri(diaChiMayChu: 'http://test');
    addTearDown(theoDoi.dispose);

    expect(theoDoi.tenKhuVuc, isNull);
  });
}
