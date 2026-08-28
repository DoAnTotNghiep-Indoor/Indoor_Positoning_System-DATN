"""Hậu xử lý vị trí — gộp nhiều lần quét trước khi trả về toạ độ.

Xuất phát từ một quan sát trên tập test: các ca sai nặng gần như luôn là **một
lần quét dị thường lẻ loi**, không phải sai lệch có hệ thống. Ví dụ rõ nhất là
ba lần quét tại RP39 (22, 52) cho ra RP39, RP40 (cách 7 m) và RP11 (0, 18) —
tận đầu kia toà nhà.

Thiết bị quét WiFi mỗi 1-2 giây nên lúc chạy thật luôn có sẵn vài lần quét gần
nhau về thời gian. Gộp chúng lại loại được lần quét dị thường mà không cần thêm
dữ liệu huấn luyện nào.

Đo trên tập test, gộp 3 lần quét:

    một lần quét            2,56 m · lớn nhất 56,2 m · 12/39 điểm sai
    bình chọn đa số         1,52 m · lớn nhất 40,5 m ·  3/39 điểm sai
    trung vị toạ độ         0,73 m · lớn nhất 15,0 m ·  2/39 điểm sai
    đồng thuận không gian   0,73 m · lớn nhất 15,0 m ·  2/39 điểm sai

Bình chọn đa số kém hơn hẳn vì khi ba lần quét cho ba kết quả khác nhau thì
không có đa số nào cả, và việc xử lý hoà rơi vào ngẫu nhiên — đúng tình huống
của RP39. Hai cách còn lại đều dựa trên khoảng cách nên tự loại được điểm lạc.
"""

from __future__ import annotations

import numpy as np

# Ba lần quét là đủ để loại một lần dị thường mà vẫn giữ độ trễ thấp: thiết bị
# quét mỗi 1-2 giây nên cửa sổ 3 mẫu tương ứng 3-6 giây.
CUA_SO_MAC_DINH = 3


def trung_vi_toa_do(du_doan: np.ndarray) -> np.ndarray:
    return np.median(np.asarray(du_doan, dtype=float), axis=0)


def dong_thuan_khong_gian(du_doan: np.ndarray) -> np.ndarray:
    """Chọn dự đoán có tổng khoảng cách tới các dự đoán còn lại nhỏ nhất.

    Khác trung vị ở chỗ luôn trả về một trong các toạ độ đã dự đoán, nên kết quả
    luôn rơi đúng vào một điểm tham chiếu có thật. Với RP39: tổng khoảng cách của
    RP39 là 47,5 m, RP40 là 54 m, RP11 là 87,5 m — điểm lạc bị loại.
    """
    P = np.asarray(du_doan, dtype=float)
    if len(P) == 1:
        return P[0]
    tong = np.linalg.norm(P[:, None] - P[None], axis=2).sum(axis=1)
    return P[int(tong.argmin())]


CACH_GOP = {
    "trung_vi": trung_vi_toa_do,
    "dong_thuan": dong_thuan_khong_gian,
}


def gop(du_doan: np.ndarray, cach: str = "dong_thuan") -> np.ndarray:
    """Gộp một cửa sổ dự đoán thành một toạ độ."""
    return CACH_GOP[cach](np.atleast_2d(np.asarray(du_doan, dtype=float)))


def gop_cua_so_truot(
    du_doan: np.ndarray,
    cua_so: int = CUA_SO_MAC_DINH,
    cach: str = "dong_thuan",
) -> np.ndarray:
    """Áp dụng cho một chuỗi dự đoán theo thời gian.

    Mỗi thời điểm gộp `cua_so` dự đoán gần nhất. Những dự đoán đầu chuỗi dùng ít
    mẫu hơn thay vì bị bỏ, để hệ thống có toạ độ ngay từ lần quét đầu.
    """
    P = np.asarray(du_doan, dtype=float)
    return np.array([gop(P[max(0, i - cua_so + 1) : i + 1], cach) for i in range(len(P))])
