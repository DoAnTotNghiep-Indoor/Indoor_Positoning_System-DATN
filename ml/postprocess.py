"""Hậu xử lý vị trí — gộp vài lần quét gần nhau trước khi trả toạ độ.

Ca sai nặng thường là MỘT lần quét lạc lẻ loi nên gộp vài lần quét là đủ để
loại. Số đo từng cách gộp nằm ở `hau_xu_ly_gop` trong model_metadata.json.
"""

from __future__ import annotations

import numpy as np

# Ba lần quét là đủ để loại một lần dị thường mà vẫn giữ độ trễ thấp: thiết bị
# quét mỗi 1-2 giây nên cửa sổ 3 mẫu tương ứng 3-6 giây.
CUA_SO_MAC_DINH = 3


def trung_vi_toa_do(du_doan: np.ndarray) -> np.ndarray:
    return np.median(np.asarray(du_doan, dtype=float), axis=0)


def dong_thuan_khong_gian(du_doan: np.ndarray) -> np.ndarray:
    """Dự đoán có tổng khoảng cách tới các dự đoán còn lại nhỏ nhất.

    Hoà thì lấy dự đoán MỚI nhất: đo ngoài phần trên train+val theo thứ tự thời
    gian, cửa sổ 3, cả năm mô hình đều tốt hơn lấy cái cũ (kNN vân tay 1,18 →
    0,78 m).
    """
    P = np.asarray(du_doan, dtype=float)
    tong = np.linalg.norm(P[:, None] - P[None], axis=2).sum(axis=1)
    return P[len(P) - 1 - int(tong[::-1].argmin())]


CACH_GOP = {
    "trung_vi": trung_vi_toa_do,
    "dong_thuan": dong_thuan_khong_gian,
}


def gop(du_doan: np.ndarray, cach: str = "dong_thuan") -> np.ndarray:
    """Gộp một cửa sổ dự đoán thành một toạ độ."""
    P = np.atleast_2d(np.asarray(du_doan, dtype=float))
    if len(P) == 0:
        # `dong_thuan` để lọt cửa sổ rỗng xuống tận `argmin` và báo "attempt to get
        # argmin of an empty sequence" — không ai lần ra được là gọi sai.
        raise ValueError("cửa sổ gộp rỗng: cần ít nhất một dự đoán")
    if cach not in CACH_GOP:
        raise ValueError(
            f"cách gộp '{cach}' không có; chọn một trong {sorted(CACH_GOP)}")
    return CACH_GOP[cach](P)


def gop_cua_so_truot(
    du_doan: np.ndarray,
    cua_so: int = CUA_SO_MAC_DINH,
    cach: str = "dong_thuan",
) -> np.ndarray:
    """Áp dụng cho một chuỗi dự đoán theo thời gian. Mỗi thời điểm gộp `cua_so` dự
    đoán gần nhất; những dự đoán đầu chuỗi dùng ít mẫu hơn thay vì bị bỏ, để hệ
    thống có toạ độ ngay từ lần quét đầu.
    """
    P = np.asarray(du_doan, dtype=float)
    return np.array([gop(P[max(0, i - cua_so + 1) : i + 1], cach) for i in range(len(P))])
