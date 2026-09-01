import 'package:flutter/material.dart';

import 'khu_vuc.dart';

/// 11 khu vực của thư viện, nhúng sẵn làm bản dự phòng.
///
/// Nguồn là `data/reference/reference_points.csv`, cũng chính là thứ `GET /map`
/// trả về. Nhúng vào ứng dụng để danh sách khu vực, ảnh và mô tả vẫn dùng được
/// khi chưa nối được máy chủ — lúc demo trước hội đồng, backend có thể chưa kịp
/// bật.
///
/// SINH TỰ ĐỘNG bằng `python -m tools.sinh_khu_vuc`, đừng sửa tay.
class KhuVucThuVien {
  KhuVucThuVien._();

  static const tatCa = <KhuVuc>[
    KhuVuc(
      nhom: 'Bàn thủ thư',
      moTa: 'Khu vực làm việc trung tâm của thủ thư.',
      moTaChiTiet: 'Bàn thủ thư là nơi làm việc trung tâm của cán bộ thư viện. Đây là khu vực hỗ trợ sinh viên và cán bộ giảng viên trong việc tìm kiếm, mượn tài liệu.',
      thuMucAnh: 'ban_thu_thu',
      icon: Icons.support_agent_outlined,
      diem: [Offset(0, 52), Offset(9, 52)],
    ),
    KhuVuc(
      nhom: 'Căn tin',
      moTa: 'Căn tin hiện đại, cung cấp nhiều loại mặt hàng.',
      moTaChiTiet: 'Căn tin hiện đại, đa dạng về các loại mặt hàng, cung cấp nhiều loại đồ ăn và thức uống. Khu vực có thể đáp ứng các nhu cầu ăn uống, mua sắm các vật dụng hỗ trợ cho cả sinh viên và cán bộ giảng viên.',
      thuMucAnh: 'can_tin',
      icon: Icons.restaurant_outlined,
      diem: [Offset(30, 14)],
    ),
    KhuVuc(
      nhom: 'Cầu thang',
      moTa: 'Cầu thang di chuyển.',
      moTaChiTiet: '',
      thuMucAnh: 'cau_thang',
      icon: Icons.stairs_outlined,
      diem: [Offset(-30, 10), Offset(-8, 10), Offset(8, 10), Offset(30, 10), Offset(-15, 18), Offset(0, 18), Offset(0, 33), Offset(-22, 34), Offset(22, 34), Offset(0, 41), Offset(-22, 45), Offset(22, 45)],
    ),
    KhuVuc(
      nhom: 'Cầu thang tầng 2',
      moTa: 'Cầu thang dẫn lên tầng 2',
      moTaChiTiet: 'Lối di chuyển lên tầng 2 của thư viện. Thư viện bố trí 2 cầu thang di chuyển ở hai bên trái phải, thuận tiện cho việc di chuyển giữa các tầng.',
      thuMucAnh: 'cau_thang_tang_2',
      icon: Icons.stairs_outlined,
      diem: [Offset(-30, 52), Offset(29, 52)],
    ),
    KhuVuc(
      nhom: 'Cửa ra vào',
      moTa: 'Cửa ra vào thư viện',
      moTaChiTiet: 'Cửa ra vào thư viện gồm 2 cửa là cửa chính ở trước thư viện và cửa sau dẫn ra bãi đỗ xe cổng sau, thuận tiện cho việc di chuyển và đảm bảo an ninh.',
      thuMucAnh: 'cua_ra_vao',
      icon: Icons.door_front_door_outlined,
      diem: [Offset(0, 0), Offset(-23, 52)],
    ),
    KhuVuc(
      nhom: 'Hành lang',
      moTa: 'Hành lang di chuyển giữa các khu vực.',
      moTaChiTiet: '',
      thuMucAnh: 'hanh_lang',
      icon: Icons.linear_scale_outlined,
      diem: [Offset(-42, 24), Offset(42, 24)],
    ),
    KhuVuc(
      nhom: 'Hội trường thư viện',
      moTa: 'Phòng Hội trường thư viện, không gian rộng lớn, hiện đại.',
      moTaChiTiet: 'Hội trường thư viện có không gian rộng lớn, hiện đại, số lượng ghế ngồi rộng lớn với khoảng 300 chỗ. Phòng phù hợp cho các buổi hội thảo, các cuộc họp và sự kiện quan trọng.',
      thuMucAnh: 'hoi_truong_thu_vien',
      icon: Icons.stadium_outlined,
      diem: [Offset(16, 0)],
    ),
    KhuVuc(
      nhom: 'Khu vực tự học',
      moTa: 'Khu vực có đầy đủ bàn ghế, ổ cắm điện, không gian yên tĩnh.',
      moTaChiTiet: 'Khu vực tự học với đầy đủ bàn ghế, ổ cắm điện và không gian yên tĩnh. Các khu vực tự học được bố trí ở nhiều nơi trong thư viện, là nơi lý tưởng cho việc học tập và nghiên cứu.',
      thuMucAnh: 'khu_vuc_tu_hoc',
      icon: Icons.school_outlined,
      diem: [Offset(-30, 14), Offset(-26, 22), Offset(-13, 22), Offset(13, 22), Offset(26, 22), Offset(-13, 33), Offset(-36, 35), Offset(36, 35), Offset(-15, 52), Offset(14, 52)],
    ),
    KhuVuc(
      nhom: 'Khu vực đọc',
      moTa: 'Khu vực cung cấp các thể loại sách, môi trường yên tĩnh.',
      moTaChiTiet: 'Khu vực đọc với không gian yên tĩnh, cung cấp nhiều loại sách và tài liệu học tập được sắp xếp gọn gàng ở các kệ sách trong khu vực. Hỗ trợ thuận tiện cho việc tìm kiếm tài liệu và học tập.',
      thuMucAnh: 'khu_vuc_doc',
      icon: Icons.menu_book_outlined,
      diem: [Offset(-43, 35), Offset(43, 35), Offset(-13, 41), Offset(13, 41), Offset(-13, 45), Offset(13, 45)],
    ),
    KhuVuc(
      nhom: 'Phòng tạp chí',
      moTa: 'Phòng lưu trữ tạp chí và nhiều sách đa dạng thể loại.',
      moTaChiTiet: 'Phòng tạp chí lưu trữ nhiều loại tạp chí và sách đa dạng thể loại, phục vụ nhu cầu nghiên cứu và học tập.',
      thuMucAnh: 'phong_tap_chi',
      icon: Icons.article_outlined,
      diem: [Offset(22, 52)],
    ),
    KhuVuc(
      nhom: 'TV3,4',
      moTa: 'Phòng máy tính TV3 và TV4.',
      moTaChiTiet: 'Phòng máy tính TV3 và TV4 với hệ thống trang thiết bị hiện đại, phòng học được trang bị các bộ máy tính được kết nối Internet chất lượng cao. Phòng học đáp ứng được các nhu cầu về học tập và làm việc một cách ổn định và mượt mà.',
      thuMucAnh: 'tv3_4',
      icon: Icons.computer_outlined,
      diem: [Offset(-16, 0)],
    ),
  ];
}
