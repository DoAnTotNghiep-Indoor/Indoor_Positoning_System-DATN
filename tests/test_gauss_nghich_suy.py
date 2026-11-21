import numpy as np
import pytest

pytest.importorskip("torch")
from ml.models.Gauss_NghichSuy import build  # noqa: E402


def test_tim_lai_diem_da_hoc_trong_phong_gia_lap():
    rng = np.random.default_rng(0)
    gx, gy = np.meshgrid(np.arange(0, 21, 5.0), np.arange(0, 21, 5.0))
    P = np.c_[gx.ravel(), gy.ravel()]
    ap = np.array([[0.0, 0.0], [20.0, 5.0], [8.0, 20.0]])
    Y = np.repeat(P, 8, 0)
    d = np.sqrt(((Y[:, None] - ap[None]) ** 2).sum(2) + 36)
    X = np.clip(1.0 - 0.45 * np.log10(d) + rng.normal(0, 0.02, d.shape), 0, None)
    loi = np.linalg.norm(build().fit(X, Y).predict(X) - Y, axis=1)
    assert loi.mean() < 3.0
