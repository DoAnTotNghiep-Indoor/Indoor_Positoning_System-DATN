"""Predictor: nạp mô hình một lần lúc khởi động rồi dự đoán toạ độ."""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib

from backend.config import settings
from backend.services.preprocessing_service import (FeatureMapper,
                                                    doc_artifact)


class HopDongLech(RuntimeError):
    """Model và feature_list.json sinh ra từ hai lần chạy pipeline khác nhau."""


class KhongDuAp(ValueError):
    """Quá ít AP quen để định vị. Mô hình vẫn trả toạ độ cho vector toàn giá trị
    điền: ngoài thư viện, khớp 0 AP, nó vẫn báo đang ở RP01."""

    def __init__(self, so_ap: int, toi_thieu: int):
        super().__init__(
            f"Chỉ khớp {so_ap} access point, cần ít nhất {toi_thieu} để định vị"
        )
        self.so_ap = so_ap
        self.toi_thieu = toi_thieu


class Predictor:
    def __init__(self, model_dir: Path | None = None):
        thu_muc = Path(model_dir) if model_dir else settings.model_dir

        self.mapper = FeatureMapper(thu_muc)
        metadata = json.loads(
            doc_artifact(thu_muc / "model_metadata.json").read_text(encoding="utf-8")
        )

        # Lệch hợp đồng không làm sập gì, chỉ làm mọi toạ độ sai âm thầm.
        cua_model = metadata["hop_dong_du_lieu"]
        cua_hop_dong = self.mapper.dau_van()
        if cua_model != cua_hop_dong:
            raise HopDongLech(
                f"model_metadata.json {cua_model} != feature_list.json {cua_hop_dong}. "
                f"Chạy lại `python -m ml.pipeline` rồi `python -m ml.train`."
            )

        self.ten_mo_hinh: str = metadata["mo_hinh_active"]
        self.model = joblib.load(doc_artifact(thu_muc / metadata["file_active"]))

        # Chạy nóng: lần đầu ~1.400 ms, các lần sau 0,3 ms.
        self.du_doan([])

    @property
    def so_ap_toi_thieu(self) -> int:
        return self.mapper.min_ap_per_scan

    def du_doan(self, scan: list[dict]) -> tuple[float, float, int, float]:
        """(x, y, số AP khớp, độ trễ ms). Không tự chặn khi thiếu AP: chạy nóng gọi
        với danh sách rỗng, việc chặn nằm ở `_mot_lan_quet`."""
        bat_dau = time.perf_counter()

        vector = self.mapper.map_scan_to_vector(scan)
        so_khop = int((vector != self.mapper.missing_rssi_value).sum())
        x, y = self.model.predict(self.mapper.chuan_hoa(vector))[0]

        do_tre = (time.perf_counter() - bat_dau) * 1000
        return float(x), float(y), so_khop, do_tre
