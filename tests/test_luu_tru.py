"""Kiểm thử tầng lưu trữ: múi giờ và ranh giới phiên định vị.

Cả hai lỗi dưới đây đều KHÔNG làm chương trình đổ, chỉ làm số liệu sai lặng lẽ —
đúng loại phải chốt bằng test chứ không phát hiện được khi bấm thử.

Chạy coroutine bằng `asyncio.run` thay vì dùng pytest-asyncio: cả bộ kiểm thử
hiện không cần plugin nào, và thêm một phụ thuộc chỉ để chạy bảy bài test thì
máy chấm lại có thêm một thứ phải cài đúng phiên bản.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend import repository
from backend.config import settings
from backend.database import PhienDinhVi

from .conftest import bo_qua_neu_chua_huan_luyen


@pytest.fixture
def chay(tmp_path):
    """Chạy một coroutine trên CSDL trống trong thư mục tạm.

    Coroutine nhận vào một `AsyncSession` đang mở. Mọi thao tác của một bài test
    phải nằm trong MỘT lần gọi: session bất đồng bộ gắn với vòng lặp sự kiện đã
    tạo ra nó, gọi hai lần là hai vòng lặp khác nhau.
    """
    from backend import database

    database.engine = database.create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'luu_tru.db'}"
    )
    database.TaoSession = database.async_sessionmaker(
        database.engine, class_=database.AsyncSession, expire_on_commit=False
    )

    def goi(than):
        async def boc():
            await database.tao_bang()
            async with database.TaoSession() as s:
                return await than(s)

        return asyncio.run(boc())

    return goi


def _ghi(session, device_id: str = "may-thu"):
    return repository.ghi_du_doan(
        session, device_id=device_id, x=1.0, y=2.0, x_gop=1.0, y_gop=2.0,
        so_ap=12, mo_hinh="kiem-thu", do_tre_ms=0.5,
    )


# --- Múi giờ ---

def test_moc_thoi_gian_doc_ra_kem_mui_gio(chay):
    """SQLite không có kiểu ngày giờ riêng nên `DateTime(timezone=True)` không
    có tác dụng — phải qua `MocThoiGian` mới giữ được UTC."""

    async def than(s):
        ghi = await _ghi(s)
        doc = (await repository.lich_su(s, gioi_han=1))[0]
        return ghi.luc, doc.luc

    luc_ghi, luc_doc = chay(than)
    assert luc_ghi.tzinfo is not None, "mất múi giờ khi ghi xuống"
    assert luc_doc.tzinfo is not None, "mất múi giờ khi đọc lên"
    assert luc_doc.utcoffset() == timedelta(0)


def test_chuoi_iso_co_hau_to_mui_gio(chay):
    """Đây mới là thứ Dashboard nhận được. Chuỗi ISO KHÔNG có offset bị
    JavaScript hiểu là giờ địa phương, làm cột "Lúc" lệch 7 tiếng."""
    from backend.schemas import MucLichSu

    ban_ghi = chay(_ghi)
    chuoi = MucLichSu.model_validate(ban_ghi).model_dump(mode="json")["luc"]
    assert chuoi.endswith("Z") or "+" in chuoi[10:], chuoi


def test_moc_thoi_gian_dung_gio_thuc(chay):
    ban_ghi = chay(_ghi)
    lech = abs((ban_ghi.luc - datetime.now(timezone.utc)).total_seconds())
    assert lech < 60, f"lệch {lech:.0f} giây so với UTC"


# --- Ranh giới phiên ---

def test_quet_lien_tuc_nam_chung_mot_phien(chay):
    async def than(s):
        return (await _ghi(s)).phien_id, (await _ghi(s)).phien_id

    a, b = chay(than)
    assert a == b


def test_vang_mat_qua_lau_thi_mo_phien_moi(chay):
    """Bộ gộp đã coi im lặng quá `reset_after_seconds` là người dùng đi chỗ khác
    rồi quay lại. Tầng lưu trữ phải hiểu "phiên" giống hệt như vậy."""

    async def than(s):
        a = await _ghi(s)
        phien = await s.get(PhienDinhVi, a.phien_id)
        phien.lan_cuoi = datetime.now(timezone.utc) - timedelta(
            seconds=settings.reset_after_seconds + 5
        )
        await s.commit()

        b = await _ghi(s)
        so_phien = len((await s.scalars(select(PhienDinhVi))).all())
        return a.phien_id, b.phien_id, so_phien

    a, b, so_phien = chay(than)
    assert b != a, "vẫn nối vào phiên cũ"
    assert so_phien == 2


def test_hai_thiet_bi_khong_dung_chung_phien(chay):
    async def than(s):
        return (await _ghi(s, "may-a")).phien_id, (await _ghi(s, "may-b")).phien_id

    a, b = chay(than)
    assert a != b


def test_bat_dau_cua_phien_moi_la_luc_no_bat_dau(chay):
    """Không phải lần đầu thiết bị từng xuất hiện — đó chính là lỗi cũ."""

    async def than(s):
        a = await _ghi(s)
        cu = await s.get(PhienDinhVi, a.phien_id)
        xua = datetime.now(timezone.utc) - timedelta(days=7)
        cu.bat_dau, cu.lan_cuoi = xua, xua
        await s.commit()

        b = await _ghi(s)
        return (await s.get(PhienDinhVi, b.phien_id)).bat_dau

    assert datetime.now(timezone.utc) - chay(than) < timedelta(minutes=1)


def test_api_lich_su_tra_ve_mui_gio(client):
    """Chốt lại ở mức HTTP, vì đó là thứ Dashboard thật sự đọc."""
    bo_qua_neu_chua_huan_luyen()

    # Phải gửi đủ số AP tối thiểu, không thì /predict từ chối bằng 422 và
    # không có bản ghi nào để kiểm múi giờ.
    import json

    from ml import config

    hop_dong = json.loads(
        (config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8")
    )
    scan = [
        {"bssid": b, "rssi": -55.0}
        for b in hop_dong["ap_columns"][: hop_dong["min_ap_per_scan"]]
    ]
    client.post("/predict", json={"device_id": "kiem-thu-mui-gio", "scan": scan})
    ds = client.get("/predictions?device_id=kiem-thu-mui-gio&gioi_han=1").json()
    assert ds, "không ghi được bản ghi nào"
    assert ds[0]["luc"].endswith("Z") or "+" in ds[0]["luc"][10:], ds[0]["luc"]
