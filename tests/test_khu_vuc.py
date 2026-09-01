"""Đối chiếu bản khu vực nhúng trong ứng dụng với reference_points.csv.

`mobile/lib/data/khu_vuc_thu_vien.dart` do `tools/sinh_khu_vuc.py` sinh ra để
ứng dụng vẫn có danh sách khu vực khi chưa nối được máy chủ. Hai nơi giữ cùng
một nội dung nên phải có bài kiểm buộc chúng đi cùng nhau — sửa CSV mà quên sinh
lại thì app hiện dữ liệu cũ mà không có gì báo.
"""

from __future__ import annotations

import re

import pandas as pd
import pytest

from ml import config
from tools import sinh_khu_vuc

DART = config.ROOT_DIR / "mobile" / "lib" / "data" / "khu_vuc_thu_vien.dart"


@pytest.fixture(scope="module")
def rp() -> pd.DataFrame:
    d = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
    return d.dropna(subset=["x", "y"])


@pytest.fixture(scope="module")
def dart() -> str:
    return DART.read_text(encoding="utf-8")


def test_ban_nhung_khop_voi_csv(dart):
    """So từng byte với thứ bộ sinh cho ra ngay lúc này."""
    assert dart == sinh_khu_vuc.sinh(), (
        "khu_vuc_thu_vien.dart đã lệch khỏi CSV — chạy "
        "`python -m tools.sinh_khu_vuc`"
    )


def test_du_so_khu_vuc(rp, dart):
    assert dart.count("KhuVuc(") == rp["nhom"].nunique()


def test_moi_khu_vuc_deu_co_ten_va_thu_muc_anh(rp, dart):
    for nhom in sorted(rp["nhom"].unique()):
        assert f"nhom: '{nhom}'" in dart or f"nhom: '{nhom}'".replace(
            "'", "\\'"
        ) in dart, nhom
    # Không khu vực nào được để trống thư mục ảnh: cột đó là khoá tra ảnh.
    assert "thuMucAnh: ''" not in dart


def test_diem_tham_chieu_khong_sot(rp, dart):
    """Tổng số Offset trong tệp phải bằng số điểm có toạ độ."""
    assert dart.count("Offset(") == len(rp)


def test_nhom_ban_thu_thu_da_sua(rp):
    """CTK45 để `categoryMap` ánh xạ ban_thu_thu sang "Kệ sách", trong khi tên
    điểm, tên thư mục ảnh và mô tả chi tiết của chính họ đều nói "Bàn thủ thư".
    """
    assert "Kệ sách" not in set(rp["nhom"])
    ban = rp[rp["thu_muc_anh"] == "ban_thu_thu"]
    assert len(ban) == 2
    assert set(ban["nhom"]) == {"Bàn thủ thư"}
    assert set(ban["ten"]) == {"Bàn thủ thư"}


def test_mo_ta_chi_tiet_dai_hon_mo_ta_mot_dong(rp):
    """Cột `mo_ta_chi_tiet` lấy từ `information.dart` của CTK45, khác hẳn câu
    một dòng trong `getPOIDescriptions()` mà cột `mo_ta` dùng."""
    co = rp[rp["mo_ta_chi_tiet"].fillna("") != ""]
    assert len(co) > 0
    for h in co.itertuples():
        assert len(h.mo_ta_chi_tiet) > len(h.mo_ta), h.rp_id


def test_loi_di_khong_can_mo_ta_chi_tiet(rp):
    """Cầu thang và hành lang là lối đi chứ không phải điểm đến — CTK45 cố ý
    không viết mô tả chi tiết cho chúng, và ứng dụng lùi về câu một dòng."""
    thieu = set(rp[rp["mo_ta_chi_tiet"].fillna("") == ""]["thu_muc_anh"])
    assert thieu == {"cau_thang", "hanh_lang"}


def test_bieu_tuong_phu_het_moi_nhom(rp):
    """Thiếu một nhóm thì bộ sinh ném KeyError chứ không lặng lẽ bỏ qua."""
    assert set(sinh_khu_vuc.ICON) == set(rp["nhom"])


def test_api_map_tra_ve_mo_ta_chi_tiet(client):
    d = client.get("/map").json()["diem_tham_chieu"]
    co = [x for x in d if x["mo_ta_chi_tiet"]]
    assert co, "GET /map không trả mô tả chi tiết"

    ban = [x for x in d if x["rp_id"] == "RP36"][0]
    assert ban["nhom"] == "Bàn thủ thư"
    assert "cán bộ thư viện" in ban["mo_ta_chi_tiet"]


def test_duong_di_khong_kem_mo_ta_chi_tiet(client):
    """Nhân đoạn dài với số chặng chỉ làm nặng response mà không ai đọc."""
    tra = client.post("/route", json={"tu_rp": "RP01", "den_rp": "RP39"})
    for b in tra.json()["duong_di"]:
        assert "mo_ta_chi_tiet" not in b


def test_khong_con_phong_hu_cau_trong_ung_dung():
    """Sáu phòng do đội giao diện tự dựng — không có trong dữ liệu khảo sát,
    cũng không có trong mã nguồn CTK45."""
    lib = config.ROOT_DIR / "mobile" / "lib"
    ma = "\n".join(
        p.read_text(encoding="utf-8")
        for p in lib.rglob("*.dart")
        if "app_localizations" not in p.name
    )
    # Chỉ tra những cụm không thể xuất hiện hợp lệ ở chỗ khác. "hội thảo" nằm
    # trong mô tả thật của Hội trường nên không dùng làm dấu hiệu được.
    for phong in ("Phòng nghiệp vụ", "nghiệp vụ 1", "nghiệp vụ 2",
                  "sau đại học", "Phòng hội thảo",
                  "Trung tâm Công nghệ thông tin"):
        assert phong not in ma, f"còn phòng hư cấu: {phong}"


def test_moi_loi_vao_deu_truyen_khu_vuc():
    """Bốn trong năm lối vào từng mở `const AreaDetailScreen()` không tham số,
    nên mọi ô bấm được đều dẫn tới một màn duy nhất tên "Không gian đọc"."""
    lib = config.ROOT_DIR / "mobile" / "lib"
    for p in lib.rglob("*.dart"):
        ma = p.read_text(encoding="utf-8")
        for goi in re.findall(r"AreaDetailScreen\([^)]*\)", ma):
            # Bỏ qua chính khai báo hàm dựng.
            if "super.key" in goi:
                continue
            assert "khuVuc:" in goi, f"{p.name}: {goi}"
