import 'dart:async';
import 'dart:math';

import 'package:flutter/widgets.dart';

import '../data/floor_map.dart';
import '../data/khu_vuc.dart';
import 'api_dinh_vi.dart';
import 'quet_wifi.dart';
import 'quyen_truy_cap.dart';

/// Vòng quét WiFi → `POST /predict` chạy liên tục khi app ở nền trước.
///
/// Chu kỳ 5 giây vì Android chặn 4 lần `startScan` mỗi 2 phút.
class TheoDoiViTri extends ChangeNotifier {
  static const chuKy = Duration(seconds: 5);

  /// Đi được ngần này mét kể từ lần hỏi tuyến trước thì hỏi lại, kể cả khi vẫn
  /// gần cùng một điểm tham chiếu — không thì quãng đường còn lại đứng im.
  static const nguongTinhLaiM = 1.0;

  final ApiDinhVi _api;
  final MayQuetWifi _mayQuet;
  final QuyenTruyCap _quyen;

  TheoDoiViTri({
    required ApiDinhVi api,
    MayQuetWifi? mayQuet,
    QuyenTruyCap quyen = const QuyenTruyCap(),
  })  : _api = api,
        _mayQuet = mayQuet ?? MayQuetWifi(),
        _quyen = quyen;

  Timer? _hen;
  bool _dangBan = false;
  bool _daHuy = false;
  bool _daXinQuyen = false;

  /// Lần quét đang bay dở chỉ được ghi kết quả nếu lượt chưa đổi, nếu không
  /// kết quả cũ về sau khi app xuống nền vẫn đè lên trạng thái.
  int _luot = 0;

  ViTri? _viTri;
  DateTime? _lucCapNhat;

  /// [NgoaiLeQuet] hoặc [NgoaiLeApi] của lần quét gần nhất, null khi ổn.
  Exception? _loi;

  List<DiemThamChieu> _banDo = const [];
  List<KhuVuc> _khuVuc = sapTheoKhoangCach(KhuVuc.tuDiem(const []), null);
  DiemThamChieu? _diemGan;

  KetQuaChiDuong? _tuyen;
  KhuVuc? _dich;
  String? _rpDich;
  String? _neoTuyen;
  Offset? _viTriNeo;
  bool _daToi = false;
  int _luotTuyen = 0;

  ViTri? get viTri => _viTri;
  Exception? get loi => _loi;
  List<DiemThamChieu> get banDo => _banDo;

  /// Khu vực sắp theo khoảng cách (chưa định vị thì theo tên). Tính sẵn một lần
  /// mỗi khi toạ độ đổi thay vì mỗi lần giao diện đọc.
  List<KhuVuc> get khuVuc => _khuVuc;
  DiemThamChieu? get diemGanNhat => _diemGan;

  KhuVuc? get khuHienTai {
    final nhom = _diemGan?.nhom;
    if (nhom == null || nhom.isEmpty) return null;
    for (final k in _khuVuc) {
      if (k.nhom == nhom) return k;
    }
    return null;
  }

  KetQuaChiDuong? get tuyen => _tuyen;
  KhuVuc? get dichTuyen => _dich;
  bool get daToi => _daToi;

  int? get giayTuCapNhat {
    final luc = _lucCapNhat;
    return luc == null ? null : DateTime.now().difference(luc).inSeconds;
  }

  /// Máy chủ gộp các lần quét theo mã này nên phải giữ nguyên suốt phiên.
  late final String deviceId =
      'dlu-${DateTime.now().millisecondsSinceEpoch.toRadixString(36)}'
      '-${Random().nextInt(0xFFFF).toRadixString(16)}';

  void doiMayChu(String diaChi) {
    if (diaChi == _api.diaChi) return;
    _api.diaChi = diaChi;
    _banDo = const [];
  }

  void batDau() {
    if (_hen != null) return;
    _luot++;
    _motVong();
    _hen = Timer.periodic(chuKy, (_) => _motVong());
  }

  void dungLai() {
    _luot++;
    _hen?.cancel();
    _hen = null;
  }

  void doiVongDoi(AppLifecycleState s) {
    if (s == AppLifecycleState.resumed) {
      batDau();
    } else if (s == AppLifecycleState.paused || s == AppLifecycleState.hidden) {
      dungLai();
    }
  }

  Future<void> xuLyQuyen() async {
    // Xin thẳng: Android chỉ báo bị chặn qua kết quả request(), không qua status.
    // Quyền đã bị chặn thì request() trả về ngay, không hiện hộp thoại.
    if (await _quyen.xin() == TrangThaiQuyen.biChan) {
      await _quyen.moCaiDat();
    } else {
      _motVong();
    }
  }

  bool _dangTaiBanDo = false;

  /// Gọi mỗi vòng cho tới khi có: máy chủ bật muộn hoặc vừa đổi địa chỉ thì
  /// bản đồ tự về mà không cần mở lại app.
  Future<void> _taiBanDo() async {
    if (_banDo.isNotEmpty || _dangTaiBanDo) return;
    _dangTaiBanDo = true;
    try {
      _banDo = await _api.layBanDo();
      _capNhatDanXuat();
      _bao();
    } catch (_) {
      // lỗi kết nối thật sẽ lộ ra ở lần /predict cùng vòng
    } finally {
      _dangTaiBanDo = false;
    }
  }

  Future<void> chiDuongToi(KhuVuc k, {String? rpId}) async {
    final vt = _viTri;
    if (vt == null) throw const NgoaiLeApi(LoiApi.khongKetNoi);

    final luot = ++_luotTuyen;
    _neoTuyen = _diemGan?.rpId;
    _viTriNeo = Offset(vt.xGop, vt.yGop);
    // Gửi tên khu vực để máy chủ chọn điểm gần nhất THEO ĐƯỜNG ĐI: điểm gần
    // nhất theo đường chim bay có thể nằm sau tường.
    final kq = await _api.chiDuong(
        tuX: vt.xGop, tuY: vt.yGop, denNhom: k.nhom, denRp: rpId);
    if (luot != _luotTuyen) return;
    _tuyen = kq;
    _dich = k;
    _rpDich = rpId;
    _daToi = kq.soChang == 0;
    _bao();
  }

  void xoaTuyen() {
    _luotTuyen++;
    _neoTuyen = null;
    _daToi = false;
    _tuyen = null;
    _dich = null;
    _rpDich = null;
    _bao();
  }

  void _bamTuyen() {
    final dich = _dich, gan = _diemGan, vt = _viTri;
    if (dich == null || gan == null || vt == null) return;
    if (_rpDich != null ? gan.rpId == _rpDich : gan.nhom == dich.nhom) {
      _daToi = true;
      return;
    }
    if (_daToi) {
      _daToi = false;
      _neoTuyen = null;
    }
    final neo = _viTriNeo;
    final diChuyenM = neo == null
        ? double.infinity
        : (Offset(vt.xGop, vt.yGop) - neo).distance * SoDoThat.metMoiDonVi;
    if (gan.rpId == _neoTuyen && diChuyenM < nguongTinhLaiM) return;
    _neoTuyen = gan.rpId;
    unawaited(chiDuongToi(dich, rpId: _rpDich).catchError((_) {}));
  }

  void _capNhatDanXuat() {
    final vt = _viTri;
    _khuVuc = sapTheoKhoangCach(KhuVuc.tuDiem(_banDo), vt);
    _diemGan = null;
    if (vt == null) return;
    var min = double.infinity;
    for (final d in _banDo) {
      final l =
          (d.x - vt.xGop) * (d.x - vt.xGop) + (d.y - vt.yGop) * (d.y - vt.yGop);
      if (l < min) {
        min = l;
        _diemGan = d;
      }
    }
  }

  Future<void> _motVong() async {
    if (_dangBan) return;
    _dangBan = true;
    final luot = _luot;
    unawaited(_taiBanDo());
    try {
      final quet = await _mayQuet.quet();
      final vt = await _api.duDoan(deviceId: deviceId, quet: quet);
      if (luot != _luot) return;
      _viTri = vt;
      _lucCapNhat = DateTime.now();
      _loi = null;
      _capNhatDanXuat();
      _bamTuyen();
    } on NgoaiLeQuet catch (e) {
      if (luot != _luot) return;
      _loi = e;
      if (e.loai == LoiQuet.thieuQuyen && !_daXinQuyen) {
        _daXinQuyen = true;
        unawaited(_quyen.xin().then((_) => _motVong(), onError: (_) {}));
      }
    } on NgoaiLeApi catch (e) {
      if (luot != _luot) return;
      _loi = e;
      // Lần quét mới không đủ AP thì toạ độ cũ không còn đáng tin: giữ lại là
      // giao diện vẫn khẳng định tên phòng cũ.
      if (e.loai == LoiApi.khongDuAp) {
        _viTri = null;
        _lucCapNhat = null;
        _capNhatDanXuat();
      }
    } catch (_) {
      // PlatformException của wifi_scan — thiếu nhánh này lỗi thoát khỏi Timer.
      if (luot != _luot) return;
      _loi = const NgoaiLeQuet(LoiQuet.thatBai);
    } finally {
      _dangBan = false;
      if (luot == _luot) _bao();
    }
  }

  void _bao() {
    if (!_daHuy) notifyListeners();
  }

  @override
  void dispose() {
    _daHuy = true;
    _hen?.cancel();
    _api.dong();
    super.dispose();
  }
}

class TheoDoiViTriScope extends InheritedNotifier<TheoDoiViTri> {
  const TheoDoiViTriScope({
    super.key,
    required TheoDoiViTri theoDoi,
    required super.child,
  }) : super(notifier: theoDoi);

  static TheoDoiViTri of(BuildContext context) => context
      .dependOnInheritedWidgetOfExactType<TheoDoiViTriScope>()!
      .notifier!;

  /// Lấy mà không đăng ký dựng lại — cho callback và painter tự nghe.
  static TheoDoiViTri doc(BuildContext context) =>
      context.getInheritedWidgetOfExactType<TheoDoiViTriScope>()!.notifier!;
}
