from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import Request
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from .config import get_settings

_pool: AsyncConnectionPool | None = None


def get_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            open=False,
            kwargs={"row_factory": dict_row, "options": "-c search_path=public,extensions"},
        )
    return _pool


async def init_pool() -> None:
    pool = get_pool()
    await pool.open()
    await pool.wait()


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")[:255]


def request_id(request: Request) -> str:
    return request.headers.get("x-request-id") or str(uuid.uuid4())


async def apply_context(conn: Any, request: Request) -> None:
    user = getattr(request.state, "user", None)
    user_id = str(user["user_id"]) if user else ""
    role_code = user["role_code"] if user else "PUBLIC"
    guest_id = str(user["guest_id"]) if user and user.get("guest_id") else ""

    await conn.execute("SELECT set_config('app.current_user_id', %s, true)", (user_id,))
    await conn.execute("SELECT set_config('app.current_role_code', %s, true)", (role_code,))
    await conn.execute("SELECT set_config('app.current_guest_id', %s, true)", (guest_id,))
    await conn.execute("SELECT set_config('app.client_ip', %s, true)", (client_ip(request),))
    await conn.execute("SELECT set_config('app.user_agent', %s, true)", (user_agent(request),))
    await conn.execute("SELECT set_config('app.request_id', %s, true)", (request_id(request),))


async def get_db(request: Request) -> AsyncIterator[Any]:
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.transaction():
            await apply_context(conn, request)
            yield conn


@asynccontextmanager
async def db_connection(request: Request | None = None) -> AsyncIterator[Any]:
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.transaction():
            if request is not None:
                await apply_context(conn, request)
            yield conn
