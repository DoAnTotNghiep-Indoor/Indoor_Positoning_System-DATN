"""Khởi tạo FastAPI: `uvicorn backend.main:app --reload`.

Mô hình nạp trong lifespan chứ không lúc import, để import không đòi artifacts/.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
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

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(map_router.router)


@app.exception_handler(RequestValidationError)
async def loi_schema(_, exc: RequestValidationError) -> JSONResponse:
    """Như mặc định của FastAPI nhưng bỏ `input`: pydantic chép lại giá trị gửi
    lên, mà inf/NaN không tuần tự hoá được nên 422 hoá thành 500."""
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(
        [{k: v for k, v in e.items() if k != "input"} for e in exc.errors()])})


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
        websocket=settings.websocket,
    )


# Dashboard phục vụ cùng máy chủ API. Mount ĐẶT CUỐI vì nó nhận mọi đường dẫn còn lại.
if settings.frontend_dir.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=settings.frontend_dir, html=True),
        name="dashboard",
    )
