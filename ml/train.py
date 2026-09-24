"""Huấn luyện và so sánh sáu mô hình định vị.

    python -m ml.train                 # đầy đủ, lưới tham số theo tài liệu
    python -m ml.train --nhanh         # lưới rút gọn, dùng lúc thử nghiệm
    python -m ml.train --mo-hinh knn wknn

Quy trình cho cả năm mô hình là một, để bảng so sánh có ý nghĩa:

    1. Quét lưới tham số, chọn cấu hình sai số thấp nhất trên tập VALIDATION
    2. Huấn luyện lại cấu hình đó trên train + validation
    3. Đánh giá MỘT LẦN trên tập TEST

Tập test chỉ được chạm đúng một lần, và quy tắc này áp cho MỌI quyết định chứ
không riêng tham số — kể cả chọn mô hình active hay mô hình cơ sở đem so sánh.
Xem `chon_theo_validation`.

Sinh ra: artifacts/model_<ten>.pkl, artifacts/model_metadata.json, và hai bảng
model_comparison.csv, error_by_reference_point.csv trong reports/tables/.
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


def _to_hop(luoi: dict, bo_qua=None) -> list[dict]:
    """Bung dict lưới thành danh sách các bộ tham số cụ thể. `bo_qua` cho mô hình
    tự loại những tổ hợp mà nó biết là trùng kết quả.
    """
    ten = list(luoi)
    ds = [dict(zip(ten, gt)) for gt in product(*(luoi[k] for k in ten))] or [{}]
    return [t for t in ds if not (bo_qua and bo_qua(t))] or [{}]


def quet_luoi(module, X_tr, y_tr, X_va, y_va, nhanh: bool = False) -> tuple[dict, float]:
    """Thử mọi tổ hợp, trả về (tham số tốt nhất, sai số trung bình trên validation)."""
    luoi = getattr(module, "LUOI_NHANH", module.LUOI_THAM_SO) if nhanh else module.LUOI_THAM_SO
    to_hop = _to_hop(luoi, getattr(module, "to_hop_trung", None))

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

    Chọn trên chính tập dùng để công bố kết quả thì lập luận hỏng và sẽ âm thầm
    sai khi thêm dữ liệu hoặc thêm mô hình. `loc` lọc bớt ứng viên; trả None
    khi hết ứng viên.
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
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "model_comparison.csv",
                   index=False)

    # Mô hình active: `config.MO_HINH_TRIEN_KHAI` nếu có trong lần chạy này, không
    # thì chọn theo VALIDATION. Sai số test bên dưới chỉ dùng để báo cáo, không
    # tham gia vào bất kỳ quyết định nào.
    tot_nhat = next((r for r in tat_ca if r["module"].__name__.rsplit(".", 1)[-1]
                     == config.MO_HINH_TRIEN_KHAI), None) or chon_theo_validation(tat_ca)

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
        # trường này với feature_list.json đang nạp; lệch nghĩa là model và hợp đồng
        # sinh ra từ hai lần chạy pipeline khác nhau. missing_rssi_value đặc biệt
        # nguy hiểm vì nó bằng min(RSSI) - 1 nên đổi theo dữ liệu.
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
    config.ghi_json(config.ARTIFACTS_DIR / "model_metadata.json", metadata)

    # Sai số theo từng điểm tham chiếu, cho mô hình tốt nhất
    theo_diem = evaluate.loi_theo_diem(
        tap["test"]["rp_id"],
        tap["test"][config.TARGET_COLS].to_numpy(dtype=float),
        tot_nhat["y_pred"],
    )
    config.ghi_csv(theo_diem,
                   config.REPORTS_DIR / "tables" / "error_by_reference_point.csv",
                   index=False)

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
    print(f"\nTriển khai: {tot_nhat['module'].TEN} — {tot:.3f} m")
    if co_so > 0:
        print(f"So với cơ sở tốt nhất ({co_so:.3f} m): "
              f"{'giảm' if tot < co_so else 'TĂNG'} {abs(tot - co_so) / co_so * 100:.1f}%")
        print("Mục tiêu tài liệu thiết kế: thấp hơn cơ sở 10-20%")

    print(f"\nĐiểm sai nhiều nhất: " + ", ".join(
        f"{r.rp_id} ({r.loi_trung_binh:.1f} m)" for r in theo_diem.head(3).itertuples()))

    hoc = pd.concat([tap["train"], tap["validation"]], ignore_index=True)
    y_ngoai = evaluate.du_doan_ngoai_phan(
        tot_nhat["module"], tot_nhat["tham_so"], hoc[ap_cols].to_numpy(dtype=float),
        hoc[config.TARGET_COLS].to_numpy(dtype=float), hoc["rp_id"])
    gop = _danh_gia_sau_khi_gop(tap["test"], tot_nhat["y_pred"], hoc, y_ngoai)
    dy, ct, cd = gop["dung_yen"], gop["cua_so_truot"], gop["chuoi_dai"]
    print("\n" + "-" * 66)
    print(f"Sau khi gộp, cửa sổ {gop['cua_so']} lần quét, theo thứ tự thời gian:")
    for nhan, g in ((f"test, {gop['so_lan_quet']} lần quét/điểm", ct),
                    ("chuỗi dài train+val, ngoài phần", cd)):
        print(f"  {nhan:32s} {g['khong_gop']:5.2f} → {g['loi_trung_binh']:5.2f} m · "
              f"sai {g['so_mau_sai_khong_gop']} → {g['so_mau_sai']}/{g['so_mau']}")
    print(f"  {'đứng yên (chặn dưới)':32s} {dy['loi_trung_binh']:5.2f} m · "
          f"sai {dy['so_vi_tri_sai']}/{dy['so_vi_tri']} vị trí")

    metadata["hau_xu_ly_gop"] = gop
    config.ghi_json(config.ARTIFACTS_DIR / "model_metadata.json", metadata)

    return bang


def _cua_so_truot(tap: pd.DataFrame, y_pred: np.ndarray) -> dict:
    """Chạy như `BoGop`: từng điểm, các lần quét theo thứ tự thời gian."""
    P = np.asarray(y_pred, dtype=float)
    Y = tap[config.TARGET_COLS].to_numpy(dtype=float)
    loi = np.concatenate([
        np.linalg.norm(postprocess.gop_cua_so_truot(P[i]) - Y[i], axis=1)
        for i in evaluate.nhom_theo_thoi_gian(tap)
    ])
    mot = np.linalg.norm(P - Y, axis=1)
    return {
        "so_mau": int(len(loi)),
        "khong_gop": float(mot.mean()),
        "so_mau_sai_khong_gop": int((mot > 1).sum()),
        "loi_trung_binh": float(loi.mean()),
        "loi_trung_vi": float(np.median(loi)),
        "loi_lon_nhat": float(loi.max()),
        "so_mau_sai": int((loi > 1).sum()),
    }


def _danh_gia_sau_khi_gop(tap_test: pd.DataFrame, y_pred: np.ndarray,
                          tap_hoc: pd.DataFrame | None = None,
                          y_ngoai_phan: np.ndarray | None = None) -> dict:
    """Sai số sau khi gộp, đo ba cách.

    `dung_yen` gộp mọi lần quét của một điểm — chặn dưới lý tưởng. `cua_so_truot`
    chạy như backend trên tập test, nhưng mỗi điểm chỉ ~3 lần quét. `chuoi_dai`
    chạy trên ~17 lần quét mỗi điểm của train+val, dự đoán ngoài phần — gần với
    lúc quét liên tục hơn.
    """
    y_that = tap_test[config.TARGET_COLS].to_numpy(dtype=float)
    nhom = evaluate.nhom_theo_thoi_gian(tap_test)
    ds = np.array([np.linalg.norm(postprocess.gop(y_pred[i]) - y_that[i[0]]) for i in nhom])
    kq = {
        "cach_gop": "dong_thuan",
        "cua_so": postprocess.CUA_SO_MAC_DINH,
        "so_lan_quet": int(np.median([len(i) for i in nhom])),
        "dung_yen": {
            "so_vi_tri": int(len(ds)),
            "so_vi_tri_sai": int((ds > 1).sum()),
            "loi_trung_binh": float(ds.mean()),
            "loi_trung_vi": float(np.median(ds)),
            "loi_lon_nhat": float(ds.max()),
        },
        "cua_so_truot": _cua_so_truot(tap_test, y_pred),
    }
    if tap_hoc is not None:
        kq["chuoi_dai"] = _cua_so_truot(tap_hoc, y_ngoai_phan)
    return kq


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
