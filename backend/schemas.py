"""Hình dạng JSON của request và response — hợp đồng với Dashboard và ứng dụng."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class MucQuet(BaseModel):
    """Một AP trong lần quét. Kèm bssid chứ không nhận mảng số trần như CTK45."""

    bssid: str = Field(min_length=1, max_length=64)

    # Không chặn khoảng ở đây: một số đọc lỗi không được làm hỏng cả lần quét,
    # `FeatureMapper` bỏ riêng số đó.
    rssi: float


class YeuCauDuDoan(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)

    # Điện thoại thật thấy vài chục AP; chặn gói rác cỡ 200.000 mục.
    scan: list[MucQuet] = Field(max_length=512)


class KetQuaDuDoan(BaseModel):
    # Khai để REST trả cùng hình dạng với WS; pydantic bỏ trường không khai.
    device_id: str

    x: float
    y: float
    x_smooth: float
    y_smooth: float
    model: str
    timestamp: datetime

    # Số AP khớp hợp đồng; thấp bất thường là vùng phủ kém hoặc AP đã đổi.
    matched_ap: int
    scan_count: int
    latency_ms: float


class MucLichSu(BaseModel):
    device_id: str
    luc: datetime
    x: float
    y: float
    x_gop: float
    y_gop: float
    so_ap_bat_duoc: int
    mo_hinh: str
    do_tre_ms: float

    model_config = {"from_attributes": True}


class TrangThai(BaseModel):
    trang_thai: str
    mo_hinh: str
    so_dac_trung: int
    gia_tri_dien_thieu: float
    cua_so_gop: int
    websocket: bool


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

    # Đoạn dài từ `information.dart` của CTK45 cho màn chi tiết; lối đi không có.
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
    """Toàn bộ dữ liệu không gian. Toạ độ theo đơn vị lưới, cùng hệ /predict; nhân
    `met_moi_don_vi` ra mét."""

    don_vi: str
    met_moi_don_vi: float = 1.0
    pham_vi: PhamVi
    diem_tham_chieu: list[DiemThamChieuDayDu]
    do_thi: ThongKeDoThi


class Canh(BaseModel):
    tu: str
    den: str
    khoang_cach_m: float

    # True: cạnh nối tay vì Map.png không vẽ cửa, chưa đối chiếu thực địa — client
    # phải vẽ khác cạnh đo được.
    cua_gia_dinh: bool = False


class DoThi(ThongKeDoThi):
    canh: list[Canh]


class YeuCauChiDuong(BaseModel):
    """Điểm đầu bằng rp_id hoặc toạ độ lưới; đích bằng rp_id hoặc tên khu vực.

    tu_x/tu_y không mặc định 0.0: RP02 nằm đúng (0, 0), quên gửi vẫn ra tuyến.
    """

    den_rp: str | None = Field(default=None, min_length=1, max_length=64)
    den_nhom: str | None = Field(default=None, min_length=1, max_length=64)
    tu_rp: str | None = Field(default=None, max_length=64)
    # `1e999` là JSON hợp lệ, đọc ra inf.
    tu_x: float | None = Field(default=None, allow_inf_nan=False)
    tu_y: float | None = Field(default=None, allow_inf_nan=False)
    thuat_toan: Literal["a_sao", "dijkstra"] = "a_sao"

    @field_validator("tu_rp", "den_rp", "den_nhom", mode="after")
    @classmethod
    def _cat_khoang_trang(cls, v: str | None) -> str | None:
        """Chuỗi rỗng coi như không gửi, để `_phai_co_diem_dau` bắt được."""
        return v.strip() or None if v is not None else None

    @model_validator(mode="after")
    def _phai_co_diem_dau(self) -> "YeuCauChiDuong":
        if self.tu_rp is None and (self.tu_x is None or self.tu_y is None):
            raise ValueError("cần tu_rp, hoặc cả tu_x lẫn tu_y")
        if (self.den_rp is None) == (self.den_nhom is None):
            raise ValueError("cần đúng một trong den_rp và den_nhom")
        return self


class BuocChiDan(BaseModel):
    """Một bước chỉ đường. `huong` là mã: bat_dau, di_thang, chech_trai,
    chech_phai, re_trai, re_phai, quay_dau; `goc_do` dương là rẽ trái."""

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
    thuat_toan: str = "a_sao"
    so_nut_mo: int = 0
