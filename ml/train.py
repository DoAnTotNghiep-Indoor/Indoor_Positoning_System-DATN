"""Huấn luyện và so sánh năm mô hình định vị.

    python -m ml.train                 # đầy đủ, lưới tham số theo tài liệu
    python -m ml.train --nhanh         # lưới rút gọn, dùng lúc thử nghiệm
    python -m ml.train --mo-hinh knn wknn

Quy trình cho cả năm mô hình là một, để bảng so sánh có ý nghĩa:

    1. Quét lưới tham số, chọn cấu hình có sai số thấp nhất trên tập VALIDATION
    2. Huấn luyện lại cấu hình đó trên train + validation
    3. Đánh giá MỘT LẦN trên tập TEST

Bước 3 chỉ chạy đúng một lần cho mỗi mô hình. Chọn tham số dựa trên tập test rồi
báo cáo kết quả trên chính tập đó là tự lừa mình — con số đẹp nhưng không nói
được gì về hiệu năng thực tế.

Quy tắc này áp cho MỌI quyết định, không riêng tham số: mô hình nào thành active,
mô hình cơ sở nào đem ra so sánh — tất cả đều chọn theo validation. Sai số test
chỉ được đọc ở bước cuối để in ra và ghi vào báo cáo. Xem `chon_theo_validation`.

Sinh ra:
    artifacts/model_<ten>.pkl          mô hình đã huấn luyện
    artifacts/model_metadata.json      tham số tốt nhất + chỉ số + mô hình active
    reports/tables/model_comparison.csv
    reports/tables/error_by_reference_point.csv
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from itertools import product

import joblib
import numpy as np
import pandas as pd

from ml import config, evaluate, postprocess
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
    ap_cols = json.loads(duong_dan.read_text(encoding="utf-8"))["ap_columns"]
    tap = {
        ten: pd.read_csv(config.SPLITS_DIR / f"{ten}.csv")
        for ten in ("train", "validation", "test")
    }
    return tap, ap_cols


def _to_hop(luoi: dict) -> list[dict]:
    """Bung dict lưới thành danh sách các bộ tham số cụ thể."""
    ten = list(luoi)
    return [dict(zip(ten, gt)) for gt in product(*(luoi[k] for k in ten))] or [{}]


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


def chon_theo_validation(ket_qua: list[dict], loc=None) -> dict | None:
    """Chọn mô hình tốt nhất theo sai số VALIDATION, không bao giờ theo test.

    Tách thành hàm riêng để bất biến này kiểm thử được — xem tests/test_train.py.
    Trước đây phép chọn nằm inline và dùng `ket_qua_test`, tức chọn trên chính
    tập dùng để công bố kết quả, đúng thứ mà docstring đầu tệp gọi là "tự lừa
    mình". Với bộ dữ liệu hiện tại hai cách cho cùng người thắng nên con số đã
    công bố không đổi, nhưng lập luận thì hỏng và sẽ âm thầm sai khi thêm dữ
    liệu hoặc thêm mô hình.

    `loc` lọc bớt ứng viên, ví dụ chỉ lấy hai mô hình cơ sở. Trả về None khi
    không còn ứng viên nào.
    """
    ung_vien = [r for r in ket_qua if loc is None or loc(r)]
    if not ung_vien:
        return None
    return min(ung_vien, key=lambda r: r["loi_validation"])


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

    tat_ca = [huan_luyen_mot(m, tap, ap_cols, nhanh) for m in chon]

    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)

    # Bảng so sánh
    bang = evaluate.bang_so_sanh([r["ket_qua_test"] for r in tat_ca])
    bang.to_csv(config.REPORTS_DIR / "tables" / "model_comparison.csv", index=False)

    # Mô hình active chọn theo VALIDATION. Sai số test bên dưới chỉ dùng để báo
    # cáo, không được tham gia vào bất kỳ quyết định nào.
    tot_nhat = chon_theo_validation(tat_ca)

    for r in tat_ca:
        khoa = r["module"].__name__.rsplit(".", 1)[-1]
        joblib.dump(r["model"], config.ARTIFACTS_DIR / f"model_{khoa}.pkl")

    khoa_tot_nhat = tot_nhat["module"].__name__.rsplit(".", 1)[-1]
    hop_dong = json.loads(
        (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8")
    )
    metadata = {
        "huan_luyen_luc": bat_dau.isoformat(timespec="seconds"),
        "mo_hinh_active": khoa_tot_nhat,
        "file_active": f"model_{khoa_tot_nhat}.pkl",
        # Dấu vân của hợp đồng dữ liệu lúc huấn luyện. Backend phải đối chiếu ba
        # trường này với feature_list.json đang nạp; lệch nghĩa là model và hợp
        # đồng sinh ra từ hai lần chạy pipeline khác nhau, dự đoán sẽ sai âm thầm.
        # missing_rssi_value đặc biệt nguy hiểm vì nó bằng min(RSSI) - 1 nên đổi
        # theo dữ liệu: thêm một lần quét yếu hơn -95 dBm là giá trị này đổi.
        "hop_dong_du_lieu": {
            "missing_rssi_value": hop_dong["missing_rssi_value"],
            "feature_count": hop_dong["feature_count"],
            "ap_columns_sha1": hashlib.sha1(
                "\n".join(hop_dong["ap_columns"]).encode("utf-8")
            ).hexdigest(),
        },
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

    # Mô hình cơ sở cũng chọn theo validation. None khi chạy --mo-hinh không kèm
    # kNN/WKNN.
    r_co_so = chon_theo_validation(tat_ca, lambda r: r["module"].TEN in ("kNN", "WKNN"))
    co_so = r_co_so["ket_qua_test"]["loi_trung_binh"] if r_co_so else 0.0
    tot = tot_nhat["ket_qua_test"]["loi_trung_binh"]
    print(f"\nTốt nhất: {tot_nhat['module'].TEN} — {tot:.3f} m")
    if co_so > 0:
        print(f"So với cơ sở tốt nhất ({co_so:.3f} m): "
              f"{'giảm' if tot < co_so else 'TĂNG'} {abs(tot - co_so) / co_so * 100:.1f}%")
        print("Mục tiêu tài liệu thiết kế: thấp hơn cơ sở 10-20%")

    print(f"\nĐiểm sai nhiều nhất: " + ", ".join(
        f"{r.rp_id} ({r.loi_trung_binh:.1f} m)" for r in theo_diem.head(3).itertuples()))

    # Hậu xử lý: gộp các lần quét tại cùng một vị trí. Thiết bị quét mỗi 1-2 giây
    # nên lúc chạy thật luôn có sẵn vài lần quét gần nhau về thời gian.
    gop = _danh_gia_sau_khi_gop(tap["test"], tot_nhat["y_pred"])
    print("\n" + "-" * 66)
    print(f"Sau khi gộp {gop['so_lan_quet']} lần quét mỗi vị trí "
          f"({postprocess.CUA_SO_MAC_DINH} là mặc định lúc chạy thật):")
    print(f"  sai số trung bình {gop['loi_trung_binh']:.2f} m "
          f"(một lần quét: {tot:.2f} m)")
    print(f"  sai số lớn nhất   {gop['loi_lon_nhat']:.1f} m "
          f"(một lần quét: {tot_nhat['ket_qua_test']['loi_lon_nhat']:.1f} m)")
    print(f"  số vị trí còn sai {gop['so_vi_tri_sai']}/{gop['so_vi_tri']}")

    metadata["hau_xu_ly_gop"] = gop
    (config.ARTIFACTS_DIR / "model_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return bang


def _danh_gia_sau_khi_gop(tap_test: pd.DataFrame, y_pred: np.ndarray) -> dict:
    """Gộp các lần quét tại cùng một điểm rồi đo lại sai số."""
    ds, so_lan = [], []
    y_that = tap_test[config.TARGET_COLS].to_numpy(dtype=float)

    for _, nhom in tap_test.assign(_i=range(len(tap_test))).groupby("rp_id"):
        idx = nhom["_i"].to_numpy()
        so_lan.append(len(idx))
        ds.append(float(np.linalg.norm(postprocess.gop(y_pred[idx]) - y_that[idx[0]])))

    ds = np.array(ds)
    return {
        "cach_gop": "dong_thuan",
        "so_lan_quet": int(np.median(so_lan)),
        "so_vi_tri": int(len(ds)),
        "so_vi_tri_sai": int((ds > 1).sum()),
        "loi_trung_binh": float(ds.mean()),
        "loi_trung_vi": float(np.median(ds)),
        "loi_lon_nhat": float(ds.max()),
    }


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
