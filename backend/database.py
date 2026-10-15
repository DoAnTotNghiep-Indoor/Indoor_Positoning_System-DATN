"""Kết nối SQLite bất đồng bộ và định nghĩa bảng.

Chỉ hai bảng lịch sử định vị; điểm tham chiếu và mô hình đã có nguồn ở
`data/reference/` và `artifacts/`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, event
from sqlalchemy.engine import Engine
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.config import settings


def bay_gio() -> datetime:
    return datetime.now(timezone.utc)


class MocThoiGian(TypeDecorator):
    """Cột thời điểm luôn đọc ra kèm UTC.

    SQLite đọc lên datetime trần, mà JavaScript hiểu chuỗi không offset là giờ địa
    phương nên Dashboard lệch 7 tiếng. Vẫn lưu trần để SQLite sắp xếp theo chuỗi.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Giá trị trần coi như đã là UTC: mọi chỗ đều ghi bằng `bay_gio()`.
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return None if value is None else value.replace(tzinfo=timezone.utc)


LUC = MocThoiGian()


class Base(DeclarativeBase):
    pass


class PhienDinhVi(Base):
    """Một thiết bị đang được định vị liên tục."""

    __tablename__ = "positioning_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    bat_dau: Mapped[datetime] = mapped_column(LUC, default=bay_gio)
    lan_cuoi: Mapped[datetime] = mapped_column(LUC, default=bay_gio)

    du_doan: Mapped[list["DuDoanViTri"]] = relationship(back_populates="phien")


class DuDoanViTri(Base):
    """Một toạ độ đã trả về; giữ cả thô lẫn đã gộp để đo hiệu quả bước gộp."""

    __tablename__ = "position_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    phien_id: Mapped[int] = mapped_column(ForeignKey("positioning_sessions.id"), index=True)
    luc: Mapped[datetime] = mapped_column(LUC, default=bay_gio, index=True)

    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    x_gop: Mapped[float] = mapped_column(Float)
    y_gop: Mapped[float] = mapped_column(Float)

    so_ap_bat_duoc: Mapped[int] = mapped_column(Integer)
    mo_hinh: Mapped[str] = mapped_column(String(64))
    do_tre_ms: Mapped[float] = mapped_column(Float)

    phien: Mapped[PhienDinhVi] = relationship(back_populates="du_doan")

    @property
    def device_id(self) -> str:
        return self.phien.device_id


@event.listens_for(Engine, "connect")
def _bat_wal(ket_noi, _) -> None:
    """WAL: commit nhanh ~5 lần (0,47 so với 2,31 ms), đọc không chặn ghi. Khoá
    ngoại phải bật tay vì SQLite mặc định KHÔNG thực thi."""
    if "sqlite" in type(ket_noi).__module__:
        con = ket_noi.cursor()
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.close()


engine = create_async_engine(settings.database_url, echo=False)
TaoSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def tao_bang() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def lay_session():
    async with TaoSession() as session:
        yield session
