import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:ips_dlu/services/api_dinh_vi.dart';
import 'package:ips_dlu/services/quet_wifi.dart';
import 'package:ips_dlu/services/theo_doi_vi_tri.dart';

/// Lớp gọi API của ứng dụng: POST /predict, GET /map, hình dạng JSON của
/// POST /route, mã lỗi và địa chỉ máy chủ sai.

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

/// Máy quét giả trả về kết quả cố định.
class _QuetGia extends MayQuetWifi {
  @override
  Future<List<DiemTruyCap>> quet() async =>
      const [DiemTruyCap(bssid: '88:dc:97:12:62:cf', rssi: -57)];
}

/// Tuyến 3 chặng mà `chi_dan` chỉ có 2 bước: hai chặng đầu thẳng hàng nên máy
/// chủ gộp lại. Đây đúng là ca phân biệt được hai nguồn dữ liệu.
String _tuyen() => jsonEncode({
      'tu': 'RP09', 'den': 'RP39',
      'quang_duong_m': 41.5,
      'so_chang': 3,
      'duong_di': [
        {'rp_id': 'RP09', 'x': 30.0, 'y': 14.0,
         'ten': 'Căn tin', 'nhom': 'Căn tin'},
        {'rp_id': 'RP10', 'x': 30.0, 'y': 24.0, 'ten': '', 'nhom': ''},
        {'rp_id': 'RP11', 'x': 30.0, 'y': 34.0, 'ten': '', 'nhom': ''},
        {'rp_id': 'RP39', 'x': 22.0, 'y': 52.0,
         'ten': 'Phòng tạp chí', 'nhom': 'Phòng tạp chí'},
      ],
      'chi_dan': [
        {'tu_rp': 'RP09', 'den_rp': 'RP11', 'den_ten': '',
         'huong': 'bat_dau', 'goc_do': 0.0, 'khoang_cach_m': 20.0},
        {'tu_rp': 'RP11', 'den_rp': 'RP39', 'den_ten': 'Phòng tạp chí',
         'huong': 're_trai', 'goc_do': 24.0, 'khoang_cach_m': 21.5},
      ],
    });

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

  test('Thân 422 không đọc được thì KHÔNG quy thành thiếu AP', () async {
    // 422 chỉ có nghĩa thiếu AP khi thân nói đúng như vậy.
    final api = ApiDinhVi('http://test',
        client: MockClient((_) async => http.Response('khong-phai-json', 422)));

    await expectLater(
      api.duDoan(deviceId: 'may-1', quet: quetMau),
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.saiDinhDang)),
    );
  });

  test('422 của pydantic không bị đọc nhầm thành thiếu AP', () async {
    // Thân thật của FastAPI khi request sai schema: `detail` là DANH SÁCH, chứ
    // không phải object như thân khong_du_ap. Quy nhầm thì giao diện hiện
    // "khớp 0 access point, cần ít nhất 0".
    const than = '{"detail":[{"type":"missing","loc":["body","device_id"],'
        '"msg":"Field required"}]}';
    final api = ApiDinhVi('http://test',
        client: MockClient((_) async => http.Response.bytes(
              utf8.encode(than),
              422,
              headers: {'content-type': 'application/json'},
            )));

    await expectLater(
      api.duDoan(deviceId: 'may-1', quet: quetMau),
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.saiDinhDang)),
    );
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

  group('Địa chỉ máy chủ thiếu scheme hoặc thiếu tên máy', () {
    // `http` ném ArgumentError — là Error chứ không phải Exception — nên
    // `on Exception` để lọt và vòng quét bắt nhầm thành "quét WiFi thất bại".
    for (final dc in ['192.168.1.5', 'localhost:8000', 'may-chu', 'http://']) {
      test('"$dc" báo đúng là sai địa chỉ', () async {
        final api = ApiDinhVi(dc);
        await expectLater(
          api.duDoan(deviceId: 'd',
              quet: const [DiemTruyCap(bssid: 'aa:bb', rssi: -1)]),
          throwsA(isA<NgoaiLeApi>()
              .having((e) => e.loai, 'loai', LoiApi.diaChiSai)),
        );
        api.dong();
      });
    }
  });

  test('Địa chỉ đúng dạng nhưng không tới được thì báo mất kết nối', () async {
    // Phân biệt được hai loại mới có ích: một bên sửa ô địa chỉ, một bên kiểm
    // tra mạng.
    //
    // Dùng client giả ném SocketException chứ không trỏ vào một tên miền không
    // tồn tại: máy có DNS bắt tên sai sẽ trả về một trang lỗi thật, và bài test
    // nhận `mayChuLoi` thay vì `khongKetNoi`.
    final api = ApiDinhVi('http://co-that:8000',
        client: MockClient((_) async =>
            throw const SocketException('không tới được')));
    await expectLater(
      api.duDoan(deviceId: 'd', quet: const [DiemTruyCap(bssid: 'a', rssi: -1)]),
      throwsA(isA<NgoaiLeApi>()
          .having((e) => e.loai, 'loai', LoiApi.khongKetNoi)),
    );
    api.dong();
  });

  test('layBanDo cũng chặn địa chỉ sai chứ không riêng duDoan', () async {
    final api = ApiDinhVi('192.168.1.5');
    await expectLater(
      api.layBanDo(),
      throwsA(isA<NgoaiLeApi>().having((e) => e.loai, 'loai', LoiApi.diaChiSai)),
    );
    api.dong();
  });

  test('Tuyến giữ đủ nút trung gian, không rút gọn theo chỉ dẫn', () {
    final kq =
        KetQuaChiDuong.tuJson(jsonDecode(_tuyen()) as Map<String, dynamic>);

    // 3 chặng nên 4 nút; chỉ dẫn chỉ có 2 bước vì đã gộp đoạn thẳng. Vẽ theo
    // chỉ dẫn sẽ mất RP10 và RP11, tuyến cắt thẳng góc qua chỗ có tường.
    expect(kq.duongDi.length, kq.soChang + 1);
    expect(kq.buoc.length, lessThan(kq.duongDi.length - 1));
    expect(kq.duongDi.map((d) => d.rpId).toList(),
        ['RP09', 'RP10', 'RP11', 'RP39']);
  });

  test('Thiếu duong_di thì trả danh sách rỗng chứ không ném lỗi', () {
    // Máy chủ cũ chưa trả trường này; app phải chạy được, chỉ là không vẽ tuyến.
    final j = jsonDecode(_tuyen()) as Map<String, dynamic>;
    j.remove('duong_di');
    expect(KetQuaChiDuong.tuJson(j).duongDi, isEmpty);
  });
}
