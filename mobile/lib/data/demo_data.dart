import 'package:flutter/material.dart';

/// Vài chuỗi cố định của toà nhà, cùng phép chọn chuỗi theo ngôn ngữ.
///
/// Ba màn Trang chủ, Tìm kiếm, Bản đồ nay đọc dữ liệu thật từ `GET /map`, nên
/// đây chỉ còn thứ không đến từ máy chủ: tên toà nhà, tên tầng, phiên bản.

/// Chọn chuỗi theo ngôn ngữ đang bật. Tên khu vực là danh từ riêng nên không
/// nằm trong `.arb`; mỗi mục giữ sẵn hai bản.
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

  static const currentFloor = 'Tầng 1 · Thư viện Đại học Đà Lạt';
  static const currentFloorEn = 'Floor 1 · Da Lat University Library';

  static const buildingName = 'Thư viện DLU';
  static const buildingNameEn = 'DLU Library';

  static const appVersion = 'v0.1';
}
