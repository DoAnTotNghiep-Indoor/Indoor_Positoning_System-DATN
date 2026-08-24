"""Huấn luyện và so sánh bốn mô hình định vị.

    python -m ml.train                 # đầy đủ, lưới tham số theo tài liệu
    python -m ml.train --nhanh         # lưới rút gọn, dùng lúc thử nghiệm
    python -m ml.train --mo-hinh knn wknn

Quy trình cho cả bốn mô hình là một, để bảng so sánh có ý nghĩa:

    1. Quét lưới tham số, chọn cấu hình có sai số thấp nhất trên tập VALIDATION
    2. Huấn luyện lại cấu hình đó trên train + validation
    3. Đánh giá MỘT LẦN trên tập TEST

Bước 3 chỉ chạy đúng một lần cho mỗi mô hình. Chọn tham số dựa trên tập test rồi
báo cáo kết quả trên chính tập đó là tự lừa mình — con số đẹp nhưng không nói
được gì về hiệu năng thực tế.

Sinh ra:
    artifacts/model_<ten>.pkl          mô hình đã huấn luyện
    artifacts/model_metadata.json      tham số tốt nhất + chỉ số + mô hình active
    reports/tables/model_comparison.csv
    reports/tables/error_by_reference_point.csv
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from itertools import product

import joblib
import numpy as np
import pandas as pd

from ml import config, evaluate
from ml import models as goi_mo_hinh

for _luong in (sys.stdout, sys.stderr):
    if hasattr(_luong, "reconfigure"):
        try:
            _luong.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def nap_du_lieu() -> tuple[dict, list[str]]:
    """Đọc ba tập đã chia và danh sách đặc trưng từ hợp đồng dữ liệu."""
    duong_dan = config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON
    if not duong_dan.exists():
        raise FileNotFoundError(
            f"Chưa có {duong_dan}. Chạy `python -m ml.pipeline` trước."
        )

    ap_cols = json.loads(duong_dan.read_text(encoding="utf-8"))["ap_columns"]

    tap = {}
    for ten in ("train", "validation", "test"):
        p = config.SPLITS_DIR / f"{ten}.csv"
        if not p.exists():
            raise FileNotFoundError(f"Thiếu {p}. Chạy `python -m ml.pipeline` trước.")
        tap[ten] = pd.read_csv(p)

    return tap, ap_cols


def _to_hop(luoi: dict) -> list[dict]:
    """Bung dict lưới thành danh sách các bộ tham số cụ thể."""
    if not luoi:
        return [{}]
    ten = list(luoi)
    return [dict(zip(ten, gt)) for gt in product(*(luoi[k] for k in ten))]


def quet_luoi(module, X_tr, y_tr, X_va, y_va, nhanh: bool = False) -> tuple[dict, float]:
    """Thử mọi tổ hợp, trả về (tham số tốt nhất, sai số trung bình trên validation)."""
    luoi = getattr(module, "LUOI_NHANH", module.LUOI_THAM_SO) if nhanh else module.LUOI_THAM_SO
    to_hop = _to_hop(luoi)

    tot_nhat, loi_tot_nhat = None, float("inf")
    for i, tham_so in enumerate(to_hop, 1):
        model = module.build(**tham_so)
        model.fit(X_tr, y_tr)
        loi = evaluate.khoang_cach_loi(y_va, model.predict(X_va)).mean()

        if loi < loi_tot_nhat:
            tot_nhat, loi_tot_nhat = tham_so, loi

        if len(to_hop) > 20 and i % max(1, len(to_hop) // 10) == 0:
            print(f"        {i}/{len(to_hop)} tổ hợp · tốt nhất {loi_tot_nhat:.3f} m", flush=True)

    return tot_nhat, loi_tot_nhat


def huan_luyen_mot(module, tap: dict, ap_cols: list[str], nhanh: bool) -> dict:
    """Chạy trọn quy trình 3 bước cho một mô hình."""
    print(f"\n  {module.TEN}")

    X_tr = tap["train"][ap_cols].to_numpy(dtype=float)
    y_tr = tap["train"][config.TARGET_COLS].to_numpy(dtype=float)
    X_va = tap["validation"][ap_cols].to_numpy(dtype=float)
    y_va = tap["validation"][config.TARGET_COLS].to_numpy(dtype=float)
    X_te = tap["test"][ap_cols].to_numpy(dtype=float)
    y_te = tap["test"][config.TARGET_COLS].to_numpy(dtype=float)

    # 1. Chọn tham số trên validation
    bat_dau = time.perf_counter()
    tham_so, loi_va = quet_luoi(module, X_tr, y_tr, X_va, y_va, nhanh)
    giay_quet = time.perf_counter() - bat_dau
    print(f"    tham số  {tham_so}")
    print(f"    validation {loi_va:.3f} m · quét {giay_quet:.1f}s")

    # 2. Huấn luyện lại trên train + validation
    X_full = np.vstack([X_tr, X_va])
    y_full = np.vstack([y_tr, y_va])
    model = module.build(**tham_so)
    bat_dau = time.perf_counter()
    model.fit(X_full, y_full)
    giay_fit = time.perf_counter() - bat_dau

    # 3. Đánh giá một lần trên test
    y_pred = model.predict(X_te)
    ms = evaluate.do_thoi_gian_du_doan(model, X_te)
    ket_qua = evaluate.danh_gia(y_te, y_pred, module.TEN, thoi_gian_ms=ms)

    print(f"    TEST  trung bình {ket_qua['loi_trung_binh']:.3f} m · "
          f"trung vị {ket_qua['loi_trung_vi']:.3f} m · "
          f"CDF90 {ket_qua['cdf_90']:.3f} m · {ms:.2f} ms/mẫu")

    return {
        "module": module,
        "model": model,
        "tham_so": tham_so,
        "loi_validation": float(loi_va),
        "giay_quet_luoi": round(giay_quet, 2),
        "giay_huan_luyen": round(giay_fit, 3),
        "ket_qua_test": ket_qua,
        "y_pred": y_pred,
    }


def run(ten_mo_hinh: list[str] | None = None, nhanh: bool = False) -> pd.DataFrame:
    bat_dau = datetime.now()
    tap, ap_cols = nap_du_lieu()

    print(f"Dữ liệu: train {len(tap['train'])} · validation {len(tap['validation'])} "
          f"· test {len(tap['test'])} · {len(ap_cols)} đặc trưng")
    print(f"Lưới tham số: {'rút gọn' if nhanh else 'đầy đủ theo tài liệu thiết kế'}")

    chon = goi_mo_hinh.DANH_SACH
    if ten_mo_hinh:
        muon = {t.lower() for t in ten_mo_hinh}
        chon = [m for m in chon if m.__name__.rsplit(".", 1)[-1].lower() in muon
                or m.TEN.lower() in muon]
        if not chon:
            raise ValueError(f"Không nhận ra mô hình: {ten_mo_hinh}")

    tat_ca = [huan_luyen_mot(m, tap, ap_cols, nhanh) for m in chon]

    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)

    # Bảng so sánh
    bang = evaluate.bang_so_sanh([r["ket_qua_test"] for r in tat_ca])
    bang.to_csv(config.REPORTS_DIR / "tables" / "model_comparison.csv", index=False)

    # Mô hình tốt nhất -> active
    tot_nhat = min(tat_ca, key=lambda r: r["ket_qua_test"]["loi_trung_binh"])

    for r in tat_ca:
        khoa = r["module"].__name__.rsplit(".", 1)[-1]
        joblib.dump(r["model"], config.ARTIFACTS_DIR / f"model_{khoa}.pkl")

    khoa_tot_nhat = tot_nhat["module"].__name__.rsplit(".", 1)[-1]
    metadata = {
        "huan_luyen_luc": bat_dau.isoformat(timespec="seconds"),
        "mo_hinh_active": khoa_tot_nhat,
        "file_active": f"model_{khoa_tot_nhat}.pkl",
        "so_dac_trung": len(ap_cols),
        "so_mau": {k: len(v) for k, v in tap.items()},
        "luoi": "rut_gon" if nhanh else "day_du",
        "cac_mo_hinh": {
            r["module"].__name__.rsplit(".", 1)[-1]: {
                "ten": r["module"].TEN,
                "tham_so": r["tham_so"],
                "loi_validation": r["loi_validation"],
                "giay_quet_luoi": r["giay_quet_luoi"],
                "giay_huan_luyen": r["giay_huan_luyen"],
                **r["ket_qua_test"],
            }
            for r in tat_ca
        },
    }
    (config.ARTIFACTS_DIR / "model_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Sai số theo từng điểm tham chiếu, cho mô hình tốt nhất
    theo_diem = evaluate.loi_theo_diem(
        tap["test"]["rp_id"],
        tap["test"][config.TARGET_COLS].to_numpy(dtype=float),
        tot_nhat["y_pred"],
    )
    theo_diem.to_csv(config.REPORTS_DIR / "tables" / "error_by_reference_point.csv", index=False)

    print("\n" + "=" * 66)
    print("BẢNG SO SÁNH — sai số trên tập test, đơn vị mét")
    print("=" * 66)
    hien = bang[["mo_hinh", "loi_trung_binh", "loi_trung_vi", "cdf_50",
                 "cdf_75", "cdf_90", "loi_lon_nhat", "thoi_gian_du_doan_ms"]]
    print(hien.to_string(index=False, float_format=lambda v: f"{v:7.3f}"))

    co_so = min(r["ket_qua_test"]["loi_trung_binh"]
                for r in tat_ca if r["module"].TEN in ("kNN", "WKNN"))
    tot = tot_nhat["ket_qua_test"]["loi_trung_binh"]
    print(f"\nTốt nhất: {tot_nhat['module'].TEN} — {tot:.3f} m")
    if co_so > 0:
        print(f"So với cơ sở tốt nhất ({co_so:.3f} m): "
              f"{'giảm' if tot < co_so else 'TĂNG'} {abs(tot - co_so) / co_so * 100:.1f}%")
        print("Mục tiêu tài liệu thiết kế: thấp hơn cơ sở 10-20%")

    print(f"\nĐiểm sai nhiều nhất: " + ", ".join(
        f"{r.rp_id} ({r.loi_trung_binh:.1f} m)" for r in theo_diem.head(3).itertuples()))

    return bang


def main() -> None:
    p = argparse.ArgumentParser(description="Huấn luyện và so sánh mô hình định vị")
    p.add_argument("--nhanh", action="store_true",
                   help="dùng lưới tham số rút gọn (chỉ để thử nghiệm)")
    p.add_argument("--mo-hinh", nargs="+", default=None,
                   help="chỉ chạy một số mô hình, ví dụ: --mo-hinh knn wknn")
    a = p.parse_args()
    run(ten_mo_hinh=a.mo_hinh, nhanh=a.nhanh)


if __name__ == "__main__":
    main()
