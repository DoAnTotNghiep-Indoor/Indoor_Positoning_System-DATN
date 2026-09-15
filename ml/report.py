"""Sinh biểu đồ báo cáo từ artifact hiện có.

    python -m ml.report

Đọc `artifacts/model_metadata.json` và các model đã huấn luyện, ghi ảnh vào
`reports/figures/`. Chạy sau mỗi lần `ml.train` để hình không lệch số liệu.

Ba trong năm màu của bảng đã kiểm định có tương phản dưới 3:1 trên nền sáng nên
biểu đồ cột đều ghi nhãn giá trị và biểu đồ đường dùng thêm kiểu nét đứt khác
nhau — vừa bù tương phản, vừa đọc được khi in đen trắng.
"""

from __future__ import annotations

import importlib
import json
import sys

import joblib
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ml import config, evaluate, postprocess  # noqa: E402

for _luong in (sys.stdout, sys.stderr):
    if hasattr(_luong, "reconfigure"):
        try:
            _luong.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

# --- Bảng màu đã qua validator (chế độ sáng, nền #fcfcfb) ---
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
NET = ["-", "--", "-.", ":", (0, (3, 1, 1, 1, 1, 1))]

SURFACE = "#fcfcfb"
MUC_CHINH = "#0b0b0b"
MUC_PHU = "#52514e"
MUC_MO = "#898781"
LUOI = "#e1e0d9"
TRUC = "#c3c2b7"

# Ramp một sắc cho mã hoá độ lớn liên tục
RAMP_XANH = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def _khung(ax) -> None:
    """Lưới và trục lùi về sau, để dữ liệu nổi lên trước."""
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=LUOI, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for vt in ("top", "right"):
        ax.spines[vt].set_visible(False)
    for vt in ("left", "bottom"):
        ax.spines[vt].set_color(TRUC)
        ax.spines[vt].set_linewidth(1)
    ax.tick_params(colors=MUC_MO, labelsize=9, length=0)
    for nhan in ax.get_xticklabels() + ax.get_yticklabels():
        nhan.set_color(MUC_PHU)


def _luu(fig, ten: str) -> str:
    thu_muc = config.REPORTS_DIR / "figures"
    thu_muc.mkdir(parents=True, exist_ok=True)
    duong_dan = thu_muc / ten
    fig.savefig(duong_dan, dpi=200, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    return f"  {duong_dan.stat().st_size / 1024:6.1f} KB  {duong_dan.name}"


def nap():
    meta = json.loads((config.ARTIFACTS_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    fl = json.loads((config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8"))
    te = pd.read_csv(config.SPLITS_DIR / "test.csv")
    ap = fl["ap_columns"]

    loi, du_doan = {}, {}
    for khoa, tt in meta["cac_mo_hinh"].items():
        m = joblib.load(config.ARTIFACTS_DIR / f"model_{khoa}.pkl")
        p = m.predict(te[ap].to_numpy(float))
        du_doan[tt["ten"]] = p
        loi[tt["ten"]] = evaluate.khoang_cach_loi(te[["x", "y"]].to_numpy(float), p)

    # xếp theo sai số trung bình để màu gắn với thứ hạng ổn định giữa các hình
    thu_tu = sorted(loi, key=lambda t: loi[t].mean())
    return meta, te, ap, loi, du_doan, thu_tu


def so_sanh_mo_hinh(loi: dict, thu_tu: list[str]) -> str:
    """Cột ngang: sai số trung bình và CDF90. Cùng đơn vị mét nên chung một trục."""
    tb = [loi[t].mean() for t in thu_tu]
    p90 = [np.percentile(loi[t], 90) for t in thu_tu]
    vt = np.arange(len(thu_tu))
    cao = 0.36

    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    _khung(ax)
    ax.barh(vt - cao / 2 - 0.01, tb, cao, color=SERIES[0], label="Sai số trung bình", zorder=3)
    ax.barh(vt + cao / 2 + 0.01, p90, cao, color=SERIES[1], label="CDF90", zorder=3)

    for i, (a, b) in enumerate(zip(tb, p90)):
        ax.text(a + 0.35, i - cao / 2 - 0.01, f"{a:.2f}", va="center", fontsize=8.5, color=MUC_CHINH)
        ax.text(b + 0.35, i + cao / 2 + 0.01, f"{b:.2f}", va="center", fontsize=8.5, color=MUC_CHINH)

    ax.set_yticks(vt)
    ax.set_yticklabels(thu_tu, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Sai số khoảng cách (m)", color=MUC_PHU, fontsize=9.5)
    ax.set_xlim(0, max(p90) * 1.16)
    ax.set_title("Sai số định vị trên tập test, một lần quét",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", loc="left", pad=30)
    # Đặt chú giải ngoài vùng vẽ: cột dài nhất chạm sát mép phải nên mọi vị trí
    # bên trong đều đè lên dữ liệu hoặc nhãn giá trị.
    ax.legend(frameon=False, fontsize=9, labelcolor=MUC_PHU, ncol=2,
              loc="lower left", bbox_to_anchor=(0, 1.005))
    return _luu(fig, "model_comparison.png")


def cdf(loi: dict, thu_tu: list[str]) -> str:
    """Đường CDF. Kiểu nét khác nhau để đọc được cả khi in đen trắng."""
    fig, ax = plt.subplots(figsize=(8, 4.8))
    _khung(ax)

    for i, ten in enumerate(thu_tu):
        x, y = evaluate.duong_cdf(loi[ten])
        ax.plot(x, y, color=SERIES[i], linestyle=NET[i], linewidth=2,
                label=ten, zorder=3, solid_capstyle="round")

    for p in (50, 75, 90):
        ax.axhline(p, color=TRUC, linewidth=0.8, linestyle=":", zorder=1)
        ax.text(ax.get_xlim()[1], p, f" {p}%", va="center", fontsize=8, color=MUC_MO)

    ax.set_xlabel("Sai số khoảng cách (m)", color=MUC_PHU, fontsize=9.5)
    ax.set_ylabel("Tỉ lệ tích luỹ số mẫu (%)", color=MUC_PHU, fontsize=9.5)
    ax.set_ylim(0, 101)
    ax.set_title("Phân bố tích luỹ sai số — đọc theo chiều ngang tại mốc 90%",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", loc="left", pad=12)
    ax.legend(frameon=False, fontsize=9, loc="lower right", labelcolor=MUC_PHU)
    return _luu(fig, "cdf_error.png")


def hieu_qua_gop(meta: dict, te: pd.DataFrame, ap: list[str], du_doan: dict) -> str:
    """Bốn cách gộp của mô hình đang triển khai, theo hai chế độ.

    `đứng yên` gộp mọi lần quét của một điểm test — chặn dưới lý tưởng. `cửa sổ
    trượt` chạy như `BoGop` trên chuỗi dài của train+val theo thời gian, dự đoán
    ngoài phần để mô hình chưa thấy mẫu nào nó đoán.
    """
    khoa = meta["mo_hinh_active"]
    tt = meta["cac_mo_hinh"][khoa]
    p, y = du_doan[tt["ten"]], te[["x", "y"]].to_numpy(float)
    hoc = pd.concat([pd.read_csv(config.SPLITS_DIR / f"{t}.csv") for t in ("train", "validation")],
                    ignore_index=True)
    yh = hoc[["x", "y"]].to_numpy(float)
    q = evaluate.du_doan_ngoai_phan(importlib.import_module(f"ml.models.{khoa}"), tt["tham_so"],
                                    hoc[ap].to_numpy(float), yh, hoc["rp_id"])
    w = postprocess.CUA_SO_MAC_DINH

    def dung_yen(fn):
        return np.array([np.linalg.norm(fn(p[i]) - y[i[0]]) for i in evaluate.nhom_theo_thoi_gian(te)])

    def truot(fn):
        return np.concatenate([
            np.linalg.norm(np.array([fn(q[i][max(0, k - w + 1): k + 1]) for k in range(len(i))])
                           - yh[i], axis=1)
            for i in evaluate.nhom_theo_thoi_gian(hoc)])

    def binh_chon(P):
        u, c = np.unique(P, axis=0, return_counts=True)
        return u[c.argmax()]

    fn = {"Bình chọn đa số": binh_chon,
          "Trung vị toạ độ": postprocess.trung_vi_toa_do,
          "Đồng thuận không gian": postprocess.dong_thuan_khong_gian}

    ten = ["Một lần quét", *fn]
    dy = [np.linalg.norm(p - y, axis=1)] + [dung_yen(f) for f in fn.values()]
    ct = [np.linalg.norm(q - yh, axis=1)] + [truot(f) for f in fn.values()]

    vt = np.arange(len(ten))
    rong = 0.38

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.1))
    for ax, lay, nhan in ((ax1, lambda a: a.mean(), "Sai số trung bình (m)"),
                          (ax2, lambda a: a.max(), "Sai số lớn nhất (m)")):
        _khung(ax)
        a, b = [lay(v) for v in dy], [lay(v) for v in ct]
        ax.bar(vt - rong / 2, a, rong, color=SERIES[0], label="đứng yên (test)", zorder=3)
        ax.bar(vt + rong / 2, b, rong, color=SERIES[1], label="cửa sổ trượt (train+val, ngoài phần)", zorder=3)
        cao = max(max(a), max(b))
        for i in vt:
            for x, v in ((i - rong / 2, a[i]), (i + rong / 2, b[i])):
                ax.text(x, v + cao * 0.03, f"{v:.2f}", ha="center",
                        fontsize=8, color=MUC_CHINH, fontweight="bold")
        ax.set_xticks(vt)
        ax.set_xticklabels([t.replace(" ", "\n", 1) for t in ten], fontsize=8.5)
        ax.set_ylabel(nhan, color=MUC_PHU, fontsize=9.5)
        ax.set_ylim(0, cao * 1.2)
    ax1.legend(frameon=False, fontsize=9, labelcolor=MUC_PHU)

    fig.suptitle("Hiệu quả gộp lần quét — chặn dưới lý tưởng so với lúc chạy thật",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", x=0.06, ha="left", y=1.02)
    fig.tight_layout()
    return _luu(fig, "aggregation_effect.png")


def ban_do_loi(meta: dict, te: pd.DataFrame, du_doan: dict) -> str:
    """Sai số theo vị trí của mô hình đang triển khai. Độ lớn liên tục nên dùng
    ramp một sắc."""
    ten = meta["cac_mo_hinh"][meta["mo_hinh_active"]]["ten"]
    theo_diem = evaluate.loi_theo_diem(
        te["rp_id"], te[["x", "y"]].to_numpy(float), du_doan[ten])

    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("xanh", RAMP_XANH)

    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    _khung(ax)
    sc = ax.scatter(theo_diem["x"], theo_diem["y"], c=theo_diem["loi_trung_binh"],
                    s=330, cmap=cmap, edgecolor=SURFACE, linewidth=1.6, zorder=3)

    for r in theo_diem.itertuples():
        sang = r.loi_trung_binh < theo_diem["loi_trung_binh"].max() * 0.55
        ax.annotate(r.rp_id.replace("RP", ""), (r.x, r.y), fontsize=7,
                    ha="center", va="center", zorder=4,
                    color=MUC_CHINH if sang else "#ffffff")

    cb = fig.colorbar(sc, ax=ax, pad=0.02)
    cb.set_label("Sai số trung bình (m)", color=MUC_PHU, fontsize=9.5)
    cb.ax.tick_params(colors=MUC_MO, labelsize=8.5, length=0)
    cb.outline.set_visible(False)

    ax.set_xlabel("x (m)", color=MUC_PHU, fontsize=9.5)
    ax.set_ylabel("y (m)", color=MUC_PHU, fontsize=9.5)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title(f"Sai số theo vị trí — {ten}",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", loc="left", pad=12)
    return _luu(fig, "error_heatmap.png")


def do_quan_trong(ap: list[str]) -> str | None:
    """Độ quan trọng đặc trưng của XGBoost, tách theo trục x và y."""
    tep = config.ARTIFACTS_DIR / "model_xgboost_model.pkl"
    if not tep.exists():
        return None

    from ml.models import xgboost_model
    q = pd.DataFrame(xgboost_model.do_quan_trong_dac_trung(joblib.load(tep), ap))
    q["tong"] = q.sum(axis=1)
    q = q.sort_values("tong", ascending=False).head(15)

    vt = np.arange(len(q))
    cao = 0.38
    fig, ax = plt.subplots(figsize=(8, 5.2))
    _khung(ax)
    ax.barh(vt - cao / 2, q["x"], cao, color=SERIES[0], label="trục x", zorder=3)
    ax.barh(vt + cao / 2, q["y"], cao, color=SERIES[1], label="trục y", zorder=3)

    # Phải giữ octet đầu: 88:dc:97 và 8e:dc:97 là hai BSSID ảo của CÙNG một radio
    # và chỉ khác nhau ở đó. Cắt mất octet đầu thì nhãn trùng nhau, không đọc được.
    ax.set_yticks(vt)
    ax.set_yticklabels([f"{b[:2]}…{b[-8:]}" for b in q.index],
                       fontsize=8, fontfamily="monospace")
    ax.invert_yaxis()
    ax.set_xlabel("Độ quan trọng", color=MUC_PHU, fontsize=9.5)
    ax.set_title("15 access point đóng góp nhiều nhất — XGBoost",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", loc="left", pad=12)
    ax.legend(frameon=False, fontsize=9, labelcolor=MUC_PHU)
    return _luu(fig, "feature_importance.png")


def phan_bo_sai_so(loi: dict, thu_tu: list[str]) -> str:
    """Histogram sai số từng mô hình. Bảng so sánh chỉ cho một con số trung bình,
    hình này cho thấy con số đó đến từ phân bố như thế nào."""
    n = len(thu_tu)
    cao_nhat = max(np.histogram(loi[t], bins=20)[0].max() for t in thu_tu)
    xa_nhat = max(loi[t].max() for t in thu_tu)

    fig, trucs = plt.subplots(1, n, figsize=(2.7 * n, 3.4), sharey=True)
    for ax, ten, mau in zip(trucs, thu_tu, SERIES):
        _khung(ax)
        ax.hist(loi[ten], bins=20, range=(0, xa_nhat), color=mau, zorder=3)
        tb = loi[ten].mean()
        ax.axvline(tb, color=MUC_CHINH, linestyle="--", linewidth=1.2, zorder=4)
        ax.set_title(f"{ten}\ntrung bình {tb:.2f} m",
                     color=MUC_CHINH, fontsize=9.5, pad=8)
        ax.set_xlabel("Sai số (m)", color=MUC_PHU, fontsize=9)
        ax.set_ylim(0, cao_nhat * 1.08)

    trucs[0].set_ylabel("Số mẫu", color=MUC_PHU, fontsize=9.5)
    fig.suptitle("Phân bố sai số — đường đứt là giá trị trung bình",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", x=0.5, y=1.06)
    return _luu(fig, "error_distribution.png")


def ti_le_xuat_hien_ap() -> str | None:
    """Biện minh cho ngưỡng lọc AP: đường cong dốc đứng ngay tại ngưỡng đã chọn.
    Đọc bảng do ml/pipeline.py ghi ra chứ không tự tính lại, để hình luôn khớp
    đúng lần chạy pipeline hiện tại.

    Bảng ấy tính TRÊN TẬP TRAIN — bước 5 chỉ được học từ train để việc chọn đặc
    trưng không nhìn val/test. Nhãn phải nói rõ, nếu không hình đọc như thể tính
    trên toàn bộ dữ liệu.
    """
    tep = config.REPORTS_DIR / "tables" / "ap_appearance_rate.csv"
    if not tep.exists():
        return None

    ty_le = pd.read_csv(tep, index_col=0)["ty_le_xuat_hien"].sort_values() * 100
    nguong = config.MIN_APPEAR_RATE * 100
    giu = ty_le >= nguong

    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    _khung(ax)
    vt = np.arange(len(ty_le))
    ax.bar(vt[~giu], ty_le[~giu], 1.0, color=SERIES[1], label=f"loại ({(~giu).sum()} AP)", zorder=3)
    ax.bar(vt[giu], ty_le[giu], 1.0, color=SERIES[0], label=f"giữ ({giu.sum()} AP)", zorder=3)
    ax.axhline(nguong, color=MUC_CHINH, linestyle="--", linewidth=1.2, zorder=4)
    ax.text(0, nguong + 2.5, f"ngưỡng {nguong:.0f}%", color=MUC_CHINH, fontsize=9)

    ax.set_xlabel("Access point, xếp theo tỉ lệ xuất hiện trên tập train",
                  color=MUC_PHU, fontsize=9.5)
    ax.set_ylabel("Tỉ lệ xuất hiện trên tập train (%)", color=MUC_PHU, fontsize=9.5)
    ax.set_xlim(-1, len(ty_le))
    ax.set_ylim(0, 104)
    ax.set_title("Tỉ lệ xuất hiện của access point trên tập train — cơ sở chọn ngưỡng",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", loc="left", pad=12)
    ax.legend(frameon=False, fontsize=9, labelcolor=MUC_PHU, loc="upper left")
    return _luu(fig, "ap_appearance_rate.png")


def chay(cho_phep_luoi_rut_gon: bool = False) -> None:
    meta, te, ap, loi, du_doan, thu_tu = nap()

    # `ml.train --nhanh` ghi đè artifact y như lần chạy đầy đủ, chỉ khác đúng
    # trường này. Không chặn thì hình và bảng trong báo cáo vẫn sinh ra bình
    # thường nhưng mang số của lưới rút gọn.
    if meta.get("luoi") != "day_du" and not cho_phep_luoi_rut_gon:
        raise SystemExit(
            f"Artifact hiện tại huấn luyện bằng lưới '{meta.get('luoi')}', không "
            f"phải lưới đầy đủ — số liệu này không dùng cho báo cáo được.\n"
            f"Chạy `python -m ml.train` (bỏ cờ --nhanh) rồi sinh hình lại, hoặc "
            f"`python -m ml.report --cho-phep-luoi-rut-gon` nếu chỉ xem thử."
        )

    print(f"Huấn luyện lúc {meta['huan_luyen_luc']} · {len(thu_tu)} mô hình · "
          f"{len(te)} mẫu test\n")

    # Hình của MỘT mô hình vẽ mô hình đang triển khai (chọn theo validation),
    # không lấy mô hình tốt nhất trên test.
    ket_qua = [
        so_sanh_mo_hinh(loi, thu_tu),
        cdf(loi, thu_tu),
        hieu_qua_gop(meta, te, ap, du_doan),
        ban_do_loi(meta, te, du_doan),
        do_quan_trong(ap),
        phan_bo_sai_so(loi, thu_tu),
        ti_le_xuat_hien_ap(),
    ]
    for d in ket_qua:
        if d:
            print(d)
    print(f"\nĐã ghi vào {config.REPORTS_DIR / 'figures'}")


if __name__ == "__main__":
    chay(cho_phep_luoi_rut_gon="--cho-phep-luoi-rut-gon" in sys.argv)
