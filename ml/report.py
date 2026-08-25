"""Sinh biểu đồ báo cáo từ artifact hiện có.

    python -m ml.report

Đọc `artifacts/model_metadata.json` và các tệp model đã huấn luyện, ghi ảnh vào
`reports/figures/`. Chạy sau mỗi lần `python -m ml.train` để hình không lệch số
liệu — đây là lý do module này tồn tại thay vì để mã vẽ nằm trong notebook.

Bảng màu lấy từ bảng phân loại đã kiểm định (blue, orange, aqua, yellow,
magenta). Ba màu aqua, yellow, magenta có tương phản dưới 3:1 trên nền sáng nên
mọi biểu đồ cột đều ghi nhãn giá trị hiện rõ, và biểu đồ đường dùng thêm kiểu nét
đứt khác nhau — vừa để bù tương phản, vừa để đọc được khi in đen trắng.

Hình xuất ra dùng cho báo cáo in nên chỉ làm một chế độ sáng, không làm nền tối.
"""

from __future__ import annotations

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


# ---------------------------------------------------------------- hình 1
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


# ---------------------------------------------------------------- hình 2
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


# ---------------------------------------------------------------- hình 3
def hieu_qua_gop(te: pd.DataFrame, du_doan: dict, thu_tu: list[str]) -> str:
    """Bốn cách gộp lần quét, so trên sai số trung bình và lớn nhất."""
    p = du_doan[thu_tu[0]]
    y = te[["x", "y"]].to_numpy(float)
    nhom = [nh["_i"].to_numpy() for _, nh in te.assign(_i=range(len(te))).groupby("rp_id")]

    def do(fn):
        return np.array([np.linalg.norm(fn(p[i]) - y[i[0]]) for i in nhom])

    def binh_chon(P):
        u, c = np.unique(P, axis=0, return_counts=True)
        return u[c.argmax()]

    cach = {
        # Một lần quét: lấy sai số của TỪNG lần quét, không lấy trung bình theo
        # điểm. Cả bốn cột phải cùng trả lời một câu hỏi — người dùng hỏi một
        # lần thì nhận sai số bao nhiêu — nên gộp trung bình trước sẽ giấu mất
        # đúng những ca tệ nhất mà việc gộp sinh ra để xử lý.
        "Một lần quét": evaluate.khoang_cach_loi(y, p),
        "Bình chọn đa số": do(binh_chon),
        "Trung vị toạ độ": do(postprocess.trung_vi_toa_do),
        "Đồng thuận không gian": do(postprocess.dong_thuan_khong_gian),
    }

    ten = list(cach)
    tb = [cach[t].mean() for t in ten]
    mx = [cach[t].max() for t in ten]
    vt = np.arange(len(ten))
    rong = 0.36

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.9))
    for ax, gt, nhan, mau in ((ax1, tb, "Sai số trung bình (m)", SERIES[0]),
                              (ax2, mx, "Sai số lớn nhất (m)", SERIES[1])):
        _khung(ax)
        ax.bar(vt, gt, rong * 1.6, color=mau, zorder=3)
        for i, v in enumerate(gt):
            ax.text(i, v + max(gt) * 0.03, f"{v:.2f}", ha="center",
                    fontsize=9, color=MUC_CHINH, fontweight="bold")
        ax.set_xticks(vt)
        ax.set_xticklabels([t.replace(" ", "\n", 1) for t in ten], fontsize=8.5)
        ax.set_ylabel(nhan, color=MUC_PHU, fontsize=9.5)
        ax.set_ylim(0, max(gt) * 1.18)

    fig.suptitle("Hiệu quả của việc gộp 3 lần quét tại cùng vị trí",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", x=0.06, ha="left", y=1.02)
    fig.tight_layout()
    return _luu(fig, "aggregation_effect.png")


# ---------------------------------------------------------------- hình 4
def ban_do_loi(te: pd.DataFrame, du_doan: dict, thu_tu: list[str]) -> str:
    """Sai số theo vị trí. Độ lớn liên tục nên dùng ramp một sắc."""
    theo_diem = evaluate.loi_theo_diem(
        te["rp_id"], te[["x", "y"]].to_numpy(float), du_doan[thu_tu[0]])

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
    ax.set_title(f"Sai số theo vị trí — {thu_tu[0]}",
                 color=MUC_CHINH, fontsize=11.5, fontweight="bold", loc="left", pad=12)
    return _luu(fig, "error_heatmap.png")


# ---------------------------------------------------------------- hình 5
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


def chay() -> None:
    meta, te, ap, loi, du_doan, thu_tu = nap()
    print(f"Huấn luyện lúc {meta['huan_luyen_luc']} · {len(thu_tu)} mô hình · "
          f"{len(te)} mẫu test\n")

    ket_qua = [
        so_sanh_mo_hinh(loi, thu_tu),
        cdf(loi, thu_tu),
        hieu_qua_gop(te, du_doan, thu_tu),
        ban_do_loi(te, du_doan, thu_tu),
        do_quan_trong(ap),
    ]
    for d in ket_qua:
        if d:
            print(d)
    print(f"\nĐã ghi vào {config.REPORTS_DIR / 'figures'}")


if __name__ == "__main__":
    chay()
