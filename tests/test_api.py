"""Kiểm thử các endpoint HTTP: /health, /predict, /predictions, /map, /graph,
/route và các tệp tĩnh của Dashboard."""

from __future__ import annotations

import json
import math
import subprocess

import pytest

from backend.services.routing_service import DoThiDiLai
from ml import config

from .conftest import bo_qua_neu_chua_huan_luyen


@pytest.fixture(scope="module")
def ap_cols() -> list[str]:
    duong_dan = config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON
    return json.loads(duong_dan.read_text(encoding="utf-8"))["ap_columns"]


def _bssid_that(so: int) -> list[dict]:
    import json
    from ml import config
    cot = json.loads(
        (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8")
    )["ap_columns"]
    return [{"bssid": b, "rssi": -55.0} for b in cot[:so]]


@pytest.fixture(scope="module")
def do_thi() -> DoThiDiLai:
    return DoThiDiLai()


API_JS = (config.ROOT_DIR / "frontend" / "src" / "js" / "api.js").as_posix()


def _mo_ta(detail, ma_http: int = 422) -> str:
    ma = (f"import {{ moTaLoi }} from 'file:///{API_JS}';"
          f"process.stdout.write(moTaLoi({json.dumps(detail)}, {ma_http}));")
    r = subprocess.run(["node", "--input-type=module", "-e", ma],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_health_bao_model_da_nap(client):
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["trang_thai"] == "ok"
    assert d["so_dac_trung"] == 36
    assert d["gia_tri_dien_thieu"] == -96.0
    assert d["websocket"] is False


def test_websocket_tam_tat_thi_khong_noi_duoc(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/location") as ws:
            ws.send_text("khong-phai-json")
            ws.receive_json()


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
    """Hai lần quét giống nhau rồi một lần lạc: toạ độ thô đi theo lần lạc, toạ
    độ đã gộp phải bị hai lần trước áp đảo."""
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
    # Dashboard hỏi định kỳ endpoint này thay cho WebSocket nên cần biết của máy nào.
    assert {m["device_id"] for m in ds} == {"gop"}
    assert all(m["do_tre_ms"] >= 0 for m in ds)


def test_thieu_device_id_thi_bao_loi(client):
    r = client.post("/predict", json={"scan": []})
    assert r.status_code == 422


def test_scan_khong_kem_bssid_thi_bao_loi(client):
    """Chặn đúng lỗi CTK45: mảng số trần không kèm BSSID phải bị từ chối."""
    r = client.post("/predict", json={"device_id": "x", "scan": [-55, -60]})
    assert r.status_code == 422


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


def test_rssi_ngoai_khoang_vat_ly_khong_duoc_tinh_la_ap_khop(client, ap_cols):
    """RSSI luôn âm, nên số dương là dữ liệu bịa chứ không phải sóng yếu.

    Không chặn thì `KhongDuAp` bó tay vì nó chỉ ĐẾM số BSSID khớp: 36 BSSID đúng
    kèm rssi = +1000 vẫn trả toạ độ với matched_ap = 36, tức báo tin cậy tối đa
    cho đầu vào vô nghĩa.
    """
    for xau in (1000.0, 0.5, 0.0, -1e9, -101.0):
        r = client.post("/predict", json={
            "device_id": "phi-ly",
            "scan": [{"bssid": b, "rssi": xau} for b in ap_cols],
        })
        assert r.status_code == 422, f"rssi = {xau} phải bị từ chối"

        # Phải là 422 CỦA CHÍNH HỆ, không phải 422 của pydantic: client bóc
        # thân theo hình dạng {"loi", "so_ap", "toi_thieu"}, còn thân pydantic
        # là một mảng lỗi trường — bóc nhầm thì giao diện mất số đếm.
        assert r.json()["detail"]["loi"] == "khong_du_ap"

    for tot in (-100.0, -55.0):
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


def test_route_theo_khu_vuc(client, do_thi):
    d = client.post("/route", json={"tu_rp": "RP16", "den_nhom": "Cầu thang"}).json()
    assert d["den"] in do_thi.diem_cua_nhom("Cầu thang")
    kq = do_thi.chi_duong(*do_thi.toa_do["RP16"], do_thi.diem_cua_nhom("Cầu thang"))
    assert d["quang_duong_m"] == pytest.approx(kq["quang_duong_m"], abs=0.01)


@pytest.mark.parametrize("than", [
    {"tu_rp": "RP01"},
    {"tu_rp": "RP01", "den_rp": "RP09", "den_nhom": "Căn tin"},
    {"tu_rp": "RP01", "den_nhom": ""},
])
def test_route_can_dung_mot_diem_den(client, than):
    assert client.post("/route", json=than).status_code == 422


def test_route_khu_vuc_la_tra_404(client):
    assert client.post("/route", json={"tu_rp": "RP01",
                                       "den_nhom": "Không có"}).status_code == 404


def test_may_chu_tra_ve_trang_dashboard(client):
    tra = client.get("/")
    assert tra.status_code == 200
    assert "text/html" in tra.headers["content-type"]
    assert "Sơ đồ tầng 1" in tra.text


def test_mount_tinh_khong_che_mat_cac_endpoint(client):
    """StaticFiles mount ở "/" nhận mọi đường dẫn còn lại. Đăng ký nhầm thứ tự
    là toàn bộ API trả về 404 dù mã của chúng không đổi một dòng."""
    for duong_dan in ("/health", "/map", "/graph", "/predictions"):
        assert client.get(duong_dan).status_code == 200, duong_dan


def test_may_chu_tra_ve_so_do_png(client):
    tra = client.get("/map/so-do.png")
    assert tra.status_code == 200
    assert tra.headers["content-type"] == "image/png"
    assert tra.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_tep_tinh_cua_dashboard_tai_duoc(client):
    for duong_dan in ("/src/css/style.css", "/src/js/dashboard.js",
                      "/src/js/coordinate.js", "/src/components/data-table.js"):
        assert client.get(duong_dan).status_code == 200, duong_dan


def test_moi_canh_do_thi_deu_noi_hai_diem_co_that(client):
    """Cạnh chỉ mang mã điểm; Dashboard tra toạ độ từ GET /map. Một mã lệch giữa
    hai endpoint là cạnh biến mất khỏi sơ đồ mà không báo gì.
    """
    canh = client.get("/graph").json()["canh"]
    co = {d["rp_id"] for d in client.get("/map").json()["diem_tham_chieu"]}

    # Số cạnh suy ra từ chính đồ thị chứ không viết cứng: thêm một điểm tham
    # chiếu là con số ấy đổi, mà bài này không kiểm số cạnh — nó kiểm mã điểm.
    assert len(canh) == client.get("/graph").json()["so_canh"]
    thieu = {c[k] for c in canh for k in ("tu", "den")} - co
    assert not thieu, f"cạnh trỏ tới điểm không có trong /map: {sorted(thieu)}"


def test_cua_gia_dinh_duoc_danh_dau_rieng(client):
    """Cạnh nhóm tự nối tay phải phân biệt được với cạnh đo từ Map.png.

    Chúng vào kết quả `/route` như mọi cạnh khác mà chưa ai đối chiếu thực địa,
    nên client phải vẽ khác — trộn chung là trình bày giả định như thể đo được.
    """
    import json

    from ml import config

    canh = client.get("/graph").json()["canh"]
    assert all("cua_gia_dinh" in c for c in canh), "thiếu cờ trên một số cạnh"

    # Đối chiếu với chính nguồn sự thật thay vì một con số viết cứng.
    that = {tuple(sorted(c)) for c in json.loads(
        (config.REFERENCE_DIR / "ban_do_tang1.json").read_text(encoding="utf-8")
    )["cua_gia_dinh"]}
    danh_dau = {tuple(sorted((c["tu"], c["den"]))) for c in canh if c["cua_gia_dinh"]}
    assert danh_dau == that
    assert 0 < len(danh_dau) < len(canh), "cửa giả định phải là thiểu số"


def test_may_chu_that_van_tra_dung_hinh_dang_ay(client):
    """Chốt hai đầu: thân máy chủ trả về phải đúng dạng mà hàm trên xử lý."""
    tra = client.post("/route", json={"den_rp": "RP09", "tu_x": 999.0, "tu_y": 5.0})
    assert tra.status_code == 422
    detail = tra.json()["detail"]
    assert isinstance(detail, dict) and detail["loi"] == "ngoai_pham_vi"
    assert "[object Object]" not in _mo_ta(detail)


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


def test_route_chon_thuat_toan(client):
    than = {"tu_x": 22, "tu_y": 52, "den_nhom": "Căn tin"}
    a = client.post("/route", json=than).json()
    d = client.post("/route", json={**than, "thuat_toan": "dijkstra"}).json()
    assert a["thuat_toan"] == "a_sao" and d["thuat_toan"] == "dijkstra"
    assert a["quang_duong_m"] == d["quang_duong_m"]
    assert a["so_nut_mo"] < d["so_nut_mo"]
    assert client.post("/route", json={**than, "thuat_toan": "bfs"}).status_code == 422


def test_route_di_tu_dung_vi_tri_nguoi_dung(client):
    d = client.post("/route", json={"tu_x": 5.0, "tu_y": 30.0, "den_nhom": "WC"}).json()
    dau = d["duong_di"][0]
    assert dau["rp_id"] == ""
    assert math.hypot(dau["x"] - 5.0, dau["y"] - 30.0) < 0.2
    assert d["so_chang"] == len(d["duong_di"]) - 1


def test_api_lich_su_tra_ve_mui_gio(client):
    """Chốt lại ở mức HTTP, vì đó là thứ Dashboard thật sự đọc."""
    bo_qua_neu_chua_huan_luyen()

    # Phải gửi đủ số AP tối thiểu, không thì /predict từ chối bằng 422 và
    # không có bản ghi nào để kiểm múi giờ.
    import json

    from ml import config

    hop_dong = json.loads(
        (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8")
    )
    scan = [
        {"bssid": b, "rssi": -55.0}
        for b in hop_dong["ap_columns"][: hop_dong["min_ap_per_scan"]]
    ]
    client.post("/predict", json={"device_id": "kiem-thu-mui-gio", "scan": scan})
    ds = client.get("/predictions?device_id=kiem-thu-mui-gio&gioi_han=1").json()
    assert ds, "không ghi được bản ghi nào"
    assert ds[0]["luc"].endswith("Z") or "+" in ds[0]["luc"][10:], ds[0]["luc"]


def test_map_tra_ve_don_vi_luoi_kem_ty_le_met(client):
    """Toạ độ Bảng 4 là đơn vị lưới, không phải mét: Hình 7 CTK45 cho 0,3508 m."""
    d = client.get("/map").json()
    assert d["don_vi"] == "don_vi_luoi"
    assert d["met_moi_don_vi"] == pytest.approx(0.3508)
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
    """Đưa toạ độ mét bất kỳ thì hệ tự neo vào điểm gần nhất. Mốc dò lấy lệch khỏi
    chính toạ độ RP01 chứ không viết cứng: dời điểm tham chiếu là bài này mất ý
    nghĩa mà vẫn xanh.
    """
    ds = client.get("/map").json()["diem_tham_chieu"]
    goc = next(m for m in ds if m["rp_id"] == "RP01")

    d = client.post("/route", json={
        "tu_x": goc["x"] + 0.2, "tu_y": goc["y"] + 0.3, "den_rp": "RP20"}).json()
    assert d["tu"] == "RP01"


def test_route_toi_diem_khong_ton_tai(client):
    assert client.post("/route", json={"tu_rp": "RP01", "den_rp": "RP99"}).status_code == 404


def test_route_thieu_diem_dau_thi_bao_loi(client):
    """Quên gửi điểm đầu phải bị từ chối, không được âm thầm lấy RP02: RP02 nằm
    đúng tại (0,0) nên mặc định 0.0 của bản trước vẫn trả về tuyến trông hợp lý.
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

    assert len(ds) == client.get("/map").json()["do_thi"]["so_diem"]
    assert all(m["ten"] and m["nhom"] and m["mo_ta"] for m in ds)
    assert next(m for m in ds if m["rp_id"] == "RP39")["ten"] == "Phòng tạp chí"


def test_duong_di_co_ten_nhung_khong_kem_mo_ta(client):
    """Chỉ đường cần tên để nói "đi tới Phòng tạp chí" thay vì "đi tới RP39".

    Mô tả thì không: nhân với số chặng chỉ làm nặng response mà không ai đọc.
    """
    d = client.post("/route", json={"tu_rp": "RP01", "den_rp": "RP39"}).json()

    assert all(m["ten"] for m in d["duong_di"] if m["rp_id"])
    assert d["duong_di"][-1]["ten"] == "Phòng tạp chí"
    assert "mo_ta" not in d["duong_di"][0]


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


def test_tu_rp_rong_bao_422_chu_khong_sap(client):
    """Chuỗi rỗng phải bị bắt như "thiếu điểm đầu", không được rơi xuống dưới.

    Trước khi sửa: validator so `tu_rp is None` nên `""` lọt qua, rồi router
    dùng `tu_rp or gan_nhat(...)` — chuỗi rỗng là falsy nên vỡ bằng TypeError
    và client nhận HTTP 500 cho một yêu cầu chỉ thiếu điểm đầu.
    """
    for rong in ("", "   "):
        assert client.post("/route", json={"den_rp": "RP03", "tu_rp": rong}).status_code == 422
    assert client.post("/route", json={"den_rp": "", "tu_rp": "RP01"}).status_code == 422


def test_toa_do_ngoai_toa_nha_bi_tu_choi(client):
    """(9999, 9999) từng được neo im lặng vào góc gần nhất rồi trả về tuyến."""
    r = client.post("/route", json={"den_rp": "RP03", "tu_x": 9999.0, "tu_y": 9999.0})
    assert r.status_code == 422
    assert r.json()["detail"]["loi"] == "ngoai_pham_vi"

    # Trong nhà và sát mép vẫn phải đi được, nếu không là chặn nhầm người thật.
    assert client.post("/route", json={
        "den_rp": "RP03", "tu_x": -41.2, "tu_y": 0.3}).status_code == 200


@pytest.mark.parametrize("duong,than", [
    ("/route", '{"tu_x":1e999,"tu_y":5,"den_rp":"RP09"}'),
    ("/route", '{"tu_x":NaN,"tu_y":5,"den_nhom":"WC"}'),
    ("/predict", '{"device_id":1e999,"scan":[]}'),
    ("/predict", '{"device_id":"a","scan":[{"bssid":-1e999,"rssi":-50}]}'),
])
def test_so_vo_han_tra_422_chu_khong_500(client, duong, than):
    """`1e999` là JSON hợp lệ và đọc ra inf."""
    r = client.post(duong, content=than, headers={"Content-Type": "application/json"})
    assert r.status_code == 422, r.text
    assert isinstance(r.json()["detail"], list)


@pytest.mark.parametrize("than", [
    {"tu_rp": "R" * 100_000, "den_rp": "RP09"},
    {"tu_rp": "RP01", "den_nhom": "N" * 100_000},
])
def test_ma_qua_dai_bi_chan_chu_khong_doi_lai_nguyen_van(client, than):
    r = client.post("/route", json=than)
    assert r.status_code == 422 and len(r.content) < 2000


def test_bssid_qua_dai_bi_chan(client):
    r = client.post("/predict", json={"device_id": "a",
                                      "scan": [{"bssid": "a" * 65, "rssi": -50}]})
    assert r.status_code == 422 and isinstance(r.json()["detail"], list)


def test_diem_den_cat_khoang_trang_nhu_diem_dau(client):
    r = client.post("/route", json={"tu_rp": " RP01 ", "den_rp": " RP09 "})
    assert r.status_code == 200 and r.json()["den"] == "RP09"


def test_swagger_khai_du_ma_loi_cua_route(client):
    ma = client.get("/openapi.json").json()["paths"]["/route"]["post"]["responses"]
    assert {"404", "409", "422"} <= set(ma)
