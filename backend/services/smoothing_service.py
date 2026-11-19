"""Gộp vài lần quét gần nhau trước khi trả toạ độ. Gọi thẳng `ml.postprocess.gop`
để backend và báo cáo dùng chung thuật toán.
"""

from __future__ import annotations

import time
from collections import deque

import numpy as np

from ml import postprocess


class BoGop:
    def __init__(self, cua_so: int = 3, reset_sau_giay: float = 30.0):
        self.cua_so = cua_so
        self.reset_sau_giay = reset_sau_giay

        # dict thường: defaultdict tạo khoá mới ngay cả khi chỉ đọc.
        self._lich_su: dict[str, deque] = {}
        self._lan_cuoi: dict[str, float] = {}

    def them(self, device_id: str, x: float, y: float) -> tuple[float, float]:
        """Thêm một dự đoán, trả về toạ độ đã gộp của thiết bị đó."""
        bay_gio = time.monotonic()

        # Im lặng quá lâu là đã đi chỗ khác; gộp với toạ độ cũ sẽ kéo lệch.
        truoc = self._lan_cuoi.get(device_id)
        if truoc is not None and bay_gio - truoc > self.reset_sau_giay:
            self.quen(device_id)

        self._lan_cuoi[device_id] = bay_gio
        lich = self._lich_su.setdefault(device_id, deque(maxlen=self.cua_so))
        lich.append((x, y))

        gop = postprocess.gop(np.array(lich, dtype=float))
        return float(gop[0]), float(gop[1])

    def so_mau_dang_giu(self, device_id: str) -> int:
        return len(self._lich_su.get(device_id, ()))

    def quen(self, device_id: str) -> None:
        self._lich_su.pop(device_id, None)
        self._lan_cuoi.pop(device_id, None)
