"""Lưới đi lại cho chỉ đường, dựng từ data/reference/mat_bang_tang1.yaml (cùng nguồn với sơ đồ trên app).

    python -m tools.luoi_di_lai [--hinh]

Ghi data/reference/ban_do_tang1.json; backend chỉ đọc tệp này. `--hinh` lưu thêm ảnh mặt nạ kèm điểm tham chiếu
vào reports/figures/luoi_di_lai.png để soát bằng mắt.

Mặt nạ đi được vẽ ở 4 điểm ảnh mỗi đơn vị lưới (~9 cm). Cái gì đi được, cái gì chặn ghi ở đầu tệp YAML. Nét chặn
dày 1 đơn vị (~35 cm) nên khe hẹp hơn thế giữa hai vật cản coi như kín; cửa hẹp nhất rộng 3 đơn vị. Chỉ giữ mảng
sàn liền với sảnh cửa chính: phòng không có cửa (Trung tâm CNTT, hội trường, phòng sau quầy) bị bỏ, chỉ đường tới
chúng dừng ở lối vào khai trong YAML hoặc điểm đi được gần nhất.

Nút đồ thị là góc lồi của vật cản cộng điểm tham chiếu: đường ngắn nhất trong mặt bằng có vật cản chỉ bẻ hướng ở
góc lồi. Cạnh nối mọi cặp nút nhìn thấy nhau.
"""
from __future__ import annotations

import base64
import json
import sys
import zlib

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from scipy import ndimage

from backend.services.routing_service import nhin_thay
from ml import config
from tools.mat_bang import doc_mat_bang

RA = config.REFERENCE_DIR / "ban_do_tang1.json"

K = 4                  # điểm ảnh mỗi đơn vị lưới
X0, X1 = -50.0, 50.0   # khối giữa ±45,5 cộng WC nhô ra tới ±49,5
Y0, Y1 = -6.0, 76.0    # bậc ngoài cửa chính tới vòm cửa sau
NET = K                # độ dày nét chặn
NET_CUA = int(1.6 * K)

# Hình 7 báo cáo CTK45 (trang 44): toà nhà cao 19,6 m trên 55,87 đơn vị lưới. Khớp số đếm gạch tại chỗ:
# một viên ~35 cm là một đơn vị (đo 03/10/2026).
MET_MOI_DON_VI = 0.3508

DI_DUOC = {"vo", "phong", "cau_thang", "san_cao", "san_thap", "ban_cong"}
KHOI_CHAN = {"gieng", "quay", "ke"}
NET_CHAN = {"tuong", "lan_can", "mep"}
SANH = (0.0, 3.0)


def px(x: float, y: float) -> tuple[float, float]:
    return (x - X0) * K, (Y1 - y) * K


def ve_mat_na() -> np.ndarray:
    rong, cao = int((X1 - X0) * K), int((Y1 - Y0) * K)
    di, chan = Image.new("1", (rong, cao)), Image.new("1", (rong, cao))
    vd, vc = ImageDraw.Draw(di), ImageDraw.Draw(chan)
    mat_bang = doc_mat_bang()

    for e in mat_bang:
        if e["loai"] in DI_DUOC:
            vd.polygon([px(*p) for p in e["diem"]], fill=1)
    for e in mat_bang:
        if e["loai"] in KHOI_CHAN and e.get("chan_duong", True):
            vc.polygon([px(*p) for p in e["diem"]], fill=1)
        elif e["loai"] == "cot":
            (x, y), r = e["tam"], e["kich_thuoc"] / 2
            hop = [px(x - r, y + r), px(x + r, y - r)]
            (vc.ellipse if e.get("hinh") == "tron" else vc.rectangle)(hop, fill=1)
    # Cầu thang xuống trong giếng vẫn đi được.
    for e in mat_bang:
        if e["loai"] == "cau_thang":
            vc.polygon([px(*p) for p in e["diem"]], fill=0)
    for e in mat_bang:
        ps = [px(*p) for p in e.get("diem", [])]
        if e["loai"] in ("vo", "phong"):
            vc.line(ps + ps[:1], fill=1, width=NET, joint="curve")
        elif e["loai"] in NET_CHAN:
            vc.line(ps, fill=1, width=NET, joint="curve")
        elif e["loai"] == "cau_thang":
            # Chỉ lên xuống ở hai đầu; hai cạnh bên là mép sàn khác mức.
            (a, b, c, d) = ps
            doc = e["huong"] in ("+y", "-y")
            for canh in ((a, d), (b, c)) if doc else ((a, b), (d, c)):
                vc.line(canh, fill=1, width=NET)
    for e in mat_bang:
        if e["loai"] == "cua":
            ps = [px(*p) for p in e["diem"]]
            vd.line(ps, fill=1, width=NET_CUA)
            vc.line(ps, fill=0, width=NET_CUA)

    o = np.array(di) & ~np.array(chan)
    nhan, _ = ndimage.label(o)
    c, r = map(round, px(*SANH))
    return nhan == nhan[r, c]


def goc_loi(o: np.ndarray) -> list[list[int]]:
    """Ô trống kề chéo một ô vật cản mà hai ô kề cạnh đều trống."""
    cao, rong = o.shape
    p = np.pad(o, 1)
    goc = np.zeros_like(o)
    for dy in (-1, 1):
        for dx in (-1, 1):
            goc |= (o & p[1 + dy:cao + 1 + dy, 1:-1] & p[1:-1, 1 + dx:rong + 1 + dx]
                    & ~p[1 + dy:cao + 1 + dy, 1 + dx:rong + 1 + dx])
    return [[int(c), int(r)] for r, c in np.argwhere(goc)]


def _nen(a: np.ndarray) -> str:
    return base64.b64encode(zlib.compress(a.tobytes(), 9)).decode()


def main() -> None:
    o = ve_mat_na()
    rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig").dropna(subset=["x", "y"])
    toa_do = {h.rp_id: (float(h.x), float(h.y)) for h in rp.itertuples()}

    # Điểm rơi trên cầu thang lên, sát tường hay ngoài mảng chính thì kéo về ô đi được gần nhất.
    xa, (ih, ic) = ndimage.distance_transform_edt(~o, return_indices=True)
    rp_px, lech = {}, {}
    for k, (x, y) in toa_do.items():
        c, r = map(round, px(x, y))
        rp_px[k] = [int(ic[r, c]), int(ih[r, c])]
        if xa[r, c]:
            lech[k] = round(float(xa[r, c]) / K, 2)

    goc = goc_loi(o)
    nut = np.array(goc + list(rp_px.values()), float)
    canh = []
    for i in range(len(nut) - 1):
        j = np.arange(i + 1, len(nut))
        canh += [[i, int(k)] for k in j[nhin_thay(o, nut[i], nut[j])]]
    ten = list(rp_px)
    nhin = [[ten[i - len(goc)], ten[j - len(goc)]] for i, j in canh if i >= len(goc)]

    kq = {
        "nguon": "data/reference/mat_bang_tang1.yaml",
        "sinh_boi": "python -m tools.luoi_di_lai",
        "luoi_toa_do": {"x_min_px": 0.0, "y_max_px": Y1 * K, "px_moi_don_vi_x": K, "px_moi_don_vi_y": K,
                        "goc_x": X0},
        "ty_le_quy_doi": {"met_moi_don_vi": MET_MOI_DON_VI, "nguon": "Hình 7 báo cáo CTK45, khớp số đếm gạch"},
        "diem_lech_khoi_san": dict(sorted(lech.items())),
        "canh_nhin_thay": nhin,
        "luoi_di_lai": {"rong": o.shape[1], "cao": o.shape[0], "mat_na": _nen(np.packbits(o)), "rp_px": rp_px,
                        "goc_px": _nen(np.array(goc, np.uint16)), "canh": _nen(np.array(canh, np.uint16))},
    }
    RA.write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{RA.name}: mặt nạ {o.shape[1]}×{o.shape[0]}, {len(goc)} góc + {len(rp_px)} điểm, {len(canh)} cạnh, "
          f"{len(nhin)} cặp điểm nhìn thấy nhau; dịch điểm: {lech}")

    if "--hinh" in sys.argv:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 7))
        ax.imshow(o, cmap="Greys_r", extent=(X0, X1, Y0, Y1))
        for k, (x, y) in toa_do.items():
            ax.plot(x, y, "r.")
            ax.annotate(k[2:], (x, y), fontsize=6, color="r")
        hinh = config.REPORTS_DIR / "figures" / "luoi_di_lai.png"
        fig.savefig(hinh, dpi=150, bbox_inches="tight")
        print(hinh)


if __name__ == "__main__":
    main()
