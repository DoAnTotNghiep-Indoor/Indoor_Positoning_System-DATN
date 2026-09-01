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
  /// Quét một lần, trả về danh sách AP kèm RSSI.
  ///
  /// Hạ BSSID về chữ thường: `feature_list.json` lưu chữ thường và backend ánh
  /// xạ theo đúng chuỗi, mà máy Android trả hoa hay thường tuỳ hãng — không
  /// chuẩn hoá thì số AP khớp về 0 mà không báo lỗi gì.
  Future<List<DiemTruyCap>> quet() async {
    final co = await WiFiScan.instance.canStartScan();
    if (co != CanStartScan.yes) throw NgoaiLeQuet(_doiLoi(co));

    // Android giới hạn 4 lần startScan mỗi 2 phút cho ứng dụng nền trước. Quá
    // hạn thì lệnh trả false, nhưng kết quả lần quét gần nhất vẫn còn trong bộ
    // đệm hệ thống — dùng lại còn hơn báo lỗi cho người dùng.
    await WiFiScan.instance.startScan();
    await Future.delayed(const Duration(seconds: 2));

    final doc = await WiFiScan.instance.canGetScannedResults();
    if (doc != CanGetScannedResults.yes) throw NgoaiLeQuet(_doiLoiDoc(doc));

    final ds = await WiFiScan.instance.getScannedResults();
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
