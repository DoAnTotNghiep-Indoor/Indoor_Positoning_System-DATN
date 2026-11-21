/// Ảnh thật của từng khu vực (nguồn ở assets/images/NGUON.md).
///
/// Tên thư mục khớp cột `thu_muc_anh` của `GET /map` nên không cần bảng tra
/// thứ hai. Số lượng viết cứng, có test đối chiếu với thư mục trên đĩa.
class AnhKhuVuc {
  AnhKhuVuc._();

  static const soAnh = <String, int>{
    'ban_cong': 3,
    'ban_thu_thu': 4,
    'can_tin': 3,
    'cau_thang': 3,
    'cau_thang_tang_2_phai': 1,
    'cau_thang_tang_2_trai': 1,
    'cua_chinh': 3,
    'hanh_lang': 2,
    'hoc_nhom': 1,
    'hoi_truong_thu_vien': 3,
    'khu_vuc_doc': 3,
    'khu_vuc_tu_hoc': 4,
    'loi_ra': 1,
    'nghiep_vu_1': 1,
    'nha_sach': 4,
    'phong_tap_chi': 3,
    'thang_may': 1,
    'tv3_4': 3,
    'wc_phai': 2,
    'wc_trai': 2,
    'xuong_tv1_2': 2,
  };

  static List<String> duongDan(String thuMuc) => [
        for (var i = 1; i <= (soAnh[thuMuc] ?? 0); i++)
          'assets/images/$thuMuc/$i.avif',
      ];
}
