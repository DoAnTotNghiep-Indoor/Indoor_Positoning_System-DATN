"""Kiểm thử API định vị — chạy thẳng qua ASGI, không cần bật server.

Fixture `client` và chốt chặn "chưa huấn luyện" nằm ở tests/conftest.py.
"""

from __future__ import annotations

import math

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


def test_quet_rong_khong_lam_sap_tang_tien_xu_ly(client):
    """Vector toàn giá trị điền thiếu vẫn phải chạy trơn qua scaler và model.

    Bài này từng khẳng định `/predict` trả 200 cho quét rỗng — đúng hành vi mà đồ
    án lấy làm điểm phê phán. Nay tầng tính toán vẫn chạy, endpoint thì từ chối.
    """
    from backend.dependencies import lay_predictor

    x, y, so_ap, do_tre = lay_predictor().du_doan([])
    assert so_ap == 0
    assert math.isfinite(x) and math.isfinite(y)
    assert do_tre >= 0


def test_gop_cua_so_truot_dap_tat_lan_quet_lac(client, ap_cols):
    """Đây là bài test cho tầng đưa sai số từ 1,90 m xuống 0,38 m. Gửi hai lần quét
    giống nhau rồi một lần quét lạc: toạ độ thô của lần thứ ba đi theo lần lạc,
    nhưng toạ độ đã gộp phải bị hai lần trước áp đảo.
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
    """Thiết bị đã rời đi phải được bỏ hẳn, không chỉ xoá lịch sử: device_id do
    client tự đặt nên số khoá không bị chặn bởi số máy thật.
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


# --- Chặn lần quét không đủ AP (đo được trên máy thật) ---

def _bssid_that(so: int) -> list[dict]:
    import json
    from ml import config
    cot = json.loads(
        (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8")
    )["ap_columns"]
    return [{"bssid": b, "rssi": -55.0} for b in cot[:so]]


def test_quet_rong_bi_tu_choi(client):
    """Chạy thật ngoài thư viện: điện thoại thấy 23 AP, khớp 0, mà mô hình vẫn
    khẳng định người dùng đứng ở RP01 trong thư viện Đại học Đà Lạt. Đúng họ lỗi
    mà cả đồ án lấy làm điểm cải tiến so với CTK45."""
    tra = client.post("/predict", json={"device_id": "trong", "scan": []})
    assert tra.status_code == 422
    assert tra.json()["detail"]["loi"] == "khong_du_ap"
    assert tra.json()["detail"]["so_ap"] == 0


def test_toan_ap_la_cung_bi_tu_choi(client):
    """Quét được nhiều AP nhưng không cái nào quen — tình huống thật ở ngoài
    thư viện, khác hẳn với quét rỗng."""
    la = [{"bssid": f"aa:bb:cc:dd:ee:{i:02x}", "rssi": -55.0} for i in range(20)]
    tra = client.post("/predict", json={"device_id": "la", "scan": la})
    assert tra.status_code == 422
    assert tra.json()["detail"]["so_ap"] == 0


def test_nguong_lay_tu_hop_dong_du_lieu(client):
    """Ngưỡng phải là `min_ap_per_scan` trong feature_list.json — chính quy tắc
    đã loại mẫu huấn luyện ở bước 6, chứ không phải một con số mới đặt ra."""
    import json
    from ml import config
    can = json.loads(
        (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8")
    )["min_ap_per_scan"]

    tra = client.post("/predict", json={"device_id": "duoi", "scan": _bssid_that(can - 1)})
    assert tra.status_code == 422
    assert tra.json()["detail"]["toi_thieu"] == can

    tra = client.post("/predict", json={"device_id": "vua", "scan": _bssid_that(can)})
    assert tra.status_code == 200, tra.text
    assert tra.json()["matched_ap"] == can


def test_lan_quet_bi_tu_choi_khong_duoc_ghi_vao_lich_su(client):
    """Toạ độ không dựa trên dữ liệu nào thì không đáng nằm trong lịch sử, và
    nó còn kéo lệch cửa sổ gộp của những lần quét đúng ngay sau đó."""
    truoc = len(client.get("/predictions?gioi_han=200").json())
    client.post("/predict", json={"device_id": "khong-ghi", "scan": []})
    assert len(client.get("/predictions?gioi_han=200").json()) == truoc


def test_ws_bao_loi_thay_vi_tra_toa_do_bia(client):
    with client.websocket_connect("/ws/location") as ws:
        ws.send_json({"device_id": "ws-trong", "scan": []})
        goi = ws.receive_json()
    assert goi["loi"] == "khong_du_ap"
    assert goi["toi_thieu"] > 0
    assert "x" not in goi



# --- Chặn đầu vào phi lý (lỗi tìm được khi rà backend) ---

def test_rssi_ngoai_khoang_vat_ly_khong_duoc_tinh_la_ap_khop(client, ap_cols):
    """RSSI luôn âm, nên số dương là dữ liệu bịa chứ không phải sóng yếu.

    Không chặn thì `KhongDuAp` bó tay vì nó chỉ ĐẾM số BSSID khớp: 36 BSSID đúng
    kèm rssi = +1000 vẫn trả toạ độ với matched_ap = 36, tức báo tin cậy tối đa
    cho đầu vào vô nghĩa.
    """
    for xau in (1000.0, 0.5, -1e9, -101.0):
        r = client.post("/predict", json={
            "device_id": "phi-ly",
            "scan": [{"bssid": b, "rssi": xau} for b in ap_cols],
        })
        assert r.status_code == 422, f"rssi = {xau} phải bị từ chối"

        # Phải là 422 CỦA CHÍNH HỆ, không phải 422 của pydantic: client bóc
        # thân theo hình dạng {"loi", "so_ap", "toi_thieu"}, còn thân pydantic
        # là một mảng lỗi trường — bóc nhầm thì giao diện mất số đếm.
        assert r.json()["detail"]["loi"] == "khong_du_ap"

    for tot in (0.0, -100.0, -55.0):
        r = client.post("/predict", json={
            "device_id": "hop-le",
            "scan": [{"bssid": b, "rssi": tot} for b in ap_cols],
        })
        assert r.status_code == 200, f"rssi = {tot} là giá trị hợp lệ"


def test_mot_so_doc_loi_khong_lam_hong_ca_lan_quet(client, ap_cols):
    """Trình điều khiển WiFi Android thỉnh thoảng trả 0 hoặc số dương cho AP ở
    rất gần. Vứt cả lần quét 36 AP chỉ vì một số đọc lỗi là đắt — số ấy bị bỏ
    qua như một BSSID lạ, phần còn lại vẫn định vị được.
    """
    tot = [{"bssid": b, "rssi": -55.0} for b in ap_cols[:-1]]
    r = client.post("/predict", json={
        "device_id": "mot-so-loi", "scan": tot + [{"bssid": ap_cols[-1], "rssi": 5.0}]})

    assert r.status_code == 200
    assert r.json()["matched_ap"] == len(tot), "số đọc lỗi không được tính là AP khớp"


def test_scan_qua_dai_bi_tu_choi(client, ap_cols):
    """Điện thoại thật thấy vài chục AP; gói 200.000 mục là gói phá."""
    that = [{"bssid": b, "rssi": -70.0} for b in ap_cols]
    rac = [{"bssid": f"aa:bb:cc:dd:ee:{i % 256:02x}", "rssi": -80.0} for i in range(600)]

    assert client.post("/predict", json={
        "device_id": "vua-du", "scan": (that + rac)[:512]}).status_code == 200
    assert client.post("/predict", json={
        "device_id": "qua-dai", "scan": (that + rac)[:513]}).status_code == 422


def test_gioi_han_lich_su_co_chan_tren_va_chan_duoi(client):
    """SQLite hiểu `LIMIT -1` là KHÔNG giới hạn, nên `?gioi_han=-1` từng trả nguyên
    bảng lịch sử vị trí cho một request không cần xác thực.
    """
    for xau in (-1, 0, 100_000_000):
        assert client.get(f"/predictions?gioi_han={xau}").status_code == 422

    assert client.get("/predictions?gioi_han=1000").status_code == 200


def test_bssid_trung_lap_khong_phu_thuoc_thu_tu_gui(client, ap_cols):
    """Cùng một lần quét gửi theo hai thứ tự phải cho cùng một toạ độ. Ghi đè theo
    thứ tự mảng thì client sắp khác là ra toạ độ khác; nay lấy trung bình, đúng
    `pivot_table(aggfunc="mean")` mà bước 3 pipeline dùng.
    """
    doi = [{"bssid": ap_cols[0], "rssi": -30.0}, {"bssid": ap_cols[0], "rssi": -90.0}]
    con_lai = [{"bssid": b, "rssi": -70.0} for b in ap_cols[1:]]

    xuoi = client.post("/predict", json={"device_id": "xuoi", "scan": doi + con_lai}).json()
    nguoc = client.post("/predict", json={
        "device_id": "nguoc", "scan": doi[::-1] + con_lai}).json()

    assert (xuoi["x"], xuoi["y"]) == (nguoc["x"], nguoc["y"])


def test_bssid_chu_hoa_van_khop_hop_dong(client, ap_cols):
    """`ScanResult.BSSID` của Android là chuỗi hoa hay thường tuỳ hãng.

    Trước khi sửa, chỉ ứng dụng Flutter hạ chữ thường còn máy chủ tra bảng phân
    biệt hoa thường: gửi đủ 36 BSSID ĐÚNG nhưng viết hoa thì `matched_ap = 0` và
    client nhận `khong_du_ap` — báo sai hẳn nguyên nhân, vì họ gửi thừa đủ AP.
    """
    thuong = [{"bssid": b, "rssi": -60.0} for b in ap_cols]
    hoa = [{"bssid": b.upper(), "rssi": -60.0} for b in ap_cols]

    a = client.post("/predict", json={"device_id": "thuong", "scan": thuong})
    b = client.post("/predict", json={"device_id": "hoa", "scan": hoa})

    assert b.status_code == 200, f"BSSID chữ hoa bị từ chối: {b.text[:120]}"
    assert b.json()["matched_ap"] == len(ap_cols)
    assert (a.json()["x"], a.json()["y"]) == (b.json()["x"], b.json()["y"])


def test_thieu_artifact_bao_ro_phai_chay_lenh_nao(tmp_path):
    """Kho vừa clone về không có `artifacts/*.pkl` — `.gitignore` chặn vì chúng
    nặng và sinh lại được. Lỗi trần chỉ trỏ vào một đường dẫn, người chạy không
    biết phải làm gì; đây là tình huống rất dễ gặp đúng hôm bảo vệ.
    """
    from backend.services.preprocessing_service import FeatureMapper, ThieuArtifact

    (tmp_path / "feature_list.json").write_text(
        json.dumps({"ap_columns": ["aa:bb:cc:dd:ee:ff"], "feature_count": 1,
                    "missing_rssi_value": -96.0, "min_ap_per_scan": 6}),
        encoding="utf-8")

    with pytest.raises(ThieuArtifact) as e:
        FeatureMapper(tmp_path)
    assert "scaler.pkl" in str(e.value)
    assert "ml.pipeline" in str(e.value) and "ml.train" in str(e.value)

    # Thiếu ngay hợp đồng dữ liệu cũng phải nói cùng một câu.
    (tmp_path / "feature_list.json").unlink()
    with pytest.raises(ThieuArtifact) as e:
        FeatureMapper(tmp_path)
    assert "feature_list.json" in str(e.value)
