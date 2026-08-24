"""Bước 4 — Ghép toạ độ thật (x, y) theo rp_id.

Bước quyết định cả đồ án: không có (x, y) thì chỉ phân lớp được điểm tham chiếu
chứ không hồi quy được toạ độ, tức mất luôn cải tiến chính so với đồ án cũ.

File thô KHÔNG chứa toạ độ cục bộ (GPS trong nhà gần như không đổi — đo được
biên độ dao động chỉ khoảng 22 m, vô dụng cho bài toán này). Toạ độ lấy từ
`data/reference/reference_points.csv`, nguồn gốc là Bảng 4 trang 46 đồ án CTK45.

Khác bản Colab: không im lặng bỏ qua khi thiếu toạ độ. Thiếu là phải nói rõ
thiếu ở đâu, rồi xử lý theo chính sách đã khai báo trong config.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml import config


def load_reference_points(csv_path: Path | str | None = None) -> pd.DataFrame:
    """Đọc bảng toạ độ điểm tham chiếu. Chỉ giữ ba cột rp_id, x, y."""
    path = Path(csv_path) if csv_path else config.REFERENCE_POINTS_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Chưa có bảng toạ độ: {path}\n"
            f"Không có file này thì không huấn luyện hồi quy (x, y) được.\n"
            f"Xem mẫu tại {config.REFERENCE_DIR / 'reference_points_template.csv'}"
        )

    # utf-8-sig để nuốt luôn BOM nếu file được sửa bằng Excel.
    rp = pd.read_csv(path, encoding="utf-8-sig")

    thieu = [c for c in ("rp_id", "x", "y") if c not in rp.columns]
    if thieu:
        raise ValueError(f"Bảng toạ độ thiếu cột {thieu}. Cần đủ: rp_id, x, y")

    rp = rp[["rp_id", "x", "y"]].copy()
    rp["x"] = pd.to_numeric(rp["x"], errors="coerce")
    rp["y"] = pd.to_numeric(rp["y"], errors="coerce")

    trung = rp["rp_id"].duplicated().sum()
    if trung:
        raise ValueError(f"Bảng toạ độ có {trung} rp_id trùng lặp — mỗi điểm chỉ được một dòng.")

    return rp


def attach_coordinates(
    fingerprint: pd.DataFrame,
    reference_points: pd.DataFrame | None = None,
    policy: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Ghép (x, y) vào bảng vân tay.

    policy="drop"  : bỏ mẫu chưa có toạ độ, pipeline chạy tiếp (mặc định)
    policy="error" : dừng lại — dùng khi đã đo đủ và muốn chặn thiếu sót
    """
    rp = reference_points if reference_points is not None else load_reference_points()
    policy = policy or config.MISSING_COORD_POLICY

    truoc = len(fingerprint)
    ket_qua = fingerprint.merge(rp, on="rp_id", how="left")

    thieu_mask = ket_qua["x"].isna() | ket_qua["y"].isna()
    rp_thieu = sorted(ket_qua.loc[thieu_mask, "rp_id"].unique())
    so_thieu = int(thieu_mask.sum())

    if so_thieu and policy == "error":
        raise ValueError(
            f"{so_thieu} lần quét chưa có toạ độ, thuộc các điểm: {rp_thieu}\n"
            f"Đo đạc thực địa rồi cập nhật {config.REFERENCE_POINTS_CSV}, "
            f"hoặc đặt MISSING_COORD_POLICY='drop' để tạm bỏ qua."
        )

    if so_thieu:
        ket_qua = ket_qua.loc[~thieu_mask].reset_index(drop=True)

    thong_ke = {
        "scan_truoc_khi_ghep": truoc,
        "scan_co_toa_do": len(ket_qua),
        "scan_bi_bo": so_thieu,
        "rp_chua_do": rp_thieu,
        "chinh_sach": policy,
    }
    return ket_qua, thong_ke
