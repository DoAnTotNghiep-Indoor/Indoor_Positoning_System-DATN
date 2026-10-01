from __future__ import annotations

import json

import pytest

from ml import config


def thieu_artifact() -> bool:
    """Thiếu scaler hoặc mô hình đang dùng — kho vừa clone có thể chưa train."""
    meta = config.ARTIFACTS_DIR / "model_metadata.json"
    if not meta.exists():
        return True
    file_active = json.loads(meta.read_text(encoding="utf-8"))["file_active"]
    return not all((config.ARTIFACTS_DIR / f).exists() for f in ("scaler.pkl", file_active))


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """TestClient (chạy lifespan để nạp mô hình), CSDL trỏ sang thư mục tạm."""
    if thieu_artifact():
        pytest.skip("chưa có mô hình — chạy `python -m ml.pipeline` rồi `python -m ml.train`")

    from fastapi.testclient import TestClient

    from backend import database
    from backend.config import settings

    settings.database_url = f"sqlite+aiosqlite:///{tmp_path_factory.mktemp('db') / 't.db'}"
    database.engine = database.create_async_engine(settings.database_url)
    database.TaoSession = database.async_sessionmaker(
        database.engine, class_=database.AsyncSession, expire_on_commit=False)

    from backend.main import app

    with TestClient(app) as c:
        yield c
