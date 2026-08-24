"""Bước 8 — Lọc nhiễu RSSI bằng Hampel filter (dựa trên MAD).

Với mỗi AP, trong từng nhóm cùng rp_id, giá trị lệch quá `k * MAD` so với trung
vị bị thay bằng chính trung vị đó. Cách này giảm nhiễu tức thời (đa đường, che
khuất, người đi ngang) mà KHÔNG xoá mẫu — quan trọng khi mỗi điểm tham chiếu chỉ
có khoảng 20 lần quét.

Hai điểm khác bản Colab:

1. Vector hoá toàn bộ. Bản cũ lặp Python qua từng cột rồi gọi `groupby.transform`
   36 lần. Ở đây tính một lần cho cả ma trận.

2. Mặc định chỉ chạy trên tập train, SAU khi đã chia tập. Xem giải thích tại
   `config.HAMPEL_ON_TRAIN_ONLY` — tóm tắt: trung vị tính trên cả mẫu test là
   một dạng rò rỉ dữ liệu, và backend lúc chạy thật cũng không thể lọc Hampel vì
   nó chỉ nhận một lần quét và không biết rp_id.
"""

from __future__ import annotations

import pandas as pd

from ml import config


def hampel_filter(
    df: pd.DataFrame,
    ap_cols: list[str],
    group_col: str = "rp_id",
    k: float | None = None,
) -> tuple[pd.DataFrame, int]:
    """Thay giá trị ngoại lai bằng trung vị nhóm.

    Trả về (bảng đã lọc, số ô bị thay).
    """
    he_so = k if k is not None else config.HAMPEL_K

    gia_tri = df[ap_cols]
    nhom = df[group_col]

    trung_vi = gia_tri.groupby(nhom).transform("median")
    do_lech = (gia_tri - trung_vi).abs()
    mad = do_lech.groupby(nhom).transform("median") * config.MAD_SCALE

    # mad == 0 nghĩa là quá nửa số mẫu trong nhóm giống hệt nhau; lúc đó ngưỡng
    # bằng 0 sẽ đánh dấu nhầm mọi giá trị khác biệt dù nhỏ, nên bỏ qua nhóm đó.
    ngoai_lai = (mad > 0) & (do_lech > he_so * mad)

    ket_qua = df.copy()
    ket_qua[ap_cols] = gia_tri.where(~ngoai_lai, trung_vi)

    return ket_qua, int(ngoai_lai.to_numpy().sum())
