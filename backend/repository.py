"""Mọi lệnh đọc ghi CSDL đi qua đây.

Tách riêng để khi thêm MongoDB cho phần lưu lần quét thô, chỗ phải sửa chỉ nằm
trong tệp này chứ không rải khắp router. Router chỉ gọi hàm, không biết phía
dưới là SQLite hay gì khác.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import DuDoanViTri, PhienDinhVi, bay_gio


async def lay_hoac_tao_phien(session: AsyncSession, device_id: str) -> PhienDinhVi:
    """Phiên đang mở của thiết bị, hoặc phiên mới nếu nó vừa vắng mặt quá lâu.

    Ngưỡng dùng chung `reset_after_seconds` với bộ gộp: im lặng quá ngần ấy
    giây thì `BoGop` đã coi như người dùng đi chỗ khác rồi quay lại và xoá lịch
    sử gộp. Không mở phiên mới ở đây thì hai tầng hiểu "phiên" khác nhau —
    `bat_dau` trở thành lần đầu thiết bị từng xuất hiện, và bảng
    `positioning_sessions` không phân định được lượt ghé nào với lượt nào.
    """
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
    cau = select(DuDoanViTri).order_by(DuDoanViTri.luc.desc()).limit(gioi_han)
    if device_id:
        cau = cau.join(PhienDinhVi).where(PhienDinhVi.device_id == device_id)
    return list(await session.scalars(cau))
