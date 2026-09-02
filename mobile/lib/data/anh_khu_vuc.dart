/// Ảnh thật của từng khu vực, do nhóm CTK45 chụp (xem assets/images/NGUON.md).
///
/// Tên thư mục khớp cột `thu_muc_anh` mà `GET /map` trả về, nên không cần bảng
/// tra thứ hai. Số lượng viết cứng chứ không đọc `AssetManifest` lúc chạy —
/// thêm ảnh là phải sửa `pubspec.yaml` ngay bên cạnh, và một bài test đối chiếu
/// hai nơi.
class AnhKhuVuc {
  AnhKhuVuc._();

  static const soAnh = <String, int>{
    'ban_thu_thu': 2,
    'can_tin': 2,
    'cau_thang': 3,
    'cau_thang_tang_2': 2,
    'cua_ra_vao': 3,
    'hanh_lang': 2,
    'hoi_truong_thu_vien': 5,
    'khu_vuc_doc': 7,
    'khu_vuc_tu_hoc': 5,
    'phong_tap_chi': 3,
    'tv3_4': 3,
  };

  /// Đường dẫn asset của mọi ảnh trong một khu vực, rỗng nếu không có ảnh.
  static List<String> duongDan(String thuMuc) => [
        for (var i = 1; i <= (soAnh[thuMuc] ?? 0); i++)
          'assets/images/$thuMuc/$i.jpg',
      ];
}
