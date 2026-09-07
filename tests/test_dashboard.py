"""Kiểm thử Dashboard web (nhóm 4, mục I).

JavaScript không có trình biên dịch bắt lỗi trước khi chạy: gõ sai một id thì
`querySelector` trả `null` và trang chết lặng. Ba loại lệch thuộc kiểu ấy nên
phải chốt bằng test:

1. Selector trong JS trỏ tới id không có trong HTML.
2. Import một tên mà mô-đun kia không export.
3. Hằng số mét↔pixel trôi khỏi nhau giữa Python, Dart và JavaScript — cùng một
   toạ độ hiện hai chỗ khác nhau, triệu chứng nhìn y hệt "mô hình đoán sai".
"""

from __future__ import annotations

import hashlib
import json
import re

import pandas as pd
import pytest

from ml import config

FRONTEND = config.ROOT_DIR / "frontend"
BAN_DO_JSON = config.REFERENCE_DIR / "ban_do_tang1.json"
FLOOR_MAP_DART = config.ROOT_DIR / "mobile" / "lib" / "data" / "floor_map.dart"


def _doc(duong_dan) -> str:
    return duong_dan.read_text(encoding="utf-8")


def _tep_js() -> list:
    return sorted(FRONTEND.glob("src/**/*.js"))


# --- 1. Selector ---

def test_moi_selector_deu_co_id_trong_html():
    html = _doc(FRONTEND / "index.html")
    co_san = set(re.findall(r'id="([^"]+)"', html))

    thieu = []
    for tep in _tep_js():
        for ma in re.findall(r"""\$\(['"]#([\w-]+)['"]\)""", _doc(tep)):
            if ma not in co_san:
                thieu.append(f"{tep.name}: #{ma}")
    assert not thieu, f"selector không có id tương ứng: {thieu}"


def test_khong_con_id_thua_trong_html():
    """Id có trong HTML mà không JS nào dùng là dấu hiệu đổi tên còn sót."""
    html = _doc(FRONTEND / "index.html")
    dung = set()
    for tep in _tep_js():
        dung |= set(re.findall(r"""\$\(['"]#([\w-]+)['"]\)""", _doc(tep)))
        dung |= set(re.findall(r"""getElementById\(['"]([\w-]+)['"]\)""", _doc(tep)))

    thua = set(re.findall(r'id="([^"]+)"', html)) - dung
    assert not thua, f"id khai trong HTML nhưng không dùng: {sorted(thua)}"


# --- 2. Import/export ---

def test_moi_import_deu_co_export_tuong_ung():
    loi = []
    for tep in _tep_js():
        ma = _doc(tep)
        for ten_import, duong_dan in re.findall(
            r"import\s*\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]", ma
        ):
            dich = (tep.parent / duong_dan).resolve()
            if not dich.exists():
                loi.append(f"{tep.name}: không có {duong_dan}")
                continue
            xuat = set(re.findall(r"export\s+(?:const|function|class)\s+(\w+)", _doc(dich)))
            for ten in (t.strip() for t in ten_import.split(",")):
                if ten and ten not in xuat:
                    loi.append(f"{tep.name}: {dich.name} không export '{ten}'")
    assert not loi, loi


def test_html_nap_dung_diem_vao():
    html = _doc(FRONTEND / "index.html")
    assert 'type="module"' in html, "thiếu type=module thì các lệnh import hỏng"
    assert "src/js/dashboard.js" in html
    assert "src/css/style.css" in html


# --- 3. Phép biến đổi mét ↔ pixel dùng chung ba nơi ---

@pytest.fixture(scope="module")
def luoi() -> dict:
    if not BAN_DO_JSON.exists():
        pytest.skip("chưa có ban_do_tang1.json — chạy `python -m tools.trich_ban_do`")
    return json.loads(_doc(BAN_DO_JSON))["luoi_toa_do"]


def _so(ma: str, khoa: str, dau_phan_cach: str) -> float:
    khop = re.search(rf"{khoa}\s*{dau_phan_cach}\s*(-?[\d.]+)", ma)
    assert khop, f"không tìm thấy {khoa}"
    return float(khop.group(1))


def test_hang_so_javascript_khop_ban_do_json(luoi):
    ma = _doc(FRONTEND / "src/js/coordinate.js")
    assert _so(ma, "gocXPx", ":") == luoi["x_min_px"]
    assert _so(ma, "gocYPx", ":") == luoi["y_max_px"]
    assert _so(ma, "pxMoiMetX", ":") == luoi["px_moi_met_x"]
    assert _so(ma, "pxMoiMetY", ":") == luoi["px_moi_met_y"]
    assert _so(ma, "gocMetX", ":") == luoi["goc_met_x"]


def test_hang_so_dart_khop_ban_do_json(luoi):
    ma = _doc(FLOOR_MAP_DART)
    assert _so(ma, "gocXPx", "=") == luoi["x_min_px"]
    assert _so(ma, "gocYPx", "=") == luoi["y_max_px"]
    assert _so(ma, "pxMoiMetX", "=") == luoi["px_moi_met_x"]
    assert _so(ma, "pxMoiMetY", "=") == luoi["px_moi_met_y"]
    assert _so(ma, "gocMetX", "=") == luoi["goc_met_x"]


def test_goc_met_x_dung_bang_toa_do_nho_nhat(luoi):
    """Số hạng này từng viết trần ở cả ba ngôn ngữ và không tệp nào khai nó, nên
    không bài test nào so được — sửa lệch một nơi thì lệch tới 86 m mà cả bộ
    kiểm thử vẫn xanh. Neo nó vào chính bảng toạ độ đã đo."""
    rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
    assert luoi["goc_met_x"] == rp["x"].dropna().min()


def test_ba_noi_deu_goi_ten_goc_thay_vi_viet_so():
    """Bài test trên chỉ so được khi hằng số có tên. Chốt luôn rằng công thức
    dùng cái tên đó chứ không dùng lại số trần bên cạnh một hằng số trang trí."""
    mau = {
        FLOOR_MAP_DART: "(x - gocMetX) * pxMoiMetX",
        FRONTEND / "src/js/coordinate.js": "(x - SO_DO.gocMetX) * SO_DO.pxMoiMetX",
        config.ROOT_DIR / "tools" / "trich_ban_do.py":
            "(x - self.goc_met_x) * self.px_moi_met_x",
    }
    for tep, cong_thuc in mau.items():
        assert cong_thuc in _doc(tep), f"{tep.name}: thiếu `{cong_thuc}`"


def test_hai_ban_so_do_giong_het_nhau():
    """Flutter chỉ đóng gói được asset nằm trong mobile/ nên Map.png phải có hai
    bản. Lệch nhau thì ứng dụng và Dashboard vẽ hai toà nhà khác nhau, trong khi
    mọi hằng số biến đổi vẫn khớp nên không gì báo lỗi."""
    goc = config.REFERENCE_DIR / "Map.png"
    chep = config.ROOT_DIR / "mobile" / "assets" / "map" / "Map.png"
    assert chep.exists(), "thiếu bản trong mobile/assets/map"
    assert hashlib.sha256(goc.read_bytes()).hexdigest() ==         hashlib.sha256(chep.read_bytes()).hexdigest(),         "hai bản Map.png đã lệch nhau — chép lại từ data/reference/"


def test_ca_ba_noi_deu_lay_y_huong_len(luoi):
    """Lật trục y là mọi điểm sai phòng mà không có lỗi nào được ném ra."""
    assert luoi["truc_y_huong_len"] is True
    assert "gocYPx - y" in _doc(FRONTEND / "src/js/coordinate.js")
    assert "gocYPx - y" in _doc(FLOOR_MAP_DART)


# --- 4. Máy chủ phục vụ được Dashboard mà không nuốt mất API ---

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

def test_moi_phuong_thuc_trong_api_js_deu_co_noi_goi():
    """Khai một lối gọi API rồi không dùng thì endpoint sống mà không ai thấy.

    `api.doThi` từng nằm im như vậy: `GET /graph` chạy tốt, có test, nhưng
    Dashboard không vẽ cạnh nào.
    """
    api_js = _doc(FRONTEND / "src" / "js" / "api.js")
    khai = set(re.findall(r"^\s{2}(\w+):", api_js, re.M))

    dung = "".join(_doc(t) for t in _tep_js() if t.name != "api.js")
    khong_goi = sorted(k for k in khai if f"api.{k}(" not in dung)
    assert not khong_goi, f"khai trong api.js mà không nơi nào gọi: {khong_goi}"


def test_dashboard_ve_canh_do_thi_len_so_do():
    dashboard = _doc(FRONTEND / "src" / "js" / "dashboard.js")
    renderer = _doc(FRONTEND / "src" / "js" / "map-renderer.js")

    assert "datCanh(" in renderer, "bộ vẽ chưa có lối nhận danh sách cạnh"
    assert "soDo.datCanh(" in dashboard, "Dashboard chưa truyền cạnh xuống bộ vẽ"

    # Cạnh phải vẽ TRƯỚC chấm, không thì nét cắt ngang qua đầu mút.
    assert renderer.index("this.canh") < renderer.index("for (const d of this.diem)")


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


def test_bo_ve_va_chu_giai_dung_cung_mot_bang_mau():
    """Chú giải nói về chính hình ngay trên nó nên màu phải khớp từng chữ. Hai tệp
    khác ngôn ngữ, không chia sẻ được hằng số, nên chốt bằng test.
    """
    renderer = _doc(FRONTEND / "src" / "js" / "map-renderer.js")
    css = _doc(FRONTEND / "src" / "css" / "style.css")
    html = _doc(FRONTEND / "index.html")

    for ten, lop in (("canh", "mau-canh"), ("cuaGiaDinh", "mau-cua")):
        mau = re.search(rf"{ten}:\s*'([^']+)'", renderer)
        assert mau, f"không thấy màu {ten} trong map-renderer.js"
        khoi = re.search(rf"\.{lop}\s*\{{[^}}]*\}}", css)
        assert khoi, f"không thấy .{lop} trong style.css"
        assert mau.group(1) in khoi.group(0), (
            f".{lop} không dùng đúng màu {ten} của bộ vẽ")
        assert lop in html, f"chú giải trong HTML thiếu .{lop}"

    # Cửa giả định phải là nét ĐỨT, cả ở hình lẫn ở chú giải.
    assert "setLineDash" in renderer
    assert "dashed" in re.search(r"\.mau-cua\s*\{[^}]*\}", css).group(0)


def test_phuong_vi_toa_nha_khop_giua_dart_va_python():
    """Phương vị toà nhà nằm ở hai nơi, hai ngôn ngữ, và phải lệch đúng 90°.

    `LaBan.gocBacSoDo` là phương vị trục +y sơ đồ, `ve_khoi_nha` khai trục dài
    tức +x. Lệch đi thì nón hướng trong app và hình khối trong báo cáo nói hai
    điều khác nhau về cùng một toà nhà, mà không có gì báo.
    """
    from tools import ve_khoi_nha

    dart = _doc(config.ROOT_DIR / "mobile" / "lib" / "services" / "la_ban.dart")
    m = re.search(r"gocBacSoDo\s*=\s*([\d.]+)", dart)
    assert m, "không thấy gocBacSoDo trong la_ban.dart"

    goc_y = float(m.group(1))
    goc_x = ve_khoi_nha.PHUONG_VI_TRUC_DAI
    assert (goc_x - goc_y) % 360 == pytest.approx(90.0, abs=0.01), (
        f"+x = {goc_x}°, +y = {goc_y}° — hai trục phải vuông góc")

    # Và góc nghiêng lưới nhà phải suy ra được từ chính phương vị đó, không
    # phải một con số viết cứng độc lập.
    assert ve_khoi_nha.NGHIENG == pytest.approx(360.0 - goc_x, abs=0.01)
