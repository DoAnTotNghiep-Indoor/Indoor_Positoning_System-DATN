"""Cấu hình đọc từ biến môi trường.

SQLite vì không cần cài server; đổi engine chỉ cần đổi DATABASE_URL.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite+aiosqlite:///{ROOT_DIR / 'data' / 'ips.db'}"
    model_dir: Path = ROOT_DIR / "artifacts"
    dashboard_dir: Path = ROOT_DIR / "dashboard"

    # Số lần quét gộp; số đo ở `hau_xu_ly_gop` trong model_metadata.json.
    cua_so_gop: int = Field(3, ge=1)

    # Quá khoảng này coi như người dùng đã rời đi, bắt đầu lại cửa sổ gộp.
    reset_after_seconds: int = Field(30, ge=1)

    allowed_origins: list[str] = ["*"]

    # DEMO=true: bỏ lần quét của điện thoại, phát lại lần quét thật ở thư viện
    # (xem services/demo_service.py). Chỉ để trình diễn ngoài thư viện.
    demo: bool = False


settings = Settings()
