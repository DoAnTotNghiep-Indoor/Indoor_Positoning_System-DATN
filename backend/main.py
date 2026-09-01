"""Khởi tạo FastAPI và đăng ký router.

    uvicorn backend.main:app --reload

Không chứa logic nghiệp vụ. Mô hình và bộ gộp nạp trong lifespan chứ không nạp
lúc import, để import module không đòi artifacts/ phải có sẵn — kiểm thử và công
cụ sinh tài liệu đều import được trước khi chạy pipeline lần nào.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from backend import dependencies, schemas
from backend.config import settings
from backend.database import tao_bang
from backend.routers import map as map_router
from backend.routers import predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    await tao_bang()
    dependencies.khoi_dong()
    yield


app = FastAPI(
    title="IPS DLU — API định vị trong nhà",
    description="WiFi Fingerprinting, Thư viện Đại học Đà Lạt. Đồ án tốt nghiệp nhóm 15.",
    version="0.1",
    lifespan=lifespan,
)

# Bản đồ và đồ thị là JSON text nên nén rất hiệu quả.
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(map_router.router)


@app.get("/health", response_model=schemas.TrangThai, tags=["health"])
async def health() -> schemas.TrangThai:
    """Xác nhận model đã nạp và hợp đồng dữ liệu khớp."""
    p = dependencies.lay_predictor()
    return schemas.TrangThai(
        trang_thai="ok",
        mo_hinh=p.ten_mo_hinh,
        so_dac_trung=p.mapper.feature_count,
        gia_tri_dien_thieu=p.mapper.missing_rssi_value,
        cua_so_gop=settings.cua_so_gop,
    )


# Dashboard web phục vụ ngay từ máy chủ API. Mount ĐẶT CUỐI TỆP vì nó nhận mọi
# đường dẫn còn lại: đăng ký trước thì nó nuốt luôn /health, /map và /predict.
#
# Nhờ vậy một lệnh `uvicorn backend.main:app` là có cả API lẫn giao diện, không
# phải dựng thêm máy chủ tĩnh và cũng không vướng CORS. Dashboard viết bằng ES
# module nên bắt buộc mở qua http://; mở thẳng tệp bằng file:// sẽ bị trình
# duyệt chặn vì chính sách cùng nguồn.
if settings.frontend_dir.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=settings.frontend_dir, html=True),
        name="dashboard",
    )