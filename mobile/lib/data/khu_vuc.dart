import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../services/api_dinh_vi.dart';
import 'khu_vuc_thu_vien.dart';

/// Một khu vực của thư viện: nhiều điểm tham chiếu cùng `nhom` gộp lại.
///
/// Khác với điểm tham chiếu, đây mới là thứ người dùng nghĩ tới khi tìm đường:
/// không ai muốn "đi tới RP27", họ muốn "đi tới Khu vực đọc".
class KhuVuc {
  /// Hai điểm cùng nhóm xa hơn ngần này thì tách cụm, mỗi cụm mang nhãn riêng.
  static const nguongCumM = 15.0;

  final String nhom;

  /// Câu một dòng, dùng cho danh sách.
  final String moTa;

  /// Đoạn dài cho màn chi tiết. Rỗng với lối đi (cầu thang, hành lang) — chúng
  /// không phải điểm đến nên CTK45 cố ý không viết mô tả cho chúng.
  final String moTaChiTiet;

  final String thuMucAnh;
  final IconData icon;

  /// Toạ độ mét của các điểm tham chiếu thuộc khu vực này.
  final List<Offset> diem;

  const KhuVuc({
    required this.nhom,
    required this.moTa,
    required this.moTaChiTiet,
    required this.thuMucAnh,
    required this.icon,
    required this.diem,
  });

  /// Khoảng cách tới điểm GẦN NHẤT của khu vực, không phải tới trọng tâm.
  ///
  /// "Cầu thang" có 12 điểm rải hai đầu toà nhà nên trọng tâm của nó rơi vào
  /// giữa nhà, chỗ không có cầu thang nào.
  double khoangCach(double x, double y) {
    var min = double.infinity;
    for (final p in diem) {
      final l = (p.dx - x) * (p.dx - x) + (p.dy - y) * (p.dy - y);
      if (l < min) min = l;
    }
    return min == double.infinity ? min : math.sqrt(min);
  }

  /// Tâm của từng CỤM điểm, mỗi cụm một chỗ đặt nhãn trên sơ đồ.
  ///
  /// Không dùng trọng tâm cả nhóm: 5 trong 11 nhóm có trọng tâm rơi cách điểm
  /// gần nhất của chính nó hơn 8 m. Gom theo liên kết đơn, hai điểm cách nhau
  /// trong [nguongCumM] thì cùng cụm.
  List<Offset> get tamCum {
    final cha = List.generate(diem.length, (i) => i);
    int goc(int i) {
      while (cha[i] != i) {
        cha[i] = cha[cha[i]];
        i = cha[i];
      }
      return i;
    }

    for (var i = 0; i < diem.length; i++) {
      for (var j = i + 1; j < diem.length; j++) {
        if ((diem[i] - diem[j]).distance <= nguongCumM) cha[goc(i)] = goc(j);
      }
    }

    final gom = <int, List<Offset>>{};
    for (var i = 0; i < diem.length; i++) {
      gom.putIfAbsent(goc(i), () => []).add(diem[i]);
    }
    return [
      for (final c in gom.values)
        c.reduce((a, b) => a + b) / c.length.toDouble(),
    ];
  }

  /// Gộp danh sách điểm của `GET /map` thành khu vực.
  ///
  /// Biểu tượng lấy theo tên nhóm từ bản nhúng sẵn: máy chủ chỉ trả dữ liệu,
  /// còn chọn biểu tượng nào là việc của giao diện.
  static List<KhuVuc> tuDiem(List<DiemThamChieu> ds) {
    final gom = <String, List<DiemThamChieu>>{};
    for (final d in ds) {
      if (d.nhom.isNotEmpty) gom.putIfAbsent(d.nhom, () => []).add(d);
    }
    if (gom.isEmpty) return KhuVucThuVien.tatCa;

    final ra = [
      for (final e in gom.entries)
        KhuVuc(
          nhom: e.key,
          moTa: e.value.first.moTa,
          moTaChiTiet: e.value.first.moTaChiTiet,
          thuMucAnh: e.value.first.thuMucAnh,
          icon: _icon(e.key),
          diem: [for (final d in e.value) Offset(d.x, d.y)],
        ),
    ];
    ra.sort((a, b) => a.nhom.compareTo(b.nhom));
    return ra;
  }

  static IconData _icon(String nhom) {
    for (final k in KhuVucThuVien.tatCa) {
      if (k.nhom == nhom) return k.icon;
    }
    return Icons.place_outlined;
  }
}

/// Sắp khu vực theo khoảng cách tới một toạ độ, gần nhất trước.
///
/// Vị trí null nghĩa là chưa định vị: giữ nguyên thứ tự bảng chữ cái thay vì
/// bịa ra một điểm quy chiếu.
List<KhuVuc> sapTheoKhoangCach(List<KhuVuc> ds, ViTri? vt) {
  if (vt == null) return ds;
  final co = [...ds];
  co.sort((a, b) => a
      .khoangCach(vt.xGop, vt.yGop)
      .compareTo(b.khoangCach(vt.xGop, vt.yGop)));
  return co;
}
