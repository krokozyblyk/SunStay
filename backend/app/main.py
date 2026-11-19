from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import AsyncConnection

from .api import admin, auth, guest, housekeeping, imports, manager, public, reports
from .config import get_settings
from .db import close_pool, get_db, init_pool
from .migrations import encrypt_sensitive_data
from .schedulers import start_schedulers, stop_schedulers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("sunstay")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SunStay API")
    await init_pool()
    try:
        await encrypt_sensitive_data()
    except Exception:
        logger.exception("Sensitive data migration failed")
    tasks = start_schedulers()
    try:
        yield
    finally:
        await stop_schedulers(tasks)
        await close_pool()
    logger.info("SunStay API stopped")


settings = get_settings()

app = FastAPI(
    title="SunStay API",
    description="Информационная система гостиницы SunStay: бронирования, заезды, folio, хаускипинг, отчёты.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(auth.settings_router, prefix=settings.api_prefix)
app.include_router(public.router, prefix=settings.api_prefix)
app.include_router(guest.router, prefix=settings.api_prefix)
app.include_router(manager.router, prefix=settings.api_prefix)
app.include_router(housekeeping.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(imports.router, prefix=settings.api_prefix)


@app.get("/api/health", tags=["system"])
async def health(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute("SELECT 1 AS ok")
    row = await cur.fetchone()
    return {"status": "ok" if row and row["ok"] == 1 else "error"}


@app.get("/api", tags=["system"])
async def api_root():
    return {
        "name": "SunStay API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
    }
