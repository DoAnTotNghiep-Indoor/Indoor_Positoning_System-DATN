"""Kiểm thử các endpoint HTTP của backend."""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from ml import config

HOP_DONG = json.loads((config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8"))
AP = HOP_DONG["ap_columns"]
TOI_THIEU = HOP_DONG["min_ap_per_scan"]


def quet(bssid=AP, rssi=-55.0):
    return [{"bssid": b, "rssi": rssi} for b in bssid]


def du_doan(client, scan, device_id="may-test"):
    return client.post("/predict", json={"device_id": device_id, "scan": scan})


# --- Hệ thống ---

def test_health(client):
    d = client.get("/health").json()
    assert d["trang_thai"] == "ok"
    assert d["so_dac_trung"] == len(AP)
    assert d["gia_tri_dien_thieu"] == HOP_DONG["missing_rssi_value"]


@pytest.mark.parametrize("duong_dan", [
    "/health", "/map", "/graph", "/predictions",
    "/", "/src/js/dashboard.js", "/src/css/style.css"])
def test_moi_duong_dan_deu_tra_ve(client, duong_dan):
    # Dashboard mount ở "/" nhận mọi đường dẫn còn lại, không được che API.
    assert client.get(duong_dan).status_code == 200


# --- /predict ---

def test_predict_tra_ve_toa_do_trong_toa_nha(client):
    d = du_doan(client, quet(AP[:12])).json()
    assert -43 <= d["x"] <= 43 and 0 <= d["y"] <= 52
    assert d["matched_ap"] == 12
    assert d["latency_ms"] < 200
    assert 0 <= d["do_trai"] < 86


def test_anh_xa_bssid(client):
    """BSSID lạ bị bỏ qua, chữ hoa vẫn khớp, BSSID lặp lấy trung bình bất kể thứ tự."""
    goc = du_doan(client, quet(), "a").json()
    them_la = du_doan(client, quet() + quet(["00:11:22:33:44:55"], -30), "b").json()
    chu_hoa = du_doan(client, quet([b.upper() for b in AP]), "c").json()
    assert (goc["x"], goc["y"]) == (them_la["x"], them_la["y"]) == (chu_hoa["x"], chu_hoa["y"])
    assert them_la["matched_ap"] == chu_hoa["matched_ap"] == len(AP)

    lap = quet(AP[:1], -30) + quet(AP[:1], -90)
    xuoi = du_doan(client, lap + quet(AP[1:]), "d").json()
    nguoc = du_doan(client, lap[::-1] + quet(AP[1:]), "e").json()
    assert (xuoi["x"], xuoi["y"]) == (nguoc["x"], nguoc["y"])


@pytest.mark.parametrize("scan", [
    [],
    quet([f"aa:bb:cc:dd:ee:{i:02x}" for i in range(20)]),  # nhiều AP nhưng không AP nào quen
    quet(AP[:TOI_THIEU - 1]),
    quet(rssi=1000.0), quet(rssi=0.0), quet(rssi=-101.0),  # RSSI ngoài khoảng vật lý
])
def test_khong_du_ap_thi_tu_choi(client, scan):
    r = du_doan(client, scan, "thieu-ap")
    assert r.status_code == 422
    assert r.json()["detail"]["loi"] == "khong_du_ap"
    assert r.json()["detail"]["toi_thieu"] == TOI_THIEU


def test_vua_du_ap_va_bo_rieng_so_doc_loi(client):
    assert du_doan(client, quet(AP[:TOI_THIEU])).status_code == 200
    r = du_doan(client, quet(AP[:-1]) + quet(AP[-1:], 5.0))
    assert r.json()["matched_ap"] == len(AP) - 1


def test_lan_quet_bi_tu_choi_khong_ghi_lich_su(client):
    truoc = len(client.get("/predictions?gioi_han=1000").json())
    du_doan(client, [], "khong-ghi")
    assert len(client.get("/predictions?gioi_han=1000").json()) == truoc


def test_gop_cua_so_va_lich_su(client):
    binh_thuong, lac = quet(AP[:12]), quet(AP[-12:])
    a = du_doan(client, binh_thuong, "gop").json()
    du_doan(client, binh_thuong, "gop")
    c = du_doan(client, lac, "gop").json()
    # Hai lần quét giống nhau áp đảo lần lạc.
    assert c["scan_count"] == 3
    assert (c["x_smooth"], c["y_smooth"]) == (a["x"], a["y"])
    assert du_doan(client, binh_thuong, "thiet-bi-khac").json()["scan_count"] == 1

    ds = client.get("/predictions", params={"device_id": "gop"}).json()
    assert len(ds) == 3 and {m["device_id"] for m in ds} == {"gop"}
    assert ds[0]["do_trai"] == pytest.approx(c["do_trai"], abs=1e-3)
    assert ds[0]["luc"].endswith("Z") or "+" in ds[0]["luc"][10:]


@pytest.mark.parametrize("than", [
    {"scan": []},
    {"device_id": "x", "scan": [-55, -60]},  # mảng số trần không kèm BSSID
    {"device_id": "x", "scan": quet(["a" * 65])},
    {"device_id": "x", "scan": quet([f"aa:bb:cc:dd:{i // 256:02x}:{i % 256:02x}"
                                     for i in range(513)])},
])
def test_predict_sai_schema(client, than):
    assert client.post("/predict", json=than).status_code == 422


@pytest.mark.parametrize("gioi_han", [-1, 0, 1001])
def test_gioi_han_lich_su(client, gioi_han):
    assert client.get(f"/predictions?gioi_han={gioi_han}").status_code == 422


# --- /map và /graph ---

def test_map(client):
    d = client.get("/map").json()
    assert d["don_vi"] == "don_vi_luoi"
    assert d["met_moi_don_vi"] == pytest.approx(0.3508)
    assert d["pham_vi"] == {"x_min": -43, "x_max": 43, "y_min": 0, "y_max": 52}
    ds = d["diem_tham_chieu"]
    assert len(ds) == d["do_thi"]["so_diem"]
    assert all(m["ten"] and m["nhom"] and m["mo_ta"] for m in ds)
    assert any(m["mo_ta_chi_tiet"] for m in ds)


def test_graph(client):
    d = client.get("/graph").json()
    canh = d["canh"]
    assert len(canh) == d["so_canh"]
    assert all(c["khoang_cach_m"] > 0 for c in canh)

    co = {m["rp_id"] for m in client.get("/map").json()["diem_tham_chieu"]}
    assert {c[k] for c in canh for k in ("tu", "den")} <= co



# --- /route ---

def test_route_giua_hai_diem(client):
    d = client.post("/route", json={"tu_rp": "RP01", "den_rp": "RP39"}).json()
    assert d["tu"] == "RP01" and d["den"] == "RP39"
    assert d["quang_duong_m"] > 0
    assert d["so_chang"] == len(d["duong_di"]) - 1
    # Đường đi có tên điểm nhưng không kèm mô tả, cho response nhẹ.
    assert d["duong_di"][-1]["ten"] == "Phòng tạp chí"
    assert all("mo_ta" not in m for m in d["duong_di"])

    hop_le = {"bat_dau", "di_thang", "chech_trai", "chech_phai", "re_trai", "re_phai", "quay_dau"}
    assert 0 < len(d["chi_dan"]) <= d["so_chang"]
    assert all(b["huong"] in hop_le and b["khoang_cach_m"] > 0 for b in d["chi_dan"])
    assert d["chi_dan"][-1]["den_ten"] == "Phòng tạp chí"


def test_route_tu_toa_do_nguoi_dung(client):
    d = client.post("/route", json={"tu_x": 5.0, "tu_y": 30.0, "den_nhom": "WC"}).json()
    dau = d["duong_di"][0]
    assert dau["rp_id"] == ""
    assert math.hypot(dau["x"] - 5.0, dau["y"] - 30.0) < 0.2


@pytest.mark.parametrize("dich", [{"den_nhom": "Căn tin"}, {"den_x": -17.5, "den_y": 64}])
def test_route_a_sao_bang_dijkstra_nhung_mo_it_nut_hon(client, dich):
    than = {"tu_x": 22, "tu_y": 52, **dich}
    a = client.post("/route", json=than).json()
    d = client.post("/route", json={**than, "thuat_toan": "dijkstra"}).json()
    assert a["quang_duong_m"] == pytest.approx(d["quang_duong_m"])
    assert a["so_nut_mo"] < d["so_nut_mo"]


@pytest.mark.parametrize("tu,dich,tren,duoi", [
    # Phòng học nhóm sau quầy: đi qua lối ra (x ≈ -23, y ≈ 57) vào hành lang cửa sau.
    ((0, 45), (-17.5, 64), (-30, 52.75), (-17, 61.75)),
    # Từ khu tự học xuống sảnh cửa chính phải qua cầu thang dưới (|x| < 8), không trèo lan can.
    ((25, 25), (0, 5), (-8, 15), (8, 19)),
])
def test_route_toi_toa_do_qua_loi_di_that(client, tu, dich, tren, duoi):
    d = client.post("/route", json={"tu_x": tu[0], "tu_y": tu[1], "den_x": dich[0], "den_y": dich[1]}).json()
    assert d["so_chang"] > 0 and d["den"] == ""
    cuoi = d["duong_di"][-1]
    assert math.hypot(cuoi["x"] - dich[0], cuoi["y"] - dich[1]) < 1
    # Có ít nhất một đoạn của tuyến cắt qua cửa ngõ [tren, duoi].
    (x0, y0), (x1, y1) = tren, duoi
    def trong(p):
        return x0 - 0.5 <= p["x"] <= x1 + 0.5 and y0 - 0.5 <= p["y"] <= y1 + 0.5
    diem = d["duong_di"]
    assert any(trong({"x": a["x"] + (b["x"] - a["x"]) * t, "y": a["y"] + (b["y"] - a["y"]) * t})
               for a, b in zip(diem, diem[1:]) for t in np.linspace(0, 1, 50))


def test_route_toi_toa_do_da_toi(client):
    d = client.post("/route", json={"tu_x": 0, "tu_y": 30, "den_x": 0.5, "den_y": 31}).json()
    assert d["so_chang"] == 0 and d["chi_dan"] == []


@pytest.mark.parametrize("than,ma", [
    ({"tu_rp": "RP01", "den_rp": "RP99"}, 404),
    ({"tu_rp": "RP99", "den_rp": "RP01"}, 404),
    ({"tu_rp": "RP01", "den_nhom": "Không có"}, 404),
    ({"tu_rp": "RP01"}, 422),
    ({"den_rp": "RP20"}, 422),
    ({"den_rp": "RP20", "tu_x": -16.2}, 422),
    ({"tu_rp": "RP01", "den_rp": "RP09", "den_nhom": "Căn tin"}, 422),
    ({"tu_rp": "RP01", "den_x": 3.0}, 422),
    ({"tu_rp": "RP01", "den_nhom": "WC", "den_x": 3.0, "den_y": 3.0}, 422),
    ({"tu_rp": "RP01", "den_rp": "RP09", "thuat_toan": "bfs"}, 422),
])
def test_route_loi(client, than, ma):
    assert client.post("/route", json=than).status_code == ma
