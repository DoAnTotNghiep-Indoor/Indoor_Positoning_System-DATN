"""ConnectionManager: quản lý các kết nối WebSocket đang mở.

Hai nhóm client khác nhau dùng chung một kênh:

- **Thiết bị được định vị** gửi lần quét lên và nhận lại toạ độ của chính nó.
- **Dashboard** chỉ xem, không gửi gì, nhận mọi toạ độ để vẽ marker.

Đồ án CTK45 chỉ có REST nên client muốn cập nhật vị trí liên tục phải polling —
tốn pin, tốn băng thông, độ trễ cao. Đây là chỗ khắc phục.
"""

from __future__ import annotations

import asyncio

from fastapi import WebSocket

# Hạn gửi cho mỗi client. Đủ rộng cho một kết nối chậm bình thường, đủ ngắn để
# một client kẹt không giữ chân cả vòng phát quá một nhịp quét.
HAN_GUI_GIAY = 2.0


class ConnectionManager:
    def __init__(self) -> None:
        self._xem: set[WebSocket] = set()
        self._khoa = asyncio.Lock()

    async def ket_noi(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._khoa:
            self._xem.add(ws)

    async def ngat(self, ws: WebSocket) -> None:
        async with self._khoa:
            self._xem.discard(ws)

    async def phat(self, du_lieu: dict, tru: WebSocket | None = None) -> None:
        """Gửi cho mọi client đang xem, trừ chính client vừa gửi lần quét.

        Client nào rớt hoặc treo thì bỏ khỏi danh sách chứ không để vòng lặp
        vỡ hay đứng lại.
        """
        async with self._khoa:
            dang_mo = list(self._xem)

        hong = []
        for ws in dang_mo:
            if ws is tru:
                continue
            try:
                # Có hạn thời gian chứ không await trần: một client còn mở
                # nhưng không đọc nữa sẽ làm bộ đệm gửi đầy, và `send_json`
                # treo vô hạn — lúc đó MỘT dashboard kẹt đóng băng luồng vị
                # trí của mọi thiết bị. Quá hạn thì coi như đã rớt.
                await asyncio.wait_for(ws.send_json(du_lieu), HAN_GUI_GIAY)
            except Exception:
                hong.append(ws)

        if hong:
            async with self._khoa:
                self._xem.difference_update(hong)


manager = ConnectionManager()
