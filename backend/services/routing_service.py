"""Đồ thị đi lại và tìm đường giữa các điểm tham chiếu.

Nút là chính các điểm tham chiếu chứ không phải GeoJSON, vì RP nằm trên chỗ đi
được theo định nghĩa. Cạnh thì cần thêm sơ đồ mặt bằng vì hai RP gần nhau vẫn
có thể có tường ở giữa; `tools/trich_ban_do.py` dò việc đó rồi ghi
`ban_do_tang1.json` nên module này không cần thư viện ảnh. Cạnh dài nhất giảm
21,0 m xuống 16,1 m.

`cua_gia_dinh` là các cạnh nối lại mảnh bị tường cắt rời — GIẢ ĐỊNH chưa kiểm
chứng thực địa; số lượng đọc từ JSON vì nó đổi theo bộ điểm tham chiếu.
"""

from __future__ import annotations

import heapq
import json
import math

import pandas as pd

from ml import config

# Mỗi điểm nối với bấy nhiêu điểm gần nhất; k lớn hơn chỉ thêm cạnh xuyên tường.
#
# k=3 KHÔNG tự nó làm đồ thị liên thông: phần dò từ sơ đồ vỡ thành 8 mảnh cỡ
# [16, 15, 6, 2, 2, 1, 1, 1], phải có `cua_gia_dinh` nối lại. Hệ quả: hành lang
# nam đi được suốt chiều dài toà nhà nhưng hai đoạn giữa dài 28,1 m, xa hơn ba
# láng giềng gần nhất của cả hai đầu nên không bao giờ thành cạnh — tuyến từ đầu
# này sang đầu kia dài gấp 1,5 lần đường thẳng. Nâng k sẽ gỡ được nhưng phải đo
# lại cạnh xuyên tường.
SO_LANG_GIENG = 3

BAN_DO_JSON = config.REFERENCE_DIR / "ban_do_tang1.json"

# Cạnh gỡ tay, cộng thêm vào phần dò được từ sơ đồ. Để trống là bình thường.
CANH_LOAI_TRU: set[tuple[str, str]] = set()


def _khoa(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


# Ngưỡng phân loại góc quay, tính bằng độ. Dưới 20° là độ lệch người đi bộ
# không nhận ra là một cú rẽ, gọi là "rẽ" thì chỉ dẫn kêu liên tục ở mọi chặng.
# Trên 135° là quay ngược lại chỗ vừa đi qua, phải nói khác hẳn "rẽ".
GOC_DI_THANG = 20.0
GOC_CHECH = 60.0
GOC_QUAY_DAU = 135.0


def _goc_quay(truoc: float, sau: float) -> float:
    """Góc phải quay khi chuyển từ hướng [truoc] sang [sau], trong (-180, 180].

    Dương là rẽ TRÁI: hệ toạ độ có x sang phải, y hướng lên, tức thuận chiều toán
    học, nên góc tăng là quay ngược kim đồng hồ.

    Trả về GÓC chứ không trả nhãn thẳng/trái/phải: có góc thì phân loại được bao
    nhiêu mức tuỳ ý, quay đầu 179° không bị đọc thành "rẽ trái", và hai điểm
    trùng nhau cho góc 0 thay vì NaN như cách tính bằng `acos`.
    """
    return (sau - truoc + 180.0) % 360.0 - 180.0


def _phan_loai(goc: float) -> str:
    do_lon = abs(goc)
    if do_lon <= GOC_DI_THANG:
        return "di_thang"
    if do_lon > GOC_QUAY_DAU:
        return "quay_dau"
    ben = "trai" if goc > 0 else "phai"
    return f"chech_{ben}" if do_lon <= GOC_CHECH else f"re_{ben}"


def _doc_ban_do() -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """(cạnh xuyên tường, cửa giả định) từ ban_do_tang1.json. Thiếu tệp thì trả hai
    tập rỗng và đồ thị lùi về bản k=3 thuần khoảng cách: sơ đồ là dữ liệu bổ sung,
    không phải phụ thuộc bắt buộc.
    """
    if not BAN_DO_JSON.exists():
        return set(), set()
    d = json.loads(BAN_DO_JSON.read_text(encoding="utf-8"))
    return ({_khoa(*c) for c in d["canh_xuyen_tuong"]},
            {_khoa(*c) for c in d["cua_gia_dinh"]})


class DoThiDiLai:
    def __init__(self, so_lang_gieng: int = SO_LANG_GIENG):
        rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
        rp = rp.dropna(subset=["x", "y"]).reset_index(drop=True)

        self.toa_do: dict[str, tuple[float, float]] = {
            h.rp_id: (float(h.x), float(h.y)) for h in rp.itertuples()
        }

        # Tên và mô tả lấy từ POI.geojson của CTK45, để chỉ đường nói được "tới
        # Phòng tạp chí" thay vì "tới RP39".
        self.nhan: dict[str, dict[str, str]] = {
            h.rp_id: {
                c: "" if pd.isna(getattr(h, c)) else str(getattr(h, c))
                for c in ("ten", "nhom", "mo_ta", "mo_ta_chi_tiet", "thu_muc_anh")
            }
            for h in rp.itertuples()
        }
        self.canh = self._dung_canh(so_lang_gieng)

        self.ke: dict[str, list[tuple[str, float]]] = {k: [] for k in self.toa_do}
        for (a, b), d in self.canh.items():
            self.ke[a].append((b, d))
            self.ke[b].append((a, d))

    def _dung_canh(self, k: int) -> dict[tuple[str, str], float]:
        xuyen_tuong, self.cua_gia_dinh = _doc_ban_do()
        bo = xuyen_tuong | CANH_LOAI_TRU

        ten = list(self.toa_do)
        canh: dict[tuple[str, str], float] = {}

        for a in ten:
            gan = sorted(
                ((self.khoang_cach(a, b), b) for b in ten if b != a),
            )[:k]
            for d, b in gan:
                khoa = _khoa(a, b)
                if khoa not in bo:
                    canh[khoa] = d

        # Thêm cửa SAU CÙNG: chúng chính là cạnh vừa bị chặn ở trên.
        for a, b in self.cua_gia_dinh:
            if a in self.toa_do and b in self.toa_do:
                canh[_khoa(a, b)] = self.khoang_cach(a, b)

        return canh

    def khoang_cach(self, a: str, b: str) -> float:
        (xa, ya), (xb, yb) = self.toa_do[a], self.toa_do[b]
        return math.hypot(xa - xb, ya - yb)

    def gan_nhat(self, x: float, y: float) -> str:
        """Điểm tham chiếu gần một toạ độ nhất — dùng để neo đầu và cuối đường đi."""
        return min(
            self.toa_do,
            key=lambda k: math.hypot(self.toa_do[k][0] - x, self.toa_do[k][1] - y),
        )

    def tim_duong(self, tu: str, den: str) -> tuple[list[str], float]:
        """Dijkstra. Trả ([], inf) khi không có đường — không xảy ra với đồ thị hiện
        tại vì nó liên thông, nhưng sẽ xảy ra nếu CANH_LOAI_TRU cắt rời một mảng.
        """
        if tu == den:
            return [tu], 0.0

        xa = {tu: 0.0}
        truoc: dict[str, str] = {}
        hang = [(0.0, tu)]
        da_xong: set[str] = set()

        while hang:
            d, nut = heapq.heappop(hang)
            if nut in da_xong:
                continue
            if nut == den:
                break
            da_xong.add(nut)

            for ke, w in self.ke[nut]:
                moi = d + w
                if moi < xa.get(ke, math.inf):
                    xa[ke] = moi
                    truoc[ke] = nut
                    heapq.heappush(hang, (moi, ke))

        if den not in xa:
            return [], math.inf

        duong = [den]
        while duong[-1] != tu:
            duong.append(truoc[duong[-1]])
        return duong[::-1], xa[den]

    def toa_do_duong(self, duong: list[str]) -> list[dict]:
        return [self.mo_ta_diem(k) for k in duong]

    def chi_dan(self, duong: list[str]) -> list[dict]:
        """Đường đi thành từng bước "đi thẳng / rẽ trái / rẽ phải" kèm số mét.

        Trả dữ liệu có cấu trúc chứ KHÔNG trả câu dựng sẵn: ứng dụng chạy hai ngôn
        ngữ, đóng cứng câu ở máy chủ là ép nó về một thứ tiếng. Góc quay tính so với
        chặng LIỀN TRƯỚC nên bước đầu mang hướng `bat_dau` — hệ biết người dùng đứng
        ở đâu nhưng không biết đang quay mặt về đâu.
        """
        if len(duong) < 2:
            return []

        chang = [
            {"tu_rp": a, "den_rp": b,
             "khoang_cach_m": self.khoang_cach(a, b),
             "phuong_vi": self._phuong_vi(a, b)}
            for a, b in zip(duong, duong[1:])
        ]

        buoc: list[dict] = []
        for i, c in enumerate(chang):
            if i == 0:
                goc, huong = 0.0, "bat_dau"
            else:
                goc = _goc_quay(chang[i - 1]["phuong_vi"], c["phuong_vi"])
                huong = _phan_loai(goc)

            # Gộp các chặng đi thẳng liên tiếp: "đi thẳng 12 m rồi đi thẳng 12 m" là hai
            # câu cho cùng một hành động. Điểm giữa vẫn còn trong `duong_di` nếu cần vẽ.
            if huong == "di_thang" and buoc:
                buoc[-1]["den_rp"] = c["den_rp"]
                buoc[-1]["khoang_cach_m"] += c["khoang_cach_m"]
                continue

            buoc.append({"tu_rp": c["tu_rp"], "den_rp": c["den_rp"],
                         "huong": huong, "goc_do": goc,
                         "khoang_cach_m": c["khoang_cach_m"]})

        for b in buoc:
            b["khoang_cach_m"] = round(b["khoang_cach_m"], 2)
            b["goc_do"] = round(b["goc_do"], 1)
            b["den_ten"] = self.nhan.get(b["den_rp"], {}).get("ten", "")
        return buoc

    def _phuong_vi(self, a: str, b: str) -> float:
        (xa, ya), (xb, yb) = self.toa_do[a], self.toa_do[b]
        return math.degrees(math.atan2(yb - ya, xb - xa))

    def mo_ta_diem(self, rp_id: str, day_du: bool = False) -> dict:
        """Toạ độ kèm nhãn. `day_du` thêm mô tả và thư mục ảnh cho màn chi tiết;
        đường đi không cần chúng vì nhân với số chặng chỉ làm nặng response.
        """
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
