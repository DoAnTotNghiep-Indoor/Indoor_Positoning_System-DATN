"""Đồ thị đi lại và tìm đường.

Hai tầng đồ thị. `DoThiDiLai.canh` nối các điểm tham chiếu nhìn thấy nhau, dùng
cho Dashboard. Chỉ đường thật chạy trên `LuoiDiLai`: nút là góc lồi của vật cản
cộng điểm tham chiếu, vì đường ngắn nhất trong mặt bằng có vật cản chỉ bẻ hướng
ở góc lồi — nên tuyến đi từ đúng vị trí người dùng, không phải từ điểm tham
chiếu gần nhất.

Toạ độ giữ đơn vị lưới của Bảng 4; mọi khoảng cách trả ra là MÉT, nhân
`met_moi_don_vi` (Hình 7 báo cáo CTK45, xem `tools/trich_ban_do.py`).
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

# Chỉ dùng khi JSON thiếu `canh_nhin_thay`: mỗi điểm nối bấy nhiêu điểm gần nhất.
SO_LANG_GIENG = 3

BAN_DO_JSON = config.REFERENCE_DIR / "ban_do_tang1.json"

# Cạnh gỡ tay, cộng thêm vào phần dò được từ sơ đồ. Để trống là bình thường.
CANH_LOAI_TRU: set[tuple[str, str]] = set()

THUAT_TOAN = ("a_sao", "dijkstra")


def _khoa(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


# Ngưỡng góc quay (độ): dưới 20° người đi bộ không coi là rẽ, trên 135° là quay đầu.
GOC_DI_THANG = 20.0
GOC_CHECH = 60.0
GOC_QUAY_DAU = 135.0

# Chặng ngắn hơn chừng một sải chân thì không đáng thành một bước chỉ dẫn.
CHANG_TOI_THIEU_M = 0.5


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


def _doc_json() -> dict | None:
    if not BAN_DO_JSON.exists():
        return None
    return json.loads(BAN_DO_JSON.read_text(encoding="utf-8"))


def _doc_ban_do() -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """(cạnh xuyên tường, cửa giả định); thiếu tệp thì hai tập rỗng."""
    d = _doc_json()
    if d is None:
        return set(), set()
    return {_khoa(*c) for c in d["canh_xuyen_tuong"]}, {_khoa(*c) for c in d["cua_gia_dinh"]}


def _doc_nhin_thay() -> set[tuple[str, str]] | None:
    d = _doc_json()
    ds = d.get("canh_nhin_thay") if d else None
    return None if ds is None else {_khoa(*c) for c in ds}


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
        self._kx, self._ky = g["px_moi_met_x"], g["px_moi_met_y"]
        self._gx = g["goc_met_x"]
        self.met_moi_don_vi = d["ty_le_quy_doi"]["met_moi_don_vi"]

        self.rp = list(l["rp_px"])
        goc = _giai_nen(l["goc_px"], np.uint16).reshape(-1, 2)
        self.so_goc = len(goc)
        self.px = np.vstack([goc, [l["rp_px"][k] for k in self.rp]]).astype(float)
        self.xy = self.sang_don_vi(self.px)
        self.chi_so = {k: self.so_goc + i for i, k in enumerate(self.rp)}
        self.han_che = {self.chi_so[k] for k in d.get("chi_noi", {}) if k in self.chi_so}

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
        hoặc ra ngoài nhà."""
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

    def tim(self, x: float, y: float, dich: set[str], thuat_toan: str = "a_sao",
            chi_noi: set[str] | None = None,
            bo: set[str] = frozenset()) -> tuple[list[int], np.ndarray, float, int]:
        """(chỉ số nút, toạ độ từng điểm trên tuyến, quãng đường mét, số nút đã mở).

        Nút -1 là điểm xuất phát. A* dùng khoảng cách thẳng tới đích gần nhất —
        không bao giờ ước lượng quá nên vẫn cho đường ngắn nhất như Dijkstra."""
        dich_i = [self.chi_so[k] for k in dich if k in self.chi_so]
        c, r = self.chieu_vao(x, y)
        goc = self.sang_don_vi(np.array([c, r], float))[0]
        if not dich_i:
            return [], goc[None], math.inf, 0

        D = self.xy[dich_i]
        if thuat_toan == "a_sao":
            h = np.sqrt(((self.xy[:, None, :] - D[None]) ** 2).sum(-1)).min(1) * self.met_moi_don_vi
            h0 = float(np.sqrt(((D - goc) ** 2).sum(-1)).min()) * self.met_moi_don_vi
        else:
            h, h0 = np.zeros(len(self.xy)), 0.0

        if chi_noi:
            thay = [self.chi_so[k] for k in chi_noi if k in self.chi_so]
        else:
            cam = self.han_che | {self.chi_so[k] for k in bo if k in self.chi_so}
            thay = [j for j in np.nonzero(nhin_thay(self.o, (c, r), self.px))[0].tolist()
                    if j not in cam]
            if not thay:
                xa = np.hypot(*(self.px - (c, r)).T)
                xa[list(cam)] = np.inf
                thay = [int(xa.argmin())]
        ke_nguon = [(int(j), self._met(goc, self.xy[j])) for j in thay]

        g = {-1: 0.0}
        truoc: dict[int, int] = {}
        hang = [(h0, 0.0, -1)]
        xong: set[int] = set()
        dich_set = set(dich_i)
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
                diem = np.vstack([goc, self.xy[nut[1:]]])
                return nut, diem, g[u], len(xong)
            for v, w in (ke_nguon if u == -1 else self.ke[u]):
                moi = g[u] + w
                if moi < g.get(v, math.inf) - 1e-12:
                    g[v] = moi
                    truoc[v] = u
                    heapq.heappush(hang, (moi + h[v], -moi, v))
        return [], goc[None], math.inf, len(xong)


class DoThiDiLai:
    def __init__(self, so_lang_gieng: int = SO_LANG_GIENG, tam_nhin: bool = True):
        rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
        rp = rp.dropna(subset=["x", "y"]).reset_index(drop=True)

        self.toa_do: dict[str, tuple[float, float]] = {
            h.rp_id: (float(h.x), float(h.y)) for h in rp.itertuples()
        }

        # Tên và mô tả lấy từ POI.geojson của CTK45.
        self.nhan: dict[str, dict[str, str]] = {
            h.rp_id: {
                c: "" if pd.isna(getattr(h, c)) else str(getattr(h, c))
                for c in ("ten", "nhom", "mo_ta", "mo_ta_chi_tiet", "thu_muc_anh")
            }
            for h in rp.itertuples()
        }

        d = _doc_json()
        self.met_moi_don_vi = d["ty_le_quy_doi"]["met_moi_don_vi"] if d else 1.0
        self.luoi = LuoiDiLai(d) if d and "luoi_di_lai" in d else None
        self.chi_noi: dict[str, list[str]] = d.get("chi_noi", {}) if d else {}
        self.cam_noi: dict[str, set[str]] = {}
        for a, b in d.get("cam_noi", []) if d else []:
            self.cam_noi.setdefault(a, set()).add(b)
            self.cam_noi.setdefault(b, set()).add(a)
        self.canh = self._dung_canh(d, so_lang_gieng, tam_nhin)

        self.ke: dict[str, list[tuple[str, float]]] = {k: [] for k in self.toa_do}
        for (a, b), w in self.canh.items():
            self.ke[a].append((b, w))
            self.ke[b].append((a, w))

    def _dung_canh(self, d: dict | None, k: int, tam_nhin: bool) -> dict[tuple[str, str], float]:
        xuyen_tuong = {_khoa(*c) for c in d["canh_xuyen_tuong"]} if d else set()
        self.cua_gia_dinh = {_khoa(*c) for c in d["cua_gia_dinh"]} if d else set()
        nhin = d.get("canh_nhin_thay") if d and tam_nhin else None
        canh: dict[tuple[str, str], float] = {}

        if nhin is not None:
            for a, b in {_khoa(*c) for c in nhin} - CANH_LOAI_TRU:
                if a in self.toa_do and b in self.toa_do:
                    canh[(a, b)] = self.khoang_cach(a, b)
        else:
            bo = xuyen_tuong | CANH_LOAI_TRU
            ten = list(self.toa_do)
            for a in ten:
                gan = sorted((self.khoang_cach(a, b), b) for b in ten if b != a)[:k]
                for w, b in gan:
                    if _khoa(a, b) not in bo:
                        canh[_khoa(a, b)] = w

        # Thêm cửa SAU CÙNG: chúng chính là cạnh vừa bị chặn ở trên.
        for a, b in self.cua_gia_dinh:
            if a in self.toa_do and b in self.toa_do:
                canh[_khoa(a, b)] = self.khoang_cach(a, b)

        return canh

    def khoang_cach(self, a: str, b: str) -> float:
        """Mét."""
        (xa, ya), (xb, yb) = self.toa_do[a], self.toa_do[b]
        return math.hypot(xa - xb, ya - yb) * self.met_moi_don_vi

    def gan_nhat(self, x: float, y: float) -> str:
        """Điểm tham chiếu gần một toạ độ nhất — dùng để neo đầu và cuối đường đi."""
        return min(
            self.toa_do,
            key=lambda k: math.hypot(self.toa_do[k][0] - x, self.toa_do[k][1] - y),
        )

    def tim_duong(self, tu: str, den: str) -> tuple[list[str], float]:
        """A* trên đồ thị điểm tham chiếu; ([], inf) khi không có đường."""
        return self._loang(tu, {den}, self._toi_dich_gan_nhat)

    def tim_duong_dijkstra(self, tu: str, den: str) -> tuple[list[str], float]:
        return self._loang(tu, {den}, lambda n, dich: 0.0)

    def diem_cua_nhom(self, nhom: str) -> set[str]:
        return {rp for rp, n in self.nhan.items() if n["nhom"] == nhom}

    def tim_duong_toi_nhom(self, tu: str, nhom: str) -> tuple[list[str], float]:
        """A* đa đích: dừng ở điểm đầu tiên của khu vực lấy ra khỏi hàng đợi — điểm
        gần nhất theo đường thẳng có thể nằm sau tường."""
        return self._loang(tu, self.diem_cua_nhom(nhom), self._toi_dich_gan_nhat)

    def _toi_dich_gan_nhat(self, nut: str, dich: set[str]) -> float:
        return min(self.khoang_cach(nut, d) for d in dich)

    def _loang(self, tu: str, dich: set[str], uoc_luong) -> tuple[list[str], float]:
        if not dich:
            return [], math.inf
        if tu in dich:
            return [tu], 0.0

        xa = {tu: 0.0}
        truoc: dict[str, str] = {}
        hang = [(uoc_luong(tu, dich), tu)]
        da_xong: set[str] = set()
        den = None

        while hang:
            _, nut = heapq.heappop(hang)
            if nut in da_xong:
                continue
            if nut in dich:
                den = nut
                break
            da_xong.add(nut)

            for ke, w in self.ke[nut]:
                moi = xa[nut] + w
                if moi < xa.get(ke, math.inf):
                    xa[ke] = moi
                    truoc[ke] = nut
                    heapq.heappush(hang, (moi + uoc_luong(ke, dich), ke))

        if den is None:
            return [], math.inf

        duong = [den]
        while duong[-1] != tu:
            duong.append(truoc[duong[-1]])
        return duong[::-1], xa[den]

    def chi_duong(self, x: float, y: float, dich: set[str],
                  thuat_toan: str = "a_sao") -> dict | None:
        """Tuyến từ toạ độ [x, y] tới điểm gần nhất THEO ĐƯỜNG ĐI trong [dich].

        Đứng sẵn ở khu vực đích — điểm tham chiếu gần nhất thuộc [dich], cùng luật
        với ứng dụng — thì tuyến rỗng. None khi không có đường."""
        tu = self.gan_nhat(x, y)
        if tu in dich:
            return {"tu": tu, "den": tu, "quang_duong_m": 0.0, "so_nut_mo": 0,
                    "duong_di": [self.mo_ta_diem(tu)], "chi_dan": []}
        if self.luoi is None:
            duong, m = self._loang(tu, dich, self._toi_dich_gan_nhat if thuat_toan == "a_sao"
                                   else lambda n, d: 0.0)
            if not duong:
                return None
            diem = [(*self.toa_do[k], k) for k in duong]
            mo = 0
        else:
            # Xuất phát theo luật nối của điểm gần nhất: chỉ ra qua điểm kề cho phép,
            # không đi thẳng tới điểm bị cấm nối.
            ke = self.chi_noi.get(tu)
            nut, xy, m, mo = self.luoi.tim(x, y, dich, thuat_toan,
                                           {tu, *ke} if ke else None,
                                           self.cam_noi.get(tu, set()))
            if not nut:
                return None
            ten_rp = {v: k for k, v in self.luoi.chi_so.items()}
            diem = [(float(px), float(py), ten_rp.get(n)) for (px, py), n in zip(xy, nut)]

        # Toạ độ là chỗ tuyến thật sự đi qua: điểm tham chiếu rơi trên kệ sách hay
        # khối cầu thang đã được kéo ra lối đi.
        return {"tu": tu, "den": diem[-1][2], "quang_duong_m": m, "so_nut_mo": mo,
                "duong_di": [{**(self.mo_ta_diem(k) if k else {"rp_id": "", "ten": "", "nhom": ""}),
                              "x": px, "y": py} for px, py, k in diem],
                "chi_dan": self._buoc(diem, tu)}

    def toa_do_duong(self, duong: list[str]) -> list[dict]:
        return [self.mo_ta_diem(k) for k in duong]

    def chi_dan(self, duong: list[str]) -> list[dict]:
        """Đường đi qua các điểm tham chiếu thành từng bước kèm số mét."""
        if len(duong) < 2:
            return []
        return self._buoc([(*self.toa_do[k], k) for k in duong], duong[0])

    def _buoc(self, diem: list[tuple[float, float, str | None]], tu: str) -> list[dict]:
        """Trả mã chứ không trả câu vì ứng dụng chạy hai ngôn ngữ; bước đầu là
        `bat_dau` vì chưa biết hướng mặt. Góc vật cản không có tên nên mang tên
        đích: tên điểm tham chiếu gần góc có thể là chỗ vừa rời đi hoặc sau tường."""
        if len(diem) < 2:
            return []
        moc = [k or diem[-1][2] for _, _, k in diem]
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
        cot = (
            ("ten", "nhom", "mo_ta", "mo_ta_chi_tiet", "thu_muc_anh")
            if day_du
            else ("ten", "nhom")
        )
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
