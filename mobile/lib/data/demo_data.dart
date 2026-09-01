import 'package:flutter/material.dart';

/// DỮ LIỆU DEMO TĨNH cho danh sách "Gần bạn", tìm kiếm và các ô truy cập nhanh.
///
/// Phần định vị đã chạy dữ liệu thật (`GET /map`, `POST /predict`); những danh
/// sách dưới đây thì chưa. Toạ độ theo hệ thiết kế 393×852, không phải mét.

/// Chọn chuỗi theo ngôn ngữ đang bật.
///
/// Tên khu vực là danh từ riêng của toà nhà nên không nằm trong `.arb`; mỗi mục
/// giữ sẵn hai bản.
String theoNgonNgu(BuildContext context, String vi, String en) =>
    Localizations.localeOf(context).languageCode == 'en' ? en : vi;

/// Mã nhóm khu vực — MÃ bất biến chứ không phải nhãn hiển thị. Lọc theo nhãn
/// thì đổi sang tiếng Anh là không chip nào khớp nữa.
class AreaCategory {
  AreaCategory._();

  static const all = 'all';
  static const study = 'study';
  static const facility = 'facility';
  static const internal = 'internal';

  /// Thứ tự này quyết định thứ tự chip lọc trên màn Tìm kiếm.
  static const danhSach = <String>[all, study, facility, internal];
}

class DemoData {
  DemoData._();

  /// Vị trí hiện tại giả lập (sau này lấy từ WebSocket).
  static const currentAreaName = 'Phòng học nhóm';
  static const currentAreaNameEn = 'Group study room';
  static const currentFloor = 'Tầng 1 · Thư viện Đại học Đà Lạt';
  static const currentFloorEn = 'Floor 1 · Da Lat University Library';

  /// Toạ độ người dùng trên sơ đồ, hệ 393x852.
  static const userX = 150.0;
  static const userY = 585.0;

  static const buildingName = 'Thư viện DLU';
  static const buildingNameEn = 'DLU Library';

  /// Đếm thẳng từ [FloorMap] chứ không viết cứng, để header không nói một đằng
  /// còn hình bên dưới một nẻo. Cộng 1 là quầy hướng dẫn — có vùng và có tên
  /// nhưng không nằm trong [FloorMap.phong].

  static const updatedSecondsAgo = 2;

  // --- Cài đặt ---
  static const appVersion = 'v0.1';
  static const serverHost = 'api.ips.dlu.edu.vn';
}
