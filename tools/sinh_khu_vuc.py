"""Sinh mobile/lib/data/khu_vuc_thu_vien.dart từ reference_points.csv.

    python -m tools.sinh_khu_vuc

Bản nhúng sẵn này để ứng dụng vẫn có danh sách khu vực, ảnh và mô tả khi chưa
nối được máy chủ. Chỉ gồm phần DỮ LIỆU; lớp `KhuVuc` và phần gộp điểm viết tay
ở `mobile/lib/data/khu_vuc.dart` để lần sinh lại không đè mất.

`tests/test_khu_vuc.py` đối chiếu tệp sinh ra với CSV, nên sửa lệch một bên là
bài test đỏ chứ không âm thầm trôi khỏi nhau.
"""

from __future__ import annotations

import pandas as pd

from ml import config

RA = config.ROOT_DIR / "mobile" / "lib" / "data" / "khu_vuc_thu_vien.dart"

# Biểu tượng cho từng nhóm. Lấy ý từ `CategoryModel` của CTK45 nhưng đổi sang
# bộ Material mà cả ứng dụng đang dùng, để nét icon đồng bộ.
ICON = {
    "TV3,4": "Icons.computer_outlined",
    "Cửa ra vào": "Icons.door_front_door_outlined",
    "Hội trường thư viện": "Icons.stadium_outlined",
    "Cầu thang": "Icons.stairs_outlined",
    "Cầu thang tầng 2": "Icons.stairs_outlined",
    "Khu vực tự học": "Icons.school_outlined",
    "Khu vực đọc": "Icons.menu_book_outlined",
    "Căn tin": "Icons.restaurant_outlined",
    "Hành lang": "Icons.linear_scale_outlined",
    "Bàn thủ thư": "Icons.support_agent_outlined",
    "Phòng tạp chí": "Icons.article_outlined",
}


def _chuoi(s) -> str:
    van = "" if not isinstance(s, str) else s
    return "'" + van.replace("\\", "\\\\").replace("'", "\\'") + "'"


def sinh() -> str:
    d = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
    d = d.dropna(subset=["x", "y"])

    khoi = []
    for nhom, g in d.groupby("nhom", sort=True):
        dau = g.iloc[0]
        diem = ", ".join(
            f"Offset({r.x:g}, {r.y:g})" for r in g.sort_values("rp_id").itertuples()
        )
        khoi.append(
            "    KhuVuc(\n"
            f"      nhom: {_chuoi(nhom)},\n"
            f"      moTa: {_chuoi(dau.mo_ta)},\n"
            f"      moTaChiTiet: {_chuoi(dau.mo_ta_chi_tiet)},\n"
            f"      thuMucAnh: {_chuoi(dau.thu_muc_anh)},\n"
            f"      icon: {ICON[nhom]},\n"
            f"      diem: [{diem}],\n"
            "    ),"
        )

    than = "\n".join(khoi)
    return f"""import 'package:flutter/material.dart';

import 'khu_vuc.dart';

/// {len(khoi)} khu vực của thư viện, nhúng sẵn làm bản dự phòng.
///
/// Nguồn là `data/reference/reference_points.csv`, cũng chính là thứ `GET /map`
/// trả về. Nhúng vào ứng dụng để danh sách khu vực, ảnh và mô tả vẫn dùng được
/// khi chưa nối được máy chủ — lúc demo trước hội đồng, backend có thể chưa kịp
/// bật.
///
/// SINH TỰ ĐỘNG bằng `python -m tools.sinh_khu_vuc`, đừng sửa tay.
class KhuVucThuVien {{
  KhuVucThuVien._();

  static const tatCa = <KhuVuc>[
{than}
  ];
}}
"""


def main() -> None:
    ma = sinh()
    RA.write_bytes(ma.encode("utf-8"))
    print(f"{RA.name}: {ma.count('KhuVuc(')} khu vực, {len(ma.splitlines())} dòng")


if __name__ == "__main__":
    main()
