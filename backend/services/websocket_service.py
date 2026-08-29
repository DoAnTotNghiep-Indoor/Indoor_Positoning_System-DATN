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

        Client nào rớt giữa chừng thì bỏ khỏi danh sách chứ không để vòng lặp
        vỡ — một dashboard đóng tab không được làm dừng cả kênh.
        """
        async with self._khoa:
            dang_mo = list(self._xem)

        hong = []
        for ws in dang_mo:
            if ws is tru:
                continue
            try:
                await ws.send_json(du_lieu)
            except Exception:
                hong.append(ws)

        if hong:
            async with self._khoa:
                self._xem.difference_update(hong)


manager = ConnectionManager()
