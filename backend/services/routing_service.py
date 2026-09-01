"""Đồ thị đi lại và tìm đường giữa các điểm tham chiếu.

Nút của đồ thị là chính 40 điểm tham chiếu chứ không phải GeoJSON, vì **RP nằm
trên chỗ đi được theo định nghĩa**: phải có người đứng đúng đó cầm máy quét mới
đo ra được toạ độ.

Cạnh thì cần thêm sơ đồ mặt bằng, vì hai RP gần nhau vẫn có thể có tường ở
giữa. `tools/trich_ban_do.py` dò việc đó trên Map.png rồi ghi ra
`ban_do_tang1.json`; module này chỉ đọc JSON nên không cần thư viện ảnh. Kết
quả: cạnh dài nhất giảm từ 21,0 m xuống 17,2 m.

`cua_gia_dinh` là sáu cạnh nối lại các mảnh bị tường cắt rời — Map.png không vẽ
cửa nên phải suy ra. Chúng là GIẢ ĐỊNH chưa kiểm chứng thực địa.
"""

from __future__ import annotations

import heapq
import json
import math

import pandas as pd

from ml import config

# Mỗi điểm nối với bấy nhiêu điểm gần nhất. k=3 vừa đủ để đồ thị liên thông
# thành một mảnh; k lớn hơn chỉ thêm cạnh dài xuyên tường.
SO_LANG_GIENG = 3

BAN_DO_JSON = config.REFERENCE_DIR / "ban_do_tang1.json"

# Cạnh gỡ tay, cộng thêm vào phần dò được từ sơ đồ. Để trống là bình thường.
CANH_LOAI_TRU: set[tuple[str, str]] = set()


def _khoa(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


# Ngưỡng phân loại góc quay, tính bằng độ.
#
# Dưới 20° là độ lệch người đi bộ không nhận ra là một cú rẽ — gọi nó là "rẽ"
# thì chỉ dẫn kêu liên tục ở mọi chặng. Trên 135° là quay ngược lại chỗ vừa đi
# qua, phải nói khác hẳn "rẽ" để người dùng biết mình đang vòng lại.
GOC_DI_THANG = 20.0
GOC_CHECH = 60.0
GOC_QUAY_DAU = 135.0


def _goc_quay(truoc: float, sau: float) -> float:
    """Góc phải quay khi chuyển từ hướng [truoc] sang [sau], trong (-180, 180].

    Dương là rẽ TRÁI: hệ toạ độ của dự án có x sang phải, y hướng lên, tức
    thuận chiều toán học, nên góc tăng là quay ngược kim đồng hồ.

    Trả về góc thay vì trả thẳng một nhãn như `getDirection` của CTK45, vì hai
    lẽ. Một, hàm đó chỉ có ba kết quả thẳng/trái/phải nên một cú quay đầu 179°
    đọc thành "rẽ trái". Hai, nó tính góc bằng `acos(dot / (mag1 * mag2))`, gặp
    hai điểm trùng nhau thì mẫu số bằng 0, `angle` thành NaN, mọi phép so đều
    sai và hàm rơi xuống nhánh cuối trả "Rẽ phải" cho một chặng không hề rẽ.
    Có góc trong tay thì phân loại được bao nhiêu mức tuỳ ý, và điểm trùng chỉ
    cho ra góc 0.
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
    """(cạnh xuyên tường, cửa giả định) từ ban_do_tang1.json.

    Thiếu tệp thì trả hai tập rỗng và đồ thị lùi về bản k=3 thuần khoảng cách:
    sơ đồ là dữ liệu bổ sung, không phải phụ thuộc bắt buộc.
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
        """Dijkstra. Trả ([], inf) khi không có đường — không xảy ra với đồ thị
        hiện tại vì nó liên thông, nhưng sẽ xảy ra nếu CANH_LOAI_TRU cắt rời
        một mảng.
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

        Trả dữ liệu có cấu trúc chứ KHÔNG trả câu dựng sẵn: ứng dụng di động
        chạy hai ngôn ngữ, đóng cứng câu ở máy chủ là ép nó về một thứ tiếng.

        Góc quay tính so với chặng LIỀN TRƯỚC nên bước đầu mang hướng
        `bat_dau` — hệ biết người dùng đứng ở đâu nhưng không biết đang quay
        mặt về đâu, muốn biết thì phải thêm từ kế chứ không sửa hàm này.
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

            # Gộp các chặng đi thẳng liên tiếp: "đi thẳng 12 m rồi đi thẳng 12 m"
            # là hai câu cho cùng một hành động. Điểm giữa vẫn còn nguyên trong
            # `duong_di` nếu client cần vẽ.
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
