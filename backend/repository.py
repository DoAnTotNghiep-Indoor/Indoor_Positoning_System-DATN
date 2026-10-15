"""Mọi lệnh đọc ghi CSDL đi qua đây, để đổi kho lưu chỉ phải sửa một tệp."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import DuDoanViTri, PhienDinhVi, bay_gio


async def lay_hoac_tao_phien(session: AsyncSession, device_id: str) -> PhienDinhVi:
    """Phiên đang mở của thiết bị, hoặc phiên mới nếu vắng quá
    `reset_after_seconds` — cùng ngưỡng `BoGop` dùng để xoá lịch sử gộp."""
    phien = await session.scalar(
        select(PhienDinhVi)
        .where(PhienDinhVi.device_id == device_id)
        .order_by(PhienDinhVi.lan_cuoi.desc())
        .limit(1)
    )
    luc = bay_gio()
    da_cu = phien is not None and (
        luc - phien.lan_cuoi > timedelta(seconds=settings.reset_after_seconds)
    )

    if phien is None or da_cu:
        phien = PhienDinhVi(device_id=device_id, bat_dau=luc, lan_cuoi=luc)
        session.add(phien)
        await session.flush()
    else:
        phien.lan_cuoi = luc
    return phien


async def ghi_du_doan(
    session: AsyncSession,
    device_id: str,
    x: float,
    y: float,
    x_gop: float,
    y_gop: float,
    so_ap: int,
    mo_hinh: str,
    do_tre_ms: float,
) -> DuDoanViTri:
    phien = await lay_hoac_tao_phien(session, device_id)
    ban_ghi = DuDoanViTri(
        phien_id=phien.id,
        x=x,
        y=y,
        x_gop=x_gop,
        y_gop=y_gop,
        so_ap_bat_duoc=so_ap,
        mo_hinh=mo_hinh,
        do_tre_ms=do_tre_ms,
    )
    session.add(ban_ghi)
    await session.commit()
    return ban_ghi


async def lich_su(
    session: AsyncSession, device_id: str | None = None, gioi_han: int = 100
) -> list[DuDoanViTri]:
    cau = (select(DuDoanViTri).options(selectinload(DuDoanViTri.phien))
           .order_by(DuDoanViTri.luc.desc()).limit(gioi_han))
    if device_id:
        cau = cau.join(PhienDinhVi).where(PhienDinhVi.device_id == device_id)
    return list(await session.scalars(cau))
