"""Kiểm thử đồ thị đi lại, /map, /route và WS /ws/location."""

from __future__ import annotations

import math

import pytest

from backend.services import routing_service
from backend.services.routing_service import DoThiDiLai


@pytest.fixture(scope="module")
def do_thi() -> DoThiDiLai:
    return DoThiDiLai()


@pytest.fixture(scope="module")
def quet_du_ap() -> list[dict]:
    """Một lần quét đủ AP quen để `/predict` chấp nhận.

    Không dùng `scan: []` được nữa: quét rỗng nay bị từ chối bằng 422, vì mô
    hình vẫn cho ra toạ độ với vector toàn giá trị điền-khi-thiếu và toạ độ đó
    không mang thông tin gì.
    """
    import json

    from ml import config

    hop_dong = json.loads(
        (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8")
    )
    return [
        {"bssid": b, "rssi": -55.0}
        for b in hop_dong["ap_columns"][: hop_dong["min_ap_per_scan"]]
    ]


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

def test_ws_tra_ve_toa_do(client, quet_du_ap):
    with client.websocket_connect("/ws/location") as ws:
        ws.send_json({"device_id": "ws-1", "scan": quet_du_ap})
        d = ws.receive_json()
        assert d["device_id"] == "ws-1"
        assert "x" in d and "x_smooth" in d
        assert d["latency_ms"] < 200


def test_ws_thieu_device_id_thi_bao_loi(client):
    with client.websocket_connect("/ws/location") as ws:
        ws.send_json({"scan": []})
        assert "loi" in ws.receive_json()


def test_ws_phat_cho_dashboard_dang_xem(client, quet_du_ap):
    """Dashboard không gửi gì vẫn nhận được toạ độ của thiết bị khác."""
    with client.websocket_connect("/ws/location") as xem:
        with client.websocket_connect("/ws/location") as may:
            may.send_json({"device_id": "may-di-dong", "scan": quet_du_ap})
            may.receive_json()
            phat = xem.receive_json()

    assert phat["device_id"] == "may-di-dong"


def test_rest_cung_phat_cho_dashboard(client, quet_du_ap):
    """Toạ độ gửi bằng POST /predict cũng phải tới được dashboard đang xem.

    Trước khi gộp hai lối, /predict tự viết lại luồng và quên bước phát nên
    dashboard chỉ nhìn thấy thiết bị nào dùng WebSocket.

    Sau khi POST thì dashboard tự gửi một lần quét của chính nó, để nếu bước
    phát bị mất thì bài test hỏng ngay ở gói tin đầu chứ không treo chờ mãi.
    """
    with client.websocket_connect("/ws/location") as xem:
        client.post("/predict", json={"device_id": "qua-rest", "scan": quet_du_ap})
        xem.send_json({"device_id": "dashboard", "scan": quet_du_ap})
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


def test_map_tra_ve_ten_va_mo_ta_cho_moi_diem(client):
    """Không điểm nào được để trống tên, nếu không giao diện phải hiện rp_id trần."""
    ds = client.get("/map").json()["diem_tham_chieu"]

    assert len(ds) == 40
    assert all(m["ten"] and m["nhom"] and m["mo_ta"] for m in ds)
    assert next(m for m in ds if m["rp_id"] == "RP39")["ten"] == "Phòng tạp chí"


def test_duong_di_co_ten_nhung_khong_kem_mo_ta(client):
    """Chỉ đường cần tên để nói "đi tới Phòng tạp chí" thay vì "đi tới RP39".

    Mô tả thì không: nhân với số chặng chỉ làm nặng response mà không ai đọc.
    """
    d = client.post("/route", json={"tu_rp": "RP01", "den_rp": "RP39"}).json()

    assert all(m["ten"] for m in d["duong_di"])
    assert d["duong_di"][-1]["ten"] == "Phòng tạp chí"
    assert "mo_ta" not in d["duong_di"][0]


def test_nhan_khop_dung_diem_tham_chieu(do_thi):
    """Ghép nhãn theo rp_id, không theo thứ tự dòng trong tệp.

    Hai cặp đối xứng qua trục giữa toà nhà phải cùng tên — đây cũng chính là
    bằng chứng dùng để xác nhận số điểm của CTK45 khớp số điểm của nhóm.
    """
    assert do_thi.nhan["RP16"]["ten"] == do_thi.nhan["RP17"]["ten"] == "Hành lang"
    assert do_thi.nhan["RP26"]["ten"] == do_thi.nhan["RP27"]["ten"] == "Khu vực đọc"


# --- Tường lấy từ sơ đồ mặt bằng (nhóm 3, mục F) ---

def test_khong_con_canh_xuyen_tuong(do_thi):
    """Mọi cạnh bị Map.png xác định là xuyên tường phải biến mất khỏi đồ thị,
    trừ các cạnh được khai lại làm cửa giả định."""
    xuyen, cua = routing_service._doc_ban_do()
    assert xuyen, "chưa đọc được ban_do_tang1.json"
    for canh in do_thi.canh:
        assert canh not in xuyen or canh in cua, f"{canh} xuyên tường"


def test_canh_dai_nhat_ngan_di_nho_tuong(do_thi):
    """Trước khi có sơ đồ, cạnh dài nhất là 22,36 m và gần như chắc chắn xuyên
    tường. Ngưỡng 18 m để bài test đỏ lên nếu ai đó vô hiệu hoá bộ lọc."""
    assert do_thi.thong_ke()["canh_dai_nhat_m"] <= 18.0


def test_cua_gia_dinh_deu_co_mat_trong_do_thi(do_thi):
    """Thiếu một cửa là đồ thị vỡ mảnh, mà test liên thông ở trên lại bắt được
    muộn và khó lần ra nguyên nhân."""
    _, cua = routing_service._doc_ban_do()
    for canh in cua:
        assert canh in do_thi.canh, f"thiếu cửa {canh}"


def test_duong_di_khong_chui_qua_tuong(do_thi):
    """Kiểm tra ở mức đường đi chứ không chỉ mức cạnh: RP01 nằm ở hàng cửa ra
    vào, RP39 ở đầu kia toà nhà, nên tuyến này đi qua gần hết các mảng sàn."""
    xuyen, cua = routing_service._doc_ban_do()
    duong, _ = do_thi.tim_duong("RP01", "RP39")
    for a, b in zip(duong, duong[1:]):
        khoa = (a, b) if a < b else (b, a)
        assert khoa not in xuyen or khoa in cua


def test_phai_di_vong_khi_co_tuong_chan(do_thi):
    """RP02 "Cửa ra vào" và RP05 "Cầu thang" cách nhau 12,8 m đường chim bay,
    nhưng giữa hai điểm là vạch cầu thang dài 544 px trong Map.png. Đường đi
    thật phải vòng qua đầu vạch đó."""
    _, quang_duong = do_thi.tim_duong("RP02", "RP05")
    chim_bay = do_thi.khoang_cach("RP02", "RP05")
    assert quang_duong > chim_bay * 1.5, (
        f"đi thẳng xuyên tường: {quang_duong:.1f} m so với {chim_bay:.1f} m"
    )


# --- Chỉ dẫn rẽ từng chặng (nhóm 4, mục H) ---

def test_re_trai_phai_dung_chieu(do_thi):
    """Kiểm bằng một ví dụ tính được bằng tay.

    Đi từ RP02 (0, 0) tới RP01 (-16, 0) là đi theo chiều x giảm. Sang chặng
    RP01 -> RP04 (-30, 10) thì y tăng. Hệ toạ độ có y hướng lên, nên khi mặt
    đang quay về phía x giảm, phía y tăng nằm bên TAY PHẢI.

    Đây là bài chặn đúng lỗi của CTK45: hàm getDirection của họ hoán vị hai
    trục nên mọi câu trái/phải đảo ngược, mà lỗi đó không làm chương trình sập.
    """
    buoc = do_thi.chi_dan(["RP02", "RP01", "RP04"])
    assert buoc[1]["huong"] in ("re_phai", "chech_phai"), buoc[1]
    assert buoc[1]["goc_do"] < 0


def test_soi_guong_thi_trai_phai_doi_cho(do_thi):
    """Toà nhà đối xứng qua trục x = 0, và các điểm tham chiếu cũng vậy. Lấy
    một tuyến rồi lấy tuyến ảnh gương của nó thì mọi góc quay phải đổi dấu."""
    trai = do_thi.chi_dan(["RP02", "RP01", "RP04", "RP08"])
    phai = do_thi.chi_dan(["RP02", "RP03", "RP07", "RP09"])
    assert len(trai) == len(phai)
    for a, b in zip(trai, phai):
        assert a["huong"] == b["huong"].replace("trai", "TAM").replace(
            "phai", "trai").replace("TAM", "phai")
        assert a["goc_do"] == pytest.approx(-b["goc_do"], abs=0.05)


def test_gop_cac_chang_di_thang_lien_tiep(do_thi):
    """RP33, RP34, RP35 cùng nằm trên y = 52 nên đi thẳng suốt: phải ra MỘT
    bước gộp chứ không phải hai bước "đi thẳng" liền nhau."""
    buoc = do_thi.chi_dan(["RP33", "RP34", "RP35"])
    assert len(buoc) == 1
    assert buoc[0]["den_rp"] == "RP35"
    assert buoc[0]["khoang_cach_m"] == pytest.approx(15.0)


def test_tong_quang_duong_chi_dan_bang_quang_duong_duong_di(do_thi):
    """Gộp bước không được làm mất mét nào."""
    duong, quang_duong = do_thi.tim_duong("RP01", "RP39")
    tong = sum(b["khoang_cach_m"] for b in do_thi.chi_dan(duong))
    assert tong == pytest.approx(quang_duong, abs=0.05)


def test_buoc_dau_khong_noi_trai_phai(do_thi):
    """Hệ biết người dùng đứng ở đâu nhưng không biết đang quay mặt về đâu."""
    buoc = do_thi.chi_dan(do_thi.tim_duong("RP01", "RP39")[0])
    assert buoc[0]["huong"] == "bat_dau"
    assert all(b["huong"] != "bat_dau" for b in buoc[1:])


def test_chi_dan_noi_lien_thanh_mot_chuoi(do_thi):
    """Điểm đến của bước trước phải là điểm bắt đầu của bước sau."""
    duong, _ = do_thi.tim_duong("RP16", "RP40")
    buoc = do_thi.chi_dan(duong)
    assert buoc[0]["tu_rp"] == duong[0]
    assert buoc[-1]["den_rp"] == duong[-1]
    for a, b in zip(buoc, buoc[1:]):
        assert a["den_rp"] == b["tu_rp"]


def test_di_toi_chinh_minh_thi_khong_co_buoc_nao(do_thi):
    assert do_thi.chi_dan(["RP01"]) == []


def test_route_tra_ve_chi_dan(client):
    tra = client.post("/route", json={"tu_rp": "RP01", "den_rp": "RP39"})
    assert tra.status_code == 200
    d = tra.json()
    assert d["chi_dan"], "thiếu chỉ dẫn"
    assert len(d["chi_dan"]) <= d["so_chang"], "gộp bước phải làm ngắn đi"

    hop_le = {"bat_dau", "di_thang", "chech_trai", "chech_phai",
              "re_trai", "re_phai", "quay_dau"}
    for b in d["chi_dan"]:
        assert b["huong"] in hop_le, b["huong"]
        assert -180 < b["goc_do"] <= 180
        assert b["khoang_cach_m"] > 0

    # Tên điểm đến đi kèm để client khỏi phải tra ngược sang /map.
    assert d["chi_dan"][-1]["den_ten"] == "Phòng tạp chí"

