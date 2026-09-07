"""FeatureMapper: ánh xạ BSSID sang vector đặc trưng theo feature_list.json.

Tầng này chặn đúng lỗi CTK45 mắc phải: backend nhận mảng số trần không kèm
BSSID rồi chỉ kiểm số lượng phần tử, nên client gửi đủ 36 giá trị nhưng sai
thứ tự thì mô hình vẫn chạy trơn và trả toạ độ sai hoàn toàn.

`artifacts/feature_list.json` là nguồn sự thật duy nhất về thứ tự cột; mọi phép
ánh xạ theo BSSID chứ không theo vị trí trong mảng, khoá bằng
tests/test_feature_mapper.py.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np

from backend.config import settings

# Khoảng RSSI có thể có thật, đơn vị dBm. Số đọc ngoài khoảng bị BỎ QUA y như
# một BSSID lạ, chứ không làm hỏng cả lần quét.
#
# Cần chặn vì `KhongDuAp` chỉ ĐẾM số BSSID khớp hợp đồng, không hỏi các con số
# có thể có thật không: đo trước khi chặn, 36 BSSID đúng kèm rssi = +1000 vẫn
# trả toạ độ với matched_ap = 36. Lọc chứ không từ chối, vì trình điều khiển
# WiFi Android thỉnh thoảng trả 0 hoặc số dương cho AP rất gần — và lọc xong
# thì lần quét toàn số bịa tự rơi về 0 AP khớp, `KhongDuAp` bắt nó với đúng mã
# `khong_du_ap` mà client đang bóc.
RSSI_NHO_NHAT = -100.0
RSSI_LON_NHAT = 0.0


class ThieuArtifact(FileNotFoundError):
    """Thiếu tệp do pipeline sinh ra.

    `.gitignore` chặn `artifacts/*.pkl` vì chúng nặng và sinh lại được, nên kho
    vừa clone về KHÔNG có scaler lẫn model. Không bắt ở đây thì người chạy chỉ
    thấy `FileNotFoundError` trỏ vào một đường dẫn.
    """

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

        # Số AP tối thiểu một lần quét phải bắt được — chính quy tắc đã dùng để
        # loại mẫu huấn luyện ở bước 6, nên lúc chạy thật và lúc huấn luyện chịu
        # chung một chuẩn.
        self.min_ap_per_scan: int = int(hop_dong["min_ap_per_scan"])
        self.scaler = joblib.load(doc_artifact(thu_muc / "scaler.pkl"))

        # Tra vị trí một lần lúc khởi động thay vì quét lại danh sách mỗi request.
        # Khoá hạ chữ thường: pipeline ghi feature_list.json bằng chữ thường, còn
        # `ScanResult.BSSID` của Android là chuỗi hoa hay thường tuỳ hãng. Chuẩn
        # hoá ở ĐÂY chứ không phó cho client — trước đây chỉ ứng dụng Flutter hạ
        # chữ, nên mọi client khác gửi đủ 36 BSSID đúng vẫn nhận 0 AP khớp kèm
        # lỗi `khong_du_ap`, tức báo sai hẳn nguyên nhân.
        self._vi_tri = {b.lower(): i for i, b in enumerate(self.ap_columns)}

    def map_scan_to_vector(self, scan: list[dict]) -> np.ndarray:
        """Dựng vector từ [{"bssid": "88:dc:...", "rssi": -67}, ...].

        BSSID lạ bị bỏ qua; BSSID có trong hợp đồng mà lần này không bắt được thì
        điền missing_rssi_value. BSSID lặp lại thì LẤY TRUNG BÌNH, đúng phép
        `pivot_table(aggfunc="mean")` của bước 3 — ghi đè theo thứ tự mảng thì
        cùng một lần quét gửi hai thứ tự cho ra hai toạ độ khác nhau.
        """
        tong = np.zeros(self.feature_count, dtype=float)
        dem = np.zeros(self.feature_count, dtype=int)
        for vi_tri, muc in enumerate(scan):
            try:
                bssid, rssi = muc["bssid"].lower(), float(muc["rssi"])
            except (KeyError, AttributeError, TypeError, ValueError) as e:
                # Hai lối vào đã có schema chặn, nhưng đây là hàm giữ hợp đồng dữ
                # liệu nên lỗi phải nói rõ mục nào hỏng thay vì ném `KeyError: 'bssid'`.
                # `AttributeError` bắt ca bssid không phải chuỗi, để nó cũng rơi vào
                # đúng câu lỗi này thay vì vỡ ở `.lower()`.
                raise ValueError(
                    f"mục quét thứ {vi_tri} không đúng dạng "
                    f"{{'bssid': str, 'rssi': số}}: {muc!r}") from e

            i = self._vi_tri.get(bssid)
            if i is None:
                continue
            if RSSI_NHO_NHAT <= rssi <= RSSI_LON_NHAT:
                tong[i] += rssi
                dem[i] += 1

        vector = np.full(self.feature_count, self.missing_rssi_value, dtype=float)
        co = dem > 0
        vector[co] = tong[co] / dem[co]
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
