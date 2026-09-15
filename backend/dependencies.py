"""Đối tượng dùng chung, dựng một lần lúc khởi động: Predictor tốn ~1.400 ms
chạy nóng, BoGop phải nhớ các lần quét trước."""

from __future__ import annotations

from backend.config import settings
from backend.services.prediction_service import Predictor
from backend.services.routing_service import DoThiDiLai
from backend.services.smoothing_service import BoGop

_predictor: Predictor | None = None
_bo_gop: BoGop | None = None
_do_thi: DoThiDiLai | None = None


def khoi_dong() -> None:
    global _predictor, _bo_gop, _do_thi
    _predictor = Predictor()
    _do_thi = DoThiDiLai()
    _bo_gop = BoGop(
        cua_so=settings.cua_so_gop,
        reset_sau_giay=settings.reset_after_seconds,
    )


def lay_predictor() -> Predictor:
    return _predictor


def lay_bo_gop() -> BoGop:
    return _bo_gop


def lay_do_thi() -> DoThiDiLai:
    return _do_thi
