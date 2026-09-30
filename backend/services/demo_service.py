"""Chế độ demo: thay lần quét của điện thoại bằng một lần quét thật đã ghi ở
thư viện, để trình diễn được khi đứng ngoài thư viện.

Chỉ thay đầu vào, mô hình vẫn chạy thật: toạ độ trả về là dự đoán của mô hình
trên một vân tay chưa từng thấy lúc huấn luyện (tập test), không phải toạ độ
ghi sẵn. Mỗi thiết bị đi một vòng qua các điểm tham chiếu, bắt đầu ở cửa ra
vào, dừng vài lần quét ở mỗi điểm để cửa sổ gộp kịp hội tụ.
"""

from __future__ import annotations

import math
from pathlib import Path
from threading import Lock

import pandas as pd

from backend.config import ROOT_DIR

TEP_QUET = ROOT_DIR / "data" / "processed" / "fingerprint_dataset_raw.csv"
DIEM_XUAT_PHAT = "RP02"  # Cửa ra vào


class PhatLaiQuet:
    def __init__(self, ap_columns: list[str], gia_tri_thieu: float,
                 duong_dan: Path = TEP_QUET, so_lan_moi_diem: int = 3):
        bang = pd.read_csv(duong_dan)
        bang = bang[bang["split"] == "test"]

        theo_diem: dict[str, list[list[dict]]] = {}
        toa_do: dict[str, tuple[float, float]] = {}
        for _, dong in bang.sort_values("scan_id").iterrows():
            scan = [{"bssid": b, "rssi": float(dong[b])}
                    for b in ap_columns if float(dong[b]) != gia_tri_thieu]
            theo_diem.setdefault(dong["rp_id"], []).append(scan)
            toa_do[dong["rp_id"]] = (float(dong["x"]), float(dong["y"]))

        # Vòng tham lam theo điểm gần nhất: trên bản đồ trông như đang đi bộ.
        con_lai = set(toa_do)
        hien_tai = DIEM_XUAT_PHAT if DIEM_XUAT_PHAT in con_lai else min(con_lai)
        thu_tu = []
        while con_lai:
            con_lai.remove(hien_tai)
            thu_tu.append(hien_tai)
            if con_lai:
                x0, y0 = toa_do[hien_tai]
                hien_tai = min(con_lai, key=lambda rp: (
                    math.dist((x0, y0), toa_do[rp]), rp))

        self.chuoi: list[tuple[str, list[dict]]] = []
        for rp in thu_tu:
            mau = theo_diem[rp]
            for i in range(so_lan_moi_diem):
                self.chuoi.append((rp, mau[i % len(mau)]))

        self._buoc: dict[str, int] = {}
        self._khoa = Lock()

    def quet_tiep(self, device_id: str) -> tuple[str, list[dict]]:
        """(rp_id đang phát, lần quét) kế tiếp của thiết bị này."""
        with self._khoa:
            i = self._buoc.get(device_id, 0)
            self._buoc[device_id] = (i + 1) % len(self.chuoi)
        return self.chuoi[i]
