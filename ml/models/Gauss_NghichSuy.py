"""Gauss nghịch suy: dựng bản đồ RSSI liên tục cho từng AP bằng hồi quy Gauss rồi định vị trực tiếp trên bản đồ.

Mỗi AP có hai bản đồ, học từ trung bình tại các điểm tham chiếu:
  - xác suất bắt được AP: hồi quy Gauss, trung bình hằng;
  - RSSI khi bắt được: hồi quy Gauss có trung bình là mô hình suy hao theo log khoảng cách
        A − softplus(B) · log10(√(|p − vị trí AP|² + h²)),
    vị trí AP, A, B học CÙNG LÚC với tham số Gauss bằng cực đại marginal likelihood (Yiu và cộng sự, ICC 2016;
    Signal Processing 131, 2017), khởi tạo bằng bình phương tối thiểu.
Nhân Matern ν = 1,5 có độ dài riêng cho trục x, y; nhiễu riêng từng điểm = dao động giữa các lần quét / số lần bắt
được, cộng nhiễu chung học được. AP không bắt được KHÔNG bị điền 0 vào bản đồ RSSI mà đi vào bản đồ xác suất.

Định vị: log-khả năng của lần quét trên mọi ô lưới 1 đơn vị cách điểm học ≤ 12 đơn vị
    AP bắt được giá trị x:  log p(q) + log N(x; μ(q), σ²(q) + dao động giữa các lần quét)
    AP không bắt được:      log(1 − p(q))
rồi lấy trung bình hậu nghiệm của các ô (softmax log-khả năng).

Học trên GPU nếu có, không thì CPU. Không nằm trong `DANH_SACH`: bản đồ dựng trên toạ độ phẳng một tầng, không dùng
được cho UJIIndoorLoc nhiều toà, nhiều tầng. Đánh giá ba giao thức:

    python -m ml.models.Gauss_NghichSuy
"""

from __future__ import annotations

import numpy as np
import torch
from scipy.optimize import least_squares
from sklearn.base import BaseEstimator, RegressorMixin

TEN = "Gauss nghịch suy"
LUOI_THAM_SO: dict = {}

TB = torch.device("cuda" if torch.cuda.is_available() else "cpu")
F64 = torch.float64
H = 6.0  # ~2 m: AP treo trần, để log không nổ khi đứng ngay dưới AP
BAN_KINH = 12.0  # ~4,2 m quanh điểm học; xa hơn thì bản đồ chỉ là ngoại suy
VONG = 500


def _t(a):
    return torch.as_tensor(np.asarray(a, float), dtype=F64, device=TB)


def _suy_hao_ban_dau(X, Y):
    """(A, B, ax, ay) từng AP bằng bình phương tối thiểu trên trung bình RSSI tại các điểm bắt được AP."""
    P, ng = np.unique(Y, axis=0, return_inverse=True)
    ng = ng.ravel()
    ra = np.zeros((X.shape[1], 4))
    for j in range(X.shape[1]):
        co = X[:, j] > 0
        n = np.bincount(ng[co], minlength=len(P))
        if (n > 0).sum() < 5:
            continue
        v = np.bincount(ng[co], X[co, j], minlength=len(P))[n > 0] / n[n > 0]
        Q, w = P[n > 0], np.sqrt(n[n > 0])
        tam = (Q * v[:, None] ** 4).sum(0) / (v ** 4).sum()

        def du(t):
            return w * (t[0] - t[1] * np.log10(np.sqrt(((Q - t[2:]) ** 2).sum(1) + H * H)) - v)

        ra[j] = least_squares(du, [v.max() + 0.3, 0.3, *tam], bounds=([-5, 0, -80, -30], [5, 5, 80, 85])).x
    return ra


def _matern32(A, B, l):
    r = torch.sqrt((((A[None, :, None] - B[None, None]) / l[:, None, None]) ** 2).sum(-1) + 1e-12)
    return (1 + np.sqrt(3) * r) * torch.exp(-np.sqrt(3) * r)


def _suy_hao(Q, ts):
    d = torch.sqrt(((Q[:, None] - ts["ap"][None]) ** 2).sum(2) + H * H)
    return ts["A"] - torch.nn.functional.softplus(ts["B"]) * torch.log10(d)


class _GaussTheoAP:
    """Hồi quy Gauss độc lập cho từng cột (AP), học chung một vòng tối ưu."""

    def __init__(self, P, T, nhieu, ts=None):
        self.P, self.T, self.nd, self.ts = P, T, nhieu, ts
        so_ap = T.shape[1]
        lech = (T - self._m(P) if ts else T - T.mean(0)).detach().std(0).clamp_min(1e-3)
        self.log_l = torch.full((so_ap, 2), np.log(10.0), dtype=F64, device=TB, requires_grad=True)
        self.log_s = torch.log(lech).clone().requires_grad_(True)
        self.log_n = torch.full((so_ap,), np.log(0.02), dtype=F64, device=TB, requires_grad=True)
        self.c = T.mean(0).detach().clone().requires_grad_(ts is None)

    def _m(self, Q):
        return _suy_hao(Q, self.ts) if self.ts else self.c.expand(len(Q), -1)

    def _K(self):
        l = self.log_l.exp().clamp(2.0, 100.0)
        K = self.log_s.exp()[:, None, None] ** 2 * _matern32(self.P, self.P, l)
        return K + torch.diag_embed(self.nd.T + self.log_n.exp()[:, None] ** 2), l

    def hoc(self):
        tham = [self.log_l, self.log_s, self.log_n, *(self.ts.values() if self.ts else [self.c])]
        opt = torch.optim.Adam(tham, lr=0.05)
        lich = torch.optim.lr_scheduler.CosineAnnealingLR(opt, VONG)
        for _ in range(VONG):
            opt.zero_grad()
            K, _ = self._K()
            r = (self.T - self._m(self.P)).T[..., None]
            L = torch.linalg.cholesky(K)
            nll = (0.5 * (r * torch.cholesky_solve(r, L)).sum((1, 2))
                   + torch.log(torch.diagonal(L, dim1=1, dim2=2)).sum(1)).sum()
            nll.backward()
            opt.step()
            lich.step()
        with torch.no_grad():
            K, self.l = self._K()
            self.L = torch.linalg.cholesky(K)
            self.a = torch.cholesky_solve((self.T - self._m(self.P)).T[..., None], self.L)
        return self

    @torch.no_grad()
    def du_doan(self, Q):
        Ks = self.log_s.exp()[:, None, None] ** 2 * _matern32(Q, self.P, self.l)
        mu = self._m(Q) + (Ks @ self.a)[..., 0].T
        v = torch.linalg.solve_triangular(self.L, Ks.transpose(1, 2), upper=False)
        return mu, (self.log_s.exp()[:, None] ** 2 - (v ** 2).sum(1)).clamp_min(1e-8).T


class GaussNghichSuy(BaseEstimator, RegressorMixin):
    def fit(self, X, y):
        X, Y = np.asarray(X, float), np.asarray(y, float)
        P, ng = np.unique(Y, axis=0, return_inverse=True)
        ng = ng.ravel()
        bat = X > 0
        n = np.bincount(ng, minlength=len(P))[:, None]
        so = np.stack([bat[ng == i].sum(0) for i in range(len(P))])
        tb = np.stack([np.where(bat[ng == i], X[ng == i], 0).sum(0) for i in range(len(P))]) / np.maximum(so, 1)
        ps = np.stack([np.where(bat[ng == i], (X[ng == i] - tb[i]) ** 2, 0).sum(0)
                       for i in range(len(P))]) / np.maximum(so, 1)
        lech_quet = np.sqrt(ps[so > 1].mean()) + 1e-3 if (so > 1).any() else 0.1

        ts0 = _suy_hao_ban_dau(X, Y)
        ts = {"A": _t(ts0[:, 0]).requires_grad_(True),
              "B": _t(np.log(np.expm1(np.maximum(ts0[:, 1], 1e-3)))).requires_grad_(True),
              "ap": _t(ts0[:, 2:]).requires_grad_(True)}
        Pt = _t(P)
        # Điểm chưa từng bắt được AP: nhiễu rất lớn, bản đồ RSSI của AP đó bỏ qua điểm này.
        rssi = _GaussTheoAP(Pt, _t(tb), _t(np.where(so > 0, (ps + 1e-4) / np.maximum(so, 1), 1e6)), ts).hoc()
        r = so / n
        bat_gp = _GaussTheoAP(Pt, _t(r), _t((r * (1 - r) + 0.01) / n)).hoc()

        gx, gy = np.meshgrid(np.arange(P[:, 0].min(), P[:, 0].max() + 1), np.arange(P[:, 1].min(), P[:, 1].max() + 1))
        luoi = np.c_[gx.ravel(), gy.ravel()]
        self.luoi_ = _t(luoi[np.linalg.norm(luoi[:, None] - P[None], axis=2).min(1) <= BAN_KINH])
        mu, var = rssi.du_doan(self.luoi_)
        p = bat_gp.du_doan(self.luoi_)[0].clamp(0.02, 0.98)
        self.mu_, self.var_ = mu, var + lech_quet ** 2
        self.log_p_, self.log_q_ = torch.log(p), torch.log1p(-p)
        return self

    @torch.no_grad()
    def log_kha_nang(self, X):
        """(số lần quét, số ô lưới): cộng log-khả năng nhiều lần quét là gộp chúng."""
        ra = []
        for s in range(0, len(X), 128):
            x = _t(X[s:s + 128])[:, None]
            ra.append(torch.where(x > 0, self.log_p_ - 0.5 * ((x - self.mu_) ** 2 / self.var_ + torch.log(self.var_)),
                                  self.log_q_).sum(2))
        return torch.cat(ra)

    def predict(self, X):
        return (torch.softmax(self.log_kha_nang(np.asarray(X, float)), 1) @ self.luoi_).cpu().numpy()


def build() -> GaussNghichSuy:
    return GaussNghichSuy()


if __name__ == "__main__":
    from ml import config
    from ml.danh_gia_cheo import chuan_bi_lan_gap, nap_bang_rong
    from ml.khac_dot import HAI_CHIEU, chuan_bi_chieu
    from ml.on_dinh import chia_lai

    def loi(Xh, Yh, Xt, Yt):
        return np.hypot(*(build().fit(Xh, Yh).predict(Xt) - Yt).T) * config.MET_MOI_DON_VI

    fp, ap_cols = nap_bang_rong()
    nn = []
    for s in range(10):
        d, ap = chia_lai(fp, ap_cols, s)
        hoc, thu = d[d["split"] != "test"], d[d["split"] == "test"]
        nn.append(loi(hoc[ap].to_numpy(float), hoc[config.TARGET_COLS].to_numpy(float),
                      thu[ap].to_numpy(float), thu[config.TARGET_COLS].to_numpy(float)).mean())
    bd = np.concatenate([loi(*bo[1:]) for bo in chuan_bi_lan_gap(fp, ap_cols)]).mean()
    kd = [loi(*chuan_bi_chieu(fp, ap_cols, h, t)).mean() for h, t in HAI_CHIEU]
    print(f"{TEN} ({TB}): chia ngẫu nhiên {np.mean(nn):.2f} ± {np.std(nn, ddof=1):.2f} m | bỏ trọn một điểm {bd:.2f} m"
          f" | khác đợt {np.mean(kd):.2f} m (A→B {kd[0]:.2f} / B→A {kd[1]:.2f})")
