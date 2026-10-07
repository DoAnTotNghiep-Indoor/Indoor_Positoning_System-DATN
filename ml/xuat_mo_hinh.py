"""Xuất kNN k động cho app chạy ngay trên điện thoại.

    python -m ml.xuat_mo_hinh        # chạy lại sau mỗi lần `ml.train`

Ghi `mobile/assets/model/k_dong.json` (mọi thứ app cần để tự đoán) và
`mobile/test/du_lieu/doi_chieu_k_dong.json` (lần quét test kèm toạ độ Python đoán ra,
để `flutter test` kiểm bản Dart cho ra đúng như vậy). `tests/test_xuat_mo_hinh.py`
báo lỗi khi tệp của app lệch với artifacts hiện tại.
"""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from ml import config

TEP_APP = config.ROOT_DIR / "mobile" / "assets" / "model" / "k_dong.json"
TEP_DOI_CHIEU = config.ROOT_DIR / "mobile" / "test" / "du_lieu" / "doi_chieu_k_dong.json"
SO_LAN_DOI_CHIEU = 200


def du_lieu_app(sieu: dict, hop_dong: dict, can, mo) -> dict:
    knn = mo.nho_.clf_
    return {
        "hop_dong": sieu["hop_dong_du_lieu"],
        "ap": hop_dong["ap_columns"],
        "gia_tri_thieu": hop_dong["missing_rssi_value"],
        "so_ap_toi_thieu": hop_dong["min_ap_per_scan"],
        "min": can.min_.tolist(),
        "scale": can.scale_.tolist(),
        "beta": mo.beta,
        "nguong": mo.nguong_,
        "k_lon": mo.k_lon_,
        # Vân tay đã nâng mũ beta (dạng kNN lưu sẵn), một hàng mỗi lần quét đã thu.
        "van_tay": np.round(knn._fit_X, 7).tolist(),
        "nhan": knn._y.tolist(),
        "toa_do": mo.nho_.toa_do_[knn.classes_].tolist(),
    }


def doi_chieu(du_lieu: dict, can, mo) -> dict:
    """Lần quét test ở dạng app gửi lên, kèm toạ độ và độ trải mà chính mô hình Python tính."""
    ap = du_lieu["ap"]
    bang = pd.read_csv(config.PROCESSED_DIR / "fingerprint_dataset_raw.csv")
    bang = bang[bang["split"] == "test"].head(SO_LAN_DOI_CHIEU)
    quet = [[{"bssid": b, "rssi": int(v)} for b, v in hang.items() if pd.notna(v)]
            for _, hang in bang[ap].iterrows()]
    X = bang[ap].fillna(du_lieu["gia_tri_thieu"]).to_numpy(float)
    X = can.transform(X)
    return {"quet": quet, "toa_do": mo.predict(X).tolist(), "do_trai": mo.do_trai(X).tolist()}


def nap() -> tuple:
    sieu = json.loads((config.ARTIFACTS_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    if sieu["mo_hinh_active"] != "fingerprint_knn_dong":
        raise SystemExit(f"Mô hình active là {sieu['mo_hinh_active']}, app chỉ chạy được kNN k động.")
    hop_dong = json.loads((config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8"))
    return (sieu, hop_dong, joblib.load(config.ARTIFACTS_DIR / config.SCALER_PKL),
            joblib.load(config.ARTIFACTS_DIR / sieu["file_active"]))


def run() -> None:
    sieu, hop_dong, can, mo = nap()
    du_lieu = du_lieu_app(sieu, hop_dong, can, mo)
    for tep, noi_dung in ((TEP_APP, du_lieu), (TEP_DOI_CHIEU, doi_chieu(du_lieu, can, mo))):
        tep.parent.mkdir(parents=True, exist_ok=True)
        tep.write_text(json.dumps(noi_dung, separators=(",", ":")), encoding="utf-8", newline="\n")
        print(f"{tep.relative_to(config.ROOT_DIR)}  {tep.stat().st_size // 1024} KB")


if __name__ == "__main__":
    run()
