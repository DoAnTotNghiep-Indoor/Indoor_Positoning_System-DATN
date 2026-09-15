"""FeatureMapper: ánh xạ BSSID sang vector đặc trưng theo feature_list.json.

Ánh xạ theo BSSID chứ không theo vị trí: CTK45 nhận mảng số trần nên gửi sai thứ
tự vẫn chạy trơn và ra toạ độ sai.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np

from backend.config import settings
from ml.config import RSSI_LON_NHAT, RSSI_NHO_NHAT


class ThieuArtifact(FileNotFoundError):
    """Thiếu tệp do pipeline sinh ra — kho vừa clone chưa có `*.pkl`."""

    def __init__(self, duong_dan: Path):
        super().__init__(
            f"Thiếu {duong_dan.name} trong {duong_dan.parent}. Chạy "
            f"`python -m ml.pipeline` rồi `python -m ml.train` để sinh lại."
        )


def doc_artifact(duong_dan: Path) -> Path:
    if not duong_dan.exists():
        raise ThieuArtifact(duong_dan)
    return duong_dan


class FeatureMapper:
    def __init__(self, model_dir: Path | None = None):
        thu_muc = Path(model_dir) if model_dir else settings.model_dir

        hop_dong = json.loads(
            doc_artifact(thu_muc / "feature_list.json").read_text(encoding="utf-8")
        )
        self.ap_columns: list[str] = hop_dong["ap_columns"]
        self.feature_count: int = hop_dong["feature_count"]
        self.missing_rssi_value: float = float(hop_dong["missing_rssi_value"])

        # Cùng ngưỡng bước 6 dùng để loại mẫu huấn luyện.
        self.min_ap_per_scan: int = int(hop_dong["min_ap_per_scan"])
        self.scaler = joblib.load(doc_artifact(thu_muc / "scaler.pkl"))

        # Hạ chữ thường ở máy chủ: BSSID của Android hoa hay thường tuỳ hãng.
        self._vi_tri = {b.lower(): i for i, b in enumerate(self.ap_columns)}

    def map_scan_to_vector(self, scan: list[dict]) -> np.ndarray:
        """Dựng vector từ [{"bssid", "rssi"}, ...]. BSSID lạ bỏ qua, thiếu thì điền
        missing_rssi_value, lặp thì lấy trung bình như `pivot_table` của bước 3."""
        tong = np.zeros(self.feature_count, dtype=float)
        dem = np.zeros(self.feature_count, dtype=int)
        for vi_tri, muc in enumerate(scan):
            try:
                bssid, rssi = muc["bssid"].lower(), float(muc["rssi"])
            except (KeyError, AttributeError, TypeError, ValueError) as e:
                # Nói rõ mục nào hỏng thay vì `KeyError: 'bssid'`.
                raise ValueError(
                    f"mục quét thứ {vi_tri} không đúng dạng "
                    f"{{'bssid': str, 'rssi': số}}: {muc!r}") from e

            i = self._vi_tri.get(bssid)
            if i is None:
                continue
            # Ngoài khoảng thì bỏ riêng số đọc ấy, không bỏ cả lần quét.
            if RSSI_NHO_NHAT <= rssi < RSSI_LON_NHAT:
                tong[i] += rssi
                dem[i] += 1

        vector = np.full(self.feature_count, self.missing_rssi_value, dtype=float)
        co = dem > 0
        vector[co] = tong[co] / dem[co]
        return vector

    def chuan_hoa(self, vector: np.ndarray) -> np.ndarray:
        """Áp scaler của tập train; ra ngoài [0, 1] là bình thường."""
        return self.scaler.transform(vector.reshape(1, -1))

    def dau_van(self) -> dict:
        """Dấu vân của hợp đồng, đối chiếu với model_metadata.json."""
        return {
            "missing_rssi_value": self.missing_rssi_value,
            "feature_count": self.feature_count,
            "ap_columns_sha1": hashlib.sha1(
                "\n".join(self.ap_columns).encode("utf-8")
            ).hexdigest(),
        }
