"""Fixture và chốt chặn dùng chung cho cả bộ kiểm thử."""

from __future__ import annotations

import json

import pytest

from ml import config


def thieu_artifact() -> bool:
    """Thiếu tệp nào trong bộ artifact cần để dựng app hay không.

    Kiểm cả .pkl chứ không chỉ model_metadata.json. Hai tệp json được commit,
    còn scaler.pkl và model_*.pkl thì .gitignore chặn vì nặng và sinh lại
    được — chỉ kiểm json thì người mới clone repo chạy pytest sẽ nhận một
    loạt FileNotFoundError thay vì thông báo bỏ qua kèm hướng dẫn.
    """
    meta = config.ARTIFACTS_DIR / "model_metadata.json"
    if not meta.exists():
        return True

    can = [
        config.ARTIFACTS_DIR / "scaler.pkl",
        config.ARTIFACTS_DIR / json.loads(meta.read_text(encoding="utf-8"))["file_active"],
    ]
    return not all(p.exists() for p in can)


def bo_qua_neu_chua_huan_luyen() -> None:
    if thieu_artifact():
        pytest.skip("chưa có mô hình — chạy `python -m ml.pipeline` rồi `python -m ml.train`")


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """TestClient chứ không phải ASGITransport trần.

    ASGITransport không chạy sự kiện lifespan, mà toàn bộ việc nạp mô hình và
    tạo bảng nằm trong đó — dùng nó thì `_predictor` là None và CSDL không có
    bảng nào. TestClient dùng như context manager sẽ chạy lifespan đầy đủ.

    CSDL trỏ vào thư mục tạm do pytest cấp, nên chạy test không đụng vào
    data/ips.db thật và mỗi mô-đun đều bắt đầu từ bảng rỗng.
    """
    bo_qua_neu_chua_huan_luyen()

    from fastapi.testclient import TestClient

    from backend import database
    from backend.config import settings

    settings.database_url = f"sqlite+aiosqlite:///{tmp_path_factory.mktemp('db') / 't.db'}"
    database.engine = database.create_async_engine(settings.database_url)
    database.TaoSession = database.async_sessionmaker(
        database.engine, class_=database.AsyncSession, expire_on_commit=False
    )

    from backend.main import app

    with TestClient(app) as c:
        yield c
