"""Sơ đồ tầng 1 thư viện dạng SVG, đặt trong khung pixel của Map.png.

    python tools/ve_so_do_tang1.py data/reference/so_do_tang1.svg
    python tools/ve_so_do_tang1.py mobile/assets/map/so_do_tang1.svg --app
    python tools/ve_so_do_tang1.py mobile/assets/map/so_do_tang1_toi.svg --app --toi

Tường, phòng, cửa: đọc tay từ sơ đồ của trường (Downloads/01.png, toạ độ ảnh thu nhỏ
2000x1242), ghép vào Map.png theo phép khớp tay của người dùng (Documents/Untitled.svg).
Bậc thang giữa sảnh, lan can, cột: lấy từ Map.png và lớp Stair/Hallways của CTK45, theo
toạ độ lưới. Khu phía trên sảnh (phòng học nhóm, nghiệp vụ 2, quầy, hai khoang bên, cầu thang
góc trên phải) theo đúng sơ đồ trường (người dùng chọn 01/10, thay cho bố cục tả theo trí nhớ); vì vậy
RP37-39 rơi vào nghiệp vụ 2. Thang máy của sơ đồ trường thực ra là cầu thang lên tầng 2. Không có dải
bậc ở cửa chính, chỉ có cầu thang chính. Căn tin ở tầng 0 dưới hội trường.
"""
import math
import sys

APP = '--app' in sys.argv
TOI = '--toi' in sys.argv

# Ảnh trường gốc (4960 px) x 0,292858 - (199,789; 212,425) = px Map.png; ảnh ở đây thu nhỏ 2,48 lần.
K, OX, OY = 0.292858 * 2.48, 1761.447162 - 1961.235796, 2785.022538 - 2997.447941


def luoi(gx, gy):
    """Toạ độ lưới -> toạ độ ảnh trường thu nhỏ."""
    return (24.5 + (gx + 43) * 11.6279 - OX) / K, (625.5 - gy * 11.6346 - OY) / K


def o_luoi(x1, y1, x2, y2):
    (a, b), (c, d) = luoi(x1, y2), luoi(x2, y1)
    return a, b, c, d


if TOI:
    SAN, TUONG, CUNG, CHU_PHU = '#18202E', '#AEB8CB', '#5B6679', '#AAB4C6'
    MAU = {'nghiep_vu': ('#252E3D', '#C3CCDC'), 'hoc_tap': ('#1C3150', '#A5CCF5'),
           'dich_vu': ('#16362C', '#94DDC2'), 'su_kien': ('#2B2550', '#C9BCFB'),
           've_sinh': ('#262C36', '#CBD2DA')}
    BAC = ('#232B39', '#3E4859', '#6B778A')
    BAN = ('#24407A', '#8AAEFF', '#C9D8FF')
else:
    SAN, TUONG, CUNG, CHU_PHU = '#F7F8FA', '#1F2937', '#94A3B8', '#374151'
    MAU = {'nghiep_vu': ('#E7EBF2', '#475569'), 'hoc_tap': ('#DCEAFB', '#1E4E8C'),
           'dich_vu': ('#DDF3E8', '#146C43'), 'su_kien': ('#ECE6FB', '#4C3A96'),
           've_sinh': ('#E9ECEF', '#495057')}
    BAC = ('#EEF0F3', '#C9CED6', '#8A93A1')
    BAN = ('#DDE5F8', '#2C5BD8', '#1E3A8A')

def hcn(x1, y1, x2, y2):
    (a, b), (c, d) = luoi(x1, y2), luoi(x2, y1)
    return [(a, b), (c, b), (c, d), (a, d)]


PHONG = [
    ('nghiep-vu-1', [(285, 428), (285, 128), (340, 72), (503, 72), (557, 127), (557, 428)],
     'Phòng nghiệp vụ 1', 'Technical Dept. 1', 'nghiep_vu'),
    # Mức quầy = hàng RP y = 52 của CTK45 (người dùng, 01/10; sơ đồ trường vẽ quầy và nghiệp vụ 2 thấp hơn
    # ~4-5 m, chắn cả hàng này). Mặt trước (y 300) trái -> phải: lên tầng 2 (RP33) - lối ra cửa sau (RP34)
    # - quầy lùi vào ~2 m (RP36/37) - cửa phòng tạp chí (RP39) - lên tầng 2 (RP40). Từ cửa sau chỉ rẽ phải
    # được (trái là nghiệp vụ 2, sau quầy); hành lang có các phòng dẫn ra lối ra.
    # Hành lang cửa sau (y 235-300) chạy từ sảnh cửa sau sang trái tới lối ra; phòng học nhóm mở ra hành lang.
    ('hoc-nhom', [(557, 127), (922, 127), (922, 235), (557, 235)], 'Phòng học nhóm', 'Group Study', 'hoc_tap'),
    ('nghiep-vu-2', [(1062, 127), (1436, 127), (1436, 209), (1250, 209), (1250, 300), (1140, 300), (1140, 209),
                     (1062, 209)], 'Phòng nghiệp vụ 2', 'Technical Dept. 2', 'nghiep_vu'),
    ('tap-chi', [(1250, 209), (1436, 209), (1436, 300), (1250, 300)], 'Phòng tạp chí', None, 'hoc_tap'),
    ('bao-tap-chi', [(1436, 445), (1436, 127), (1488, 72), (1653, 72), (1708, 127), (1708, 445)],
     'Phòng báo & tạp chí', 'Periodicals', 'hoc_tap'),
    ('sau-dai-hoc', [(1436, 445), (1708, 445), (1708, 645), (1436, 645)], 'Phòng đọc sau đại học', 'Postgraduate Room', 'hoc_tap'),
    ('kho-1', [(287, 428), (340, 428), (340, 645), (287, 645)], None, None, 'nghiep_vu'),
    ('phong-hop', [(340, 468), (505, 468), (505, 645), (340, 645)], 'Phòng họp', 'Meeting', 'nghiep_vu'),
    ('kho-2', [(505, 468), (557, 468), (557, 645), (505, 645)], None, None, 'nghiep_vu'),
    # Sơ đồ trường vẽ CNTT, hội trường, WC lọt trong hai góc dưới khối chính; thật ra là toà riêng, WC ở tầng
    # lửng đi xuống từ sảnh dưới.
    # Ảnh vệ tinh (docs/tai_lieu_tham_khao/hinh_dang_thu_vien): tầng 1 là khối giữa; CNTT và hội trường là hai
    # khối vuông ~23 m xoay 45°, nối qua hai sân lát ở hai góc phía cửa chính. Đo tay trên ảnh xoay về khung này.
    # Đặt theo RP: cạnh trong đi qua góc dưới khối chính, sát hai đầu sảnh dưới (RP01 | RP03).
    ('cntt', [(15, 923), (765, 1673), (15, 2423), (-735, 1673)], 'Trung tâm CNTT', 'Phòng máy TV3, TV4', 'dich_vu'),
    ('hoi-truong', [(1979, 923), (2729, 1673), (1979, 2423), (1229, 1673)], 'Hội trường', 'Conference Hall', 'su_kien'),
]
NHAN = {'cntt': (-60, 1760), 'hoi-truong': (2054, 1760), 'nghiep-vu-2': (1250, 168), 'bao-tap-chi': (1572, 250), 'nghiep-vu-1': (421, 270), 'sau-dai-hoc': (1572, 545)}

# (x1, y1, x2, y2, phía mở: +1/-1 theo pháp tuyến trái của đoạn)
CUA = [
    (557, 380, 557, 450, 1), (1062, 140, 1062, 200, -1), (700, 235, 790, 235, 1), (1262, 300, 1338, 300, -1),
    (1436, 225, 1436, 290, -1), (1436, 482, 1436, 620, -1),
    (383, 468, 466, 468, -1), (300, 428, 338, 428, -1), (512, 468, 552, 468, -1),
    (277, 1102, 277, 1172, 1), (1718, 1102, 1718, 1172, -1),  # từ đầu sảnh dưới lên sảnh chờ hai toà
]
CUA_DOI = [(922, 115, 1062, 115, 1), (878, 1185, 1120, 1185, -1),
           (178, 1412, 238, 1472, 1), (1816, 1412, 1756, 1472, -1)]  # cửa gỗ từ sảnh chờ vào phòng

VO = [(277, 1185), (277, 122), (338, 60), (507, 60), (560, 115), (1433, 115), (1488, 60),
      (1658, 60), (1718, 122), (1718, 1185)]
# Mặt trước mức quầy, hở ở lối ra (640-740, RP34); hốc quầy 1000-1140 lùi tới y 209.
# Sảnh dưới = dải RP y -2..12 (ảnh trường y 961-1185, chỗ sơ đồ trường vẽ CNTT, hội trường, WC). Tường trên
# của sảnh hở ở cầu thang giữa và hai bậc bên (RP04/45, RP07/44).
TUONG_TRONG = ['M557,127 V645', 'M285,645 H557', 'M1436,645 H1708', 'M557,300 H640',
               'M740,300 H1000 V209 H1140', 'M281,961 H500 M600,961 H860 M1134,961 H1394 M1494,961 H1714']

# Sàn nhiều cao độ (người dùng, 01/10): mức quầy -> 2 bậc nhỏ hai bên trước quầy -> khu tự đọc -> cầu thang
# giữa -> sảnh dưới ở cửa chính. Hai bên sảnh dưới là cầu thang lên/xuống: phía TV3/4 lên TV3/4, xuống WC
# (tầng lửng, xuống nữa là TV1/2); phía hội trường lên hội trường, xuống căn tin (tầng 0). Mỗi bên là một
# cặp ở mép sảnh: làn lên thẳng hàng cửa phòng, làn xuống ngay trên dẫn sang dải tầng lửng (WC). Cặp cầu
# thang có mũi tên sát tường ngoài của sơ đồ trường chính là cặp này, vẽ lệch chỗ. Không có dải bậc ở cửa
# chính. Toạ độ ảnh trường.
# Lên tầng 2: chạy ngang ở hai đầu mặt trước, thẳng hàng quầy (RP33, RP40). Không có thang máy, không có
# cầu thang ở góc trên phải (từ cửa sau rẽ trái bị chặn).
BAC_ANH = [(560, 305, 636, 365), (1350, 305, 1431, 365)]
# Sảnh dưới = phần mái cam trên ảnh vệ tinh, ngoài khối chính phía cửa chính (người dùng, 01/10); hai đầu
# sảnh chạm hai toà, mỗi đầu một cặp bậc: làn lên vào toà, làn xuống (WC, TV1/2 | căn tin).
CAP_SANH = [(285, 1100, 420, 1178), (285, 1010, 420, 1092),        # trái: lên TV3/4 (RP01), xuống WC (RP43)
            (1574, 1100, 1709, 1178), (1574, 1010, 1709, 1092)]  # phải: lên hội trường (RP03), xuống căn tin, WC (RP09, RP42)
# Đi lên/xuống theo chiều dọc (vạch ngang): 2 bậc nhỏ xuống khu tự đọc (RP29, RP32), cầu thang giữa (lệch phải, người dùng
# không nhớ rõ kích thước).
# Cầu thang giữa đi thẳng từ sảnh dưới lên khu quầy (ảnh cua_ra_vao/3), trên cột RP x = 0: RP11 (y 18) ở
# chiếu nghỉ, RP19 (y 33) trên đợt hai, RP28 (y 41) ngay trên đỉnh. Rộng ~4,4 m.
BAC_DOC = [(600, 430, 690, 475), (1305, 430, 1395, 475),
           (860, 880, 1134, 1080), (860, 520, 1134, 780),   # cầu thang giữa: RP05/06 đợt dưới, RP19 đợt trên
           (500, 961, 600, 1150), (1394, 961, 1494, 1150)]  # bậc hai bên từ sảnh dưới lên khu tự đọc
CHIEU_NGHI = (860, 780, 1134, 880)  # RP11
# Lan can: mép sàn mức quầy giữa hai bậc nhỏ (Map.png có gờ quanh bệ quầy).
LAN_CAN = [[(690, 432), (1305, 432)]]
QUAY = (1012, 216, 1128, 258)  # toạ độ ảnh trường, sát lưng hốc
COT = [(x, 20.7) for x in (-32.4, -22.3, 22.8, 32.8)]  # hàng cột y 7,4 của Map.png rơi vào CNTT/hội trường: bỏ


def diem(ps):
    return ' '.join(f'{x:.1f},{y:.1f}' for x, y in ps)


def cua(x1, y1, x2, y2, phia, doi=False):
    dx, dy = x2 - x1, y2 - y1
    dai = math.hypot(dx, dy)
    nx, ny = -dy / dai * phia, dx / dai * phia
    ra = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{SAN}" stroke-width="9"/>']
    doi = doi or dai > 90
    canh = [((x1, y1), (x2, y2), dai)] if not doi else [
        ((x1, y1), ((x1 + x2) / 2, (y1 + y2) / 2), dai / 2),
        ((x2, y2), ((x1 + x2) / 2, (y1 + y2) / 2), dai / 2)]
    for (hx, hy), (ex, ey), r in canh:
        if r > 45:
            k = 45 / r
            ex, ey, r = hx + (ex - hx) * k, hy + (ey - hy) * k, 45
        tx, ty = hx + nx * r, hy + ny * r
        quet = 1 if (tx - hx) * (ey - hy) - (ty - hy) * (ex - hx) > 0 else 0
        ra.append(f'<path d="M{hx},{hy} L{tx:.1f},{ty:.1f} A{r:.1f},{r:.1f} 0 0 {quet} {ex:.1f},{ey:.1f}" '
                  f'fill="none" stroke="{CUNG}" stroke-width="2"/>')
    return ra


def nhan(cx, cy, vi, en, mau, co=19):
    ra = [f'<text x="{cx:.1f}" y="{cy if not en else cy - 6:.1f}" text-anchor="middle" font-size="{co}" '
          f'font-weight="600" fill="{mau}">{vi.replace("&", "&amp;")}</text>']
    if en:
        ra.append(f'<text x="{cx:.1f}" y="{cy + 16:.1f}" text-anchor="middle" font-size="12.5" fill="{mau}" '
                  f'fill-opacity="0.75">{en}</text>')
    return ra


def bac(x1, y1, x2, y2, doc=None):
    """Khối bậc: nền đặc + vạch bậc; `doc` = đi lên theo chiều dọc (vạch nằm ngang), mặc định theo
    cạnh dài. Không dùng <pattern> vì flutter_svg bỏ qua."""
    ra = [f'<rect x="{x1:.1f}" y="{y1:.1f}" width="{x2 - x1:.1f}" height="{y2 - y1:.1f}" rx="3" '
          f'fill="{BAC[0]}" stroke="{BAC[2]}" stroke-width="2"/>']
    doc = (y2 - y1) > (x2 - x1) if doc is None else doc
    a, b = (y1, y2) if doc else (x1, x2)
    for t in range(int(a) + 9, int(b) - 4, 9):
        ra.append(f'<line x1="{x1:.1f}" y1="{t}" x2="{x2:.1f}" y2="{t}"/>' if doc
                  else f'<line x1="{t}" y1="{y1:.1f}" x2="{t}" y2="{y2:.1f}"/>')
    return f'<g stroke="{BAC[1]}" stroke-width="2.5">' + ''.join(ra) + '</g>'


# Ngoài khối giữa: hai sân lát và sảnh vào dẫn ra quảng trường (bậc ở cuối).
# Sảnh chờ trong góc phía sảnh dưới của mỗi toà (ảnh tv3_4/2-3, hoi_truong_thu_vien/3-4): cầu thang lên tới
# một khoảng có bàn ghế, rồi cửa gỗ hai cánh vào phòng. Dải sâu ~5 m dọc cạnh trong của hình vuông.
SANH_CHO = [[(165, 1073), (577, 1485), (414, 1648), (2, 1236)],
            [(1829, 1073), (1417, 1485), (1580, 1648), (1992, 1236)]]
o = [bac(650, 1189, 1344, 1275, doc=True),
     f'<path d="M906,115 V80 A89,40 0 0 1 1085,80 V115 Z" fill="{SAN}" stroke="{TUONG}" stroke-width="4"/>',
     f'<polygon id="vo" points="{diem(VO)}" fill="{SAN}" stroke="{TUONG}" stroke-width="8" stroke-linejoin="round"/>',
     *nhan(760, 650, 'Khu tự đọc', 'Reading Space', MAU['hoc_tap'][1], 22),
     *nhan(1240, 650, 'Khu tự đọc', 'Reading Space', MAU['hoc_tap'][1], 22),
     '<g id="phong">']
for id_, ps, *_rest, loai in PHONG:
    o.append(f'<polygon id="{id_}" points="{diem(ps)}" fill="{MAU[loai][0]}" stroke="{TUONG}" '
             f'stroke-width="4" stroke-linejoin="round"/>')
o.append('</g>')
o += [f'<polygon points="{diem(ps)}" fill="{SAN}" stroke="{TUONG}" stroke-width="4" stroke-linejoin="round"/>'
      for ps in SANH_CHO]
o += [f'<path d="{d}" fill="none" stroke="{TUONG}" stroke-width="4"/>' for d in TUONG_TRONG]
o.append('<g id="cau-thang">')
o += [bac(*b) for b in BAC_ANH]
o += [bac(*b, doc=True) for b in BAC_DOC]
o.append(f'<rect x="{CHIEU_NGHI[0]}" y="{CHIEU_NGHI[1]}" width="{CHIEU_NGHI[2] - CHIEU_NGHI[0]}" height="{CHIEU_NGHI[3] - CHIEU_NGHI[1]}" '
         f'fill="{BAC[0]}" stroke="{BAC[2]}" stroke-width="2"/>')
o += [bac(*b, doc=False) for b in CAP_SANH]
o.append('</g>')
for ds in LAN_CAN:
    o.append(f'<polyline points="{diem(ds)}" fill="none" stroke="{TUONG}" '
             f'stroke-width="3" stroke-dasharray="10 5"/>')
for p in COT:
    x, y = luoi(*p)
    o.append(f'<rect x="{x - 7:.1f}" y="{y - 7:.1f}" width="14" height="14" rx="2" fill="{TUONG}"/>')
a, b, c, d = QUAY
o.append(f'<path d="M{a:.1f},{b:.1f} H{c:.1f} V{b + (d - b) * 0.45:.1f} Q{(a + c) / 2:.1f},{d + (d - b) * 0.35:.1f} '
         f'{a:.1f},{b + (d - b) * 0.45:.1f} Z" fill="{BAN[0]}" stroke="{BAN[1]}" stroke-width="3"/>')
o += nhan((a + c) / 2, (b + d) / 2 + 2, 'Quầy', None, BAN[2], 14)
o.append('<g id="cua">')
for c_ in CUA:
    o += cua(*c_)
for c_ in CUA_DOI:
    o += cua(*c_, doi=True)
o.append('</g><g id="nhan">')
for id_, ps, vi, en, loai in PHONG:
    if not vi:
        continue
    xs, ys = [p[0] for p in ps], [p[1] for p in ps]
    cx, cy = NHAN.get(id_, ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2 + 6))
    o += nhan(cx, cy, vi, en, MAU[loai][1], 15 if id_.startswith('wc') else 19)
o += nhan(690, 292, 'Lối ra', None, CHU_PHU, 12)[:1] + nhan(870, 272, 'Hành lang', None, CHU_PHU, 13)[:1] + nhan(997, 838, 'Cầu thang giữa', None, CHU_PHU, 13)[:1] + nhan(725, 1080, 'Sảnh dưới', None, CHU_PHU, 16)[:1]
o += nhan(598, 388, 'Lên tầng 2', None, CHU_PHU, 12)[:1] + nhan(1390, 388, 'Lên tầng 2', None, CHU_PHU, 12)[:1]
o += nhan(997, 1150, 'Cửa chính', None, CHU_PHU, 14)[:1] + nhan(290, 1365, 'Sảnh chờ', None, CHU_PHU, 13)[:1] + nhan(1704, 1365, 'Sảnh chờ', None, CHU_PHU, 13)[:1]
o += nhan(997, 1305, 'Xuống quảng trường', None, CHU_PHU, 13)[:1]
o += nhan(992, 150, 'Lối ra', None, CHU_PHU, 14)[:1]
o += nhan(352, 1203, 'Lên TV3, TV4', None, MAU['dich_vu'][1], 12)[:1] + nhan(352, 995, 'Xuống WC, TV1, TV2', None, CHU_PHU, 12)[:1]
o += nhan(1642, 1203, 'Lên hội trường', None, MAU['su_kien'][1], 12)[:1] + nhan(1642, 995, 'Xuống căn tin, WC', None, CHU_PHU, 12)[:1]
o.append('</g>')

x0, y0 = -735 * K + OX - 12, 40 * K + OY - 12
w, h = (2729 + 735) * K + 24, (2423 - 40) * K + 24
cg = []
if not APP:
    h += 102
    MUC = [(MAU['nghiep_vu'][0], None, 'Nghiệp vụ, họp'), (MAU['hoc_tap'][0], None, 'Học tập, đọc'),
           (MAU['dich_vu'][0], None, 'Trung tâm CNTT'), (MAU['su_kien'][0], None, 'Hội trường'),
           (MAU['ve_sinh'][0], None, 'Vệ sinh'), (BAC[1], BAC[2], 'Bậc, cầu thang'),
           (BAN[0], BAN[1], 'Quầy hướng dẫn')]
    # Chú giải đặt dưới mép dưới hai khối chéo (y 2423 ảnh trường), toạ độ bên trong giữ như cũ.
    cg = [f'<g id="chu-giai" transform="translate(0,{(2423 - 1190) * K:.1f})" font-size="11.5" fill="#374151">',
          '<text x="0" y="688" font-size="17" font-weight="700" fill="#111827">Tầng 1 · Thư viện Đại học Đà Lạt</text>']
    x = 0
    for nen, vien, chu in MUC:
        cg.append(f'<rect x="{x:.1f}" y="708" width="15" height="15" rx="3" fill="{nen}" stroke="{vien or TUONG}" stroke-width="1.5"/>')
        cg.append(f'<text x="{x + 21:.1f}" y="720">{chu}</text>')
        x += 21 + len(chu) * 6.4 + 16
    cg.append(f'<line x1="{x:.1f}" y1="716" x2="{x + 18:.1f}" y2="716" stroke="{TUONG}" stroke-width="2" stroke-dasharray="5 3"/>'
              f'<text x="{x + 24:.1f}" y="720">Lan can</text>')
    x += 24 + 7 * 6.4 + 16
    cg.append(f'<path d="M{x:.1f},723 V708 A15,15 0 0 1 {x + 15:.1f},723" fill="none" stroke="{CUNG}" stroke-width="1.8"/>'
              f'<line x1="{x - 2:.1f}" y1="723" x2="{x + 17:.1f}" y2="723" stroke="{TUONG}" stroke-width="2"/>'
              f'<text x="{x + 23:.1f}" y="720">Cửa</text>')
    dai = 10 / 0.3508 * 11.6279  # 10 m ra px Map.png
    t = 985 - dai
    cg.append(f'<g stroke="{TUONG}" stroke-width="2"><line x1="{t:.1f}" y1="684" x2="985" y2="684"/>'
              f'<line x1="{t:.1f}" y1="678" x2="{t:.1f}" y2="690"/>'
              f'<line x1="{t + dai / 2:.1f}" y1="680" x2="{t + dai / 2:.1f}" y2="688"/>'
              f'<line x1="985" y1="678" x2="985" y2="690"/></g>'
              f'<text x="{t:.1f}" y="672" text-anchor="middle">0</text>'
              f'<text x="{t + dai / 2:.1f}" y="672" text-anchor="middle">5</text>'
              f'<text x="985" y="672" text-anchor="middle">10 m</text>')
    # Trục +y sơ đồ có phương vị 248,5° (LaBan.gocBacSoDo) nên Bắc lệch 111,5° theo chiều kim đồng hồ.
    cg.append('<g transform="translate(1030,712) rotate(111.5)"><circle r="17" fill="#FFFFFF" stroke="#CBD5E1"/>'
              '<path d="M0,-14 L6,6 L0,2 L-6,6 Z" fill="#E03131"/></g>'
              '<text x="1030" y="748" text-anchor="middle" font-size="10.5" font-weight="700" fill="#E03131">B</text></g>')

ra = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" '
      'font-family="Inter, Segoe UI, Arial, sans-serif">',
      '<!-- Khung toạ độ = pixel của Map.png (lưới -> px: x = 24.5 + (gx + 43) * 11.6279, y = 625.5 - gy * 11.6346). -->']
if not APP:
    ra.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="#FFFFFF"/>')
ra += [f'<g transform="matrix({K:.6f},0,0,{K:.6f},{OX:.3f},{OY:.3f})">', *o, '</g>', *cg, '</svg>']
open(sys.argv[1], 'w', encoding='utf-8').write('\n'.join(ra))
