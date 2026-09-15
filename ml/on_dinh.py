"""Độ ổn định của bảng so sánh: chia lại nhiều seed, kèm khoảng tin cậy.

    python -m ml.on_dinh

Bảng chính chỉ là MỘT cách chia (seed 42). Ở đây chia lại với nhiều seed, làm
lại bước 5-10 cho từng lần chia, giữ nguyên tham số đã chọn lúc huấn luyện, rồi
đo trên tập test của chính lần chia đó. Khoảng tin cậy 95% là bootstrap trên
tập test seed 42 — hai khoảng chồng nhau thì chưa đủ căn cứ nói mô hình nào hơn.
"""

from __future__ import annotations

import json
import warnings

import joblib
import numpy as np
import pandas as pd

from ml import config, evaluate
from ml import models as goi_mo_hinh
from ml import preprocess as pre
from ml.danh_gia_cheo import _luoi_da_dung, _tham_so, nap_bang_rong

SO_SEED = 10
SO_LAN_BOOTSTRAP = 5000


def chia_lai(fp: pd.DataFrame, ap_cols: list[str], seed: int) -> tuple[pd.DataFrame, list[str]]:
    """Bước 9 với seed khác rồi bước 5-10, như `ml.pipeline`."""
    goc = config.RANDOM_STATE
    config.RANDOM_STATE = seed
    try:
        d, _ = pre.split_dataset(fp)
    finally:
        config.RANDOM_STATE = goc
    la = d["split"] == "train"
    d, ap, _ = pre.filter_access_points(d, ap_cols, tinh_tren=d[la])
    d, _ = pre.filter_sparse_scans(d, ap)
    la = d["split"] == "train"
    gt = pre.compute_missing_value(d[la], ap)
    d, _, _ = pre.fill_missing(d, ap, missing_value=gt)
    loc, _ = pre.hampel_filter(d[la], ap, gia_tri_dien=gt)
    d = pd.concat([loc, d[~la]], ignore_index=True)
    d, _, _ = pre.scale_dataset(d, ap)
    return d, ap


def khoang_tin_cay(loi: np.ndarray, so_lan: int = SO_LAN_BOOTSTRAP) -> tuple[float, float]:
    loi = np.asarray(loi, dtype=float)
    tb = loi[np.random.default_rng(0).integers(0, len(loi), (so_lan, len(loi)))].mean(axis=1)
    return float(np.percentile(tb, 2.5)), float(np.percentile(tb, 97.5))


def run(so_seed: int = SO_SEED, ten_mo_hinh: list[str] | None = None,
        cho_phep_luoi_rut_gon: bool = False) -> pd.DataFrame:
    luoi = _luoi_da_dung()
    if luoi not in (None, "day_du") and not cho_phep_luoi_rut_gon:
        raise SystemExit(f"Tham số lấy từ lưới '{luoi}', không phải lưới đầy đủ — "
                         f"chạy `python -m ml.train` trước.")

    chon = goi_mo_hinh.DANH_SACH
    if ten_mo_hinh:
        muon = {t.lower() for t in ten_mo_hinh}
        chon = [m for m in chon if m.__name__.rsplit(".", 1)[-1] in muon or m.TEN.lower() in muon]
    khoa = {m.TEN: m.__name__.rsplit(".", 1)[-1] for m in chon}

    fp, ap_cols = nap_bang_rong()
    theo_seed = {m.TEN: [] for m in chon}
    for seed in range(so_seed):
        d, ap = chia_lai(fp, ap_cols, seed)
        hoc, thu = d[d["split"] != "test"], d[d["split"] == "test"]
        for m in chon:
            mo = m.build(**_tham_so(khoa[m.TEN], m)).fit(
                hoc[ap].to_numpy(float), hoc[config.TARGET_COLS].to_numpy(float))
            theo_seed[m.TEN].append(float(evaluate.khoang_cach_loi(
                thu[config.TARGET_COLS].to_numpy(float), mo.predict(thu[ap].to_numpy(float))).mean()))

    ap42 = json.loads((config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8"))["ap_columns"]
    te = pd.read_csv(config.SPLITS_DIR / "test.csv")
    hang = pd.DataFrame(theo_seed).rank(axis=1)
    dong = []
    for m in chon:
        loi42 = evaluate.khoang_cach_loi(
            te[config.TARGET_COLS].to_numpy(float),
            joblib.load(config.ARTIFACTS_DIR / f"model_{khoa[m.TEN]}.pkl").predict(te[ap42].to_numpy(float)))
        thap, cao = khoang_tin_cay(loi42)
        s = np.array(theo_seed[m.TEN])
        dong.append({"mo_hinh": m.TEN, "seed_42": float(loi42.mean()), "ci95_thap": thap, "ci95_cao": cao,
                     "tb_cac_seed": float(s.mean()), "lech_chuan": float(s.std(ddof=1)) if len(s) > 1 else 0.0,
                     "nho_nhat": float(s.min()), "lon_nhat": float(s.max()),
                     "so_seed_dung_dau": int((hang[m.TEN] == 1).sum())})
    bang = pd.DataFrame(dong).sort_values("tb_cac_seed").reset_index(drop=True)

    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "model_stability.csv", index=False)
    print(f"Chia ngẫu nhiên lại {so_seed} seed · khoảng tin cậy 95% bootstrap trên test seed 42\n")
    print(bang.to_string(index=False, float_format=lambda v: f"{v:6.2f}"))
    return bang


if __name__ == "__main__":
    import argparse

    bo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    bo.add_argument("--so-seed", type=int, default=SO_SEED)
    bo.add_argument("--mo-hinh", nargs="*", default=None)
    bo.add_argument("--cho-phep-luoi-rut-gon", action="store_true")
    a = bo.parse_args()
    warnings.filterwarnings("ignore")
    run(a.so_seed, a.mo_hinh, a.cho_phep_luoi_rut_gon)
