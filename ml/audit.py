"""Rà soát dữ liệu trước khi huấn luyện: `python -m ml.audit`.

Ba phép kiểm, giữ lại vì cả ba đều đã tìm ra vấn đề thật: rò rỉ giữa các tập
(mỗi điểm ~20 lần quét trong 13 phút nên hai lần cách nhau vài giây gần như
giống hệt), độ ổn định từng vị trí (11 điểm sóng bất ổn, cần đo lại), và so
sánh giữa các buổi (buổi 13/01 nhiễu gấp 2,5 lần, qua đó lộ ra mỗi điểm chỉ
được đo đúng một buổi).

Mã thoát 1 nếu phát hiện rò rỉ.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from ml import config

for _luong in (sys.stdout, sys.stderr):
    if hasattr(_luong, "reconfigure"):
        try:
            _luong.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

NGUONG_RO_RI = 0.10          # khoảng cách đặc trưng dưới mức này coi là bản sao
NGUONG_GIAY = 10             # cách nhau dưới mức này coi là cùng một phép đo
BOI_PHAN_TAN = 2.0           # phân tán vượt bấy nhiêu lần trung vị thì cảnh báo
GAN_TRONG_MAT_BANG_M = 10.0  # dưới mức này coi là cùng một chỗ trên mặt bằng


def kiem_mot_tang(raw, ap, rp) -> tuple[bool, list[str]]:
    """Bằng chứng dữ liệu nằm trên MỘT mặt phẳng. Trả (có vấn đề chặn, các dòng in).

    Điểm ở tầng khác nhưng bị gán toạ độ tầng 1 lộ ra theo hai cách: trùng khít
    toạ độ với một điểm khác, hoặc gần nhau trên bản vẽ mà vân tay lệch hẳn.
    """
    chan, ra = False, []

    cot_tang = [c for c in rp.columns if c.lower() in ("tang", "floor", "floor_id")]
    if cot_tang:
        chan = True
        ra.append(f"  [!] Bảng toạ độ có cột '{cot_tang[0]}' mà pipeline không đọc "
                  f"— nhiều tầng đang bị trộn thành một mặt phẳng")

    van = raw.groupby("rp_id")[ap].mean()
    toa = raw.groupby("rp_id")[["x", "y"]].first().loc[van.index]
    ten = list(van.index)
    XY, VT = toa.to_numpy(float), van.to_numpy(float)
    d2d = np.linalg.norm(XY[:, None] - XY[None], axis=2)
    dvt = np.linalg.norm(VT[:, None] - VT[None], axis=2)
    tren = np.triu_indices(len(ten), 1)

    chong = [(ten[i], ten[j]) for i, j in zip(*tren) if d2d[i, j] == 0]
    if chong:
        chan = True
        ra.append(f"  [!] {len(chong)} cặp điểm trùng khít toạ độ: {chong[:4]}")
    else:
        ra.append(f"  [ok] {len(ten)} điểm, không cặp nào trùng toạ độ")

    gan = [(i, j) for i, j in zip(*tren) if d2d[i, j] < GAN_TRONG_MAT_BANG_M]
    nguong = float(np.percentile(dvt[tren], 75))
    la = [(ten[i], ten[j], d2d[i, j]) for i, j in gan if dvt[i, j] > nguong]
    if la:
        ra.append(f"  [.] {len(la)}/{len(gan)} cặp gần nhau nhưng vân tay khác hẳn: "
                  + ", ".join(f"{p}-{q} ({k:.0f} m)" for p, q, k in la[:3]))
    else:
        ra.append(f"  [ok] {len(gan)} cặp cách dưới {GAN_TRONG_MAT_BANG_M:.0f} m đều "
                  f"có vân tay tương ứng — nhất quán với một tầng")
    return chan, ra

def kiem_diem_thieu_van_tay(raw, rp) -> list[str]:
    """Điểm có toạ độ nhưng không lần quét nào — mô hình không bao giờ báo ra được.

    Không phải lỗi: `/route` vẫn dẫn tới chúng, và một cái WC thì cần chỉ đường
    chứ không cần nhận dạng. Nhưng khoảng cách giữa số điểm trên bản đồ và số
    điểm huấn luyện phải hiện ra, vì nó lặng lẽ giới hạn phạm vi định vị.
    """
    co_toa_do = rp.dropna(subset=["x", "y"])
    thieu = sorted(set(co_toa_do["rp_id"]) - set(raw["rp_id"]))
    if not thieu:
        return [f"  [ok] cả {len(co_toa_do)} điểm trên bản đồ đều có vân tay"]

    theo_nhom = {}
    for r in co_toa_do[co_toa_do.rp_id.isin(thieu)].itertuples():
        theo_nhom.setdefault(str(r.nhom), []).append(r.rp_id)
    mo_ta = " · ".join(f"{n}: {', '.join(v)}" for n, v in sorted(theo_nhom.items()))
    return [f"  [.] {len(thieu)}/{len(co_toa_do)} điểm trên bản đồ không có vân tay "
            f"— chỉ đường tới được, định vị thì không",
            f"      {mo_ta}"]


def chay() -> int:
    hop_dong = json.loads(
        (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8")
    )
    ap = hop_dong["ap_columns"]
    gt_thieu = hop_dong["missing_rssi_value"]

    d = pd.read_csv(config.PROCESSED_DIR / "fingerprint_dataset_sorted.csv")
    raw = pd.read_csv(config.PROCESSED_DIR / "fingerprint_dataset_raw.csv")
    X = d[ap].to_numpy(float)
    ro_ri = False

    print(f"{len(d)} mẫu · {len(ap)} đặc trưng · {d['rp_id'].nunique()} điểm")

    print("\n1. RÒ RỈ GIỮA CÁC TẬP")
    la_tr = (d["split"] == "train").to_numpy()
    la_te = (d["split"] == "test").to_numpy()
    D = np.linalg.norm(X[la_te][:, None] - X[la_tr][None], axis=2)

    ban_sao = int((D.min(axis=1) < NGUONG_RO_RI).sum())
    if ban_sao:
        ro_ri = True
        print(f"  [!] {ban_sao}/{la_te.sum()} mẫu test có bản sao gần khít trong train "
              f"— kết quả đánh giá sẽ lạc quan giả")
    else:
        print(f"  [ok] Không mẫu test nào có bản sao (gần nhất {D.min():.3f})")

    tg = pd.to_datetime(d["scan_id"], format="%Y:%m:%d:%H:%M:%S")
    chenh = np.abs(
        (tg[la_te].to_numpy() - tg[la_tr].to_numpy()[D.argmin(axis=1)]) / np.timedelta64(1, "s")
    )
    if (chenh < NGUONG_GIAY).sum():
        ro_ri = True
        print(f"  [!] {int((chenh < NGUONG_GIAY).sum())} mẫu test có mẫu train cách dưới "
              f"{NGUONG_GIAY} giây — gần như cùng một phép đo")
    else:
        print(f"  [ok] Mẫu train gần nhất cách ít nhất {chenh.min():.0f} giây")

    print("\n2. ĐỘ ỔN ĐỊNH CỦA TỪNG VỊ TRÍ")
    phan_tan = raw.groupby("rp_id")[ap].apply(
        lambda x: float(np.linalg.norm(
            x.to_numpy(float) - x.to_numpy(float).mean(axis=0), axis=1
        ).mean())
    )
    trung_vi = float(phan_tan.median())
    bat_on = phan_tan[phan_tan > trung_vi * BOI_PHAN_TAN].sort_values(ascending=False)

    print(f"  Phân tán nội bộ trung vị: {trung_vi:.1f}")
    for ten, v in bat_on.items():
        print(f"    {ten}  {v:.1f}  ({v / trung_vi:.1f}x trung vị) — nên kiểm tra thực địa")

    print("\n3. SO SÁNH GIỮA CÁC BUỔI THU")
    ngay = pd.to_datetime(raw["scan_id"], format="%Y:%m:%d:%H:%M:%S").dt.date
    buoi = pd.DataFrame({
        "ngay": ngay,
        "rp_id": raw["rp_id"],
        "so_ap": (raw[ap] > gt_thieu).sum(axis=1),
    }).groupby("ngay").agg(
        so_diem=("rp_id", "nunique"), so_mau=("rp_id", "size"), ap_tb=("so_ap", "mean")
    )
    buoi["phan_tan"] = [
        float(phan_tan[raw.loc[ngay == n, "rp_id"].unique()].mean()) for n in buoi.index
    ]

    for n, r in buoi.iterrows():
        diem = sorted(raw.loc[ngay == n, "rp_id"].unique())
        print(f"  {n}  {r.so_diem:2.0f} điểm ({diem[0]}–{diem[-1]}) · {r.so_mau:3.0f} mẫu · "
              f"phân tán {r.phan_tan:5.1f} · AP trung bình {r.ap_tb:4.1f}")

    tot = buoi["phan_tan"].min()
    for n, r in buoi[buoi["phan_tan"] > tot * 1.5].iterrows():
        print(f"  [.] Buổi {n} nhiễu gấp {r.phan_tan / tot:.1f} lần buổi tốt nhất và bắt được "
              f"ít hơn {buoi['ap_tb'].max() - r.ap_tb:.1f} AP — nên thu lại")

    print("\n4. GIẢ THIẾT MỘT TẦNG")
    rp = pd.read_csv(config.REFERENCE_POINTS_CSV, encoding="utf-8-sig")
    chan_tang, dong_in = kiem_mot_tang(raw, ap, rp)
    ro_ri = ro_ri or chan_tang
    for _d in dong_in:
        print(_d)

    print("\n5. PHẠM VI ĐỊNH VỊ")
    for _d in kiem_diem_thieu_van_tay(raw, rp):
        print(_d)

    print("\n" + ("KẾT LUẬN: có rò rỉ, không tin được kết quả đánh giá" if ro_ri
                  else "KẾT LUẬN: dữ liệu đạt yêu cầu, huấn luyện được"))
    return 1 if ro_ri else 0


if __name__ == "__main__":
    raise SystemExit(chay())
