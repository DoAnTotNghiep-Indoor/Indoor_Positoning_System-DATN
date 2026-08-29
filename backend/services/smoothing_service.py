"""Gộp nhiều lần quét gần nhau về thời gian trước khi trả toạ độ.

Đây là tầng đưa sai số trung bình từ 2,56 m xuống 0,73 m trên tập test, và số
vị trí sai từ 12/39 xuống 2/39. Phép gộp không tự viết lại — gọi thẳng
`ml.postprocess.gop` để backend và bảng số liệu trong báo cáo dùng đúng một
thuật toán.

Lý do gộp hiệu quả: các ca sai nặng gần như luôn là MỘT lần quét dị thường lẻ
loi chứ không phải sai lệch có hệ thống. Thiết bị quét mỗi 1-2 giây nên lúc chạy
thật luôn có sẵn vài lần quét gần nhau để loại điểm lạc.
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

        # dict thường chứ không defaultdict: với defaultdict thì chỉ ĐỌC
        # so_mau_dang_giu() bằng một device_id lạ cũng tạo ra một khoá mới.
        self._lich_su: dict[str, deque] = {}
        self._lan_cuoi: dict[str, float] = {}
        self._lan_don = time.monotonic()

    def them(self, device_id: str, x: float, y: float) -> tuple[float, float]:
        """Thêm một dự đoán, trả về toạ độ đã gộp của thiết bị đó."""
        bay_gio = time.monotonic()
        self._don_thiet_bi_da_roi(bay_gio)

        # Im lặng quá lâu nghĩa là người dùng đã đi chỗ khác rồi quay lại; gộp
        # với toạ độ cũ sẽ kéo kết quả về vị trí họ không còn đứng nữa.
        truoc = self._lan_cuoi.get(device_id)
        if truoc is not None and bay_gio - truoc > self.reset_sau_giay:
            self.quen(device_id)

        self._lan_cuoi[device_id] = bay_gio
        lich = self._lich_su.setdefault(device_id, deque(maxlen=self.cua_so))
        lich.append((x, y))

        gop = postprocess.gop(np.array(lich, dtype=float))
        return float(gop[0]), float(gop[1])

    def _don_thiet_bi_da_roi(self, bay_gio: float) -> None:
        """Bỏ hẳn thiết bị đã im lặng quá lâu, không chỉ xoá lịch sử của nó.

        Thiếu bước này thì hai dict trên chỉ có lớn lên: device_id do client tự
        đặt nên số khoá không bị chặn bởi số máy thật, và máy chủ chạy liên tục
        sẽ giữ lại mọi thiết bị từng gọi tới dù chúng đã rời đi từ lâu.

        Quét cả dict nên chỉ chạy giãn cách, không chạy mỗi lần quét.
        """
        if bay_gio - self._lan_don < self.reset_sau_giay:
            return
        self._lan_don = bay_gio

        da_roi = [
            d for d, t in self._lan_cuoi.items() if bay_gio - t > self.reset_sau_giay
        ]
        for d in da_roi:
            self.quen(d)

    def so_mau_dang_giu(self, device_id: str) -> int:
        return len(self._lich_su.get(device_id, ()))

    def quen(self, device_id: str) -> None:
        self._lich_su.pop(device_id, None)
        self._lan_cuoi.pop(device_id, None)
