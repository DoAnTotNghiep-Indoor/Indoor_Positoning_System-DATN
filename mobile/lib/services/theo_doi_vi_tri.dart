import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';

import '../data/khu_vuc.dart';
import 'api_dinh_vi.dart';
import 'kenh_vi_tri.dart';
import 'quet_wifi.dart';

enum TrangThai { dung, dangChay, loi }

/// Vòng lặp quét WiFi rồi gửi lên máy chủ, giữ toạ độ mới nhất cho giao diện.
///
/// Chu kỳ 5 giây vì Android chặn 4 lần `startScan` mỗi 2 phút.
class TheoDoiViTri extends ChangeNotifier {
  static const chuKy = Duration(seconds: 5);

  final MayQuetWifi _mayQuet;
  final ApiDinhVi _api;

  /// Lối gửi lần quét. Null nghĩa là đi thẳng REST — dùng trong kiểm thử, nơi
  /// máy chủ giả chỉ nói HTTP.
  final KenhViTri? _kenh;

  TheoDoiViTri({
    required String diaChiMayChu,
    MayQuetWifi? mayQuet,
    ApiDinhVi? api,
    KenhViTri? kenh,
  })  : _mayQuet = mayQuet ?? MayQuetWifi(),
        _api = api ?? ApiDinhVi(diaChiMayChu),
        _kenh = kenh;

  Timer? _hen;
  bool _dangBan = false;
  bool _daHuy = false;

  /// Tăng mỗi lần bật hoặc tắt theo dõi. Lần quét đang bay dở chỉ được ghi kết
  /// quả nếu số lượt chưa đổi, nếu không bấm Dừng xong vẫn bị kéo về `dangChay`.
  int _luot = 0;

  /// Đang tạm dừng vì ứng dụng xuống nền, chứ không phải người dùng bấm dừng.
  bool _tamDung = false;

  TrangThai _trangThai = TrangThai.dung;
  ViTri? _viTri;
  LoiQuet? _loiQuet;
  LoiApi? _loiApi;
  int? _maHttp;
  int? _soApKhop;
  int? _soApToiThieu;

  DateTime? _lucCapNhat;

  List<DiemThamChieu> _banDo = const [];

  /// Tuyến đang hiện trên sơ đồ, null khi chưa chỉ đường. Giữ ở đây để tuyến
  /// sống sót khi rời màn Chi tiết. Neo ở điểm xuất phát và KHÔNG tự tính lại:
  /// chấm vị trí vẫn chạy, còn tính lại thì tuyến nhảy mỗi vòng quét.
  KetQuaChiDuong? _tuyen;
  KhuVuc? _dichTuyen;

  /// Chốt lượt riêng cho tuyến, cùng vai trò với `_luot` của vòng quét: một
  /// tuyến về muộn không được đè lên tuyến mới, cũng không được dựng lại sau
  /// khi người dùng đã bấm xoá.
  int _luotTuyen = 0;

  TrangThai get trangThai => _trangThai;
  ViTri? get viTri => _viTri;
  List<DiemThamChieu> get banDo => _banDo;
  KetQuaChiDuong? get tuyen => _tuyen;
  KhuVuc? get dichTuyen => _dichTuyen;

  /// Số giây kể từ lần có toạ độ gần nhất, null nếu chưa có lần nào. Giao diện
  /// phải hỏi giá trị này chứ không viết cứng như header cũ "2 giây trước".
  int? get giayTuCapNhat {
    final luc = _lucCapNhat;
    return luc == null ? null : DateTime.now().difference(luc).inSeconds;
  }

  /// Khu vực thư viện, sắp theo khoảng cách. Chưa tải được `/map` thì lùi về
  /// bản nhúng: nội dung y hệt, chỉ không đổi theo dữ liệu thực địa mới.
  List<KhuVuc> get khuVuc =>
      sapTheoKhoangCach(KhuVuc.tuDiem(_banDo), _viTri);

  /// Điểm tham chiếu gần nhất, null nếu chưa định vị hoặc chưa có bản đồ. Mô
  /// hình luôn trả đúng toạ độ một điểm nên phép tìm này khớp tuyệt đối.
  DiemThamChieu? get diemGanNhat {
    final vt = _viTri;
    if (vt == null || _banDo.isEmpty) return null;

    var gan = _banDo.first;
    var min = double.infinity;
    for (final d in _banDo) {
      final l =
          (d.x - vt.xGop) * (d.x - vt.xGop) + (d.y - vt.yGop) * (d.y - vt.yGop);
      if (l < min) {
        min = l;
        gan = d;
      }
    }
    return gan;
  }

  /// Tên khu vực đang đứng, null để giao diện lùi về hiện toạ độ mét.
  String? get tenKhuVuc {
    final ten = diemGanNhat?.ten ?? '';
    return ten.isEmpty ? null : ten;
  }

  LoiQuet? get loiQuet => _loiQuet;
  LoiApi? get loiApi => _loiApi;
  int? get maHttp => _maHttp;
  int? get soApKhop => _soApKhop;
  int? get soApToiThieu => _soApToiThieu;

  /// Mã thiết bị gửi kèm mỗi lần quét. Máy chủ dùng nó để gộp các lần quét của
  /// cùng một máy, nên phải giữ nguyên suốt phiên chạy.
  late final String deviceId =
      'dlu-${DateTime.now().millisecondsSinceEpoch.toRadixString(36)}'
      '-${Random().nextInt(0xFFFF).toRadixString(16)}';

  void doiMayChu(String diaChi) {
    _api.diaChi = diaChi;
    // Kênh đang mở vẫn trỏ về máy chủ cũ; đóng để vòng sau nối lại chỗ mới.
    _kenh?.dong();
  }

  /// Đường đi tới khu vực [k]. Ném [NgoaiLeApi] `khongKetNoi` khi chưa định vị:
  /// đoán một điểm xuất phát sẽ cho ra tuyến sai trông rất hợp lý.
  Future<KetQuaChiDuong> chiDuongToi(KhuVuc k) async {
    final vt = _viTri;
    if (vt == null) throw const NgoaiLeApi(LoiApi.khongKetNoi);

    // Đích là điểm GẦN NHẤT thuộc khu vực đó, không phải điểm đầu danh sách:
    // "Cầu thang" có 12 điểm rải hai đầu toà nhà.
    String? den;
    var min = double.infinity;
    for (final d in _banDo) {
      if (d.nhom != k.nhom) continue;
      final l = (d.x - vt.xGop) * (d.x - vt.xGop) +
          (d.y - vt.yGop) * (d.y - vt.yGop);
      if (l < min) {
        min = l;
        den = d.rpId;
      }
    }
    if (den == null) throw const NgoaiLeApi(LoiApi.saiDinhDang);

    final luot = ++_luotTuyen;
    final kq = await _api.chiDuong(tuX: vt.xGop, tuY: vt.yGop, denRp: den);
    if (luot != _luotTuyen) return kq;
    _tuyen = kq;
    _dichTuyen = k;
    _bao();
    return kq;
  }

  void xoaTuyen() {
    _luotTuyen++;
    if (_tuyen == null) return;
    _tuyen = null;
    _dichTuyen = null;
    _bao();
  }

  void batDau() {
    if (_hen != null) return;
    _luot++;
    _tamDung = false;
    _trangThai = TrangThai.dangChay;
    _loiQuet = null;
    _loiApi = null;
    _bao();

    taiBanDo();
    _motVong();
    _hen = Timer.periodic(chuKy, (_) => _motVong());
  }

  /// Tải bản đồ song song, không chặn vòng quét; hỏng thì bỏ qua. Công khai vì
  /// màn Bản đồ gọi ngay khi mở tab, không đợi bật định vị.
  Future<void> taiBanDo() async {
    if (_banDo.isNotEmpty) return;
    try {
      _banDo = await _api.layBanDo();
      _bao();
    } catch (_) {
      // im lặng: lỗi kết nối thật sẽ lộ ra ở lần gọi /predict ngay sau đó
    }
  }

  void dungLai() {
    _luot++;
    _hen?.cancel();
    _hen = null;
    // Đóng kênh khi thôi theo dõi: để mở là giữ một socket sống suốt phiên chỉ
    // để nhận toạ độ của máy khác.
    _kenh?.dong();
    _trangThai = TrangThai.dung;
    _bao();
  }

  /// Ngừng quét khi ứng dụng xuống nền, quét lại khi quay lên — chỉ khi TRƯỚC
  /// ĐÓ đang chạy, để không đè lên ý muốn của người đã tự bấm dừng.
  void doiVongDoi(AppLifecycleState trangThaiUngDung) {
    final chayNen = trangThaiUngDung == AppLifecycleState.resumed;
    if (!chayNen && _hen != null) {
      _tamDung = true;
      dungLai();
    } else if (chayNen && _tamDung) {
      batDau();
    }
  }

  Future<void> _motVong() async {
    // Một lần quét mất ~2 giây cộng thời gian gọi mạng: bỏ nhịp thay vì xếp
    // hàng chồng lên nhau.
    if (_dangBan) return;
    _dangBan = true;
    final luot = _luot;
    try {
      final quet = await _mayQuet.quet();
      final vt = _kenh != null
          ? await _kenh.duDoan(deviceId: deviceId, quet: quet)
          : await _api.duDoan(deviceId: deviceId, quet: quet);
      if (luot != _luot) return;
      _viTri = vt;
      _lucCapNhat = DateTime.now();
      _loiQuet = null;
      _loiApi = null;
      _trangThai = TrangThai.dangChay;
    } on NgoaiLeQuet catch (e) {
      if (luot != _luot) return;
      _loiQuet = e.loai;
      _loiApi = null;
      _trangThai = TrangThai.loi;
    } on NgoaiLeApi catch (e) {
      if (luot != _luot) return;
      _loiApi = e.loai;
      _maHttp = e.maHttp;
      _soApKhop = e.soAp;
      _soApToiThieu = e.toiThieu;
      _loiQuet = null;
      _trangThai = TrangThai.loi;

      // Toạ độ cũ không còn đáng tin khi lần quét mới thiếu dữ liệu: giữ lại thì
      // giao diện vẫn hiện tên phòng cũ như thể người dùng còn đứng đó.
      if (e.loai == LoiApi.khongDuAp) {
        _viTri = null;
        _lucCapNhat = null;
      }
    } catch (_) {
      if (luot != _luot) return;
      // Chủ yếu là PlatformException từ wifi_scan. Thiếu nhánh này thì lỗi
      // thoát ra ngoài Timer và trạng thái kẹt ở dangChay.
      _loiQuet = LoiQuet.thatBai;
      _loiApi = null;
      _trangThai = TrangThai.loi;
    } finally {
      _dangBan = false;
      if (luot == _luot) _bao();
    }
  }

  /// Một lần quét đang bay dở vẫn chạy nốt sau khi widget bị tháo, mà
  /// ChangeNotifier ném lỗi nếu bị dùng sau dispose.
  void _bao() {
    if (!_daHuy) notifyListeners();
  }

  @override
  void dispose() {
    _daHuy = true;
    _hen?.cancel();
    _kenh?.dong();
    _api.dong();
    super.dispose();
  }
}

/// Cấp [TheoDoiViTri] cho cả cây widget, cùng cách với AppSettingsScope.
class TheoDoiViTriScope extends InheritedNotifier<TheoDoiViTri> {
  const TheoDoiViTriScope({
    super.key,
    required TheoDoiViTri theoDoi,
    required super.child,
  }) : super(notifier: theoDoi);

  static TheoDoiViTri of(BuildContext context) {
    final scope =
        context.dependOnInheritedWidgetOfExactType<TheoDoiViTriScope>();
    assert(scope != null, 'Thiếu TheoDoiViTriScope phía trên cây widget');
    return scope!.notifier!;
  }
}
