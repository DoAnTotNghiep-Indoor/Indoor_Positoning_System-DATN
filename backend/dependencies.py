"""Những thứ dùng chung giữa các router.

Predictor và BoGop nạp một lần lúc khởi động rồi giữ ở cấp module: Predictor
phải trả giá chạy nóng khoảng 1.400 ms cho lần dự đoán đầu tiên (xem
prediction_service.py), còn BoGop phải nhớ các lần quét trước nên không thể
dựng mới mỗi lần.
"""

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
