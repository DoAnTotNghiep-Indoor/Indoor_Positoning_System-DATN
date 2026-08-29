"""Kết nối SQLite bất đồng bộ và định nghĩa bảng.

Chỉ hai bảng, không phải 16 như bản thiết kế đầy đủ. Lưu đúng thứ chưa có chỗ
nào khác giữ: lịch sử vị trí đã dự đoán. Điểm tham chiếu và mô hình vẫn đọc từ
`data/reference/` và `artifacts/` vì hai chỗ đó đã là nguồn sự thật rồi, chép
vào CSDL chỉ tạo thêm một bản có thể lệch.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.config import settings


def bay_gio() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class PhienDinhVi(Base):
    """Một thiết bị đang được định vị liên tục."""

    __tablename__ = "positioning_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    bat_dau: Mapped[datetime] = mapped_column(DateTime, default=bay_gio)
    lan_cuoi: Mapped[datetime] = mapped_column(DateTime, default=bay_gio)

    du_doan: Mapped[list["DuDoanViTri"]] = relationship(back_populates="phien")


class DuDoanViTri(Base):
    """Một toạ độ đã trả về cho client.

    Giữ cả toạ độ thô lẫn toạ độ sau khi gộp: chênh lệch giữa hai cột này chính
    là số liệu chứng minh hiệu quả của bước hậu xử lý trong báo cáo.
    """

    __tablename__ = "position_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    phien_id: Mapped[int] = mapped_column(ForeignKey("positioning_sessions.id"), index=True)
    luc: Mapped[datetime] = mapped_column(DateTime, default=bay_gio, index=True)

    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    x_gop: Mapped[float] = mapped_column(Float)
    y_gop: Mapped[float] = mapped_column(Float)

    so_ap_bat_duoc: Mapped[int] = mapped_column(Integer)
    mo_hinh: Mapped[str] = mapped_column(String(64))
    do_tre_ms: Mapped[float] = mapped_column(Float)

    phien: Mapped[PhienDinhVi] = relationship(back_populates="du_doan")


engine = create_async_engine(settings.database_url, echo=False)
TaoSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def tao_bang() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def lay_session():
    async with TaoSession() as session:
        yield session
