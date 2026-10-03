from __future__ import annotations

import json

import pytest

from ml import xuat_mo_hinh
from tests.conftest import thieu_artifact


@pytest.mark.skipif(thieu_artifact(), reason="chưa có mô hình")
def test_mo_hinh_trong_app_khop_artifacts():
    """Học lại mà quên xuất thì app định vị bằng mô hình cũ mà không ai biết."""
    tren_app = json.loads(xuat_mo_hinh.TEP_APP.read_text(encoding="utf-8"))
    hien_tai = xuat_mo_hinh.du_lieu_app(*xuat_mo_hinh.nap())
    assert tren_app == json.loads(json.dumps(hien_tai)), "chạy `python -m ml.xuat_mo_hinh`"
