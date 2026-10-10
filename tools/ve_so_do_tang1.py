"""Vẽ sơ đồ tầng 1 dạng SVG từ data/reference/mat_bang_tang1.yaml, trong khung pixel của Map.png.

    python -m tools.ve_so_do_tang1 data/reference/so_do_tang1.svg [--diem]
    python -m tools.ve_so_do_tang1 mobile/assets/map/so_do_tang1.svg --app
    python -m tools.ve_so_do_tang1 mobile/assets/map/so_do_tang1_toi.svg --app --toi
    python -m tools.ve_so_do_tang1 dashboard/so_do_tang1.svg --dashboard

Hình học, đơn vị và quy ước ghi ở đầu tệp YAML; ở đây chỉ có cách vẽ. `--diem` chấm thêm điểm tham chiếu để
đối chiếu; `--toi` bảng màu tối; `--app` bỏ nền trắng, chú giải và chữ, ghi tên ra `nhan_tang1.json` cạnh tệp
SVG để app vẽ thành nhãn nổi, luôn đứng thẳng khi xoay bản đồ; `--dashboard` cắt khung như app nhưng giữ chữ.
viewBox in ra cuối cùng phải chép vào `SoDoThat` (mobile/lib/data/floor_map.dart) và `SO_DO`
(dashboard/src/js/coordinate.js).
"""
import csv
import json
import math
import sys
from pathlib import Path

from tools.mat_bang import doc_mat_bang, tam

GOC = Path(__file__).parents[1]
APP = '--app' in sys.argv
KHUNG_APP = APP or '--dashboard' in sys.argv
TOI = '--toi' in sys.argv
DIEM = '--diem' in sys.argv

if TOI:
    SAN, TUONG, CUNG, CHU_PHU = '#18202E', '#AEB8CB', '#5B6679', '#AAB4C6'
    MAU = {'nghiep_vu': ('#252E3D', '#C3CCDC'), 'hoc_tap': ('#1C3150', '#A5CCF5'),
           'dich_vu': ('#16362C', '#94DDC2'), 'su_kien': ('#2B2550', '#C9BCFB'),
           've_sinh': ('#262C36', '#CBD2DA')}
    BAC = ('#232B39', '#3E4859', '#6B778A')
    BAN = ('#24407A', '#8AAEFF', '#C9D8FF')
    GIENG, THAP, KE = '#10151F', '#1D2533', '#6B5A45'
else:
    SAN, TUONG, CUNG, CHU_PHU = '#F7F8FA', '#1F2937', '#94A3B8', '#374151'
    MAU = {'nghiep_vu': ('#E7EBF2', '#475569'), 'hoc_tap': ('#DCEAFB', '#1E4E8C'),
           'dich_vu': ('#DDF3E8', '#146C43'), 'su_kien': ('#ECE6FB', '#4C3A96'),
           've_sinh': ('#E9ECEF', '#495057')}
    BAC = ('#EEF0F3', '#C9CED6', '#8A93A1')
    BAN = ('#DDE5F8', '#2C5BD8', '#1E3A8A')
    GIENG, THAP, KE = '#D5DAE1', '#E8EBEF', '#B89B74'
DUT = ' stroke-dasharray="12 7"'

# Thứ tự lớp: vùng lớn trước, chi tiết sau, chữ trên cùng.
LOP = ['phong_ngoai', 'cau_thang_ngoai', 'vo', 'vom', 'vung', 'phong', 'san_cao', 'san_thap', 'gieng', 'ban_cong',
       'cau_thang', 'tuong', 'lan_can', 'ke', 'cot', 'quay', 'cua', 'nhan']


def P(x, y):
    """Lưới -> pixel Map.png (cùng phép đổi với SoDoThat.sangPixel)."""
    return 24.5 + (x + 43) * 11.6279, 625.5 - y * 11.6346


def diem(ps):
    return ' '.join('%.1f,%.1f' % P(*p) for p in ps)


def da_giac(ps, nen, vien=None, net=4, dut=False):
    return (f'<polygon points="{diem(ps)}" fill="{nen}" stroke="{vien or TUONG}" stroke-width="{net}" '
            f'stroke-linejoin="round"{DUT if dut else ""}/>')


def duong(ps, net=4, mau=None, dut=False, gach=None):
    kieu = f' stroke-dasharray="{gach}"' if gach else (DUT if dut else '')
    return f'<polyline points="{diem(ps)}" fill="none" stroke="{mau or TUONG}" stroke-width="{net}"{kieu}/>'


def chu(x, y, vi, mau=CHU_PHU, co=13, en=None):
    px, py = P(x, y)
    ra = (f'<text x="{px:.1f}" y="{py - (6 if en else -4):.1f}" text-anchor="middle" font-size="{co}" '
          f'font-weight="600" fill="{mau}">{vi.replace("&", "&amp;")}</text>')
    if en:
        ra += (f'<text x="{px:.1f}" y="{py + 14:.1f}" text-anchor="middle" font-size="11.5" fill="{mau}" '
               f'fill-opacity="0.75">{en}</text>')
    return ra


def cua(a, b, phia, doi):
    """Khe cửa trên tường + cung mở; `phia` +1/-1 theo pháp tuyến trái của đoạn (trong pixel)."""
    (x1, y1), (x2, y2) = P(*a), P(*b)
    dx, dy = x2 - x1, y2 - y1
    dai = math.hypot(dx, dy)
    nx, ny = -dy / dai * phia, dx / dai * phia
    ra = [f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SAN}" stroke-width="9"/>']
    giua = ((x1 + x2) / 2, (y1 + y2) / 2)
    canh = [((x1, y1), giua, dai / 2), ((x2, y2), giua, dai / 2)] if doi else [((x1, y1), (x2, y2), dai)]
    for (hx, hy), (ex, ey), r in canh:
        if r > 45:
            k = 45 / r
            ex, ey, r = hx + (ex - hx) * k, hy + (ey - hy) * k, 45
        tx, ty = hx + nx * r, hy + ny * r
        quet = 1 if (tx - hx) * (ey - hy) - (ty - hy) * (ex - hx) > 0 else 0
        ra.append(f'<path d="M{hx:.1f},{hy:.1f} L{tx:.1f},{ty:.1f} A{r:.1f},{r:.1f} 0 0 {quet} {ex:.1f},{ey:.1f}" '
                  f'fill="none" stroke="{CUNG}" stroke-width="2"/>')
    return ''.join(ra)


ICON_MAU = {'hoc_tap': 'doc', 'nghiep_vu': 'van_phong', 'dich_vu': 'may_tinh', 'su_kien': 'hoi_truong',
            've_sinh': 'wc'}
ICON_LOAI = {'cau_thang': 'thang', 'gieng': 'thang', 'quay': 'quay', 'ban_cong': 'ghe', 'san_cao': 'ghe',
             'san_thap': 'wc'}


def nhan_cua(e):
    """Phần tử có tên -> nhãn {ten, en, x, y, mau, co, icon, cap, nhom, mo_ta, den, anh}; không tên thì None.
    `den` là điểm chỉ đường của địa điểm riêng (có `mo_ta`)."""
    if not e.get('ten'):
        return None
    loai = e['loai']
    x, y = e['tai'] if 'tai' in e else tam(e['diem'])
    to = loai in ('phong', 'nhan', 'quay')
    den = e.get('loi_vao', (x, y)) if e.get('mo_ta') else None
    return {'ten': e['ten'], 'en': e.get('en'), 'x': round(x, 2), 'y': round(y, 2), 'mau': e.get('mau'),
            'co': e.get('co', 13 if to else 11),
            'icon': e.get('icon') or ICON_MAU.get(e.get('mau')) or ICON_LOAI.get(loai, 'diem'),
            'cap': e.get('cap', 2 if to else 3), 'nhom': e.get('nhom'), 'mo_ta': e.get('mo_ta'),
            'den': [round(v, 2) for v in den] if den else None, 'anh': e.get('anh')}


def ve(e):
    """Một phần tử -> (lớp, svg hình)."""
    loai, ps = e['loai'], e.get('diem')
    dut = e.get('nguon', 'do_tai_cho') != 'do_tai_cho'
    if loai == 'phong':
        return ('phong_ngoai' if tam(ps)[1] < 0 else 'phong'), da_giac(ps, MAU[e['mau']][0], dut=dut)
    if loai == 'vung':
        return loai, f'<polygon points="{diem(ps)}" fill="{MAU[e["mau"]][0]}" fill-opacity="0.55"/>'
    if loai == 'cau_thang':
        hinh = da_giac(ps, BAC[0], BAC[2], 2, dut)
        x1, y1 = min(p[0] for p in ps), min(p[1] for p in ps)
        x2, y2 = max(p[0] for p in ps), max(p[1] for p in ps)
        doc = e['huong'] in ('+y', '-y')
        a, b = (y1, y2) if doc else (x1, x2)
        t = math.floor(a) + 1
        while t < b - 0.4:
            hinh += duong([(x1, t), (x2, t)] if doc else [(t, y1), (t, y2)], 2.5, BAC[1])
            t += 1
        return ('cau_thang_ngoai' if y2 <= 0 else 'cau_thang'), hinh
    if loai == 'vo':
        return loai, da_giac(ps, SAN, net=8)
    if loai == 'vom':
        (x1, y1), (x2, y2) = P(*ps[0]), P(*ps[2])
        r = (x2 - x1) / 2
        return loai, (f'<path d="M{x1:.1f},{y1:.1f} V{y2:.1f} A{r:.1f},{r * 0.45:.1f} 0 0 1 {x2:.1f},{y2:.1f} '
                      f'V{y1:.1f}" fill="{SAN}" stroke="{TUONG}" stroke-width="4"/>')
    if loai in ('san_cao', 'san_thap', 'gieng', 'ban_cong'):
        nen = {'san_cao': BAC[0], 'san_thap': THAP, 'gieng': GIENG, 'ban_cong': SAN}[loai]
        return loai, da_giac(ps, nen, BAC[2], 2, dut)
    if loai == 'tuong':
        return loai, duong(ps, e.get('net', 4), dut=dut)
    if loai == 'lan_can':
        return loai, duong(ps, 3, gach='10 5')
    if loai == 'ke':
        return loai, da_giac(ps, KE, KE, 1)
    if loai == 'cot':
        (x, y), k = e['tam'], e['kich_thuoc']
        if e.get('hinh') == 'tron':
            px, py = P(x, y)
            return loai, f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{k / 2 * 11.63:.1f}" fill="{TUONG}"/>'
        return loai, da_giac([(x - k / 2, y - k / 2), (x + k / 2, y - k / 2), (x + k / 2, y + k / 2),
                              (x - k / 2, y + k / 2)], TUONG, TUONG, 1, dut)
    if loai == 'quay':
        return loai, da_giac(ps, BAN[0], BAN[1], 3)
    if loai == 'cua':
        return loai, cua(ps[0], ps[1], e['mo'], e.get('doi', False))
    if loai in ('nhan', 'mep'):
        return 'nhan', ''
    raise ValueError(f'loại lạ: {loai}')


hinh = {k: [] for k in LOP}
nhan_ = []
for e in doc_mat_bang():
    lop, h = ve(e)
    hinh[lop].append(h)
    if n := nhan_cua(e):
        nhan_.append(n)
o = [h for k in LOP for h in hinh[k]]
if APP:
    (Path(sys.argv[1]).parent / 'nhan_tang1.json').write_text(json.dumps(
        [{k: v for k, v in n.items() if k not in ('mau', 'co') and v is not None} for n in nhan_],
        ensure_ascii=False, indent=1), encoding='utf-8')
else:
    for n in nhan_:
        mau = BAN[2] if n['icon'] == 'quay' else MAU[n['mau']][1] if n['mau'] else CHU_PHU
        o.append(chu(n['x'], n['y'], n['ten'], mau, n['co'], n['en'] if n['co'] >= 13 else None))

if DIEM:
    with open(GOC / 'data/reference/reference_points.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['x']:
                px, py = P(float(r['x']), float(r['y']))
                o.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="#E03131"/><text x="{px + 7:.1f}" '
                         f'y="{py - 4:.1f}" font-size="10" fill="#C92A2A">{r["rp_id"][2:]}</text>')

# App cắt quanh khối giữa (hai toà chéo nằm ngoài vùng định vị, vẽ hết thì khối giữa nhỏ đi một nửa);
# bản tham chiếu vẽ đủ.
(x0, y0), (x1, y1) = (P(-95, 84), P(95, -55)) if KHUNG_APP else (P(-136, 108), P(141, -102))
w, h = x1 - x0, y1 - y0
cg = []
if not KHUNG_APP:
    h += 90
    day = y0 + h - 70
    MUC = [(MAU['nghiep_vu'][0], 'Nghiệp vụ'), (MAU['hoc_tap'][0], 'Học tập, đọc'), (MAU['dich_vu'][0], 'CNTT'),
           (MAU['su_kien'][0], 'Hội trường'), (MAU['ve_sinh'][0], 'Vệ sinh'), (BAC[0], 'Bậc, cầu thang'),
           (GIENG, 'Giếng xuống tầng 0'), (THAP, 'Sàn thấp'), (BAN[0], 'Quầy'), (KE, 'Kệ sách')]
    cg = [f'<rect x="{x0:.1f}" y="{day - 34:.1f}" width="{w:.1f}" height="{y0 + h - day + 34:.1f}" fill="#FFFFFF"/>'
          f'<g font-size="12" fill="#374151"><text x="{x0 + 12:.1f}" y="{day:.1f}" font-size="18" font-weight="700" '
          f'fill="#111827">Tầng 1 · Thư viện Đại học Đà Lạt</text>']
    x = x0 + 12
    for nen, ten in MUC:
        cg.append(f'<rect x="{x:.1f}" y="{day + 16:.1f}" width="15" height="15" rx="3" fill="{nen}" stroke="{TUONG}" '
                  f'stroke-width="1.2"/><text x="{x + 21:.1f}" y="{day + 28:.1f}">{ten}</text>')
        x += 21 + len(ten) * 6.6 + 18
    for kieu, ten in (('stroke-dasharray="10 5"', 'Lan can'), (DUT.strip(), 'Chưa đo tại chỗ')):
        cg.append(f'<line x1="{x:.1f}" y1="{day + 24:.1f}" x2="{x + 22:.1f}" y2="{day + 24:.1f}" stroke="{TUONG}" '
                  f'stroke-width="3" {kieu}/><text x="{x + 28:.1f}" y="{day + 28:.1f}">{ten}</text>')
        x += 28 + len(ten) * 6.6 + 18
    dai = 10 / 0.3508 * 11.6279
    t = x0 + w - 40 - dai
    cg.append(f'<g stroke="{TUONG}" stroke-width="2"><line x1="{t:.1f}" y1="{day:.1f}" x2="{t + dai:.1f}" y2="{day:.1f}"/>'
              f'<line x1="{t:.1f}" y1="{day - 6:.1f}" x2="{t:.1f}" y2="{day + 6:.1f}"/>'
              f'<line x1="{t + dai:.1f}" y1="{day - 6:.1f}" x2="{t + dai:.1f}" y2="{day + 6:.1f}"/></g>'
              f'<text x="{t:.1f}" y="{day - 10:.1f}" text-anchor="middle">0</text>'
              f'<text x="{t + dai:.1f}" y="{day - 10:.1f}" text-anchor="middle">10 m</text></g>')

ra = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" '
      'font-family="Inter, Segoe UI, Arial, sans-serif">',
      '<!-- Sinh từ data/reference/mat_bang_tang1.yaml. Khung = pixel Map.png '
      '(lưới -> px: x = 24.5 + (gx + 43) * 11.6279, y = 625.5 - gy * 11.6346). -->']
if not APP:
    ra.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="#FFFFFF"/>')
ra += [*o, *cg, '</svg>']
Path(sys.argv[1]).write_text('\n'.join(ra), encoding='utf-8')
print(f'viewBox {x0:.1f} {y0:.1f} {w:.1f} {h:.1f}')
