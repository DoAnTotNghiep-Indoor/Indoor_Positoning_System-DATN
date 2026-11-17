"""Bộ 3: HistGB + KAN + Transformer — mô hình triển khai.

Ba bộ phân lớp 40 điểm tham chiếu khác loại nhau (cây tăng cường, mạng spline, attention trên
tập AP) nên thường sai ở những lần quét khác nhau. Mỗi lần quét cho một vector điểm: trung bình
log(p + 0,001) của ba mô hình. Gộp K lần quét là cộng các vector này (tức nhân xác suất), đổi
lại thành xác suất rồi lấy trung vị hình học có trọng số trên toạ độ 40 điểm. Một điểm chiếm từ
nửa trọng số trở lên thì kết quả rơi đúng điểm đó; ngược lại rơi vào giữa các điểm.

Cả ba học trên dữ liệu đã nhân 5 lần (lệch máy, nhiễu, mất AP). KAN và Transformer học trên GPU
khi máy có: nhanh khoảng 9 lần, nhưng ra kết quả khác CPU (dao động như khi đổi seed).
"""

from __future__ import annotations

import copy
import math

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import HistGradientBoostingClassifier
from torch import nn

TEN = "Bộ 3 (HistGB + KAN + Transformer)"
LUOI_THAM_SO: dict = {}

TB = "cuda" if torch.cuda.is_available() else "cpu"

# Cộng vào xác suất trước khi lấy log: một mô hình cho xác suất gần 0 không phủ quyết cả bộ.
EPS = 1e-3
VONG_TRUNG_VI = 100


def tang_cuong(X, nhan, seed, so_ban=4, lech=0.08, nhieu=0.03, mat=0.1):
    """Thêm `so_ban` bản: lệch máy (một mức chung cho mọi AP nghe được), nhiễu từng AP, mất AP.

    Trên thang MinMax, 0 là không nghe thấy; 1 dB ứng khoảng 0,015.
    """
    rng = np.random.default_rng(seed)
    Xs, ns = [X], [nhan]
    for _ in range(so_ban):
        A = X + rng.uniform(-lech, lech, (len(X), 1)) + rng.normal(0, nhieu, X.shape)
        Xs.append(np.where((X > 0) & (rng.random(X.shape) > mat), np.clip(A, 0.001, 1.3), 0.0))
        ns.append(nhan)
    return np.vstack(Xs), np.concatenate(ns)


class LopKan(nn.Module):
    """Mỗi cạnh vào i → ra j là hàm học được w·silu(x) + Σ c·B(x), B là B-spline bậc k trên [-1, 1]."""

    def __init__(self, vao: int, ra: int, G: int = 5, k: int = 3):
        super().__init__()
        self.k, self.h = k, 2.0 / G
        self.register_buffer("t", -1.0 + self.h * torch.arange(-k, G + k + 1, dtype=torch.float32))
        self.Wb = nn.Parameter(torch.randn(vao, ra) / math.sqrt(vao))
        self.Ws = nn.Parameter(torch.randn(vao * (G + k), ra) * 0.1 / math.sqrt(vao * (G + k)))
        self.b = nn.Parameter(torch.zeros(ra))

    def forward(self, a):
        t, x = self.t, a[..., None]
        B = ((x >= t[:-1]) & (x < t[1:])).to(a.dtype)
        for p in range(1, self.k + 1):
            B = (x - t[:-(p + 1)]) / (p * self.h) * B[..., :-1] + (t[p + 1:] - x) / (p * self.h) * B[..., 1:]
        return F.silu(a) @ self.Wb + B.flatten(1) @ self.Ws + self.b


class Kan(nn.Module):
    def __init__(self, vao: int, ra: int, an: int = 64):
        super().__init__()
        self.lop = nn.Sequential(LopKan(vao, an), LopKan(an, ra))

    def forward(self, x):
        return self.lop(2 * x - 1)


class ApTransformer(nn.Module):
    """Mỗi AP nghe thấy là một token (nhúng định danh AP + nhúng mức RSSI); AP không nghe thấy bị
    che khỏi attention thay vì coi là một mức RSSI. Token [CLS] ra 40 lớp."""

    def __init__(self, vao: int, ra: int, dim: int = 32, lop: int = 2, dau: int = 4):
        super().__init__()
        self.ap = nn.Parameter(torch.randn(vao, dim) * 0.1)
        self.muc = nn.Linear(1, dim)
        self.cls = nn.Parameter(torch.zeros(1, 1, dim))
        lop_tf = nn.TransformerEncoderLayer(dim, dau, 2 * dim, dropout=0.1, batch_first=True, norm_first=True)
        self.tf = nn.TransformerEncoder(lop_tf, lop, enable_nested_tensor=False)
        self.ra = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, ra))

    def forward(self, x):
        t = torch.cat([self.cls.expand(len(x), -1, -1), self.ap + self.muc(x.unsqueeze(-1))], 1)
        che = torch.cat([torch.zeros(len(x), 1, dtype=torch.bool, device=x.device), x <= 0], 1)
        return self.ra(self.tf(t, src_key_padding_mask=che)[:, 0])


def hoc_mang(net, toi_uu, X, nhan, so_vong, kien_nhan, seed, lo=256):
    """Lô 256, dừng sớm theo cross-entropy trên 10 % dữ liệu học tách riêng, giữ bản tốt nhất."""
    rng = np.random.default_rng(seed)
    thu = rng.permutation(len(X))
    kt, tap = thu[:len(X) // 10], thu[len(X) // 10:]
    net = net.to(TB)
    opt = toi_uu(net)
    X = torch.as_tensor(X, dtype=torch.float32, device=TB)
    Y = torch.as_tensor(nhan, device=TB)
    kt = torch.as_tensor(kt, device=TB)
    tot, ban, cho = math.inf, None, 0
    for _ in range(so_vong):
        net.train()
        rng.shuffle(tap)
        for s in range(0, len(tap), lo):
            i = torch.as_tensor(tap[s:s + lo], device=TB)
            mat = F.cross_entropy(net(X[i]), Y[i])
            opt.zero_grad()
            mat.backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            v = F.cross_entropy(net(X[kt]), Y[kt]).item()
        if v < tot - 1e-4:
            tot, cho, ban = v, 0, copy.deepcopy(net.state_dict())
        else:
            cho += 1
            if cho >= kien_nhan:
                break
    net.load_state_dict(ban)
    return net.cpu().eval()


def cay_phang(hgb: HistGradientBoostingClassifier) -> dict:
    """Mọi cây HistGB nối thành mảng phẳng, cây thứ i*C + c là vòng i của lớp c, lá có
    `dac_trung` = -1. Để đoán cả rừng một lượt (scikit-learn gọi riêng khoảng 5.600 cây, một lần
    quét mất 40-50 ms) và để xuất nguyên dạng cho app."""
    dac_trung, nguong, trai, phai, gia_tri, goc = [], [], [], [], [], []
    o = 0
    for vong in hgb._predictors:
        for p in vong:
            n = p.nodes
            goc.append(o)
            la = n["is_leaf"].astype(bool)
            dac_trung.append(np.where(la, -1, n["feature_idx"]))
            nguong.append(np.where(la, 0.0, n["num_threshold"]))
            trai.append(np.where(la, 0, n["left"] + o))
            phai.append(np.where(la, 0, n["right"] + o))
            gia_tri.append(np.where(la, n["value"], 0.0))
            o += len(n)
    noi = lambda ds, kieu: np.concatenate(ds).astype(kieu)  # noqa: E731
    return {"goc_lop": np.ravel(hgb._baseline_prediction).astype(float), "goc": np.array(goc, np.int32),
            "dac_trung": noi(dac_trung, np.int32), "nguong": noi(nguong, float), "trai": noi(trai, np.int32),
            "phai": noi(phai, np.int32), "gia_tri": noi(gia_tri, float)}


def logit_cay(c: dict, X: np.ndarray) -> np.ndarray:
    """Logit từng lớp: đi đồng thời mọi cây, mỗi vòng xuống một tầng, so `x <= ngưỡng` như
    scikit-learn."""
    n = np.tile(c["goc"], (len(X), 1))
    while (f := c["dac_trung"][n]).max() >= 0:
        x = np.take_along_axis(X, np.maximum(f, 0), axis=1)
        n = np.where(f < 0, n, np.where(x <= c["nguong"][n], c["trai"][n], c["phai"][n]))
    return c["goc_lop"] + c["gia_tri"][n].reshape(len(X), -1, len(c["goc_lop"])).sum(1)


def trung_vi_hinh_hoc(L: np.ndarray, toa_do: np.ndarray) -> np.ndarray:
    """Mỗi hàng điểm (log xác suất chưa chuẩn hoá) → trung vị hình học có trọng số (Weiszfeld)."""
    P = np.exp(L - L.max(1, keepdims=True))
    P /= P.sum(1, keepdims=True)
    X = P @ toa_do
    for _ in range(VONG_TRUNG_VI):
        w = P / np.maximum(np.linalg.norm(toa_do[None] - X[:, None], axis=2), 1e-9)
        X = w @ toa_do / w.sum(1, keepdims=True)
    return X


class BoBa(BaseEstimator, RegressorMixin):
    def __init__(self, seed: int = 0):
        self.seed = seed

    def fit(self, X, y):
        self.toa_do_, nhan = np.unique(np.asarray(y, dtype=float), axis=0, return_inverse=True)
        X, nhan = tang_cuong(np.clip(np.asarray(X, dtype=float), 0.0, None), nhan.ravel(), self.seed)
        c = len(self.toa_do_)
        self.cay_ = cay_phang(HistGradientBoostingClassifier(
            max_iter=150, learning_rate=0.1, random_state=self.seed).fit(X, nhan))

        torch.manual_seed(self.seed)
        kan = Kan(X.shape[1], c)
        # L2 như KAN bản NumPy đã đánh giá: phạt trọng số, không phạt bias.
        self.kan_ = hoc_mang(kan, lambda m: torch.optim.Adam(
            [{"params": [p for n, p in m.named_parameters() if not n.endswith(".b")], "weight_decay": 1e-4},
             {"params": [p for n, p in m.named_parameters() if n.endswith(".b")]}], lr=3e-3),
            X, nhan, so_vong=300, kien_nhan=20, seed=self.seed)

        torch.manual_seed(self.seed)
        self.tf_ = hoc_mang(ApTransformer(X.shape[1], c),
                            lambda m: torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=1e-4),
                            X, nhan, so_vong=150, kien_nhan=15, seed=self.seed)
        return self

    def xac_suat(self, X) -> list[np.ndarray]:
        """Xác suất 40 điểm của HistGB, KAN, Transformer."""
        X = np.clip(np.asarray(X, dtype=float), 0.0, None)
        with torch.no_grad():
            t = torch.as_tensor(X, dtype=torch.float32)
            mang = [torch.softmax(m(t), 1).numpy().astype(float) for m in (self.kan_, self.tf_)]
        z = logit_cay(self.cay_, X)
        z = np.exp(z - z.max(1, keepdims=True))
        return [z / z.sum(1, keepdims=True), *mang]

    def dau_ra(self, X) -> np.ndarray:
        """Vector điểm từng lần quét, thứ được giữ trong cửa sổ gộp."""
        return np.mean([np.log(p + EPS) for p in self.xac_suat(X)], axis=0)

    def gop(self, D) -> np.ndarray:
        """Cửa sổ vector điểm → một toạ độ."""
        return trung_vi_hinh_hoc(np.asarray(D, dtype=float).sum(0, keepdims=True), self.toa_do_)[0]

    def predict(self, X):
        return trung_vi_hinh_hoc(self.dau_ra(X), self.toa_do_)


def build(seed: int = 0) -> BoBa:
    return BoBa(seed=seed)
