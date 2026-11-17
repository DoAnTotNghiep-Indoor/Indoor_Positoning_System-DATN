"""Predictor: nạp mô hình một lần lúc khởi động rồi dự đoán toạ độ."""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np

from backend.config import settings
from backend.services.preprocessing_service import (FeatureMapper,
                                                    doc_artifact)
from ml import postprocess


class HopDongLech(RuntimeError):
    """Model và feature_list.json sinh ra từ hai lần chạy pipeline khác nhau."""


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
        self.dau_ra, self.ham_gop = postprocess.cach_gop(self.model)

        # Chạy nóng: lần đầu chậm hơn hẳn các lần sau.
        self.du_doan([])

    @property
    def so_ap_toi_thieu(self) -> int:
        return self.mapper.min_ap_per_scan

    def du_doan(self, scan: list[dict]) -> tuple[float, float, np.ndarray, int, float]:
        """(x, y, đầu ra để `BoGop` gộp, số AP khớp, độ trễ ms). Không tự chặn khi
        thiếu AP — mô hình vẫn trả toạ độ cho vector toàn giá trị điền, nên
        `/predict` phải chặn."""
        bat_dau = time.perf_counter()

        vector = self.mapper.map_scan_to_vector(scan)
        so_khop = int((vector != self.mapper.missing_rssi_value).sum())
        d = self.dau_ra(self.mapper.chuan_hoa(vector))[0]
        x, y = self.ham_gop(d[None])

        do_tre = (time.perf_counter() - bat_dau) * 1000
        return float(x), float(y), d, so_khop, do_tre
