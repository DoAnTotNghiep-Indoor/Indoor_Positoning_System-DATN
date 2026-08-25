"""Rà soát dữ liệu trước khi huấn luyện.

    python -m ml.audit

Chạy lại mỗi khi bổ sung dữ liệu mới. Kiểm tra quan trọng nhất là **rò rỉ giữa
các tập**: dữ liệu được thu liên tiếp tại từng điểm, mỗi điểm khoảng 20 lần quét
trong 13 phút, nên hai lần quét cách nhau vài giây gần như giống hệt nhau. Nếu
chúng rơi vào cả tập train lẫn tập test thì mô hình chỉ việc nhận ra bản sao và
mọi con số đánh giá đều vô nghĩa.

Mã thoát khác 0 nếu có cảnh báo nghiêm trọng, để dùng được trong CI.
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
BOI_PHAN_TAN = 2.0           # phân tán nội bộ vượt bấy nhiêu lần trung vị thì cảnh báo


class KetQua:
    def __init__(self) -> None:
        self.canh_bao: list[str] = []
        self.ghi_chu: list[str] = []

    def loi(self, s: str) -> None:
        self.canh_bao.append(s)
        print(f"  [!] {s}")

    def ok(self, s: str) -> None:
        print(f"  [ok] {s}")

    def chu_y(self, s: str) -> None:
        self.ghi_chu.append(s)
        print(f"  [.] {s}")


def _muc(so: int, ten: str) -> None:
    print(f"\n{'=' * 74}\n{so}. {ten}\n{'=' * 74}")


def chay() -> int:
    kq = KetQua()

    duong_dan = config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON
    if not duong_dan.exists():
        print(f"Chưa có {duong_dan}. Chạy `python -m ml.pipeline` trước.")
        return 2

    hop_dong = json.loads(duong_dan.read_text(encoding="utf-8"))
    ap = hop_dong["ap_columns"]
    gt_thieu = hop_dong["missing_rssi_value"]

    d = pd.read_csv(config.PROCESSED_DIR / "fingerprint_dataset_sorted.csv")
    raw = pd.read_csv(config.PROCESSED_DIR / "fingerprint_dataset_raw.csv")
    X = d[ap].to_numpy(float)

    print(f"Dữ liệu: {len(d)} mẫu · {len(ap)} đặc trưng · {d['rp_id'].nunique()} điểm")

    # ---------------------------------------------------------------- 1
    _muc(1, "GIÁ TRỊ HỢP LỆ")
    if np.isnan(X).any() or np.isinf(X).any():
        kq.loi(f"Có {int(np.isnan(X).sum())} ô NaN và {int(np.isinf(X).sum())} ô vô cực")
    else:
        kq.ok("Không có NaN hay vô cực")

    if d[config.TARGET_COLS].isna().any().any():
        kq.loi("Có mẫu thiếu toạ độ (x, y) — không huấn luyện hồi quy được")
    else:
        kq.ok("Mọi mẫu đều có toạ độ")

    # ---------------------------------------------------------------- 2
    _muc(2, "RÒ RỈ GIỮA CÁC TẬP")
    la_tr = (d["split"] == "train").to_numpy()
    la_te = (d["split"] == "test").to_numpy()

    if la_tr.any() and la_te.any():
        D = np.linalg.norm(X[la_te][:, None] - X[la_tr][None], axis=2)
        d1 = D.min(axis=1)
        so_ban_sao = int((d1 < NGUONG_RO_RI).sum())
        if so_ban_sao:
            kq.loi(f"{so_ban_sao}/{la_te.sum()} mẫu test có bản sao gần khít trong train "
                   f"(khoảng cách < {NGUONG_RO_RI}) — kết quả đánh giá sẽ lạc quan giả")
        else:
            kq.ok(f"Không mẫu test nào có bản sao trong train "
                  f"(gần nhất {d1.min():.3f} > {NGUONG_RO_RI})")

        tg = pd.to_datetime(d["scan_id"], format="%Y:%m:%d:%H:%M:%S", errors="coerce")
        if tg.notna().all():
            chenh = np.abs(
                (tg[la_te].to_numpy() - tg[la_tr].to_numpy()[D.argmin(axis=1)])
                / np.timedelta64(1, "s")
            )
            so_gan = int((chenh < NGUONG_GIAY).sum())
            if so_gan:
                kq.loi(f"{so_gan} mẫu test có mẫu train cách dưới {NGUONG_GIAY} giây — "
                       f"gần như cùng một phép đo")
            else:
                kq.ok(f"Mẫu test và mẫu train gần nhất cách ít nhất {chenh.min():.0f} giây")

    # ---------------------------------------------------------------- 3
    _muc(3, "CÂN BẰNG VÀ ĐỘ PHỦ")
    g = d.groupby("rp_id").size()
    kq.ok(f"Số mẫu mỗi điểm: {g.min()}–{g.max()} (trung vị {g.median():.0f})")

    ct = pd.crosstab(d["rp_id"], d["split"])
    vang = ct.index[(ct == 0).any(axis=1)].tolist()
    if vang:
        kq.loi(f"{len(vang)} điểm vắng mặt ở ít nhất một tập: {vang}")
    else:
        kq.ok("Mọi điểm đều có mặt ở cả ba tập")

    # ---------------------------------------------------------------- 4
    _muc(4, "CỘT ĐẶC TRƯNG")
    vo_dung = [c for c in ap if raw[c].nunique() == 1]
    if vo_dung:
        kq.loi(f"{len(vo_dung)} cột có giá trị hằng số, nên loại: {vo_dung}")
    else:
        kq.ok("Mọi cột đều có biến thiên")

    ty_le_thieu = (raw[ap] == gt_thieu).to_numpy().mean()
    kq.ok(f"Ô mang giá trị điền thiếu: {ty_le_thieu * 100:.1f}%")

    # ---------------------------------------------------------------- 5
    _muc(5, "ĐỘ ỔN ĐỊNH CỦA TỪNG VỊ TRÍ")
    phan_tan = raw.groupby("rp_id")[ap].apply(
        lambda x: float(np.linalg.norm(
            x.to_numpy(float) - x.to_numpy(float).mean(axis=0), axis=1
        ).mean())
    )
    trung_vi = float(phan_tan.median())
    bat_on = phan_tan[phan_tan > trung_vi * BOI_PHAN_TAN].sort_values(ascending=False)

    kq.ok(f"Phân tán nội bộ trung vị: {trung_vi:.1f}")
    if len(bat_on):
        kq.chu_y(f"{len(bat_on)} điểm có phân tán trên {BOI_PHAN_TAN:g} lần trung vị — "
                 f"môi trường sóng không ổn định, nên kiểm tra thực địa:")
        for ten, v in bat_on.items():
            print(f"        {ten}  {v:.1f}  ({v / trung_vi:.1f}× trung vị)")

    # ---------------------------------------------------------------- 5b
    _muc(6, "SO SÁNH GIỮA CÁC BUỔI THU")
    tg_raw = pd.to_datetime(raw["scan_id"], format="%Y:%m:%d:%H:%M:%S", errors="coerce")
    if tg_raw.notna().all():
        ngay = tg_raw.dt.date
        so_ap_bat = (raw[ap] > gt_thieu).sum(axis=1)
        buoi = pd.DataFrame({
            "ngay": ngay,
            "rp_id": raw["rp_id"],
            "so_ap": so_ap_bat,
        }).groupby("ngay").agg(
            so_diem=("rp_id", "nunique"),
            so_mau=("rp_id", "size"),
            ap_trung_binh=("so_ap", "mean"),
        )
        buoi["phan_tan"] = [
            float(phan_tan[raw.loc[ngay == n, "rp_id"].unique()].mean()) for n in buoi.index
        ]

        for n, r in buoi.iterrows():
            print(f"        {n}  {r.so_diem:2.0f} điểm · {r.so_mau:3.0f} mẫu · "
                  f"phân tán {r.phan_tan:5.1f} · AP trung bình {r.ap_trung_binh:4.1f}")

        tot = buoi["phan_tan"].min()
        xau = buoi[buoi["phan_tan"] > tot * 1.5]
        if len(xau):
            for n, r in xau.iterrows():
                diem = sorted(raw.loc[ngay == n, "rp_id"].unique())
                kq.chu_y(
                    f"Buổi {n} nhiễu gấp {r.phan_tan / tot:.1f} lần buổi tốt nhất và bắt được "
                    f"ít hơn {buoi['ap_trung_binh'].max() - r.ap_trung_binh:.1f} AP. "
                    f"Nên thu lại {len(diem)} điểm: {diem[0]}–{diem[-1]}"
                )
        else:
            kq.ok("Các buổi thu tương đương nhau về chất lượng")

    # ---------------------------------------------------------------- 6
    _muc(7, "TRÙNG LẶP")
    trung = int(d.duplicated(subset=ap).sum())
    if trung:
        kq.chu_y(f"{trung} vector đặc trưng trùng khít (vô hại nếu cùng điểm, cùng tập)")
    else:
        kq.ok("Không có vector trùng khít")

    # ---------------------------------------------------------------- 7
    _muc(8, "TOẠ ĐỘ ĐIỂM THAM CHIẾU")
    t = d.groupby("rp_id")[config.TARGET_COLS].first()
    if t.duplicated().any():
        kq.loi("Có hai điểm khác nhau mang cùng toạ độ")
    else:
        kq.ok(f"{len(t)} điểm, toạ độ đôi một khác nhau")

    Dt = np.linalg.norm(t.to_numpy(float)[:, None] - t.to_numpy(float)[None], axis=2)
    np.fill_diagonal(Dt, np.inf)
    kq.ok(f"Khoảng cách tới điểm lân cận: nhỏ nhất {Dt.min():.1f} m · "
          f"trung vị {np.median(Dt.min(axis=1)):.1f} m")

    # ---------------------------------------------------------------- tổng kết
    print(f"\n{'=' * 74}")
    if kq.canh_bao:
        print(f"KẾT LUẬN: {len(kq.canh_bao)} vấn đề cần xử lý trước khi huấn luyện")
        for s in kq.canh_bao:
            print(f"  - {s}")
        return 1

    print("KẾT LUẬN: dữ liệu đạt yêu cầu, huấn luyện được")
    if kq.ghi_chu:
        print(f"\n{len(kq.ghi_chu)} điểm đáng lưu ý nhưng không chặn:")
        for s in kq.ghi_chu:
            print(f"  - {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(chay())
