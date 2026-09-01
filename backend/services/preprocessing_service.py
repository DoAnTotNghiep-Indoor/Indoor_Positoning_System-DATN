"""FeatureMapper: ánh xạ BSSID sang vector đặc trưng theo feature_list.json.

Tầng này tồn tại để chặn đúng lỗi đồ án CTK45 mắc phải: backend nhận mảng số
trần không kèm BSSID rồi chỉ kiểm tra số lượng phần tử, nên client gửi đủ 36
giá trị nhưng sai thứ tự thì mô hình vẫn chạy trơn tru và trả toạ độ sai hoàn
toàn, không một cảnh báo nào.

Cách chặn: `artifacts/feature_list.json` là nguồn sự thật duy nhất về thứ tự
cột, và mọi phép ánh xạ đều theo BSSID chứ không bao giờ theo vị trí trong
mảng. Hợp đồng này được khoá bằng tests/test_feature_mapper.py.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np

from backend.config import settings


class FeatureMapper:
    def __init__(self, model_dir: Path | None = None):
        thu_muc = Path(model_dir) if model_dir else settings.model_dir

        hop_dong = json.loads(
            (thu_muc / "feature_list.json").read_text(encoding="utf-8")
        )
        self.ap_columns: list[str] = hop_dong["ap_columns"]
        self.feature_count: int = hop_dong["feature_count"]
        self.missing_rssi_value: float = float(hop_dong["missing_rssi_value"])

        # Số AP tối thiểu một lần quét phải bắt được. Chính quy tắc đã dùng để
        # loại mẫu huấn luyện ở bước 6 của pipeline, nên lúc chạy thật và lúc
        # huấn luyện chịu chung một chuẩn.
        self.min_ap_per_scan: int = int(hop_dong["min_ap_per_scan"])
        self.scaler = joblib.load(thu_muc / "scaler.pkl")

        # Tra vị trí một lần lúc khởi động thay vì quét lại danh sách mỗi request.
        self._vi_tri = {b: i for i, b in enumerate(self.ap_columns)}

    def map_scan_to_vector(self, scan: list[dict]) -> np.ndarray:
        """Dựng vector từ [{"bssid": "88:dc:...", "rssi": -67}, ...].

        BSSID lạ (AP mới lắp, hotspot điện thoại) bị bỏ qua; BSSID có trong hợp
        đồng nhưng lần này không bắt được thì điền missing_rssi_value.
        """
        vector = np.full(self.feature_count, self.missing_rssi_value, dtype=float)
        for muc in scan:
            i = self._vi_tri.get(muc["bssid"])
            if i is not None:
                vector[i] = float(muc["rssi"])
        return vector

    def chuan_hoa(self, vector: np.ndarray) -> np.ndarray:
        """Áp scaler đã học lúc huấn luyện.

        Giá trị ra có thể nằm ngoài [0, 1] và đó không phải lỗi: scaler chỉ fit
        trên tập train nên lần quét mạnh hơn mọi mẫu train sẽ vượt 1.
        """
        return self.scaler.transform(vector.reshape(1, -1))

    def dau_van(self) -> dict:
        """Dấu vân của hợp đồng, để đối chiếu với model_metadata.json.

        Lệch nghĩa là model và hợp đồng sinh ra từ hai lần chạy pipeline khác
        nhau — dự đoán sẽ sai âm thầm chứ không báo lỗi.
        """
        return {
            "missing_rssi_value": self.missing_rssi_value,
            "feature_count": self.feature_count,
            "ap_columns_sha1": hashlib.sha1(
                "\n".join(self.ap_columns).encode("utf-8")
            ).hexdigest(),
        }
