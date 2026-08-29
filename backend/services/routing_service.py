"""Đồ thị đi lại và tìm đường giữa các điểm tham chiếu.

Đồ thị dựng từ chính 39 điểm tham chiếu chứ không từ GeoJSON, vì một tính chất
của cách thu dữ liệu: **RP nằm trên chỗ đi được theo định nghĩa** — phải có
người đứng đúng đó cầm máy quét mới đo ra được toạ độ. Không điểm nào nằm trong
tường hay trong đồ đạc.

Nhờ vậy chỉ đường chạy được ngay mà không phải chờ số hoá bản đồ. Khi xin được
bộ GeoJSON của CTK45 (layer Paths, Hallways, Doors) thì thay nguồn cạnh ở đây,
API bên ngoài không đổi.

Hạn chế đã biết: hai RP cách nhau vẫn có thể có tường ở giữa, mà không có Room
polygon thì không tự phát hiện được. Cạnh dài nhất trong đồ thị hiện tại là
22,4 m — gần như chắc chắn xuyên tường. Dùng CANH_LOAI_TRU để gỡ tay từng cạnh
sai; 39 nút là đủ ít để rà bằng mắt.
"""

from __future__ import annotations

import heapq
import math

import pandas as pd

from ml import config

# Mỗi điểm nối với bấy nhiêu điểm gần nhất. k=3 vừa đủ để đồ thị liên thông
# thành một mảnh; k lớn hơn chỉ thêm cạnh dài xuyên tường.
SO_LANG_GIENG = 3

# Cạnh đã rà bằng mắt và xác định là xuyên tường. Thêm cặp (rp_a, rp_b) vào đây.
CANH_LOAI_TRU: set[tuple[str, str]] = set()


def _khoa(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


class DoThiDiLai:
    def __init__(self, so_lang_gieng: int = SO_LANG_GIENG):
        rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
        rp = rp.dropna(subset=["x", "y"]).reset_index(drop=True)

        self.toa_do: dict[str, tuple[float, float]] = {
            h.rp_id: (float(h.x), float(h.y)) for h in rp.itertuples()
        }
        self.canh = self._dung_canh(so_lang_gieng)

        self.ke: dict[str, list[tuple[str, float]]] = {k: [] for k in self.toa_do}
        for (a, b), d in self.canh.items():
            self.ke[a].append((b, d))
            self.ke[b].append((a, d))

    def _dung_canh(self, k: int) -> dict[tuple[str, str], float]:
        ten = list(self.toa_do)
        canh: dict[tuple[str, str], float] = {}

        for a in ten:
            gan = sorted(
                ((self.khoang_cach(a, b), b) for b in ten if b != a),
            )[:k]
            for d, b in gan:
                khoa = _khoa(a, b)
                if khoa not in CANH_LOAI_TRU:
                    canh[khoa] = d

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
        """Dijkstra. Trả về (danh sách rp_id theo thứ tự, tổng quãng đường mét).

        Trả về ([], inf) khi không có đường — không xảy ra với đồ thị hiện tại
        vì nó liên thông, nhưng sẽ xảy ra nếu CANH_LOAI_TRU cắt rời một mảng.
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
        return [
            {"rp_id": k, "x": self.toa_do[k][0], "y": self.toa_do[k][1]} for k in duong
        ]

    def thong_ke(self) -> dict:
        dd = list(self.canh.values())
        return {
            "so_diem": len(self.toa_do),
            "so_canh": len(self.canh),
            "canh_ngan_nhat_m": round(min(dd), 2),
            "canh_dai_nhat_m": round(max(dd), 2),
            "bac_trung_binh": round(2 * len(self.canh) / len(self.toa_do), 2),
        }
