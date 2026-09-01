import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:ips_dlu/l10n/app_localizations.dart';
import 'package:ips_dlu/screens/settings_screen.dart';
import 'package:ips_dlu/services/api_dinh_vi.dart';
import 'package:ips_dlu/services/quet_wifi.dart';
import 'package:ips_dlu/services/quyen_truy_cap.dart';
import 'package:ips_dlu/services/theo_doi_vi_tri.dart';
import 'package:ips_dlu/theme/app_settings.dart';

/// Kiểm thử bốn lỗi tìm được khi rà lại nhóm 2. Cả bốn đều không làm app sập,
/// chỉ khiến người dùng nhìn thấy thứ sai — nên phải chốt bằng test.

String _traLoi() => jsonEncode({
      'x': 13.0, 'y': 41.0, 'x_smooth': 12.5, 'y_smooth': 40.5,
      'model': 'k', 'timestamp': '2026-08-31T10:00:00Z',
      'matched_ap': 12, 'scan_count': 3, 'latency_ms': 0.4,
    });

class _QuetCham extends MayQuetWifi {
  @override
  Future<List<DiemTruyCap>> quet() async {
    await Future.delayed(const Duration(milliseconds: 200));
    return const [DiemTruyCap(bssid: 'aa:bb:cc:dd:ee:ff', rssi: -57)];
  }
}

TheoDoiViTri _theoDoi() => TheoDoiViTri(
      diaChiMayChu: 'http://x',
      mayQuet: _QuetCham(),
      api: ApiDinhVi('http://x',
          client: MockClient((_) async => http.Response.bytes(
              utf8.encode(_traLoi()), 200,
              headers: {'content-type': 'application/json'}))),
    );

class _KhoGia implements KhoTuyChon {
  final Map<String, String> o;
  _KhoGia([Map<String, String>? ban]) : o = {...?ban};

  @override
  Future<String?> doc(String khoa) async => o[khoa];

  @override
  Future<void> ghi(String khoa, String gt) async => o[khoa] = gt;
}

class _KhoHong implements KhoTuyChon {
  @override
  Future<String?> doc(String khoa) async => throw StateError('kênh nền tảng');

  @override
  Future<void> ghi(String khoa, String gt) async =>
      throw StateError('kênh nền tảng');
}

class _QuyenGia implements QuyenTruyCap {
  TrangThaiQuyen tra;
  int soLanXin = 0;
  int soLanMoCaiDat = 0;

  _QuyenGia(this.tra);

  @override
  Future<TrangThaiQuyen> kiemTra() async => tra;

  @override
  Future<TrangThaiQuyen> xin() async {
    soLanXin++;
    return tra = TrangThaiQuyen.daCap;
  }

  @override
  Future<void> moCaiDat() async => soLanMoCaiDat++;
}

Widget _manCaiDat(QuyenTruyCap quyen) => AppSettingsScope(
      settings: AppSettings(),
      child: MaterialApp(
        locale: const Locale('vi'),
        localizationsDelegates: L.localizationsDelegates,
        supportedLocales: L.supportedLocales,
        // Giống hệt main.dart: GlassScaffold không phải Material nên ô nhập địa
        // chỉ máy chủ không có Material tổ tiên và ném assertion.
        builder: (context, child) => Material(
          type: MaterialType.transparency,
          child: child ?? const SizedBox.shrink(),
        ),
        home: SettingsScreen(quyen: quyen),
      ),
    );

/// Màn Cài đặt là một ListView dài; dòng quyền nằm gần cuối nên trên khung
/// 800×600 mặc định nó chưa được dựng. Cho khung cao hẳn để cả trang có mặt,
/// thay vì cuộn tìm — bài test ở đây quan tâm nội dung, không quan tâm bố cục.
Future<void> _mo(WidgetTester tester, QuyenTruyCap quyen) async {
  tester.view.physicalSize = const Size(800, 2400);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(_manCaiDat(quyen));
  await tester.pumpAndSettle();
}

void main() {
  // --- 1. Bấm Dừng giữa lúc đang quét ---

  test('Bấm Dừng giữa lúc đang quét thì trạng thái phải Ở YÊN là dừng',
      () async {
    final td = _theoDoi();
    td.batDau();
    await Future.delayed(const Duration(milliseconds: 40));
    td.dungLai();
    expect(td.trangThai, TrangThai.dung);

    // Lần quét đang bay dở về đích sau đó vài trăm mili giây. Nó KHÔNG được
    // kéo trạng thái về dangChay, vì timer đã tắt và không còn gì chạy nữa.
    await Future.delayed(const Duration(milliseconds: 400));
    expect(td.trangThai, TrangThai.dung,
        reason: 'lần quét cũ đã ghi đè trạng thái sau khi người dùng bấm Dừng');
    td.dispose();
  });

  test('Toạ độ của lần quét đã bị huỷ không được hiện lên', () async {
    final td = _theoDoi();
    td.batDau();
    await Future.delayed(const Duration(milliseconds: 40));
    td.dungLai();
    await Future.delayed(const Duration(milliseconds: 400));
    expect(td.viTri, isNull);
    td.dispose();
  });

  // --- 2. Địa chỉ máy chủ sai ---

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

  // --- 3 và 4. Dòng quyền truy cập ---

  testWidgets('Chưa cấp quyền thì Cài đặt KHÔNG được nói "Đã cấp"',
      (tester) async {
    await _mo(tester, _QuyenGia(TrangThaiQuyen.chuaCap));

    expect(find.text('Chưa cấp'), findsOneWidget);
    expect(find.text('Đã cấp'), findsNothing);
    expect(find.text('Chạm để cấp quyền'), findsOneWidget);
  });

  testWidgets('Đã cấp quyền thì hiện đúng và không mời bấm', (tester) async {
    await _mo(tester, _QuyenGia(TrangThaiQuyen.daCap));

    expect(find.text('Đã cấp'), findsOneWidget);
    expect(find.text('Chạm để cấp quyền'), findsNothing);
  });

  testWidgets('Chạm vào dòng chưa cấp thì xin quyền', (tester) async {
    final quyen = _QuyenGia(TrangThaiQuyen.chuaCap);
    await _mo(tester, quyen);

    await tester.tap(find.text('Chưa cấp'), warnIfMissed: false);
    await tester.pumpAndSettle();

    expect(quyen.soLanXin, 1);
    expect(find.text('Đã cấp'), findsOneWidget);
  });

  testWidgets('Quyền bị chặn thì mở Cài đặt hệ thống chứ không xin lại',
      (tester) async {
    // Hỏi lại không có tác dụng khi người dùng đã chọn "Không hỏi lại".
    final quyen = _QuyenGia(TrangThaiQuyen.biChan);
    await _mo(tester, quyen);

    expect(find.text('Bị chặn'), findsOneWidget);
    await tester.tap(find.text('Bị chặn'), warnIfMissed: false);
    await tester.pumpAndSettle();

    expect(quyen.soLanMoCaiDat, 1);
    expect(quyen.soLanXin, 0);
  });

  testWidgets('Không đọc được quyền thì không bịa ra trạng thái',
      (tester) async {
    // Chạy trong test là không có kênh nền tảng nào. Thà để "Đang kiểm tra…"
    // còn hơn khẳng định một điều mình không biết.
    await _mo(tester, const QuyenTruyCap());

    expect(find.text('Đã cấp'), findsNothing);
    expect(find.text('Đang kiểm tra…'), findsOneWidget);
  });

  testWidgets('Chu kỳ quét hiện trên màn hình phải khớp hằng số thật',
      (tester) async {
    // Chuỗi cũ viết cứng "2 giây" trong khi vòng quét chạy 5 giây — mà 5 giây
    // là mức Android cho phép, nhanh hơn thì hệ điều hành trả lại kết quả cũ
    // trong bộ đệm. Nay lấy thẳng từ hằng số nên không lệch lại được.
    await _mo(tester, _QuyenGia(TrangThaiQuyen.daCap));
    expect(
        find.text(
            'Mỗi ${TheoDoiViTri.chuKy.inSeconds} giây — mức Android cho phép'),
        findsOneWidget);
    expect(find.textContaining('2 giây'), findsNothing);
  });

  // --- 5. Nhớ tuỳ chọn giữa hai lần mở app ---

  test('Địa chỉ máy chủ đã lưu được đọc lại khi mở app', () async {
    // Trên điện thoại thật địa chỉ phải là IP nội bộ của máy chạy backend.
    // Bắt gõ lại mỗi lần mở app là hỏng buổi demo.
    final kho = _KhoGia();
    final cu = AppSettings(kho: kho);
    cu.datDiaChiMayChu('http://192.168.1.50:8000');
    await Future.delayed(Duration.zero);

    final moi = AppSettings(kho: kho);
    await moi.nap();
    expect(moi.diaChiMayChu, 'http://192.168.1.50:8000');
  });

  test('Chế độ sáng/tối và ngôn ngữ cũng được nhớ', () async {
    final kho = _KhoGia();
    final cu = AppSettings(kho: kho)
      ..datCheDo(ThemeMode.dark)
      ..datNgonNgu(const Locale('en'));
    await Future.delayed(Duration.zero);
    expect(cu.cheDo, ThemeMode.dark);

    final moi = AppSettings(kho: kho);
    await moi.nap();
    expect(moi.cheDo, ThemeMode.dark);
    expect(moi.ngonNgu.languageCode, 'en');
  });

  test('Kho hỏng thì vẫn mở được app với giá trị mặc định', () async {
    final tuyChon = AppSettings(kho: _KhoHong());
    await tuyChon.nap();
    expect(tuyChon.diaChiMayChu, 'http://10.0.2.2:8000');
    expect(tuyChon.cheDo, ThemeMode.system);

    tuyChon.datCheDo(ThemeMode.dark);
    await Future.delayed(Duration.zero);
    expect(tuyChon.cheDo, ThemeMode.dark, reason: 'ghi hỏng không được chặn UI');
  });

  test('Giá trị đã lưu hỏng định dạng thì bỏ qua chứ không đổ', () async {
    final tuyChon =
        AppSettings(kho: _KhoGia({'che_do': 'khong-phai-che-do-nao'}));
    await tuyChon.nap();
    expect(tuyChon.cheDo, ThemeMode.system);
  });

  testWidgets('Màn Cài đặt không còn công tắc nào không nối vào đâu',
      (tester) async {
    // "Tự động cập nhật vị trí" và "Giữ màn hình sáng" từng bật/tắt được nhưng
    // chỉ đổi một biến trong State: tắt "Tự động cập nhật" thì vòng quét vẫn
    // chạy y nguyên. Một công tắc không làm gì còn tệ hơn là không có, vì người
    // dùng tin là mình vừa đổi được một thứ.
    await _mo(tester, _QuyenGia(TrangThaiQuyen.daCap));

    for (final chu in ['Tự động cập nhật vị trí', 'Giữ màn hình sáng']) {
      expect(find.text(chu), findsNothing, reason: 'còn công tắc chết: $chu');
    }
    // Phải là GlassSwitch chứ không phải Switch của Material: GlassSwitch tự
    // vẽ nên `find.byType(Switch)` không tìm thấy gì kể cả khi công tắc còn đó,
    // tức phép so đó xanh vĩnh viễn và không khoá được điều gì.
    expect(find.byType(GlassSwitch), findsNothing);
  });
}
