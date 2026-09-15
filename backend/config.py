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
    reference_dir: Path = ROOT_DIR / "data" / "reference"
    frontend_dir: Path = ROOT_DIR / "frontend"

    # Số lần quét gộp; số đo ở `hau_xu_ly_gop` trong model_metadata.json.
    cua_so_gop: int = Field(3, ge=1)

    # Quá khoảng này coi như người dùng đã rời đi, bắt đầu lại cửa sổ gộp.
    reset_after_seconds: int = Field(30, ge=1)

    allowed_origins: list[str] = ["*"]

    # Tạm tắt: mọi client đi REST. Bật lại là có /ws/location như cũ.
    websocket: bool = False


settings = Settings()
