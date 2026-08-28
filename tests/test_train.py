"""Kiểm thử quy trình huấn luyện — trọng tâm là chống rò rỉ tập test.

Bài test cốt lõi ở đây khoá một bất biến đã từng bị vi phạm: mọi quyết định phải
dựa trên tập validation, tập test chỉ được đọc ở bước cuối để in ra báo cáo.

Lỗi cũ rất khó thấy vì nó không làm gì sai lộ liễu — với bộ dữ liệu hiện tại,
chọn theo test và chọn theo validation cho ra cùng một người thắng, nên bảng kết
quả không đổi và không có kiểm thử nào đỏ. Nó chỉ sai về lập luận, và sẽ âm thầm
chọn nhầm khi thêm dữ liệu hoặc thêm mô hình.
"""

from __future__ import annotations

from ml.train import chon_theo_validation


def _mo_hinh(ten: str, loi_validation: float, loi_test: float) -> dict:
    """Bản ghi kết quả tối giản, đúng hình dạng mà `run()` dựng ra."""

    class _Module:
        TEN = ten

    return {
        "module": _Module,
        "loi_validation": loi_validation,
        "ket_qua_test": {"loi_trung_binh": loi_test},
    }


def test_chon_theo_validation_chu_khong_theo_test():
    """Bài test quan trọng nhất của tệp này.

    Dựng đúng tình huống hai cách chọn cho hai kết quả KHÁC nhau: mô hình A tốt
    hơn trên validation, mô hình B tốt hơn trên test. Phải chọn A.

    Nếu ai đó đổi lại thành `min(..., key=lambda r: r["ket_qua_test"][...])` thì
    bài này đỏ ngay, kể cả khi toàn bộ pipeline vẫn chạy trơn.
    """
    a = _mo_hinh("A", loi_validation=3.0, loi_test=9.0)
    b = _mo_hinh("B", loi_validation=8.0, loi_test=1.0)

    chon = chon_theo_validation([a, b])

    assert chon is a, "Phải chọn theo validation, không được nhìn vào sai số test"
    assert chon["module"].TEN == "A"


def test_loc_ung_vien():
    """`loc` dùng để chọn riêng trong nhóm mô hình cơ sở."""
    ds = [
        _mo_hinh("kNN vân tay (Bray-Curtis)", 2.0, 2.0),
        _mo_hinh("kNN", 5.0, 5.0),
        _mo_hinh("WKNN", 4.0, 4.0),
    ]

    co_so = chon_theo_validation(ds, lambda r: r["module"].TEN in ("kNN", "WKNN"))

    assert co_so["module"].TEN == "WKNN"


def test_khong_con_ung_vien_thi_tra_ve_none():
    """Trả None chứ không ném ValueError.

    Đây là đường đi của `python -m ml.train --mo-hinh fingerprint_knn`: không có
    mô hình cơ sở nào trong danh sách. Bản trước gọi thẳng `min()` trên chuỗi
    rỗng nên sập ở dòng gần cuối, sau khi đã huấn luyện xong toàn bộ.
    """
    ds = [_mo_hinh("kNN vân tay (Bray-Curtis)", 2.0, 2.0)]

    assert chon_theo_validation(ds, lambda r: r["module"].TEN in ("kNN", "WKNN")) is None


def test_danh_sach_rong():
    assert chon_theo_validation([]) is None


def test_hoa_thi_lay_cai_dau_tien():
    """Bằng điểm validation thì giữ thứ tự khai báo trong ml/models/__init__.py.

    Không phải yêu cầu nghiệp vụ, nhưng cố định lại để kết quả tái lập được giữa
    các lần chạy — đồ án cần con số ổn định khi in vào báo cáo.
    """
    a = _mo_hinh("A", loi_validation=3.0, loi_test=9.0)
    b = _mo_hinh("B", loi_validation=3.0, loi_test=1.0)

    assert chon_theo_validation([a, b]) is a
