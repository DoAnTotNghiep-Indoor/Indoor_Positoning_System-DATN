"""Kiểm thử Dashboard web (nhóm 4, mục I).

JavaScript không có trình biên dịch bắt lỗi trước khi chạy: gõ sai một id thì
`document.querySelector` trả `null`, và trang chết lặng ở đúng chỗ đó mà không
báo gì. Ba loại lệch dưới đây đều thuộc kiểu ấy nên phải chốt bằng test:

1. Selector trong JS trỏ tới id không có trong HTML.
2. Import một tên mà mô-đun kia không export.
3. Hằng số biến đổi mét↔pixel trôi khỏi nhau giữa ba nơi cùng dùng nó —
   Python, Dart và JavaScript. Lệch ở đây thì cùng một toạ độ hiện ở hai chỗ
   khác nhau trên hai màn hình, mà triệu chứng nhìn y hệt "mô hình đoán sai".
"""

from __future__ import annotations

import json
import re

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


def test_hang_so_dart_khop_ban_do_json(luoi):
    ma = _doc(FLOOR_MAP_DART)
    assert _so(ma, "gocXPx", "=") == luoi["x_min_px"]
    assert _so(ma, "gocYPx", "=") == luoi["y_max_px"]
    assert _so(ma, "pxMoiMetX", "=") == luoi["px_moi_met_x"]
    assert _so(ma, "pxMoiMetY", "=") == luoi["px_moi_met_y"]


def test_ca_ba_noi_deu_lay_y_huong_len(luoi):
    """Lật trục y là 40 điểm sai phòng mà không có lỗi nào được ném ra."""
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
