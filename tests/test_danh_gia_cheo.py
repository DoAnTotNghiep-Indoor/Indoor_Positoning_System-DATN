"""Kiểm thử giao thức đánh giá thứ hai — bỏ trọn một điểm tham chiếu.

Giao thức sinh ra để loại một loại rò rỉ nên bản thân nó phải sạch trước. Ba
bất biến khoá đúng ba chỗ có thể lặng lẽ mang rò rỉ trở lại: đọc nhầm tệp đã
chuẩn hoá, khớp scaler một lần bên ngoài vòng lặp, và để điểm đang bị giữ lại
lọt vào phần huấn luyện.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest
from sklearn.model_selection import LeaveOneGroupOut

from ml import danh_gia_cheo


def test_doc_du_lieu_dBm_tho_chu_khong_doc_tep_da_chuan_hoa():
    # data/splits/*.csv đã chuẩn hoá bằng scaler khớp trên toàn tập train, tức
    # đã thấy mọi điểm tham chiếu. Nạp chúng vào đây là mang lại đúng thứ rò rỉ
    # mà module này sinh ra để loại bỏ.
    ma = inspect.getsource(danh_gia_cheo)
    assert "SPLITS_DIR" not in ma
    assert danh_gia_cheo.NGUON_THO == "fingerprint_dataset_raw.csv"

    X, _, _, _ = danh_gia_cheo.nap_tho()
    # dBm thô nằm quanh -96..-29; đã chuẩn hoá thì nằm trong [0, 1].
    assert X.min() < -20, "dữ liệu trông như đã chuẩn hoá, không phải dBm thô"


def test_moi_lan_gap_khop_scaler_lai_tren_rieng_phan_huan_luyen():
    # Khớp một lần bên ngoài vòng lặp thì min/max của điểm đang bị giữ lại lọt
    # vào phép chuẩn hoá. Bắt bằng cách đếm: phải có đúng một MinMaxScaler mới
    # cho mỗi lần gấp, và mỗi cái chỉ được nhìn phần huấn luyện.
    thay = []

    class _Ghi:
        def fit(self, X):
            thay.append(len(X))
            self._n = X.shape[1]
            return self

        def transform(self, X):
            return np.asarray(X, dtype=float)

    goc = danh_gia_cheo.MinMaxScaler
    danh_gia_cheo.MinMaxScaler = _Ghi
    try:
        X, Y, nhom, _ = danh_gia_cheo.nap_tho()
        # Một mô hình rẻ nhất là đủ: bài test đo cách chia, không đo chất lượng.
        from ml.models import knn
        danh_gia_cheo.chay_mot_mo_hinh(knn, X, Y, nhom, {"n_neighbors": 1})
    finally:
        danh_gia_cheo.MinMaxScaler = goc

    so_gap = len(np.unique(nhom))
    assert len(thay) == so_gap, "phải khớp scaler lại trong TỪNG lần gấp"
    assert all(n < len(X) for n in thay), "scaler đã nhìn thấy cả tập"


def test_diem_dang_giu_lai_khong_co_mat_trong_phan_huan_luyen():
    _, Y, nhom, _ = danh_gia_cheo.nap_tho()
    X = np.zeros((len(Y), 1))
    for i_hoc, i_thu in LeaveOneGroupOut().split(X, Y, groups=nhom):
        giu = set(nhom[i_thu])
        assert len(giu) == 1, "mỗi lần gấp phải giữ lại đúng một điểm"
        assert not (giu & set(nhom[i_hoc])), "điểm bị giữ lại vẫn lọt vào lúc học"


def test_tham_so_lay_dung_bo_da_chon_luc_huan_luyen():
    # Hai bảng so sánh chỉ có nghĩa nếu chạy cùng một cấu hình mô hình; khác
    # tham số thì phần chênh lệch lẫn cả tác dụng của việc dò lưới.
    from ml.models import xgboost_model
    t = danh_gia_cheo._tham_so("xgboost_model", xgboost_model)
    assert t, "không lấy được tham số nào"
    assert set(t) <= set(xgboost_model.LUOI_THAM_SO), "tham số lạ so với lưới"


@pytest.mark.parametrize("khoa", ["knn", "wknn", "random_forest",
                                  "xgboost_model", "fingerprint_knn"])
def test_moi_mo_hinh_deu_co_tham_so_dung_duoc(khoa):
    import importlib
    mo_dun = importlib.import_module(f"ml.models.{khoa}")
    mo_hinh = mo_dun.build(**danh_gia_cheo._tham_so(khoa, mo_dun))
    assert hasattr(mo_hinh, "fit") and hasattr(mo_hinh, "predict")


def test_report_tu_choi_so_lieu_cua_luoi_rut_gon(monkeypatch):
    """`ml.train --nhanh` ghi đè artifact y như lần chạy đầy đủ.

    Trường `luoi` trong model_metadata.json là dấu hiệu duy nhất phân biệt, mà
    trước đây không nơi nào đọc nó — chạy lưới rút gọn rồi quên chạy lại là báo
    cáo mang số sai mà không ai biết.
    """
    from ml import report

    def gia(*_a, **_k):
        return ({"luoi": "nhanh", "huan_luyen_luc": "2026-01-01T00:00:00"},
                [], None, {}, {}, [])

    monkeypatch.setattr(report, "nap", gia)

    with pytest.raises(SystemExit) as e:
        report.chay()
    assert "lưới đầy đủ" in str(e.value)

    # Vẫn phải xem thử được khi người chạy nói rõ là mình biết.
    monkeypatch.setattr(report, "so_sanh_mo_hinh", lambda *a, **k: None)
    monkeypatch.setattr(report, "cdf", lambda *a, **k: None)
    monkeypatch.setattr(report, "hieu_qua_gop", lambda *a, **k: None)
    monkeypatch.setattr(report, "ban_do_loi", lambda *a, **k: None)
    monkeypatch.setattr(report, "do_quan_trong", lambda *a, **k: None)
    monkeypatch.setattr(report, "phan_bo_sai_so", lambda *a, **k: None)
    monkeypatch.setattr(report, "ti_le_xuat_hien_ap", lambda *a, **k: None)
    report.chay(cho_phep_luoi_rut_gon=True)


def test_artifact_hien_tai_dung_luoi_day_du():
    """Chốt luôn trên artifact thật: số đang nằm trong báo cáo phải là số của
    lưới đầy đủ."""
    import json

    from ml import config

    meta = json.loads(
        (config.ARTIFACTS_DIR / "model_metadata.json").read_text(encoding="utf-8")
    )
    assert meta["luoi"] == "day_du", (
        f"artifact đang là lưới '{meta['luoi']}' — chạy lại `python -m ml.train`")


def test_danh_gia_cheo_cung_tu_choi_luoi_rut_gon(monkeypatch):
    """`_tham_so` lấy siêu tham số từ chính model_metadata.json, nên bảng bỏ
    trọn một điểm — chỗ chốt thứ hạng XGBoost cho cả đồ án — thừa hưởng luôn
    lưới mà `ml.train` đã chạy."""
    monkeypatch.setattr(danh_gia_cheo, "_luoi_da_dung", lambda: "nhanh")

    with pytest.raises(SystemExit) as e:
        danh_gia_cheo.run()
    assert "lưới đầy đủ" in str(e.value)
