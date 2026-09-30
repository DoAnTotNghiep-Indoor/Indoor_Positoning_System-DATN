import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../services/api_dinh_vi.dart';
import 'khu_vuc_thu_vien.dart';

/// Một khu vực: các điểm tham chiếu cùng `nhom` gộp lại. Người dùng muốn "đi
/// tới Khu vực đọc", không phải "đi tới RP27".
class KhuVuc {
  final String nhom;
  final String moTa;

  /// Rỗng với lối đi (cầu thang, hành lang) — CTK45 không viết cho chúng.
  final String moTaChiTiet;
  final String thuMucAnh;
  final IconData icon;
  final List<Offset> diem;

  const KhuVuc({
    required this.nhom,
    required this.moTa,
    required this.moTaChiTiet,
    required this.thuMucAnh,
    required this.icon,
    required this.diem,
  });

  /// Tới điểm GẦN NHẤT chứ không tới trọng tâm: "Cầu thang" rải hai đầu nhà nên
  /// trọng tâm rơi vào giữa, chỗ không có cầu thang nào.
  double khoangCach(double x, double y) {
    var min = double.infinity;
    for (final p in diem) {
      min = math.min(min, (p.dx - x) * (p.dx - x) + (p.dy - y) * (p.dy - y));
    }
    return math.sqrt(min);
  }

  static List<KhuVuc> tuDiem(List<DiemThamChieu> ds) {
    final gom = <String, List<DiemThamChieu>>{};
    for (final d in ds) {
      if (d.nhom.isNotEmpty) gom.putIfAbsent(d.nhom, () => []).add(d);
    }
    if (gom.isEmpty) return KhuVucThuVien.tatCa;

    final icon = {for (final k in KhuVucThuVien.tatCa) k.nhom: k.icon};
    return [
      for (final e in gom.entries)
        KhuVuc(
          nhom: e.key,
          moTa: e.value.first.moTa,
          moTaChiTiet: e.value.first.moTaChiTiet,
          thuMucAnh: e.value.first.thuMucAnh,
          icon: icon[e.key] ?? Icons.place_outlined,
          diem: [for (final d in e.value) Offset(d.x, d.y)],
        ),
    ]..sort((a, b) => a.nhom.compareTo(b.nhom));
  }
}

List<KhuVuc> sapTheoKhoangCach(List<KhuVuc> ds, ViTri? vt) {
  if (vt == null) return ds;
  final kc = {for (final k in ds) k: k.khoangCach(vt.xGop, vt.yGop)};
  return [...ds]..sort((a, b) => kc[a]!.compareTo(kc[b]!));
}
