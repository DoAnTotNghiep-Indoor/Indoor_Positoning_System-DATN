"""Đồ thị đi lại và tìm đường.

Mặt nạ đi được và đồ thị dựng sẵn từ sơ đồ `mat_bang_tang1.yaml` bằng
`tools/luoi_di_lai.py`. Chỉ đường chạy trên `LuoiDiLai`: nút là góc lồi của vật
cản cộng điểm tham chiếu, vì đường ngắn nhất trong mặt bằng có vật cản chỉ bẻ
hướng ở góc lồi — nên tuyến đi từ đúng vị trí người dùng, không phải từ điểm
tham chiếu gần nhất. `DoThiDiLai.canh` (cặp điểm tham chiếu nhìn thấy nhau) chỉ
để Dashboard vẽ.

Toạ độ giữ đơn vị lưới của Bảng 4; mọi khoảng cách trả ra là MÉT.
"""

from __future__ import annotations

import base64
import heapq
import json
import math
import zlib

import numpy as np
import pandas as pd

from ml import config

BAN_DO_JSON = config.REFERENCE_DIR / "ban_do_tang1.json"
COT_NHAN = ("ten", "nhom", "mo_ta", "mo_ta_chi_tiet", "thu_muc_anh")


def _khoa(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


# Ngưỡng góc quay (độ): dưới 20° người đi bộ không coi là rẽ, trên 135° là quay đầu.
GOC_DI_THANG = 20.0
GOC_CHECH = 60.0
GOC_QUAY_DAU = 135.0

# Chặng ngắn hơn chừng một sải chân thì không đáng thành một bước chỉ dẫn.
CHANG_TOI_THIEU_M = 0.5

# Cách đích toạ độ dưới ngần này là đã tới: sai số định vị cỡ vài mét.
DA_TOI_M = 2.0


def _goc_quay(truoc: float, sau: float) -> float:
    """Góc quay từ hướng [truoc] sang [sau], trong [-180, 180); dương là rẽ trái
    (y hướng lên nên góc tăng là ngược kim đồng hồ)."""
    return (sau - truoc + 180.0) % 360.0 - 180.0


def _phan_loai(goc: float) -> str:
    do_lon = abs(goc)
    if do_lon <= GOC_DI_THANG:
        return "di_thang"
    if do_lon > GOC_QUAY_DAU:
        return "quay_dau"
    ben = "trai" if goc > 0 else "phai"
    return f"chech_{ben}" if do_lon <= GOC_CHECH else f"re_{ben}"


def nhin_thay(o: np.ndarray, p, Q) -> np.ndarray:
    """Đoạn từ pixel [p] tới từng pixel trong [Q] có nằm trọn trong mặt nạ [o].

    Lấy mẫu mỗi nửa pixel dọc đoạn. Lượt thưa trước loại phần lớn đoạn bị chắn;
    mẫu thưa là tập con mẫu dày nên kết quả y như chỉ chạy lượt dày."""
    # Làm tròn đầu mút: mẫu trúng đúng ,5 thì nhiễu dấu phẩy động đổi hẳn pixel.
    p = np.rint(np.asarray(p, float))
    Q = np.rint(np.atleast_2d(np.asarray(Q, float)))
    d = Q - p
    dai = np.maximum(np.abs(d).max(axis=1), 1e-9)
    ra = np.ones(len(Q), bool)
    phang, rong = o.ravel(), o.shape[1]
    for buoc in (8.0, 0.5):
        i = np.nonzero(ra)[0]
        if not len(i):
            break
        k = np.arange(int(np.ceil(dai[i].max() / buoc)) + 1) * buoc
        t = np.minimum(k[None, :] / dai[i, None], 1.0)[..., None]
        s = np.rint(p + d[i, None, :] * t).astype(np.int64)
        ra[i] = phang[s[..., 1] * rong + s[..., 0]].all(axis=1)
    return ra


def _giai_nen(chuoi: str, kieu) -> np.ndarray:
    return np.frombuffer(zlib.decompress(base64.b64decode(chuoi)), kieu)


class LuoiDiLai:
    def __init__(self, d: dict):
        l = d["luoi_di_lai"]
        bit = np.unpackbits(_giai_nen(l["mat_na"], np.uint8))
        self.o = bit[: l["rong"] * l["cao"]].reshape(l["cao"], l["rong"]).astype(bool)

        g = d["luoi_toa_do"]
        self._x0, self._y0 = g["x_min_px"], g["y_max_px"]
        self._kx, self._ky = g["px_moi_don_vi_x"], g["px_moi_don_vi_y"]
        self._gx = g["goc_x"]
        self.met_moi_don_vi = d["ty_le_quy_doi"]["met_moi_don_vi"]

        self.rp = list(l["rp_px"])
        goc = _giai_nen(l["goc_px"], np.uint16).reshape(-1, 2)
        self.so_goc = len(goc)
        self.px = np.vstack([goc, [l["rp_px"][k] for k in self.rp]]).astype(float)
        self.xy = self.sang_don_vi(self.px)
        self.chi_so = {k: self.so_goc + i for i, k in enumerate(self.rp)}

        self.ke: list[list[tuple[int, float]]] = [[] for _ in self.px]
        for i, j in _giai_nen(l["canh"], np.uint16).reshape(-1, 2).tolist():
            w = self._met(self.xy[i], self.xy[j])
            self.ke[i].append((j, w))
            self.ke[j].append((i, w))

    def _met(self, a, b) -> float:
        return float(math.hypot(a[0] - b[0], a[1] - b[1])) * self.met_moi_don_vi

    def sang_px(self, x: float, y: float) -> tuple[float, float]:
        return self._x0 + (x - self._gx) * self._kx, self._y0 - y * self._ky

    def sang_don_vi(self, px: np.ndarray) -> np.ndarray:
        px = np.atleast_2d(px)
        return np.c_[self._gx + (px[:, 0] - self._x0) / self._kx, (self._y0 - px[:, 1]) / self._ky]

    def chieu_vao(self, x: float, y: float) -> tuple[int, int]:
        """Pixel đi được gần [x, y] nhất: vị trí dự đoán hay rơi vào tường, kệ sách
        hoặc ra ngoài nhà, đích hay nằm trong phòng không có cửa."""
        u, v = self.sang_px(x, y)
        cao, rong = self.o.shape
        c0, r0 = min(max(round(u), 0), rong - 1), min(max(round(v), 0), cao - 1)
        if self.o[r0, c0]:
            return c0, r0
        # Cửa sổ đặt quanh pixel đã kẹp vào ảnh nên chỉ chắc chứa mọi ô cách [u, v]
        # không quá k - lech.
        lech = math.hypot(u - c0, v - r0)
        k = 4
        while True:
            a, b = max(0, r0 - k), min(cao, r0 + k + 1)
            e, f = max(0, c0 - k), min(rong, c0 + k + 1)
            ca_anh = a == 0 and e == 0 and b == cao and f == rong
            hang, cot = np.nonzero(self.o[a:b, e:f])
            if len(hang):
                d2 = (hang + a - v) ** 2 + (cot + e - u) ** 2
                i = int(d2.argmin())
                if math.sqrt(d2[i]) <= k - lech or ca_anh:
                    return int(cot[i] + e), int(hang[i] + a)
                k = math.ceil(math.sqrt(d2[i]) + lech)
            else:
                k *= 2

    def _thay(self, cr: tuple[int, int]) -> list[tuple[int, float]]:
        """Nút nhìn thấy từ pixel [cr], kèm mét; không thấy nút nào thì lấy nút gần nhất."""
        xy = self.sang_don_vi(np.array(cr, float))[0]
        thay = np.nonzero(nhin_thay(self.o, cr, self.px))[0]
        if not len(thay):
            thay = [int(np.hypot(*(self.px - cr).T).argmin())]
        return [(int(j), self._met(xy, self.xy[j])) for j in thay]

    def tim(self, x: float, y: float, dich: set[str] | tuple[float, float],
            thuat_toan: str = "a_sao") -> tuple[list[int], np.ndarray, float, int]:
        """(chỉ số nút, toạ độ từng điểm trên tuyến, quãng đường mét, số nút đã mở).

        Đích là tập rp_id, hoặc một toạ độ (x, y). Nút -1 là điểm xuất phát, -2 là
        đích toạ độ. A* dùng khoảng cách thẳng tới đích gần nhất — không bao giờ
        ước lượng quá nên vẫn cho đường ngắn nhất như Dijkstra."""
        c, r = self.chieu_vao(x, y)
        goc = self.sang_don_vi(np.array([c, r], float))[0]
        if isinstance(dich, tuple):
            cr_dich = self.chieu_vao(*dich)
            D = self.sang_don_vi(np.array(cr_dich, float))
            ke_dich = dict(self._thay(cr_dich))
            dich_set = {-2}
        else:
            dich_i = [self.chi_so[k] for k in dich if k in self.chi_so]
            if not dich_i:
                return [], goc[None], math.inf, 0
            D, ke_dich, dich_set = self.xy[dich_i], {}, set(dich_i)

        if thuat_toan == "a_sao":
            h = np.sqrt(((self.xy[:, None, :] - D[None]) ** 2).sum(-1)).min(1) * self.met_moi_don_vi
            h0 = float(np.sqrt(((D - goc) ** 2).sum(-1)).min()) * self.met_moi_don_vi
        else:
            h, h0 = np.zeros(len(self.xy)), 0.0

        ke_nguon = self._thay((c, r))
        if ke_dich and nhin_thay(self.o, (c, r), [cr_dich])[0]:
            ke_nguon.append((-2, self._met(goc, D[0])))

        g = {-1: 0.0}
        truoc: dict[int, int] = {}
        hang = [(h0, 0.0, -1)]
        xong: set[int] = set()
        while hang:
            _, _, u = heapq.heappop(hang)
            if u in xong:
                continue
            xong.add(u)
            if u in dich_set:
                nut = [u]
                while nut[-1] != -1:
                    nut.append(truoc[nut[-1]])
                nut.reverse()
                diem = np.vstack([goc, *(D[0] if n == -2 else self.xy[n] for n in nut[1:])])
                return nut, diem, g[u], len(xong)
            ke = ke_nguon if u == -1 else self.ke[u]
            if u in ke_dich:
                ke = [*ke, (-2, ke_dich[u])]
            for v, w in ke:
                moi = g[u] + w
                if moi < g.get(v, math.inf) - 1e-12:
                    g[v] = moi
                    truoc[v] = u
                    heapq.heappush(hang, (moi + (0.0 if v == -2 else h[v]), -moi, v))
        return [], goc[None], math.inf, len(xong)


class DoThiDiLai:
    def __init__(self):
        rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig").dropna(subset=["x", "y"])
        self.toa_do: dict[str, tuple[float, float]] = {
            h.rp_id: (float(h.x), float(h.y)) for h in rp.itertuples()}
        # Tên và mô tả lấy từ POI.geojson của CTK45.
        self.nhan: dict[str, dict[str, str]] = {
            h.rp_id: {c: "" if pd.isna(getattr(h, c)) else str(getattr(h, c)) for c in COT_NHAN}
            for h in rp.itertuples()}

        d = json.loads(BAN_DO_JSON.read_text(encoding="utf-8"))
        self.met_moi_don_vi = d["ty_le_quy_doi"]["met_moi_don_vi"]
        self.luoi = LuoiDiLai(d)
        # Cặp điểm tham chiếu nhìn thấy nhau, cho Dashboard vẽ.
        self.canh = {_khoa(*c): self.khoang_cach(*c) for c in d["canh_nhin_thay"]}

    def khoang_cach(self, a: str, b: str) -> float:
        """Mét."""
        (xa, ya), (xb, yb) = self.toa_do[a], self.toa_do[b]
        return math.hypot(xa - xb, ya - yb) * self.met_moi_don_vi

    def gan_nhat(self, x: float, y: float) -> str:
        """Điểm tham chiếu gần một toạ độ nhất, cùng luật "đang ở khu nào" của ứng dụng."""
        return min(
            self.toa_do,
            key=lambda k: math.hypot(self.toa_do[k][0] - x, self.toa_do[k][1] - y),
        )

    def diem_cua_nhom(self, nhom: str) -> set[str]:
        return {rp for rp, n in self.nhan.items() if n["nhom"] == nhom}

    def chi_duong(self, x: float, y: float, dich: set[str] | tuple[float, float],
                  thuat_toan: str = "a_sao") -> dict | None:
        """Tuyến từ toạ độ [x, y] tới điểm gần nhất THEO ĐƯỜNG ĐI trong tập rp_id
        [dich], hoặc tới toạ độ [dich].

        Tuyến rỗng khi đã tới: điểm tham chiếu gần nhất thuộc [dich] (cùng luật với
        ứng dụng), hoặc cách đích toạ độ dưới `DA_TOI_M`. None khi không có đường."""
        tu = self.gan_nhat(x, y)
        if isinstance(dich, set) and tu in dich:
            return {"tu": tu, "den": tu, "quang_duong_m": 0.0, "so_nut_mo": 0,
                    "duong_di": [self.mo_ta_diem(tu)], "chi_dan": []}
        nut, xy, m, mo = self.luoi.tim(x, y, dich, thuat_toan)
        if not nut:
            return None
        if isinstance(dich, tuple) and m < DA_TOI_M:
            return {"tu": tu, "den": "", "quang_duong_m": 0.0, "so_nut_mo": mo,
                    "duong_di": [{"rp_id": "", "ten": "", "nhom": "", "x": float(xy[-1][0]),
                                  "y": float(xy[-1][1])}], "chi_dan": []}
        ten_rp = {v: k for k, v in self.luoi.chi_so.items()}
        diem = [(float(px), float(py), ten_rp.get(n)) for (px, py), n in zip(xy, nut)]

        # Toạ độ là chỗ tuyến thật sự đi qua: điểm tham chiếu rơi trên cầu thang hay
        # sát tường đã được kéo ra lối đi.
        return {"tu": tu, "den": diem[-1][2] or "", "quang_duong_m": m, "so_nut_mo": mo,
                "duong_di": [{**(self.mo_ta_diem(k) if k else {"rp_id": "", "ten": "", "nhom": ""}),
                              "x": px, "y": py} for px, py, k in diem],
                "chi_dan": self._buoc(diem, tu)}

    def _buoc(self, diem: list[tuple[float, float, str | None]], tu: str) -> list[dict]:
        """Trả mã chứ không trả câu vì ứng dụng chạy hai ngôn ngữ; bước đầu là
        `bat_dau` vì chưa biết hướng mặt. Góc vật cản không có tên nên mang tên
        đích: tên điểm tham chiếu gần góc có thể là chỗ vừa rời đi hoặc sau tường."""
        if len(diem) < 2:
            return []
        moc = [k or diem[-1][2] or "" for _, _, k in diem]
        moc[0] = tu

        chang = [[math.hypot(xb - xa, yb - ya) * self.met_moi_don_vi,
                  math.degrees(math.atan2(yb - ya, xb - xa)), moc[i], moc[i + 1]]
                 for i, ((xa, ya, _), (xb, yb, _)) in enumerate(zip(diem, diem[1:]))]
        # Chặng ngắn hơn sải chân không thành bước riêng: số mét dồn sang chặng kề.
        gon: list[list] = []
        con_du = 0.0
        for c in chang:
            if c[0] + con_du < CHANG_TOI_THIEU_M and c is not chang[-1]:
                con_du += c[0]
                continue
            c[0] += con_du
            con_du = 0.0
            if gon and c[0] < CHANG_TOI_THIEU_M:
                gon[-1][0] += c[0]
                gon[-1][3] = c[3]
            else:
                gon.append(c)
        if gon:
            gon[0][2] = tu

        buoc: list[dict] = []
        for i, (dai, phuong_vi, a, b) in enumerate(gon):
            if i == 0:
                goc, huong = 0.0, "bat_dau"
            else:
                goc = _goc_quay(gon[i - 1][1], phuong_vi)
                huong = _phan_loai(goc)

            # Gộp chặng đi thẳng liên tiếp; điểm giữa vẫn còn trong `duong_di`.
            if huong == "di_thang" and buoc:
                buoc[-1]["den_rp"] = b
                buoc[-1]["khoang_cach_m"] += dai
                continue

            buoc.append({"tu_rp": a, "den_rp": b,
                         "huong": huong, "goc_do": goc, "khoang_cach_m": dai})

        for b in buoc:
            b["khoang_cach_m"] = round(b["khoang_cach_m"], 2)
            b["goc_do"] = round(b["goc_do"], 1)
            b["den_ten"] = self.nhan.get(b["den_rp"], {}).get("ten", "")
        return buoc

    def mo_ta_diem(self, rp_id: str, day_du: bool = False) -> dict:
        """Toạ độ kèm nhãn; `day_du` thêm mô tả và thư mục ảnh cho màn chi tiết."""
        x, y = self.toa_do[rp_id]
        nhan = self.nhan.get(rp_id, {})
        cot = COT_NHAN if day_du else ("ten", "nhom")
        return {"rp_id": rp_id, "x": x, "y": y, **{c: nhan.get(c, "") for c in cot}}

    def thong_ke(self) -> dict:
        dd = list(self.canh.values())
        return {
            "so_diem": len(self.toa_do),
            "so_canh": len(self.canh),
            "canh_ngan_nhat_m": round(min(dd), 2),
            "canh_dai_nhat_m": round(max(dd), 2),
            "bac_trung_binh": round(2 * len(self.canh) / len(self.toa_do), 2),
        }
