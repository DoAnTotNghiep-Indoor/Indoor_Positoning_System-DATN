"""Đọc data/reference/mat_bang_tang1.yaml thành danh sách phần tử với hình học đã tính ra số.

Dùng chung cho `tools/ve_so_do_tang1.py` (vẽ SVG) và `tools/luoi_di_lai.py` (lưới tìm đường). Quy ước hình
học ghi ở đầu tệp YAML.
"""
import math
from pathlib import Path

import yaml

YAML = Path(__file__).parents[1] / 'data/reference/mat_bang_tang1.yaml'
DIEM_DON = ('tam', 'tai', 'loi_vao')
CAP = ('ten', 'nhom', 'mo_ta')


def doc_mat_bang() -> list[dict]:
    """Mỗi phần tử có `diem` (đa giác / đường gấp khúc theo lưới), kể cả bản đối xứng qua x = 0."""
    d = yaml.safe_load(YAML.read_text(encoding='utf-8'))
    moc = {k: float(v) for k, v in d['moc'].items()}

    def so(v):
        return float(eval(v, {'__builtins__': {}}, moc)) if isinstance(v, str) else float(v)

    ra = []
    for e in d['phan_tu']:
        e = dict(e)
        if 'hcn' in e:
            x1, y1, x2, y2 = map(so, e.pop('hcn'))
            e['diem'] = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        elif 'hcn_tam' in e:
            x, y, w, h = map(so, e.pop('hcn_tam'))
            t = math.radians(e.get('xoay', 0))
            e['diem'] = [(x + a * math.cos(t) - b * math.sin(t), y + a * math.sin(t) + b * math.cos(t))
                         for a, b in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        elif 'diem' in e:
            e['diem'] = [(so(x), so(y)) for x, y in e['diem']]
        for k in DIEM_DON:
            if k in e:
                e[k] = tuple(map(so, e[k]))
        # Cặp [trái, phải] cho bản đối xứng; phần tử thường dùng bản phải.
        trai = {k: e[k][0] if isinstance(e[k], list) else e[k] for k in CAP if k in e}
        ra.append(dict(e, **{k: e[k][1] if isinstance(e[k], list) else e[k] for k in CAP if k in e}))
        if e.get('doi_xung'):
            ra.append(dict(e, **trai, diem=[(-x, y) for x, y in e.get('diem', [])], mo=-e.get('mo', 1),
                           huong={'+x': '-x', '-x': '+x'}.get(e.get('huong'), e.get('huong')),
                           **{k: (-e[k][0], e[k][1]) for k in DIEM_DON if k in e}))
    return ra


def tam(ps):
    xs, ys = [p[0] for p in ps], [p[1] for p in ps]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
