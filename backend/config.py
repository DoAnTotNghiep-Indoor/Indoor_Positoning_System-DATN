"""Cấu hình đọc từ biến môi trường, không hardcode thông tin nhạy cảm.

Chọn SQLite chứ không phải PostgreSQL: không cần cài server, chạy được ngay
trên máy cá nhân lẫn máy chấm. Schema tránh cú pháp riêng của mọi engine nên
đổi engine chỉ phải đổi DATABASE_URL. Hướng mở rộng đã tính trước là MongoDB
cho phần lưu lần quét thô, và mọi truy cập CSDL đi qua backend/repository.py
để chỗ phải đổi chỉ nằm ở một tệp.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite+aiosqlite:///{ROOT_DIR / 'data' / 'ips.db'}"
    model_dir: Path = ROOT_DIR / "artifacts"
    reference_dir: Path = ROOT_DIR / "data" / "reference"
    frontend_dir: Path = ROOT_DIR / "frontend"

    # Số lần quét gộp lại trước khi trả toạ độ: 1,92 m xuống 0,38 m trên tập
    # test, xem ml/postprocess.py.
    cua_so_gop: int = 3

    # Quá khoảng này coi như người dùng đã rời đi, bắt đầu lại cửa sổ gộp.
    reset_after_seconds: int = 30

    allowed_origins: list[str] = ["*"]


settings = Settings()
