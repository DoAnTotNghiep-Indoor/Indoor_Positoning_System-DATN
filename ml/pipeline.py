"""Chạy toàn bộ pipeline tiền xử lý bằng một lệnh.

    python -m ml.pipeline
    python -m ml.pipeline --min-appear-rate 0.10      # thí nghiệm so sánh ngưỡng

Sinh ra đầy đủ artifact, không phụ thuộc Google Colab:

    artifacts/feature_list.json      hợp đồng dữ liệu với backend
    artifacts/scaler.pkl             tham số chuẩn hoá học từ tập train
    artifacts/pipeline_manifest.json nhật ký lần chạy, phục vụ tái lập
    data/processed/fingerprint_dataset_raw.csv     bản CHƯA chuẩn hoá
    data/processed/fingerprint_dataset_sorted.csv  bản đã chuẩn hoá
    data/splits/{train,validation,test}.csv

Bản chưa chuẩn hoá được giữ lại có chủ đích: mất nó thì không quay về đơn vị dBm
được nữa, đúng tình huống đã xảy ra khi chạy trên Colab lần trước.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

import joblib
import pandas as pd

from ml import config
from ml import preprocess as pre

# Console Windows mặc định cp1252, không in được tiếng Việt có dấu.
for _luong in (sys.stdout, sys.stderr):
    if hasattr(_luong, "reconfigure"):
        try:
            _luong.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def _log(buoc: str, noi_dung: str) -> None:
    print(f"[{buoc:>5}] {noi_dung}", flush=True)


def run(
    min_appear_rate: float | None = None,
    hampel_train_only: bool | None = None,
) -> dict:
    """Chạy 12 bước, ghi artifact, trả về nhật ký lần chạy."""
    bat_dau = datetime.now()
    ty_le_ap = min_appear_rate if min_appear_rate is not None else config.MIN_APPEAR_RATE
    hampel_rieng = config.HAMPEL_ON_TRAIN_ONLY if hampel_train_only is None else hampel_train_only

    for thu_muc in (config.PROCESSED_DIR, config.SPLITS_DIR, config.ARTIFACTS_DIR):
        thu_muc.mkdir(parents=True, exist_ok=True)

    # --- Bước 1: nạp dữ liệu thô ---
    df = pre.load_raw()
    mo_ta = pre.describe_raw(df)
    _log("1", f"{mo_ta['so_dong']:,} dòng · {mo_ta['so_lan_quet']} lần quét · "
              f"{mo_ta['so_rp']} điểm · {mo_ta['so_bssid']} BSSID · "
              f"RSSI {mo_ta['rssi_min']:.0f}…{mo_ta['rssi_max']:.0f} dBm")

    # --- Bước 2: gom theo lần quét ---
    df = pre.build_scan_id(df)
    scan_meta = pre.build_scan_meta(df)
    _log("2", f"{len(scan_meta)} lần quét · {mo_ta['so_thiet_bi']} thiết bị")

    # --- Bước 3: pivot sang bảng vân tay ---
    fingerprint, ap_cols = pre.to_wide(df, scan_meta)
    _log("3", f"bảng vân tay {fingerprint.shape[0]} × {len(ap_cols)} cột AP")

    # --- Bước 4: ghép toạ độ thật ---
    fingerprint, tk_toa_do = pre.attach_coordinates(fingerprint)
    _log("4", f"{tk_toa_do['scan_co_toa_do']}/{tk_toa_do['scan_truoc_khi_ghep']} lần quét có toạ độ"
              + (f" · bỏ {tk_toa_do['scan_bi_bo']} mẫu của {tk_toa_do['rp_chua_do']}"
                 if tk_toa_do["scan_bi_bo"] else ""))

    # --- Bước 5: lọc AP hiếm gặp ---
    fingerprint, ap_cols, ty_le_xuat_hien = pre.filter_access_points(
        fingerprint, ap_cols, min_appear_rate=ty_le_ap
    )
    _log("5", f"giữ {len(ap_cols)}/{len(ty_le_xuat_hien)} AP (ngưỡng ≥ {ty_le_ap:.0%})")

    # --- Bước 6: loại mẫu quét quá nghèo ---
    fingerprint, tk_scan = pre.filter_sparse_scans(fingerprint, ap_cols)
    _log("6", f"loại {tk_scan['scan_bi_loai']} mẫu · còn {tk_scan['scan_sau']} · "
              f"AP mỗi mẫu: min {tk_scan['ap_moi_scan_min']}, "
              f"trung vị {tk_scan['ap_moi_scan_trung_vi']:.0f}")

    # --- Bước 7: điền RSSI thiếu ---
    fingerprint, gia_tri_thieu, so_o_trong = pre.fill_missing(fingerprint, ap_cols)
    _log("7", f"điền {so_o_trong:,} ô trống bằng {gia_tri_thieu:.0f} dBm")

    # --- Bước 9 trước bước 8 khi lọc nhiễu riêng cho tập train ---
    fingerprint, tk_chia = pre.split_dataset(fingerprint)
    _log("9", f"{tk_chia['chien_luoc']} · " +
              " · ".join(f"{k} {v}" for k, v in tk_chia["so_mau"].items()))
    if "canh_bao" in tk_chia:
        _log("!", tk_chia["canh_bao"])

    # --- Bước 8: lọc nhiễu Hampel ---
    if hampel_rieng:
        la_train = fingerprint["split"] == "train"
        da_loc, so_ngoai_lai = pre.hampel_filter(fingerprint.loc[la_train], ap_cols)
        fingerprint = pd.concat([da_loc, fingerprint.loc[~la_train]], ignore_index=True)
        _log("8", f"thay {so_ngoai_lai:,} giá trị ngoại lai — chỉ trên tập train")
    else:
        fingerprint, so_ngoai_lai = pre.hampel_filter(fingerprint, ap_cols)
        _log("8", f"thay {so_ngoai_lai:,} giá trị ngoại lai — trên toàn bộ dữ liệu")

    # Lưu bản chưa chuẩn hoá TRƯỚC khi scale — không có bản này thì mất đơn vị dBm.
    cot_meta = [c for c in config.META_COLS if c in fingerprint.columns]
    fingerprint = fingerprint[cot_meta + ap_cols]
    duong_dan_raw = config.PROCESSED_DIR / "fingerprint_dataset_raw.csv"
    fingerprint.sort_values("rp_id", kind="stable").to_csv(duong_dan_raw, index=False)

    # --- Bước 10: chuẩn hoá min-max ---
    fingerprint, scaler, tk_scale = pre.scale_dataset(fingerprint, ap_cols)
    _log("10", f"fit trên train · khoảng giá trị {tk_scale['nho_nhat']:.3f} → {tk_scale['lon_nhat']:.3f}")

    # --- Bước 12: sắp xếp cột và dòng ---
    fingerprint = fingerprint.sort_values("rp_id", kind="stable").reset_index(drop=True)

    # --- Bước 11: ghi artifact ---
    feature_list = {
        "ap_columns": ap_cols,
        "feature_count": len(ap_cols),
        "missing_rssi_value": gia_tri_thieu,
        "min_ap_per_scan": config.MIN_AP_PER_SCAN,
        "min_appear_rate": ty_le_ap,
        "target_columns": config.TARGET_COLS,
        "scaler_file": config.SCALER_PKL,
        "created_at": bat_dau.isoformat(timespec="seconds"),
    }
    (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).write_text(
        json.dumps(feature_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    joblib.dump(scaler, config.ARTIFACTS_DIR / config.SCALER_PKL)

    duong_dan_sorted = config.PROCESSED_DIR / "fingerprint_dataset_sorted.csv"
    fingerprint.to_csv(duong_dan_sorted, index=False)
    for ten in ("train", "validation", "test"):
        fingerprint[fingerprint["split"] == ten].to_csv(
            config.SPLITS_DIR / f"{ten}.csv", index=False
        )

    # Tỉ lệ xuất hiện của AP — dùng vẽ biểu đồ biện minh ngưỡng trong báo cáo.
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
    ty_le_xuat_hien.rename("ty_le_xuat_hien").to_csv(
        config.REPORTS_DIR / "tables" / "ap_appearance_rate.csv", header=True
    )

    manifest = {
        "chay_luc": bat_dau.isoformat(timespec="seconds"),
        "thoi_gian_giay": round((datetime.now() - bat_dau).total_seconds(), 2),
        "tham_so": {
            "min_appear_rate": ty_le_ap,
            "min_ap_per_scan": config.MIN_AP_PER_SCAN,
            "hampel_k": config.HAMPEL_K,
            "hampel_chi_tren_train": hampel_rieng,
            "chien_luoc_chia": tk_chia["chien_luoc"],
            "random_state": config.RANDOM_STATE,
        },
        "du_lieu_tho": mo_ta,
        "ghep_toa_do": tk_toa_do,
        "loc_mau": tk_scan,
        "chia_tap": tk_chia,
        "chuan_hoa": tk_scale,
        "so_o_trong_da_dien": so_o_trong,
        "gia_tri_dien_thieu": gia_tri_thieu,
        "so_ngoai_lai_hampel": so_ngoai_lai,
        "kich_thuoc_cuoi": list(fingerprint.shape),
    }
    (config.ARTIFACTS_DIR / config.MANIFEST_JSON).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _log("11", f"ghi {config.FEATURE_LIST_JSON}, {config.SCALER_PKL}, "
               f"{config.MANIFEST_JSON} và 3 tệp split")
    _log("12", f"dataset cuối {fingerprint.shape[0]} × {fingerprint.shape[1]} → {duong_dan_sorted.name}")
    print(f"\nXong sau {manifest['thoi_gian_giay']}s. "
          f"Bản chưa chuẩn hoá giữ tại {duong_dan_raw.name}")

    return manifest


def main() -> None:
    p = argparse.ArgumentParser(description="Pipeline tiền xử lý dữ liệu WiFi fingerprinting")
    p.add_argument("--min-appear-rate", type=float, default=None,
                   help="ngưỡng lọc AP, mặc định %(default)s (thử 0.0 / 0.10 / 0.20)")
    p.add_argument("--hampel-all", action="store_true",
                   help="lọc nhiễu trên toàn bộ dữ liệu như bản Colab cũ (không khuyến nghị)")
    a = p.parse_args()

    run(
        min_appear_rate=a.min_appear_rate,
        hampel_train_only=False if a.hampel_all else None,
    )


if __name__ == "__main__":
    main()
