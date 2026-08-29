"""Predictor: nạp mô hình một lần lúc khởi động rồi dự đoán toạ độ.

Nạp một lần chứ không mỗi request. Mô hình đang phục vụ là fingerprint_knn,
chỉ 198 KB, nên chi phí thật không nằm ở đọc đĩa mà ở lần dự đoán ĐẦU TIÊN:
sklearn nạp muộn phần tính khoảng cách nên lần đó tốn khoảng 1.400 ms, các lần
sau chỉ 0,3 ms. Dựng lại Predictor mỗi request là mỗi request lãnh trọn con số
đó — vượt hẳn ngân sách 200 ms của yêu cầu phi chức năng.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib

from backend.config import settings
from backend.services.preprocessing_service import FeatureMapper


class HopDongLech(RuntimeError):
    """Model và feature_list.json sinh ra từ hai lần chạy pipeline khác nhau."""


class Predictor:
    def __init__(self, model_dir: Path | None = None):
        thu_muc = Path(model_dir) if model_dir else settings.model_dir

        self.mapper = FeatureMapper(thu_muc)
        metadata = json.loads(
            (thu_muc / "model_metadata.json").read_text(encoding="utf-8")
        )

        # Đối chiếu dấu vân trước khi nạp model. Đây là chỗ duy nhất trong
        # backend còn giữ lại một phép kiểm bắt buộc: lệch hợp đồng không làm
        # chương trình sập, nó chỉ làm mọi toạ độ sai mà không ai biết.
        cua_model = metadata["hop_dong_du_lieu"]
        cua_hop_dong = self.mapper.dau_van()
        if cua_model != cua_hop_dong:
            raise HopDongLech(
                f"model_metadata.json {cua_model} != feature_list.json {cua_hop_dong}. "
                f"Chạy lại `python -m ml.pipeline` rồi `python -m ml.train`."
            )

        self.ten_mo_hinh: str = metadata["mo_hinh_active"]
        self.model = joblib.load(thu_muc / metadata["file_active"])

        # Chạy nóng ngay tại đây. Lần predict đầu tiên tốn khoảng 1.400 ms vì
        # sklearn nạp muộn phần tính khoảng cách, các lần sau chỉ 0,3 ms. Không
        # chạy nóng thì đúng request đầu của người dùng lãnh trọn con số đó —
        # vượt hẳn ngưỡng 200 ms của yêu cầu phi chức năng.
        self.du_doan([])

    def du_doan(self, scan: list[dict]) -> tuple[float, float, int, float]:
        """Trả về (x, y, số AP khớp hợp đồng, độ trễ mili giây)."""
        bat_dau = time.perf_counter()

        vector = self.mapper.map_scan_to_vector(scan)
        so_khop = int((vector != self.mapper.missing_rssi_value).sum())
        x, y = self.model.predict(self.mapper.chuan_hoa(vector))[0]

        do_tre = (time.perf_counter() - bat_dau) * 1000
        return float(x), float(y), so_khop, do_tre
