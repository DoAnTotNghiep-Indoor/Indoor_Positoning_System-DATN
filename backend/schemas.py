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
    """Một điểm tham chiếu kèm nhãn, đủ để hiển thị mà không cần tra thêm."""

    rp_id: str
    x: float
    y: float
    ten: str = ""
    nhom: str = ""


class DiemThamChieuDayDu(DiemThamChieu):
    """Thêm mô tả và thư mục ảnh — chỉ `GET /map` trả về, đường đi thì không."""

    mo_ta: str = ""

    # Đoạn dài lấy từ `information.dart` của CTK45: có số chỗ ngồi, số cửa, số
    # cầu thang. `mo_ta` một dòng dùng cho danh sách, đoạn này cho màn chi tiết.
    # Lối đi (cầu thang, hành lang) không có — CTK45 cố ý bỏ vì đó không phải
    # điểm đến.
    mo_ta_chi_tiet: str = ""

    thu_muc_anh: str = ""


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
    diem_tham_chieu: list[DiemThamChieuDayDu]
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


class BuocChiDan(BaseModel):
    """Một bước "đi thẳng / rẽ trái / rẽ phải" kèm số mét.

    Không có câu chữ dựng sẵn — xem lý do ở `DoThiDiLai.chi_dan`. `huong` là
    một trong: bat_dau, di_thang, chech_trai, chech_phai, re_trai, re_phai,
    quay_dau. `goc_do` dương là rẽ trái.
    """

    tu_rp: str
    den_rp: str
    den_ten: str = ""
    huong: str
    goc_do: float
    khoang_cach_m: float


class KetQuaChiDuong(BaseModel):
    tu: str
    den: str
    quang_duong_m: float
    so_chang: int
    duong_di: list[DiemThamChieu]

    # Các bước đã gộp chặng đi thẳng liên tiếp, nên thường ít hơn `so_chang`.
    chi_dan: list[BuocChiDan] = []
