"""Năm mô hình của đề tài trên bộ dữ liệu công khai UJIIndoorLoc.

    python -m ml.ujiindoorloc

Học trên `trainingData.csv`, kiểm trên `validationData.csv` (đo sau 4 tháng, người và máy
khác) — đúng giao thức công bố của bộ dữ liệu. Toạ độ `LONGITUDE`, `LATITUDE` đã là mét. Hai
cách đo sai số 2D:

    toàn bộ        trên cả 1.111 mẫu kiểm — cách CCpos báo cáo
    đúng toà+tầng  chỉ trên mẫu đoán đúng cả toà nhà và tầng (Torres-Sospedra và c.s., 2015),
                   kèm tỉ lệ đoán đúng — cách nhóm hợp tác báo cáo kNN Sørensen

Toà và tầng đoán bằng kNN Sørensen (Bray-Curtis) + powed, k = 7, bỏ phiếu — dùng chung cho
mọi mô hình để cột thứ hai chỉ khác nhau ở toạ độ.

Tiền xử lý theo cùng tinh thần pipeline của thư viện: RSSI 100 (không bắt được) thành ô trống,
bỏ AP chưa bao giờ bắt được trong tập học, điền thiếu bằng giá trị nhỏ nhất trừ 1, chuẩn hoá
min-max học trên tập học. Tham số chọn bằng lưới rút gọn (`LUOI_NHANH`) trên 15% tập học tách
riêng. kNN k động chọn ngưỡng và k lớn trên một mẫu con của tập học (giả lập bỏ trọn
từng điểm trên ~900 toạ độ × 20 nghìn lần quét quá chậm), rồi dựng trên toàn bộ tập học.
"""

from __future__ import annotations

import time
import warnings
from itertools import product

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler

from ml import config, evaluate
from ml import models as goi_mo_hinh
from ml.models import fingerprint_knn_dong as kdong

THU_MUC = config.RAW_DIR / "ujiindoorloc"
KHONG_BAT = 100
MAU_CON_K_DONG = 5000
K_TOA_TANG = 7


def nap() -> tuple:
    hoc = pd.read_csv(THU_MUC / "trainingData.csv")
    thu = pd.read_csv(THU_MUC / "validationData.csv")
    wap = [c for c in hoc.columns if c.startswith("WAP")]
    Xh = hoc[wap].replace(KHONG_BAT, np.nan)
    Xt = thu[wap].replace(KHONG_BAT, np.nan)
    giu = Xh.columns[Xh.notna().any()]
    gia_tri_dien = float(np.nanmin(Xh[giu].to_numpy())) - 1
    Xh, Xt = Xh[giu].fillna(gia_tri_dien), Xt[giu].fillna(gia_tri_dien)
    can = MinMaxScaler().fit(Xh.to_numpy(float))
    toa = ["LONGITUDE", "LATITUDE"]
    print(f"UJIIndoorLoc: học {len(Xh)} · kiểm {len(Xt)} · {len(giu)}/{len(wap)} AP · "
          f"điền {gia_tri_dien:.0f} dBm · {hoc[toa].drop_duplicates().shape[0]} toạ độ học")
    nhan = lambda d: (d["BUILDINGID"] * 10 + d["FLOOR"]).to_numpy()
    return (can.transform(Xh.to_numpy(float)), hoc[toa].to_numpy(float),
            np.clip(can.transform(Xt.to_numpy(float)), 0, None), thu[toa].to_numpy(float),
            nhan(hoc), nhan(thu))


def doan_toa_tang(Xh, nhan_hoc, Xt, beta: float = 4.0) -> np.ndarray:
    """Mã toà × 10 + tầng của từng mẫu kiểm, bỏ phiếu k láng giềng Sørensen trên biểu diễn powed."""
    clf = KNeighborsClassifier(n_neighbors=K_TOA_TANG, metric="braycurtis", algorithm="brute")
    return clf.fit(kdong.bieu_dien_powed(Xh, beta), nhan_hoc).predict(kdong.bieu_dien_powed(Xt, beta))


def chon_tham_so(mo_dun, X, Y) -> dict:
    luoi = getattr(mo_dun, "LUOI_NHANH", mo_dun.LUOI_THAM_SO)
    to_hop = [dict(zip(luoi, v)) for v in product(*luoi.values())]
    if len(to_hop) == 1:
        return to_hop[0]
    Xa, Xb, Ya, Yb = train_test_split(X, Y, test_size=0.15, random_state=config.RANDOM_STATE)
    return min(to_hop, key=lambda t: evaluate.khoang_cach_loi(
        Yb, mo_dun.build(**t).fit(Xa, Ya).predict(Xb)).mean())


def dung_k_dong(tham_so: dict, X, Y):
    chon = np.random.default_rng(config.RANDOM_STATE).choice(len(X), MAU_CON_K_DONG, replace=False)
    ca = kdong.tinh_ca_ben_trong(X[chon], Y[chon], tham_so.get("beta", 4.0), tham_so.get("power", 1.0))
    nguong, _, k_lon = kdong.chon_tham_so(ca)
    return kdong.DinhViKDong(nguong=nguong, k_lon=k_lon, **tham_so).fit(X, Y)


def run() -> pd.DataFrame:
    Xh, Yh, Xt, Yt, nhan_hoc, nhan_thu = nap()
    dung = doan_toa_tang(Xh, nhan_hoc, Xt) == nhan_thu
    print(f"  đoán đúng toà nhà + tầng: {dung.mean():.2%} ({dung.sum()}/{len(dung)})")
    ket_qua = []
    for mo_dun in goi_mo_hinh.DANH_SACH:
        t = time.time()
        tham_so = chon_tham_so(mo_dun, Xh, Yh)
        mo_hinh = dung_k_dong(tham_so, Xh, Yh) if mo_dun is kdong else mo_dun.build(**tham_so).fit(Xh, Yh)
        P = mo_hinh.predict(Xt)
        kq = evaluate.danh_gia(Yt, P, mo_dun.TEN)
        loi_dung = evaluate.khoang_cach_loi(Yt[dung], P[dung])
        kq["loi_trung_binh_dung_toa_tang"] = float(loi_dung.mean())
        kq["ti_le_dung_toa_tang"] = float(dung.mean())
        kq["tham_so"] = str(tham_so)
        ket_qua.append(kq)
        print(f"  {mo_dun.TEN:36s} TB {kq['loi_trung_binh']:6.2f} m · trung vị "
              f"{kq['loi_trung_vi']:5.2f} m · CDF90 {kq['cdf_90']:6.2f} m · "
              f"đúng toà+tầng {loi_dung.mean():5.2f} m · {time.time() - t:.0f}s")

    bang = evaluate.bang_so_sanh(ket_qua)
    (config.REPORTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
    config.ghi_csv(bang, config.REPORTS_DIR / "tables" / "ujiindoorloc.csv", index=False)
    return bang


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    run()
