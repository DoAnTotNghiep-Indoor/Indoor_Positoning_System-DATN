"""Kiểm thử hậu xử lý gộp nhiều lần quét."""

from __future__ import annotations

import numpy as np
import pytest

from ml import postprocess


def test_mot_du_doan_thi_giu_nguyen():
    for cach in postprocess.CACH_GOP:
        np.testing.assert_allclose(postprocess.gop([[3.0, 4.0]], cach), [3.0, 4.0])


def test_dong_thuan_loai_diem_lac():
    """Đúng tình huống RP39: hai dự đoán gần nhau, một dự đoán lạc sang đầu kia."""
    du_doan = np.array([[22.0, 52.0], [29.0, 52.0], [0.0, 18.0]])
    np.testing.assert_allclose(
        postprocess.dong_thuan_khong_gian(du_doan), [22.0, 52.0]
    )


def test_trung_vi_cung_loai_duoc_diem_lac():
    du_doan = np.array([[22.0, 52.0], [29.0, 52.0], [0.0, 18.0]])
    np.testing.assert_allclose(postprocess.trung_vi_toa_do(du_doan), [22.0, 52.0])


def test_dong_thuan_luon_tra_ve_diem_co_that():
    """Khác trung vị: kết quả phải nằm trong danh sách dự đoán gốc."""
    du_doan = np.array([[0.0, 0.0], [10.0, 10.0], [0.0, 10.0]])
    kq = postprocess.dong_thuan_khong_gian(du_doan)
    assert any(np.allclose(kq, p) for p in du_doan)


def test_tat_ca_giong_nhau_thi_tra_ve_chinh_no():
    du_doan = np.tile([7.0, -3.0], (5, 1))
    for cach in postprocess.CACH_GOP:
        np.testing.assert_allclose(postprocess.gop(du_doan, cach), [7.0, -3.0])


def test_cach_gop_khong_hop_le():
    with pytest.raises(ValueError, match="không hợp lệ"):
        postprocess.gop([[0.0, 0.0]], "khong_ton_tai")


def test_cua_so_truot_giu_nguyen_do_dai():
    chuoi = np.array([[0.0, 0.0], [1.0, 1.0], [50.0, 50.0], [1.0, 1.0], [0.0, 0.0]])
    kq = postprocess.gop_cua_so_truot(chuoi, cua_so=3)
    assert kq.shape == chuoi.shape


def test_cua_so_truot_co_ket_qua_ngay_tu_mau_dau():
    """Không được bỏ trống những mẫu đầu chuỗi — hệ thống cần toạ độ ngay."""
    chuoi = np.array([[5.0, 5.0], [6.0, 6.0]])
    kq = postprocess.gop_cua_so_truot(chuoi, cua_so=3)
    np.testing.assert_allclose(kq[0], [5.0, 5.0])


def test_cua_so_truot_dap_tat_mot_lan_quet_di_thuong():
    chuoi = np.array([[0.0, 0.0], [0.0, 0.0], [40.0, 40.0], [0.0, 0.0]])
    kq = postprocess.gop_cua_so_truot(chuoi, cua_so=3, cach="dong_thuan")
    # Mẫu dị thường ở vị trí 2 bị hai mẫu lành hai bên áp đảo
    np.testing.assert_allclose(kq[3], [0.0, 0.0])
    assert np.linalg.norm(kq[2]) < 40.0
