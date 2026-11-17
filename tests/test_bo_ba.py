from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from ml.models import bo_ba


def test_cay_noi_phang_khop_scikit_learn():
    """Máy chủ và app đều đi cây theo dạng nối phẳng thay vì gọi scikit-learn; đọc sai cấu trúc
    nút (đổi phiên bản scikit-learn) thì xác suất lệch mà không báo lỗi."""
    rng = np.random.default_rng(0)
    X = np.where(rng.random((600, 8)) < 0.3, 0.0, rng.random((600, 8)))
    hgb = HistGradientBoostingClassifier(max_iter=20, random_state=0).fit(X, rng.integers(0, 5, 600))
    z = bo_ba.logit_cay(bo_ba.cay_phang(hgb), X)
    p = np.exp(z - z.max(1, keepdims=True))
    np.testing.assert_allclose(p / p.sum(1, keepdims=True), hgb.predict_proba(X), atol=1e-12)
