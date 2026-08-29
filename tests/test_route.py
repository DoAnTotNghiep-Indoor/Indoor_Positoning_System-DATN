"""Kiểm thử đồ thị đi lại, /map, /route và WS /ws/location."""

from __future__ import annotations

import math

import pytest

from backend.services.routing_service import DoThiDiLai


@pytest.fixture(scope="module")
def do_thi() -> DoThiDiLai:
    return DoThiDiLai()


# --- Đồ thị ---

def test_do_thi_lien_thong(do_thi):
    """Không được có điểm cô lập, nếu không có đích đến nào không tới được.

    Ngưỡng khoảng cách thuần để lại điểm cô lập ngay cả ở 12 m vì các điểm tham
    chiếu thưa và không đều — đó là lý do dùng k láng giềng gần nhất.
    """
    tu = next(iter(do_thi.toa_do))
    for den in do_thi.toa_do:
        duong, m = do_thi.tim_duong(tu, den)
        assert duong, f"không có đường từ {tu} tới {den}"
        assert math.isfinite(m)


def test_moi_diem_deu_co_canh(do_thi):
    for k in do_thi.toa_do:
        assert do_thi.ke[k], f"{k} không nối với điểm nào"


def test_duong_di_lien_tuc(do_thi):
    """Hai điểm liền nhau trên đường đi phải thực sự có cạnh nối."""
    duong, _ = do_thi.tim_duong("RP01", "RP39")
    for a, b in zip(duong, duong[1:]):
        assert any(k == b for k, _ in do_thi.ke[a]), f"{a} và {b} không có cạnh"


def test_quang_duong_bang_tong_cac_chang(do_thi):
    duong, tong = do_thi.tim_duong("RP01", "RP39")
    cong = sum(do_thi.khoang_cach(a, b) for a, b in zip(duong, duong[1:]))
    assert cong == pytest.approx(tong)


def test_quang_duong_khong_ngan_hon_duong_chim_bay(do_thi):
    """Bất biến hình học: đi theo đồ thị không thể ngắn hơn đường thẳng."""
    for a, b in (("RP01", "RP39"), ("RP03", "RP27"), ("RP11", "RP40")):
        _, tong = do_thi.tim_duong(a, b)
        assert tong >= do_thi.khoang_cach(a, b) - 1e-9


def test_di_va_ve_bang_nhau(do_thi):
    _, xuoi = do_thi.tim_duong("RP05", "RP33")
    _, nguoc = do_thi.tim_duong("RP33", "RP05")
    assert xuoi == pytest.approx(nguoc)


def test_tu_minh_toi_minh_la_khong_met(do_thi):
    duong, m = do_thi.tim_duong("RP07", "RP07")
    assert duong == ["RP07"] and m == 0.0


def test_gan_nhat_tra_ve_dung_diem(do_thi):
    x, y = do_thi.toa_do["RP11"]
    assert do_thi.gan_nhat(x + 0.4, y - 0.4) == "RP11"


# --- API ---

def test_map_tra_ve_don_vi_met(client):
    d = client.get("/map").json()
    assert d["don_vi"] == "met"
    assert len(d["diem_tham_chieu"]) == d["do_thi"]["so_diem"]

    # Phạm vi phải khớp toà nhà thật: x trong [-43, 43], y trong [0, 52].
    assert d["pham_vi"]["x_min"] == -43 and d["pham_vi"]["x_max"] == 43
    assert d["pham_vi"]["y_min"] == 0 and d["pham_vi"]["y_max"] == 52


def test_graph_liet_ke_du_canh(client):
    d = client.get("/graph").json()
    assert len(d["canh"]) == d["so_canh"]
    assert all(c["khoang_cach_m"] > 0 for c in d["canh"])


def test_route_tra_ve_duong_di(client):
    d = client.post("/route", json={"tu_rp": "RP01", "den_rp": "RP39"}).json()
    assert d["tu"] == "RP01" and d["den"] == "RP39"
    assert d["so_chang"] == len(d["duong_di"]) - 1
    assert d["quang_duong_m"] > 0


def test_route_neo_tu_toa_do(client):
    """Đưa toạ độ mét bất kỳ thì hệ tự neo vào điểm tham chiếu gần nhất."""
    d = client.post("/route", json={"tu_x": -16.2, "tu_y": 0.3, "den_rp": "RP20"}).json()
    assert d["tu"] == "RP01"


def test_route_toi_diem_khong_ton_tai(client):
    assert client.post("/route", json={"tu_rp": "RP01", "den_rp": "RP99"}).status_code == 404


# --- WebSocket ---

def test_ws_tra_ve_toa_do(client):
    with client.websocket_connect("/ws/location") as ws:
        ws.send_json({"device_id": "ws-1", "scan": []})
        d = ws.receive_json()
        assert d["device_id"] == "ws-1"
        assert "x" in d and "x_smooth" in d
        assert d["latency_ms"] < 200


def test_ws_thieu_device_id_thi_bao_loi(client):
    with client.websocket_connect("/ws/location") as ws:
        ws.send_json({"scan": []})
        assert "loi" in ws.receive_json()


def test_ws_phat_cho_dashboard_dang_xem(client):
    """Dashboard không gửi gì vẫn nhận được toạ độ của thiết bị khác."""
    with client.websocket_connect("/ws/location") as xem:
        with client.websocket_connect("/ws/location") as may:
            may.send_json({"device_id": "may-di-dong", "scan": []})
            may.receive_json()
            phat = xem.receive_json()

    assert phat["device_id"] == "may-di-dong"


def test_rest_cung_phat_cho_dashboard(client):
    """Toạ độ gửi bằng POST /predict cũng phải tới được dashboard đang xem.

    Trước khi gộp hai lối, /predict tự viết lại luồng và quên bước phát nên
    dashboard chỉ nhìn thấy thiết bị nào dùng WebSocket.

    Sau khi POST thì dashboard tự gửi một lần quét của chính nó, để nếu bước
    phát bị mất thì bài test hỏng ngay ở gói tin đầu chứ không treo chờ mãi.
    """
    with client.websocket_connect("/ws/location") as xem:
        client.post("/predict", json={"device_id": "qua-rest", "scan": []})
        xem.send_json({"device_id": "dashboard", "scan": []})
        dau_tien = xem.receive_json()

    assert dau_tien["device_id"] == "qua-rest"


def test_route_thieu_diem_dau_thi_bao_loi(client):
    """Quên gửi điểm đầu phải bị từ chối, không được âm thầm lấy RP02.

    RP02 nằm đúng tại (0, 0) nên mặc định tu_x = tu_y = 0.0 của bản trước khiến
    yêu cầu thiếu điểm đầu vẫn trả về một tuyến đường trông rất hợp lý.
    """
    assert client.post("/route", json={"den_rp": "RP20"}).status_code == 422


def test_route_thieu_mot_nua_toa_do_thi_bao_loi(client):
    assert client.post("/route", json={"den_rp": "RP20", "tu_x": -16.2}).status_code == 422


def test_route_tu_diem_khong_ton_tai(client):
    """Điểm đầu lạ phải ra 404 như điểm đến, không phải 500.

    Bản trước chỉ kiểm đầu đến nên tu_rp lạ lọt xuống Dijkstra và vỡ KeyError.
    """
    r = client.post("/route", json={"tu_rp": "RP99", "den_rp": "RP01"})
    assert r.status_code == 404
    assert "RP99" in r.json()["detail"]
