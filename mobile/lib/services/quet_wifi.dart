import 'dart:async';

import 'package:wifi_scan/wifi_scan.dart';

class DiemTruyCap {
  final String bssid;
  final int rssi;

  const DiemTruyCap({required this.bssid, required this.rssi});

  Map<String, dynamic> toJson() => {'bssid': bssid, 'rssi': rssi};
}

/// Vì sao không quét được. Tách riêng chứ không gộp thành một lỗi chung vì mỗi
/// loại cần một cách xử lý khác: xin lại quyền, mở Cài đặt, hay bật định vị.
enum LoiQuet { thieuQuyen, quyenBiChan, tatDinhVi, khongHoTro, thatBai }

class NgoaiLeQuet implements Exception {
  final LoiQuet loai;
  const NgoaiLeQuet(this.loai);
}

class MayQuetWifi {
  StreamSubscription<List<WiFiAccessPoint>>? _nghe;
  Completer<List<WiFiAccessPoint>>? _cho;

  /// Chờ đúng lúc hệ thống báo quét xong thay vì ngủ một khoảng cố định: ngủ
  /// ngắn thì đọc phải bộ đệm của lần trước, ngủ dài thì phí thời gian.
  ///
  /// Hạ BSSID về chữ thường: `feature_list.json` lưu chữ thường và backend ánh xạ
  /// theo đúng chuỗi, mà máy Android trả hoa hay thường tuỳ hãng — không chuẩn
  /// hoá thì số AP khớp về 0 mà không báo lỗi gì.
  Future<List<DiemTruyCap>> quet() async {
    final co = await WiFiScan.instance.canStartScan();
    if (co != CanStartScan.yes) throw NgoaiLeQuet(_doiLoi(co));

    final doc = await WiFiScan.instance.canGetScannedResults();
    if (doc != CanGetScannedResults.yes) throw NgoaiLeQuet(_doiLoiDoc(doc));

    // Plugin phát ngay bộ đệm cũ khi vừa đăng ký; sự kiện đó về trước kết quả
    // của startScan nên rơi vào lúc `_cho` còn null và bị bỏ qua.
    _nghe ??= WiFiScan.instance.onScannedResultsAvailable.listen((ds) {
      final c = _cho;
      if (c != null && !c.isCompleted) c.complete(ds);
    });
    // startScan trả false khi máy còn bật giới hạn quét (Tuỳ chọn nhà phát
    // triển > Điều tiết quét Wi-Fi) hoặc đang bận: đọc luôn bộ đệm hiện có.
    final ds = await WiFiScan.instance.startScan()
        ? await (_cho = Completer()).future.timeout(
            const Duration(seconds: 10),
            onTimeout: WiFiScan.instance.getScannedResults)
        : await WiFiScan.instance.getScannedResults();
    _cho = null;
    return [
      for (final ap in ds)
        if (ap.bssid.isNotEmpty)
          DiemTruyCap(bssid: ap.bssid.toLowerCase(), rssi: ap.level),
    ];
  }

  LoiQuet _doiLoi(CanStartScan c) => switch (c) {
        CanStartScan.notSupported => LoiQuet.khongHoTro,
        CanStartScan.noLocationPermissionRequired => LoiQuet.thieuQuyen,
        CanStartScan.noLocationPermissionDenied => LoiQuet.quyenBiChan,
        CanStartScan.noLocationPermissionUpgradeAccuracy => LoiQuet.quyenBiChan,
        CanStartScan.noLocationServiceDisabled => LoiQuet.tatDinhVi,
        _ => LoiQuet.thatBai,
      };

  LoiQuet _doiLoiDoc(CanGetScannedResults c) => switch (c) {
        CanGetScannedResults.notSupported => LoiQuet.khongHoTro,
        CanGetScannedResults.noLocationPermissionRequired => LoiQuet.thieuQuyen,
        CanGetScannedResults.noLocationPermissionDenied => LoiQuet.quyenBiChan,
        CanGetScannedResults.noLocationPermissionUpgradeAccuracy =>
          LoiQuet.quyenBiChan,
        CanGetScannedResults.noLocationServiceDisabled => LoiQuet.tatDinhVi,
        _ => LoiQuet.thatBai,
      };
}
