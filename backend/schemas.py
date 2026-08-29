"""Hình dạng JSON của request và response.

Định dạng của /predict giữ đúng như tài liệu kế hoạch của nhóm: đây là hợp đồng
giữa model và frontend nên khoá cứng sớm để không phải sửa Dashboard nhiều lần.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class MucQuet(BaseModel):
    """Một AP bắt được trong lần quét.

    Bắt buộc kèm bssid chứ không nhận mảng số trần — xem lý do trong
    backend/services/preprocessing_service.py.
    """

    bssid: str
    rssi: float


class YeuCauDuDoan(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    scan: list[MucQuet]


class KetQuaDuDoan(BaseModel):
    x: float
    y: float
    x_smooth: float
    y_smooth: float
    model: str
    timestamp: datetime

    # Số AP trong lần quét khớp với hợp đồng dữ liệu. Thấp bất thường nghĩa là
    # client đang ở vùng phủ kém, hoặc hạ tầng WiFi đã đổi kể từ lúc thu dữ liệu.
    matched_ap: int
    scan_count: int
    latency_ms: float


class MucLichSu(BaseModel):
    luc: datetime
    x: float
    y: float
    x_gop: float
    y_gop: float
    so_ap_bat_duoc: int
    mo_hinh: str

    model_config = {"from_attributes": True}


class TrangThai(BaseModel):
    trang_thai: str
    mo_hinh: str
    so_dac_trung: int
    gia_tri_dien_thieu: float
    cua_so_gop: int


# --- Bản đồ và chỉ đường ---


class DiemThamChieu(BaseModel):
    rp_id: str
    x: float
    y: float


class PhamVi(BaseModel):
    x_min: float
    x_max: float
    y_min: float
    y_max: float


class ThongKeDoThi(BaseModel):
    so_diem: int
    so_canh: int
    canh_ngan_nhat_m: float
    canh_dai_nhat_m: float
    bac_trung_binh: float


class BanDo(BaseModel):
    """Toàn bộ dữ liệu không gian trong một response.

    `don_vi` luôn là "met" và trùng hệ với toạ độ /predict trả về. Client tự
    đổi sang khung vẽ của nó — sơ đồ hoạ tiết là việc riêng của từng client.
    """

    don_vi: str
    pham_vi: PhamVi
    diem_tham_chieu: list[DiemThamChieu]
    do_thi: ThongKeDoThi


class Canh(BaseModel):
    tu: str
    den: str
    khoang_cach_m: float


class DoThi(ThongKeDoThi):
    canh: list[Canh]


class YeuCauChiDuong(BaseModel):
    """Điểm đầu cho bằng rp_id, hoặc bằng toạ độ mét để hệ tự neo.

    Không có giá trị mặc định cho tu_x/tu_y. Bản trước để mặc định 0.0, mà
    RP02 nằm đúng tại (0, 0): client quên gửi điểm đầu vẫn nhận về một tuyến
    đường trông hợp lý xuất phát từ RP02, không một cảnh báo nào. Đúng họ lỗi
    mà cả dự án lấy làm điểm cải tiến so với CTK45 — nhận thiếu dữ liệu mà vẫn
    trả kết quả tự tin.
    """

    den_rp: str
    tu_rp: str | None = None
    tu_x: float | None = None
    tu_y: float | None = None

    @model_validator(mode="after")
    def _phai_co_diem_dau(self) -> "YeuCauChiDuong":
        if self.tu_rp is None and (self.tu_x is None or self.tu_y is None):
            raise ValueError("cần tu_rp, hoặc cả tu_x lẫn tu_y")
        return self


class KetQuaChiDuong(BaseModel):
    tu: str
    den: str
    quang_duong_m: float
    so_chang: int
    duong_di: list[DiemThamChieu]
