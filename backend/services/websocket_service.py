"""Các kết nối WebSocket đang mở: thiết bị gửi lần quét, dashboard chỉ xem."""

from __future__ import annotations

import asyncio

from fastapi import WebSocket

# Hạn gửi mỗi client: client kẹt không được giữ chân vòng phát quá một nhịp quét.
HAN_GUI_GIAY = 2.0


class ConnectionManager:
    def __init__(self) -> None:
        self._xem: set[WebSocket] = set()
        self._khoa = asyncio.Lock()
        self._dang_dong: set[asyncio.Task] = set()

    async def ket_noi(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._khoa:
            self._xem.add(ws)

    async def ngat(self, ws: WebSocket) -> None:
        async with self._khoa:
            self._xem.discard(ws)

    async def phat(self, du_lieu: dict, tru: WebSocket | None = None) -> None:
        """Gửi cho mọi client trừ `tru`; client rớt hoặc treo bị loại và đóng."""
        async with self._khoa:
            dang_mo = [ws for ws in self._xem if ws is not tru]

        # Song song: gửi lần lượt thì mỗi client treo cộng một hạn giờ vào /predict.
        async def gui(ws: WebSocket) -> WebSocket | None:
            try:
                await asyncio.wait_for(ws.send_json(du_lieu), HAN_GUI_GIAY)
            except Exception:
                return ws
            return None

        hong = [ws for ws in await asyncio.gather(*map(gui, dang_mo)) if ws is not None]

        if hong:
            async with self._khoa:
                self._xem.difference_update(hong)
            # Đóng hẳn để client tự nối lại thay vì treo ở "Đang kết nối".
            for ws in hong:
                t = asyncio.create_task(self._dong(ws))
                self._dang_dong.add(t)
                t.add_done_callback(self._dang_dong.discard)

    @staticmethod
    async def _dong(ws: WebSocket) -> None:
        try:
            await asyncio.wait_for(ws.close(code=1011), HAN_GUI_GIAY)
        except Exception:
            pass


manager = ConnectionManager()
