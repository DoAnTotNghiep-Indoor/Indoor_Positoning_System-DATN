"""Giao thức đánh giá thứ hai: bỏ trọn một điểm tham chiếu ra khỏi lúc học.

Cách chia hiện tại bốc ngẫu nhiên theo LẦN QUÉT, mà mỗi điểm chỉ được đo trong
đúng một phiên ~15 phút, cùng máy cùng ngày. Hệ quả: cả 40 điểm đều có mặt ở cả
ba tập, 75% bản ghi test có láng giềng train gần nhất nằm ngay tại điểm của
chính nó — bảng đó đo "nhận lại được lần quét vài phút trước", không phải
"định vị được một người lạ". Giao thức này giữ nguyên mô hình và tham số, chỉ
đổi cách chia: mỗi lần gấp bỏ hẳn một điểm khỏi tập huấn luyện rồi đoán các lần
quét tại chính điểm đó.

Hai con số là hai chặn của cùng một sự thật, không con nào thay được con nào:

    chia ngẫu nhiên theo lần quét  ->  chặn LẠC QUAN (rò rỉ phiên đo)
    bỏ trọn một điểm tham chiếu    ->  chặn BI QUAN  (không có dữ liệu tại chỗ)

Sai số lúc triển khai nằm giữa hai chặn. Chạy: python -m ml.danh_gia_cheo
"""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from ml import config, evaluate
from ml import preprocess as pre
from ml import models as goi_mo_hinh


def _luoi_da_dung() -> str | None:
    """Lưới mà `ml.train` đã dùng, đọc từ chính tệp cấp tham số cho hàm dưới."""
    duong_dan = config.ARTIFACTS_DIR / "model_metadata.json"
    if not duong_dan.exists():
        return None
    return json.loads(duong_dan.read_text(encoding="utf-8")).get("luoi")


def _tham_so(khoa: str, mo_dun) -> dict:
    """Tham số đã chọn lúc huấn luyện, để hai bảng so sánh cùng một cấu hình."""
    duong_dan = config.ARTIFACTS_DIR / "model_metadata.json"
    if duong_dan.exists():
        sieu = json.loads(duong_dan.read_text(encoding="utf-8"))
        muc = sieu.get("cac_mo_hinh", {}).get(khoa)
        if muc and muc.get("tham_so"):
            return muc["tham_so"]
    return {k: v[0] for k, v in mo_dun.LUOI_THAM_SO.items()}


def nap_bang_rong() -> tuple[pd.DataFrame, list[str]]:
    """Bảng vân tay dBm sau bước 4, CHƯA học tham số nào từ dữ liệu.

    Không đọc tệp pipeline ghi ra: bộ AP, giá trị điền và Hampel ở đó đều học từ
    tập train có mặt MỌI điểm, kể cả điểm mà lần gấp định giữ lại.
    """
    df = pre.build_scan_id(pre.loc_rssi_ngoai_khoang(pre.load_raw())[0])
    fp, ap_cols = pre.to_wide(df, pre.build_scan_meta(df))
    fp, _ = pre.attach_coordinates(fp)
    return fp, ap_cols


def chuan_bi_lan_gap(fp: pd.DataFrame, ap_cols: list[str]) -> list[tuple]:
    """Mỗi lần gấp giữ lại một điểm, làm lại bước 5-10 chỉ trên phần học.

    Trả [(rp, X_học, Y_học, X_thử, Y_thử)], X đã chuẩn hoá. Phần thử không qua
    Hampel: lúc chạy thật mỗi lần quét đứng một mình, không có nhóm để lọc.
    """
    ra = []
    for rp in sorted(fp["rp_id"].unique()):
        hoc, thu = fp[fp["rp_id"] != rp], fp[fp["rp_id"] == rp]
        hoc, ap, _ = pre.filter_access_points(hoc, ap_cols, tinh_tren=hoc)
        thu = thu[[c for c in thu.columns if c not in ap_cols] + ap]
        hoc, _ = pre.filter_sparse_scans(hoc, ap)
        thu, _ = pre.filter_sparse_scans(thu, ap)
        if thu.empty:
            continue
        gt = pre.compute_missing_value(hoc, ap)
        hoc, _, _ = pre.fill_missing(hoc, ap, missing_value=gt)
        thu, _, _ = pre.fill_missing(thu, ap, missing_value=gt)
        hoc, _ = pre.hampel_filter(hoc, ap, gia_tri_dien=gt)
        can = MinMaxScaler().fit(hoc[ap].to_numpy(float))
        ra.append((rp,
                   can.transform(hoc[ap].to_numpy(float)),
                   hoc[config.TARGET_COLS].to_numpy(float),
                   can.transform(thu[ap].to_numpy(float)),
                   thu[config.TARGET_COLS].to_numpy(float)))
    return ra


def chay_mot_mo_hinh(mo_dun, cac_gap: list[tuple], tham_so: dict) -> np.ndarray:
    """Sai số từng mẫu qua toàn bộ các lần gấp, đơn vị mét."""
    loi = []
    for _, Xh, Yh, Xt, Yt in cac_gap:
        mo_hinh = mo_dun.build(**tham_so)
        mo_hinh.fit(Xh, Yh)
        loi.append(evaluate.khoang_cach_loi(Yt, mo_hinh.predict(Xt)))
    return np.concatenate(loi)


def run(ten_mo_hinh: list[str] | None = None,
        cho_phep_luoi_rut_gon: bool = False) -> pd.DataFrame:
    # Bảng này lấy tham số từ model_metadata.json, tức thừa hưởng lưới mà `ml.train`
    # đã chạy. Chạy `--nhanh` rồi quên chạy lại là bảng bỏ-trọn-một-điểm mang tham
    # số của lưới rút gọn mà không dấu hiệu gì.
    luoi = _luoi_da_dung()
    if luoi not in (None, "day_du") and not cho_phep_luoi_rut_gon:
        raise SystemExit(
            f"Tham số đang lấy từ lần huấn luyện bằng lưới '{luoi}', không phải "
            f"lưới đầy đủ — bảng này không dùng cho báo cáo được.\n"
            f"Chạy `python -m ml.train` (bỏ cờ --nhanh) rồi chạy lại, hoặc thêm "
            f"`--cho-phep-luoi-rut-gon` nếu chỉ xem thử."
        )

    fp, ap_cols = nap_bang_rong()
    cac_gap = chuan_bi_lan_gap(fp, ap_cols)
    print(f"Bỏ trọn một điểm tham chiếu: {len(cac_gap)} lần gấp · {len(fp)} bản ghi "
          f"· làm lại bước 5-10 trong từng lần gấp")

    chon = goi_mo_hinh.DANH_SACH
    if ten_mo_hinh:
        muon = {t.lower() for t in ten_mo_hinh}
        chon = [m for m in chon if m.__name__.rsplit(".", 1)[-1].lower() in muon
                or m.TEN.lower() in muon]

    ket_qua = []
    for mo_dun in chon:
        khoa = mo_dun.__name__.rsplit(".", 1)[-1]
        loi = chay_mot_mo_hinh(mo_dun, cac_gap, _tham_so(khoa, mo_dun))
        # danh_gia() nhận toạ độ chứ không nhận sai số, nên dựng lại một cặp (thật,
        # dự đoán) lệch nhau đúng bằng sai số đã đo — mọi chỉ số khoảng cách và CDF
        # ra y hệt.
        khong = np.zeros((len(loi), 2))
        ket_qua.append(evaluate.danh_gia(
            khong, np.column_stack([loi, np.zeros_like(loi)]), mo_dun.TEN))

    bang = evaluate.bang_so_sanh(ket_qua)
    bang = bang.drop(columns=[c for c in ("mae_x", "mae_y", "rmse_x", "rmse_y")
                              if c in bang.columns])

    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
    config.ghi_csv(bang,
                   config.REPORTS_DIR / "tables" / "model_comparison_bo_diem.csv",
                   index=False)

    print("\n" + "=" * 72)
    print("BỎ TRỌN MỘT ĐIỂM THAM CHIẾU — toạ độ cần đoán chưa từng thấy lúc học")
    print("=" * 72)
    cot = ["mo_hinh", "loi_trung_binh", "loi_trung_vi",
           "cdf_50", "cdf_75", "cdf_90", "loi_lon_nhat"]
    print(bang[cot].to_string(index=False, float_format=lambda v: f"{v:7.2f}"))

    _in_doi_chieu(bang)
    return bang


def _in_doi_chieu(bang_bo_diem: pd.DataFrame) -> None:
    """Đặt hai giao thức cạnh nhau. Thứ hạng đảo ngược mới là điều cần thấy."""
    cu = config.REPORTS_DIR / "tables" / "model_comparison.csv"
    if not cu.exists():
        return
    ngau_nhien = pd.read_csv(cu).set_index("mo_hinh")["loi_trung_binh"]

    print("\n" + "-" * 72)
    print("HAI GIAO THỨC, CÙNG NĂM MÔ HÌNH — sai số trung bình, mét")
    print("-" * 72)
    print(f"{'mô hình':28s} {'chia ngẫu nhiên':>16s} {'bỏ trọn một điểm':>18s}")
    for _, d in bang_bo_diem.iterrows():
        a = ngau_nhien.get(d["mo_hinh"])
        print(f"{d['mo_hinh']:28s} {a:14.2f} m {d['loi_trung_binh']:16.2f} m"
              if a is not None else
              f"{d['mo_hinh']:28s} {'—':>16s} {d['loi_trung_binh']:16.2f} m")
    print("\nCột trái là chặn lạc quan, cột phải là chặn bi quan. Xem docstring "
          "đầu tệp\nvề lý do hai cột lệch nhau và vì sao thứ hạng đảo.")


if __name__ == "__main__":
    import argparse

    bo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    bo.add_argument("--mo-hinh", nargs="*", default=None,
                    help="chỉ chạy các mô hình này, mặc định chạy cả năm")
    bo.add_argument("--cho-phep-luoi-rut-gon", action="store_true",
                    help="chạy cả khi artifact sinh ra từ lưới rút gọn")
    tham = bo.parse_args()

    warnings.filterwarnings("ignore")
    run(tham.mo_hinh, tham.cho_phep_luoi_rut_gon)
