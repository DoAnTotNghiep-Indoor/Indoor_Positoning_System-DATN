"""Xuất Bộ 3 (HistGB + KAN + Transformer) cho app chạy ngay trên điện thoại.

    python -m ml.xuat_mo_hinh        # chạy lại sau mỗi lần `ml.train`

Ghi `mobile/assets/model/bo_ba.json` (mọi thứ app cần để tự đoán) và
`mobile/test/du_lieu/doi_chieu_bo_ba.json` (lần quét test kèm vector điểm và toạ độ
Python tính ra, để `flutter test` kiểm bản Dart cho ra đúng như vậy).
`tests/test_xuat_mo_hinh.py` báo lỗi khi tệp của app lệch với artifacts hiện tại.
"""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from ml import config
from ml.models import bo_ba

TEP_APP = config.ROOT_DIR / "mobile" / "assets" / "model" / "bo_ba.json"
TEP_DOI_CHIEU = config.ROOT_DIR / "mobile" / "test" / "du_lieu" / "doi_chieu_bo_ba.json"
SO_LAN_DOI_CHIEU = 200


def _so(a, chu_so: int = 8) -> list:
    """Mảng → list số thực. Trọng số mạng là float32 nên 8 chữ số thập phân là đủ."""
    return np.round(np.asarray(a, dtype=float), chu_so).tolist()


def _cay(c: dict) -> dict:
    """Cây HistGB đã nối phẳng (`bo_ba.cay_phang`). Ngưỡng giữ đủ chữ số: so `x <= ngưỡng`
    phải ra đúng như Python."""
    return {k: _so(v, 10) if k == "gia_tri" else v.tolist() for k, v in c.items()}


def _kan(kan) -> list:
    return [{"k": L.k, "h": L.h, "t": _so(L.t), "Wb": _so(L.Wb.detach()), "Ws": _so(L.Ws.detach()),
             "b": _so(L.b.detach())} for L in kan.lop]


def _tf(tf) -> dict:
    lop0 = tf.tf.layers[0]
    return {"dau": lop0.self_attn.num_heads, "eps": lop0.norm1.eps,
            **{ten: _so(w) for ten, w in tf.state_dict().items()}}


def du_lieu_app(sieu: dict, hop_dong: dict, can, mo) -> dict:
    return {
        "hop_dong": sieu["hop_dong_du_lieu"],
        "ap": hop_dong["ap_columns"],
        "gia_tri_thieu": hop_dong["missing_rssi_value"],
        "so_ap_toi_thieu": hop_dong["min_ap_per_scan"],
        "min": can.min_.tolist(),
        "scale": can.scale_.tolist(),
        "eps": bo_ba.EPS,
        "vong_trung_vi": bo_ba.VONG_TRUNG_VI,
        "toa_do": mo.toa_do_.tolist(),
        "hgb": _cay(mo.cay_),
        "kan": _kan(mo.kan_),
        "tf": _tf(mo.tf_),
    }


def doi_chieu(du_lieu: dict, can, mo) -> dict:
    """Lần quét test ở dạng app gửi lên, kèm vector điểm, toạ độ một lần quét và toạ độ
    gộp 3 lần quét liên tiếp mà chính mô hình Python tính."""
    ap = du_lieu["ap"]
    bang = pd.read_csv(config.PROCESSED_DIR / "fingerprint_dataset_raw.csv")
    bang = bang[bang["split"] == "test"].head(SO_LAN_DOI_CHIEU)
    quet = [[{"bssid": b, "rssi": int(v)} for b, v in hang.items() if pd.notna(v)]
            for _, hang in bang[ap].iterrows()]
    X = can.transform(bang[ap].fillna(du_lieu["gia_tri_thieu"]).to_numpy(float))
    D = mo.dau_ra(X)
    return {"quet": quet, "diem": D.tolist(), "toa_do": mo.predict(X).tolist(),
            "toa_do_gop": [mo.gop(D[max(0, i - 2): i + 1]).tolist() for i in range(len(D))]}


def nap() -> tuple:
    sieu = json.loads((config.ARTIFACTS_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    if sieu["mo_hinh_active"] != "bo_ba":
        raise SystemExit(f"Mô hình active là {sieu['mo_hinh_active']}, app chỉ chạy được Bộ 3.")
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
