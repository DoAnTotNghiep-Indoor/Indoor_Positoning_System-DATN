"""Giao thức đánh giá thứ ba: học trên một đợt đo, kiểm trên đợt kia.

    python -m ml.khac_dot

Đợt A là dữ liệu thô của một máy (Samsung SM-S908E), đợt B là phần của ba máy còn lại
trong dữ liệu CTK45 (xem data/raw/ctk45_xu_ly/README.md). Hai đợt có cùng 40 điểm tham
chiếu nhưng khác máy, khác thời điểm đo — gần với lúc chạy thật nhất trong ba giao thức:
người dùng đứng ở chỗ đã khảo sát nhưng cầm máy khác, vào hôm khác.

Mỗi chiều làm lại bước 5-10 chỉ trên đợt dùng để học; tham số mô hình lấy từ lần huấn
luyện (`model_metadata.json`). Sai số đo bằng đơn vị lưới như các bảng khác, in kèm mét.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from ml import config, evaluate
from ml import models as goi_mo_hinh
from ml import preprocess as pre
from ml.danh_gia_cheo import _luoi_da_dung, _tham_so, nap_bang_rong

MET_MOI_DON_VI = 0.3508
HAI_CHIEU = (("A", "B"), ("B", "A"))


def chuan_bi_chieu(fp: pd.DataFrame, ap_cols: list[str], dot_hoc: str, dot_thu: str) -> tuple:
    """(X_học, Y_học, X_thử, Y_thử) đã chuẩn hoá, mọi tham số học trên đợt `dot_hoc`."""
    hoc, thu = fp[fp["dot"] == dot_hoc], fp[fp["dot"] == dot_thu]
    hoc, ap, _ = pre.filter_access_points(hoc, ap_cols, tinh_tren=hoc)
    thu = thu[[c for c in thu.columns if c not in ap_cols] + ap]
    hoc, _ = pre.filter_sparse_scans(hoc, ap)
    thu, _ = pre.filter_sparse_scans(thu, ap)
    gt = pre.compute_missing_value(hoc, ap)
    hoc, _, _ = pre.fill_missing(hoc, ap, missing_value=gt)
    thu, _, _ = pre.fill_missing(thu, ap, missing_value=gt)
    hoc, _ = pre.hampel_filter(hoc, ap, gia_tri_dien=gt)
    can = MinMaxScaler().fit(hoc[ap].to_numpy(float))
    return (can.transform(hoc[ap].to_numpy(float)), hoc[config.TARGET_COLS].to_numpy(float),
            can.transform(thu[ap].to_numpy(float)), thu[config.TARGET_COLS].to_numpy(float))


def run(ten_mo_hinh: list[str] | None = None) -> pd.DataFrame:
    luoi = _luoi_da_dung()
    if luoi not in (None, "day_du"):
        raise SystemExit(f"Tham số lấy từ lưới '{luoi}', không phải lưới đầy đủ — "
                         f"chạy `python -m ml.train` trước.")

    fp, ap_cols = nap_bang_rong()
    if set(fp["dot"]) != {"A", "B"}:
        raise SystemExit("Cần cả hai đợt A và B — kiểm `GOP_DOT_B` trong ml/config.py.")
    chieu = {f"{h}→{t}": chuan_bi_chieu(fp, ap_cols, h, t) for h, t in HAI_CHIEU}
    print("Khác đợt đo: " + " · ".join(f"{k} học {len(v[0])}, kiểm {len(v[2])}"
                                        for k, v in chieu.items()))

    chon = goi_mo_hinh.DANH_SACH
    if ten_mo_hinh:
        muon = {t.lower() for t in ten_mo_hinh}
        chon = [m for m in chon if m.__name__.rsplit(".", 1)[-1].lower() in muon]

    dong = []
    for mo_dun in chon:
        khoa = mo_dun.__name__.rsplit(".", 1)[-1]
        tham_so = _tham_so(khoa, mo_dun)
        hang = {"mo_hinh": mo_dun.TEN}
        cac_loi = []
        for ten_chieu, (Xh, Yh, Xt, Yt) in chieu.items():
            loi = evaluate.khoang_cach_loi(Yt, mo_dun.build(**tham_so).fit(Xh, Yh).predict(Xt))
            hang[f"loi_trung_binh_{ten_chieu}"] = float(loi.mean())
            hang[f"loi_trung_vi_{ten_chieu}"] = float(np.median(loi))
            cac_loi.append(loi.mean())
        # Trung bình hai chiều, mỗi chiều nặng như nhau dù số lần quét kiểm khác nhau.
        hang["loi_trung_binh"] = float(np.mean(cac_loi))
        dong.append(hang)
        print(f"  {mo_dun.TEN:36s} " + "  ".join(
            f"{k} {hang[f'loi_trung_binh_{k}'] * MET_MOI_DON_VI:5.2f} m" for k in chieu)
            + f"  · TB {hang['loi_trung_binh'] * MET_MOI_DON_VI:5.2f} m")

    bang = pd.DataFrame(dong).sort_values("loi_trung_binh").reset_index(drop=True)
    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "model_comparison_khac_dot.csv", index=False)
    return bang


if __name__ == "__main__":
    import argparse

    bo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    bo.add_argument("--mo-hinh", nargs="*", default=None, help="chỉ chạy các mô hình này")
    warnings.filterwarnings("ignore")
    run(bo.parse_args().mo_hinh)
