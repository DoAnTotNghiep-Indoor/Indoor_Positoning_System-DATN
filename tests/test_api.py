"""Kiểm thử API định vị — chạy thẳng qua ASGI, không cần bật server.

Fixture `client` và chốt chặn "chưa huấn luyện" nằm ở tests/conftest.py.
"""

from __future__ import annotations

import json

import pytest

from ml import config


@pytest.fixture(scope="module")
def ap_cols() -> list[str]:
    duong_dan = config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON
    return json.loads(duong_dan.read_text(encoding="utf-8"))["ap_columns"]


def test_health_bao_model_da_nap(client):
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["trang_thai"] == "ok"
    assert d["so_dac_trung"] == 36
    assert d["gia_tri_dien_thieu"] == -96.0


def test_predict_tra_ve_toa_do(client, ap_cols):
    r = client.post("/predict", json={
        "device_id": "may-test",
        "scan": [{"bssid": b, "rssi": -55} for b in ap_cols[:12]],
    })
    assert r.status_code == 200
    d = r.json()

    # Toạ độ phải nằm trong phạm vi toà nhà: x trong [-43, 43], y trong [0, 52].
    assert -43 <= d["x"] <= 43 and 0 <= d["y"] <= 52
    assert d["matched_ap"] == 12
    assert d["model"]

    # Yêu cầu phi chức năng: dưới 200 ms cho cả đường đi.
    assert d["latency_ms"] < 200


def test_predict_bo_qua_bssid_la(client, ap_cols):
    """AP mới lắp hoặc hotspot điện thoại không được làm lệch kết quả."""
    quen = [{"bssid": b, "rssi": -60} for b in ap_cols[:8]]
    them_la = quen + [{"bssid": "00:11:22:33:44:55", "rssi": -30}]

    a = client.post("/predict", json={"device_id": "a", "scan": quen}).json()
    b = client.post("/predict", json={"device_id": "b", "scan": them_la}).json()

    assert (a["x"], a["y"]) == (b["x"], b["y"])
    assert a["matched_ap"] == b["matched_ap"] == 8


def test_quet_rong_van_tra_ve_toa_do(client):
    """Không bắt được AP nào thì vector toàn giá trị điền thiếu, vẫn phải chạy."""
    r = client.post("/predict", json={"device_id": "rong", "scan": []})
    assert r.status_code == 200
    assert r.json()["matched_ap"] == 0


def test_gop_cua_so_truot_dap_tat_lan_quet_lac(client, ap_cols):
    """Đây là bài test cho tầng đưa sai số từ 2,56 m xuống 0,73 m.

    Gửi hai lần quét giống nhau rồi một lần quét lạc. Toạ độ thô của lần thứ ba
    đi theo lần quét lạc, nhưng toạ độ đã gộp phải bị hai lần trước áp đảo.
    """
    binh_thuong = [{"bssid": b, "rssi": -55} for b in ap_cols[:12]]
    lac = [{"bssid": b, "rssi": -55} for b in ap_cols[-12:]]

    a = client.post("/predict", json={"device_id": "gop", "scan": binh_thuong}).json()
    client.post("/predict", json={"device_id": "gop", "scan": binh_thuong})
    c = client.post("/predict", json={"device_id": "gop", "scan": lac}).json()

    assert c["scan_count"] == 3
    assert (c["x_smooth"], c["y_smooth"]) == (a["x"], a["y"])


def test_thiet_bi_khac_nhau_khong_lan_lich_su(client, ap_cols):
    scan = [{"bssid": b, "rssi": -55} for b in ap_cols[:12]]
    r = client.post("/predict", json={"device_id": "rieng-biet", "scan": scan})
    assert r.json()["scan_count"] == 1


def test_lich_su_ghi_xuong_csdl(client):
    r = client.get("/predictions", params={"device_id": "gop"})
    assert r.status_code == 200
    ds = r.json()
    assert len(ds) == 3
    assert all(m["mo_hinh"] for m in ds)


def test_thieu_device_id_thi_bao_loi(client):
    r = client.post("/predict", json={"scan": []})
    assert r.status_code == 422


def test_scan_khong_kem_bssid_thi_bao_loi(client):
    """Chặn đúng lỗi CTK45: mảng số trần không kèm BSSID phải bị từ chối."""
    r = client.post("/predict", json={"device_id": "x", "scan": [-55, -60]})
    assert r.status_code == 422


def test_bo_gop_khong_phinh_theo_so_thiet_bi():
    """Thiết bị đã rời đi phải được bỏ hẳn, không chỉ xoá lịch sử.

    device_id do client tự đặt nên số khoá không bị chặn bởi số máy thật; thiếu
    bước dọn thì máy chủ chạy liên tục sẽ giữ lại mọi thiết bị từng gọi tới.
    """
    import time

    from backend.services.smoothing_service import BoGop

    bo_gop = BoGop(cua_so=3, reset_sau_giay=0.05)
    bo_gop.them("da-roi", 1.0, 2.0)
    time.sleep(0.12)
    bo_gop.them("dang-o-day", 3.0, 4.0)

    assert list(bo_gop._lich_su) == ["dang-o-day"]
    assert list(bo_gop._lan_cuoi) == ["dang-o-day"]


def test_doc_thiet_bi_la_khong_tao_khoa_moi():
    """so_mau_dang_giu() chỉ để đọc — bản defaultdict cũ tạo khoá khi đọc."""
    from backend.services.smoothing_service import BoGop

    bo_gop = BoGop()
    assert bo_gop.so_mau_dang_giu("chua-tung-thay") == 0
    assert bo_gop._lich_su == {}
