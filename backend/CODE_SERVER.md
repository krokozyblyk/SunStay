# SunStay — текст серверной части

> Сгенерировано: 18.11.2026 14:27

Полные листинги FastAPI-ядра, analytics-микросервиса, конфигурации Docker Compose, PDF-сервиса и API-тестов. Файл является приложением к проекту и не вставляется в пояснительную записку целиком.

## Состав

- `backend/requirements.txt`
- `backend/Dockerfile`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/db.py`
- `backend/app/security.py`
- `backend/app/crypto.py`
- `backend/app/audit.py`
- `backend/app/migrations.py`
- `backend/app/schedulers.py`
- `backend/app/deps.py`
- `backend/app/schemas.py`
- `backend/app/utils.py`
- `backend/app/api/auth.py`
- `backend/app/api/public.py`
- `backend/app/api/guest.py`
- `backend/app/api/manager.py`
- `backend/app/api/housekeeping.py`
- `backend/app/api/admin.py`
- `backend/app/api/reports.py`
- `backend/app/api/imports.py`
- `backend/app/services/pdf.py`
- `backend/app/services/backup.py`
- `backend/tests/test_api.py`
- `analytics/requirements.txt`
- `analytics/Dockerfile`
- `analytics/app/main.py`
- `docker-compose.yml`
- `frontend/nginx.conf`

## `backend/requirements.txt`

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
psycopg[binary,pool]==3.2.3
pydantic-settings==2.7.1
PyJWT==2.10.1
bcrypt==4.2.1
python-multipart==0.0.20
reportlab==4.2.5
cryptography==44.0.0
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.25.0

```

## `backend/Dockerfile`

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql-client fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

RUN mkdir -p /backups

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

## `backend/app/main.py`

```python
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

```

## `backend/app/config.py`

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SunStay API"
    app_env: str = "development"
    api_prefix: str = "/api"

    database_url: str = "postgresql://sunstay_app:sunstay_app@localhost:5432/hotel"
    database_admin_url: str = "postgresql://postgres:postgres@localhost:5432/hotel"
    analytics_database_url: str = "postgresql://sunstay_analytics:sunstay_analytics@localhost:5432/hotel"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7

    data_encryption_key: str = "bh9O5gpBkH-qPkJSoUkiWswjQyQqWcQ7ZHZU6BO_C9s="
    backup_file_name: str = "sunstay_latest.dump"

    cors_origins: str = "http://localhost:5173,http://localhost:8080,http://localhost"
    backup_dir: str = "/backups"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

```

## `backend/app/db.py`

```python
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
            kwargs={"row_factory": dict_row},
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

```

## `backend/app/security.py`

```python
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from .config import get_settings

ROLE_CODES = {
    "Гость": "GUEST",
    "Менеджер": "MANAGER",
    "Хаускипинг": "HOUSEKEEPING",
    "Управляющий отелем": "HOTEL_MANAGER",
    "Администратор БД": "DB_ADMIN",
}


def role_code(role_name: str) -> str:
    return ROLE_CODES.get(role_name, "UNKNOWN")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int, role: str, permissions: list[str] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "permissions": permissions or [],
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise ValueError("invalid token") from exc
    if payload.get("type") != "access":
        raise ValueError("invalid token type")
    return payload


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

```

## `backend/app/crypto.py`

```python
from __future__ import annotations

import hashlib
import re
from functools import lru_cache

from cryptography.fernet import Fernet

from .config import get_settings


@lru_cache
def _fernet() -> Fernet:
    return Fernet(get_settings().data_encryption_key.encode("utf-8"))


def normalize_phone(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_document(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "").upper()


def hash_value(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def encrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def mask_phone(value: str | None) -> str | None:
    digits = normalize_phone(value)
    if not digits:
        return None
    if len(digits) <= 2:
        return "+7 ***-**-**"
    return f"+7 ***-**-{digits[-2:]}"


def mask_document(value: str | None) -> str | None:
    normalized = normalize_document(value)
    if not normalized:
        return None
    if len(normalized) <= 4:
        return "****"
    return f"**** {normalized[-4:]}"


def phone_fields(value: str | None) -> dict[str, str | None]:
    normalized = normalize_phone(value)
    return {
        "phone": mask_phone(value),
        "phone_enc": encrypt_value(value),
        "phone_hash": hash_value(normalized) if normalized else None,
    }


def document_fields(value: str | None) -> dict[str, str | None]:
    normalized = normalize_document(value)
    return {
        "document_number": mask_document(value),
        "document_number_enc": encrypt_value(value),
        "document_number_hash": hash_value(normalized) if normalized else None,
    }


def checkin_document_fields(value: str | None) -> dict[str, str | None]:
    normalized = normalize_document(value)
    return {
        "guest_document_number": mask_document(value),
        "guest_document_number_enc": encrypt_value(value),
        "guest_document_number_hash": hash_value(normalized) if normalized else None,
    }

```

## `backend/app/audit.py`

```python
from __future__ import annotations

import json
from typing import Any

from .db import get_pool


def _json_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


async def write_audit_event(
    *,
    user_id: int | None,
    table_name: str,
    record_id: int | None = None,
    action: str = "ERROR",
    old_value: Any = None,
    new_value: Any = None,
    error_message: str | None = None,
    is_error: bool = False,
    event_type: str = "DATA_CHANGE",
    severity: str = "INFO",
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    try:
        async with get_pool().connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO audit_log (
                        user_id, table_name, record_id, action,
                        old_value, new_value, ip_address, user_agent, request_id,
                        is_error, error_message, event_type, severity
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        table_name,
                        record_id,
                        action,
                        _json_text(old_value),
                        _json_text(new_value),
                        ip_address,
                        user_agent,
                        request_id,
                        is_error,
                        error_message,
                        event_type,
                        severity,
                    ),
                )
    except Exception:
        # Аудит не должен ломать основную операцию.
        pass

```

## `backend/app/migrations.py`

```python
from __future__ import annotations

import logging

from .crypto import checkin_document_fields, document_fields, phone_fields
from .db import get_pool

logger = logging.getLogger("sunstay.migrations")


async def encrypt_sensitive_data() -> None:
    """Идемпотентно шифрует существующие открытые контакты и маскирует их."""
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.transaction():
            guests = await conn.execute(
                """
                SELECT guest_id, phone, phone_enc, document_number, document_number_enc
                FROM guests
                WHERE phone_enc IS NULL OR document_number_enc IS NULL
                """
            )
            for guest in await guests.fetchall():
                guest_id = guest["guest_id"]
                phone = guest["phone"]
                document = guest["document_number"]
                if phone and guest["phone_enc"] is None and "*" not in phone:
                    values = phone_fields(phone)
                    await conn.execute(
                        "UPDATE guests SET phone = %s, phone_enc = %s, phone_hash = %s WHERE guest_id = %s",
                        (values["phone"], values["phone_enc"], values["phone_hash"], guest_id),
                    )
                if document and guest["document_number_enc"] is None and "*" not in document:
                    values = document_fields(document)
                    await conn.execute(
                        """
                        UPDATE guests
                        SET document_number = %s, document_number_enc = %s, document_number_hash = %s
                        WHERE guest_id = %s
                        """,
                        (
                            values["document_number"],
                            values["document_number_enc"],
                            values["document_number_hash"],
                            guest_id,
                        ),
                    )

            users = await conn.execute(
                "SELECT user_id, phone, phone_enc FROM users WHERE phone_enc IS NULL AND phone IS NOT NULL"
            )
            for user in await users.fetchall():
                phone = user["phone"]
                if phone and "*" not in phone:
                    values = phone_fields(phone)
                    await conn.execute(
                        "UPDATE users SET phone = %s, phone_enc = %s, phone_hash = %s WHERE user_id = %s",
                        (values["phone"], values["phone_enc"], values["phone_hash"], user["user_id"]),
                    )

            checkins = await conn.execute(
                """
                SELECT checkin_id, guest_document_number, guest_document_number_enc
                FROM check_ins
                WHERE guest_document_number_enc IS NULL AND guest_document_number IS NOT NULL
                """
            )
            for checkin in await checkins.fetchall():
                document = checkin["guest_document_number"]
                if document and "*" not in document:
                    values = checkin_document_fields(document)
                    await conn.execute(
                        """
                        UPDATE check_ins
                        SET guest_document_number = %s,
                            guest_document_number_enc = %s,
                            guest_document_number_hash = %s
                        WHERE checkin_id = %s
                        """,
                        (
                            values["guest_document_number"],
                            values["guest_document_number_enc"],
                            values["guest_document_number_hash"],
                            checkin["checkin_id"],
                        ),
                    )

    logger.info("Sensitive contact encryption migration completed")

```

## `backend/app/schedulers.py`

```python
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from .db import get_pool
from .services.backup import run_backup_sync

logger = logging.getLogger("sunstay.schedulers")


async def release_expired_holds() -> int:
    pool = get_pool()
    released = 0
    async with pool.connection() as conn:
        async with conn.transaction():
            cur = await conn.execute(
                "SELECT reason_id FROM cancellation_reasons WHERE name = 'Истекло время ожидания'"
            )
            reason = await cur.fetchone()
            reason_id = reason["reason_id"] if reason else None

            cur = await conn.execute(
                """
                SELECT b.booking_id, b.status, b.hold_until,
                       g.full_name AS guest_name, r.room_number
                FROM bookings b
                JOIN guests g ON g.guest_id = b.guest_id
                JOIN rooms r ON r.room_id = b.room_id
                WHERE b.status IN ('NEW','CONFIRMED')
                  AND b.hold_until IS NOT NULL
                  AND b.hold_until < now()
                """
            )
            expired = await cur.fetchall()
            for booking in expired:
                await conn.execute(
                    """
                    UPDATE bookings
                    SET status = 'CANCELLED',
                        cancellation_reason_id = %s
                    WHERE booking_id = %s
                    """,
                    (reason_id, booking["booking_id"]),
                )
                await conn.execute(
                    """
                    INSERT INTO audit_log (
                        user_id, table_name, record_id, action,
                        old_value, new_value, is_error, event_type, severity
                    ) VALUES (
                        NULL, 'bookings', %s, 'AUTO_RELEASE',
                        %s, %s, FALSE, 'AUTO_RELEASE', 'INFO'
                    )
                    """,
                    (
                        booking["booking_id"],
                        json.dumps(
                            {"status": booking["status"], "hold_until": str(booking["hold_until"])},
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "status": "CANCELLED",
                                "reason": "Истекло время ожидания",
                                "guest": booking["guest_name"],
                                "room": booking["room_number"],
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
                released += 1
    if released:
        logger.info("Released %s expired booking holds", released)
    return released


async def hold_release_loop() -> None:
    while True:
        try:
            await release_expired_holds()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Hold release scheduler failed")
        await asyncio.sleep(60)


async def backup_loop() -> None:
    while True:
        try:
            pool = get_pool()
            async with pool.connection() as conn:
                cur = await conn.execute(
                    """
                    SELECT key, value FROM system_settings
                    WHERE key IN ('backup.enabled','backup.schedule_time','backup.last_run_at')
                    """
                )
                settings = {row["key"]: row["value"] for row in await cur.fetchall()}

            enabled = bool(settings.get("backup.enabled", True))
            schedule_time = str(settings.get("backup.schedule_time") or "03:00")
            last_run = settings.get("backup.last_run_at")
            now = datetime.now()
            should_run = (
                enabled
                and now.strftime("%H:%M") == schedule_time
                and (not last_run or str(last_run)[:10] != now.strftime("%Y-%m-%d"))
            )
            if should_run:
                result = await asyncio.to_thread(run_backup_sync)
                logger.info("Scheduled backup finished: %s", result.get("status"))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Backup scheduler failed")
        await asyncio.sleep(30)


def start_schedulers() -> list[asyncio.Task]:
    return [
        asyncio.create_task(hold_release_loop(), name="hold-release"),
        asyncio.create_task(backup_loop(), name="backup"),
    ]


async def stop_schedulers(tasks: list[asyncio.Task]) -> None:
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

```

## `backend/app/deps.py`

```python
﻿from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status
from psycopg import AsyncConnection

from .db import apply_context, get_db
from .security import decode_access_token, role_code


async def _load_user(conn: AsyncConnection, user_id: int) -> dict[str, Any]:
    cur = await conn.execute(
        """
        SELECT
            u.user_id,
            u.role_id,
            r.name AS role_name,
            u.full_name,
            u.email,
            u.phone,
            u.is_active,
            u.last_login_at,
            g.guest_id
        FROM users u
        JOIN roles r ON r.role_id = u.role_id
        LEFT JOIN guests g ON g.user_id = u.user_id
        WHERE u.user_id = %s
        """,
        (user_id,),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    if not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Учётная запись заблокирована")

    cur = await conn.execute(
        "SELECT permission_code FROM fn_user_permissions(%s::integer)",
        (user_id,),
    )
    permissions = [r["permission_code"] for r in await cur.fetchall()]

    await conn.execute(
        """
        UPDATE users
        SET last_seen_at = now()
        WHERE user_id = %s
          AND (last_seen_at IS NULL OR last_seen_at < now() - interval '1 minute')
        """,
        (user_id,),
    )

    user = dict(row)
    user["role_code"] = role_code(row["role_name"])
    user["permissions"] = permissions
    return user


async def get_optional_user(
    request: Request,
    conn: AsyncConnection = Depends(get_db),
) -> dict[str, Any] | None:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        return None

    try:
        user = await _load_user(conn, user_id)
    except HTTPException:
        return None
    request.state.user = user
    await apply_context(conn, request)
    return user


async def get_current_user(
    request: Request,
    conn: AsyncConnection = Depends(get_db),
) -> dict[str, Any]:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = header.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await _load_user(conn, user_id)
    request.state.user = user
    await apply_context(conn, request)
    return user


def require_permission(permission: str) -> Callable:
    async def dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if permission not in user["permissions"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав: {permission}",
            )
        return user

    return dependency


def require_role(*roles: str) -> Callable:
    async def dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user["role_code"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return user

    return dependency

```

## `backend/app/schemas.py`

```python
from __future__ import annotations

from datetime import date, time
from typing import Any, Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    document_number: str = Field(min_length=3, max_length=50)
    phone: str | None = None
    email: str
    password: str = Field(min_length=8, max_length=128)
    pdn_consent: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class RefreshRequest(BaseModel):
    refresh_token: str


class SettingsUpdate(BaseModel):
    theme: Literal["light", "dark", "system"] = "system"
    language: Literal["ru", "en"] = "ru"
    date_format: str = "dd.MM.yyyy"
    number_format: str = "space_comma"
    page_size: Literal[10, 25, 50] = 25
    saved_filters: list[dict[str, Any]] = Field(default_factory=list)


class PublicBookingCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    document_number: str = Field(min_length=3, max_length=50)
    phone: str | None = None
    email: str | None = None
    pdn_consent: bool = True
    room_id: int
    rate_id: int
    checkin_date: date
    checkout_date: date
    promo_code: str | None = None
    adults: int = Field(default=1, ge=1, le=10)
    children: int = Field(default=0, ge=0, le=10)
    payment_method: Literal["CARD", "ONLINE", "CASH", "BANK_TRANSFER"] = "ONLINE"
    payment_amount: float = 0
    source: Literal["SITE", "PHONE", "WALK_IN", "OTA"] = "SITE"
    arrival_time: time | None = None
    hold_minutes: int = Field(default=60, ge=5, le=1440)


class ManagerBookingCreate(BaseModel):
    guest_id: int
    room_id: int
    rate_id: int
    checkin_date: date
    checkout_date: date
    promo_id: int | None = None
    adults: int = Field(default=1, ge=1, le=10)
    children: int = Field(default=0, ge=0, le=10)
    source: Literal["SITE", "PHONE", "WALK_IN", "OTA"] = "SITE"
    arrival_time: time | None = None
    hold_minutes: int = Field(default=60, ge=5, le=1440)


class MoveBookingRequest(BaseModel):
    room_id: int
    checkin_date: date
    checkout_date: date


class CheckInRequest(BaseModel):
    document_number: str
    deposit_amount: float = 0
    payment_method: Literal["CARD", "CASH", "BANK_TRANSFER", "ONLINE"] = "CARD"


class CheckOutRequest(BaseModel):
    payment_amount: float = 0
    payment_method: Literal["CARD", "CASH", "BANK_TRANSFER", "ONLINE"] = "CARD"


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    method: Literal["CARD", "CASH", "BANK_TRANSFER", "ONLINE"] = "CARD"
    payment_type: Literal["PAYMENT", "DEPOSIT"] = "PAYMENT"


class RefundCreate(BaseModel):
    amount: float = Field(gt=0)
    reason: str = Field(min_length=3, max_length=255)


class ServiceOrderCreate(BaseModel):
    service_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class NightAuditRequest(BaseModel):
    business_date: date


class RoomStatusUpdate(BaseModel):
    status_name: str
    reason_id: int | None = None


class HousekeepingTaskCreate(BaseModel):
    room_id: int
    staff_id: int | None = None
    task_type: Literal["DAILY", "POST_CHECKOUT", "ON_REQUEST"] = "DAILY"
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"] = "NORMAL"


class ConsumableWriteOff(BaseModel):
    consumable_id: int
    quantity: float = Field(gt=0)


class MaintenanceCreate(BaseModel):
    room_id: int
    description: str = Field(min_length=3, max_length=2000)
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"] = "NORMAL"
    task_id: int | None = None
    assigned_to: int | None = None


class MaintenanceStatusUpdate(BaseModel):
    status: Literal["OPEN", "IN_PROGRESS", "DONE", "CANCELLED"]


class UserCreate(BaseModel):
    role_id: int
    full_name: str = Field(min_length=3, max_length=200)
    email: str
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)
    is_active: bool = True


class UserUpdate(BaseModel):
    role_id: int | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class RoleAssignRequest(BaseModel):
    role_id: int


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str]


class GuestCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=200)
    document_number: str = Field(min_length=3, max_length=50)
    phone: str | None = None
    email: str | None = None
    pdn_consent: bool = True


class ImportCommitRequest(BaseModel):
    filename: str | None = None
    rows: list[dict[str, Any]]


class HoldUpdateRequest(BaseModel):
    arrival_time: time | None = None
    hold_minutes: int = Field(default=60, ge=5, le=1440)


class BlockUserRequest(BaseModel):
    reason_id: int | None = None
    custom_reason: str | None = Field(default=None, max_length=500)

```

## `backend/app/utils.py`

```python
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from psycopg import AsyncConnection


def json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def row_to_dict(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: json_value(value) for key, value in row.items()}


def rows_to_dicts(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: json_value(value) for key, value in row.items()} for row in rows]


def csv_response(rows: list[dict[str, Any]], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    buffer.write("\ufeff")
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json_value(value) for key, value in row.items()})
    else:
        buffer.write("")

    content = buffer.getvalue().encode("utf-8")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([content]), media_type="text/csv; charset=utf-8", headers=headers)


async def fetch_one(conn: AsyncConnection, query: str, params: tuple = ()) -> dict[str, Any] | None:
    cur = await conn.execute(query, params)
    return await cur.fetchone()


async def fetch_all(conn: AsyncConnection, query: str, params: tuple = ()) -> list[dict[str, Any]]:
    cur = await conn.execute(query, params)
    return list(await cur.fetchall())


async def get_booking(conn: AsyncConnection, booking_id: int) -> dict[str, Any]:
    row = await fetch_one(
        conn,
        """
        SELECT
            b.*,
            g.full_name AS guest_name,
            g.document_number,
            g.phone AS guest_phone,
            g.email AS guest_email,
            r.room_number,
            rt.name AS room_type,
            rp.name AS rate_name,
            rp.price_per_night,
            pc.code AS promo_code,
            cr.name AS cancellation_reason
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN rate_plans rp ON rp.rate_id = b.rate_id
        LEFT JOIN promo_codes pc ON pc.promo_id = b.promo_id
        LEFT JOIN cancellation_reasons cr ON cr.reason_id = b.cancellation_reason_id
        WHERE b.booking_id = %s
        """,
        (booking_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    return row_to_dict(row) or {}


async def get_folio(conn: AsyncConnection, folio_id: int) -> dict[str, Any]:
    row = await fetch_one(
        conn,
        """
        SELECT
            f.*,
            b.booking_id,
            b.checkin_date,
            b.checkout_date,
            g.full_name AS guest_name,
            g.document_number,
            g.phone AS guest_phone,
            g.email AS guest_email,
            r.room_number,
            rt.name AS room_type,
            fn_folio_charged(f.folio_id) AS charged_total,
            fn_folio_paid(f.folio_id) AS paid_total,
            fn_folio_balance(f.folio_id) AS balance
        FROM folios f
        JOIN bookings b ON b.booking_id = f.booking_id
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        WHERE f.folio_id = %s
        """,
        (folio_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Folio не найден")
    return row_to_dict(row) or {}


def guest_access_denied(booking: dict[str, Any], user: dict[str, Any]) -> bool:
    return user["role_code"] == "GUEST" and booking.get("guest_id") != user.get("guest_id")

```

## `backend/app/api/auth.py`

```python
﻿from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from ..audit import write_audit_event
from ..crypto import document_fields, phone_fields
from ..db import get_db, get_pool
from ..deps import get_current_user
from ..schemas import LoginRequest, RefreshRequest, RegisterRequest, SettingsUpdate
from ..security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    refresh_expiry,
    role_code,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings_router = APIRouter(prefix="/settings", tags=["settings"])

DEMO_ACCOUNTS = [
    {"role": "Гость", "email": "guest.demo@sunstay.example"},
    {"role": "Менеджер", "email": "smirnova@sunstay.example"},
    {"role": "Хаускипинг", "email": "fedorov@sunstay.example"},
    {"role": "Управляющий отелем", "email": "volkov@sunstay.example"},
    {"role": "Администратор БД", "email": "dba@sunstay.example"},
]


def public_user(user: dict) -> dict:
    return {
        "user_id": user["user_id"],
        "role_id": user["role_id"],
        "role_name": user["role_name"],
        "role_code": user["role_code"],
        "full_name": user["full_name"],
        "email": user["email"],
        "phone": user.get("phone"),
        "guest_id": user.get("guest_id"),
        "permissions": user.get("permissions", []),
    }


async def fetch_user_by_email(conn: AsyncConnection, email: str) -> dict | None:
    cur = await conn.execute(
        """
        SELECT
            u.user_id, u.role_id, r.name AS role_name, u.full_name, u.email, u.phone,
            u.password_hash, u.is_active, u.failed_login_attempts,
            (u.locked_until IS NOT NULL AND u.locked_until > now()) AS is_locked,
            CASE
                WHEN u.locked_until IS NOT NULL AND u.locked_until > now()
                THEN GREATEST(1, CEIL(EXTRACT(EPOCH FROM (u.locked_until - now()))))::INTEGER
                ELSE 0
            END AS lock_seconds,
            g.guest_id
        FROM users u
        JOIN roles r ON r.role_id = u.role_id
        LEFT JOIN guests g ON g.user_id = u.user_id
        WHERE lower(u.email) = lower(%s)
        """,
        (email,),
    )
    return await cur.fetchone()


async def load_permissions(conn: AsyncConnection, user_id: int) -> list[str]:
    cur = await conn.execute(
        "SELECT permission_code FROM fn_user_permissions(%s::integer)",
        (user_id,),
    )
    return [row["permission_code"] for row in await cur.fetchall()]


async def log_attempt(
    email: str,
    ip: str,
    success: bool,
    user: dict | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    message: str | None = None,
    count_failure: bool = True,
    force_blocked: bool = False,
) -> bool:
    async with get_pool().connection() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO login_attempts (email, ip_address, success) VALUES (%s, %s, %s)",
                (email, ip, success),
            )

            user_id = user["user_id"] if user else None
            audit_value = json.dumps({"email": email, "ip": ip}, ensure_ascii=False)
            if user_id:
                await conn.execute(
                    """
                    SELECT set_config('app.current_user_id', %s, true),
                           set_config('app.client_ip', %s, true),
                           set_config('app.request_id', %s, true)
                    """,
                    (str(user_id), ip, request_id or ""),
                )

            if success:
                if user_id:
                    await conn.execute(
                        """
                        UPDATE users
                        SET failed_login_attempts = 0,
                            locked_until = NULL,
                            last_login_at = now()
                        WHERE user_id = %s
                        """,
                        (user_id,),
                    )
                await conn.execute(
                    """
                    INSERT INTO audit_log (
                        user_id, table_name, record_id, action, new_value,
                        ip_address, user_agent, request_id, is_error, event_type, severity
                    ) VALUES (%s, 'auth', %s, 'LOGIN_SUCCESS', %s, %s, %s, %s, FALSE, 'LOGIN_SECURITY', 'INFO')
                    """,
                    (user_id, user_id, audit_value, ip, user_agent, request_id),
                )
                return False

            locked = False
            if user_id and count_failure:
                cur = await conn.execute(
                    """
                    WITH updated AS (
                        UPDATE users
                        SET failed_login_attempts = CASE
                                WHEN failed_login_attempts + 1 >= 3 THEN 0
                                ELSE failed_login_attempts + 1
                            END,
                            locked_until = CASE
                                WHEN failed_login_attempts + 1 >= 3
                                    THEN now() + interval '30 seconds'
                                ELSE locked_until
                            END
                        WHERE user_id = %s
                        RETURNING user_id, locked_until
                    )
                    SELECT user_id,
                           (locked_until IS NOT NULL AND locked_until > now()) AS locked
                    FROM updated
                    """,
                    (user_id,),
                )
                row = await cur.fetchone()
                locked = bool(row and row["locked"])

            action = "LOGIN_BLOCKED" if (locked or force_blocked) else "LOGIN_FAILED"
            severity = "WARNING" if action == "LOGIN_BLOCKED" else "INFO"
            await conn.execute(
                """
                INSERT INTO audit_log (
                    user_id, table_name, record_id, action, new_value,
                    ip_address, user_agent, request_id,
                    is_error, error_message, event_type, severity
                ) VALUES (%s, 'auth', %s, %s, %s, %s, %s, %s, TRUE, %s, 'LOGIN_SECURITY', %s)
                """,
                (
                    user_id,
                    user_id,
                    action,
                    audit_value,
                    ip,
                    user_agent,
                    request_id,
                    message,
                    severity,
                ),
            )
            return locked


async def issue_tokens(conn: AsyncConnection, user: dict) -> dict:
    permissions = await load_permissions(conn, user["user_id"])
    role = role_code(user["role_name"])
    access_token = create_access_token(user["user_id"], role, permissions)
    refresh_token = new_refresh_token()
    await conn.execute(
        """
        INSERT INTO user_sessions (user_id, refresh_token_hash, user_agent, ip_address, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user["user_id"], hash_refresh_token(refresh_token), "", "", refresh_expiry()),
    )
    user_payload = dict(user)
    user_payload["role_code"] = role
    user_payload["permissions"] = permissions
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": public_user(user_payload),
    }


@router.post("/login")
async def login(payload: LoginRequest, request: Request, conn: AsyncConnection = Depends(get_db)):
    user = await fetch_user_by_email(conn, payload.email)
    ip = request.client.host if request.client else ""
    ua = request.headers.get("user-agent")
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())

    if not user:
        await log_attempt(
            payload.email, ip, False,
            user_agent=ua, request_id=rid,
            message="Пользователь не найден",
        )
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if not user["is_active"]:
        await log_attempt(
            payload.email, ip, False, user=user,
            user_agent=ua, request_id=rid,
            message="Учётная запись заблокирована администратором",
            count_failure=False, force_blocked=True,
        )
        raise HTTPException(status_code=403, detail="Учётная запись заблокирована")

    if user["is_locked"]:
        await log_attempt(
            payload.email, ip, False, user=user,
            user_agent=ua, request_id=rid,
            message="Попытка входа во время блокировки",
            count_failure=False, force_blocked=True,
        )
        seconds = user.get("lock_seconds") or 30
        raise HTTPException(
            status_code=423,
            detail=f"Слишком много попыток. Повторите через {seconds} сек.",
            headers={"Retry-After": str(seconds)},
        )

    if not verify_password(payload.password, user["password_hash"]):
        locked = await log_attempt(
            payload.email, ip, False, user=user,
            user_agent=ua, request_id=rid,
            message="Неверный пароль",
            count_failure=True,
        )
        if locked:
            raise HTTPException(
                status_code=423,
                detail="Слишком много попыток. Повторите через 30 сек.",
                headers={"Retry-After": "30"},
            )
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    await log_attempt(
        payload.email, ip, True, user=user,
        user_agent=ua, request_id=rid,
    )
    return await issue_tokens(conn, user)


@router.post("/refresh")
async def refresh(payload: RefreshRequest, conn: AsyncConnection = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    cur = await conn.execute(
        """
        SELECT s.session_id, u.*, r.name AS role_name, g.guest_id
        FROM user_sessions s
        JOIN users u ON u.user_id = s.user_id
        JOIN roles r ON r.role_id = u.role_id
        LEFT JOIN guests g ON g.user_id = u.user_id
        WHERE s.refresh_token_hash = %s
          AND s.revoked_at IS NULL
          AND s.expires_at > now()
        """,
        (token_hash,),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Сессия недействительна")

    await conn.execute(
        "UPDATE user_sessions SET revoked_at = now() WHERE session_id = %s",
        (row["session_id"],),
    )
    return await issue_tokens(conn, row)


@router.post("/logout")
async def logout(payload: RefreshRequest, conn: AsyncConnection = Depends(get_db)):
    await conn.execute(
        "UPDATE user_sessions SET revoked_at = now() WHERE refresh_token_hash = %s",
        (hash_refresh_token(payload.refresh_token),),
    )
    return {"ok": True}


@router.post("/register")
async def register(payload: RegisterRequest, conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute("SELECT 1 FROM users WHERE lower(email) = lower(%s)", (payload.email,))
    if await cur.fetchone():
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")

    document = document_fields(payload.document_number)
    phone = phone_fields(payload.phone)

    cur = await conn.execute(
        "SELECT 1 FROM guests WHERE document_number_hash = %s",
        (document["document_number_hash"],),
    )
    if await cur.fetchone():
        raise HTTPException(status_code=409, detail="Гость с таким документом уже существует")

    cur = await conn.execute(
        """
        INSERT INTO users (role_id, full_name, email, phone, phone_enc, phone_hash, password_hash)
        VALUES (1, %s, %s, %s, %s, %s, %s)
        RETURNING user_id, role_id, full_name, email, phone
        """,
        (
            payload.full_name,
            payload.email,
            phone["phone"],
            phone["phone_enc"],
            phone["phone_hash"],
            hash_password(payload.password),
        ),
    )
    user = await cur.fetchone()
    await conn.execute(
        """
        INSERT INTO guests (
            full_name, document_number, document_number_enc, document_number_hash,
            phone, phone_enc, phone_hash, email, pdn_consent, user_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            payload.full_name,
            document["document_number"],
            document["document_number_enc"],
            document["document_number_hash"],
            phone["phone"],
            phone["phone_enc"],
            phone["phone_hash"],
            payload.email,
            payload.pdn_consent,
            user["user_id"],
        ),
    )
    await conn.execute(
        "INSERT INTO user_settings (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
        (user["user_id"],),
    )
    user["role_name"] = "Гость"
    cur = await conn.execute("SELECT guest_id FROM guests WHERE user_id = %s", (user["user_id"],))
    guest = await cur.fetchone()
    user["guest_id"] = guest["guest_id"] if guest else None
    return await issue_tokens(conn, user)


@router.get("/me")
async def me(user: dict = Depends(get_current_user), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute("SELECT * FROM user_settings WHERE user_id = %s", (user["user_id"],))
    settings = await cur.fetchone()
    return {"user": public_user(user), "settings": settings}


@router.get("/demo-accounts")
async def demo_accounts():
    return [
        {**account, "password": "SunStay2026!"}
        for account in DEMO_ACCOUNTS
    ]


@settings_router.get("")
async def get_settings(user: dict = Depends(get_current_user), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute("SELECT * FROM user_settings WHERE user_id = %s", (user["user_id"],))
    row = await cur.fetchone()
    if not row:
        cur = await conn.execute(
            "INSERT INTO user_settings (user_id) VALUES (%s) RETURNING *",
            (user["user_id"],),
        )
        row = await cur.fetchone()
    return row


@settings_router.put("")
async def update_settings(
    payload: SettingsUpdate,
    user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        """
        INSERT INTO user_settings
            (user_id, theme, language, date_format, number_format, page_size, saved_filters, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, now())
        ON CONFLICT (user_id) DO UPDATE SET
            theme = EXCLUDED.theme,
            language = EXCLUDED.language,
            date_format = EXCLUDED.date_format,
            number_format = EXCLUDED.number_format,
            page_size = EXCLUDED.page_size,
            saved_filters = EXCLUDED.saved_filters,
            updated_at = now()
        """,
        (
            user["user_id"],
            payload.theme,
            payload.language,
            payload.date_format,
            payload.number_format,
            payload.page_size,
            Jsonb(payload.saved_filters),
        ),
    )
    cur = await conn.execute("SELECT * FROM user_settings WHERE user_id = %s", (user["user_id"],))
    return await cur.fetchone()

```

## `backend/app/api/public.py`

```python
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg import AsyncConnection

from ..audit import write_audit_event
from ..crypto import document_fields, phone_fields
from ..db import get_db
from ..schemas import PublicBookingCreate
from ..utils import get_booking, row_to_dict, rows_to_dicts

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/room-types")
async def room_types(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT
            rt.room_type_id,
            rt.name,
            rt.capacity,
            rt.description,
            (SELECT MIN(rp.price_per_night)
             FROM rate_plans rp
             WHERE rp.room_type_id = rt.room_type_id) AS min_price,
            (SELECT COUNT(*) FROM rooms r WHERE r.room_type_id = rt.room_type_id) AS rooms_count,
            (SELECT COALESCE(json_agg(DISTINCT a.name), '[]'::json)
             FROM rooms r
             JOIN room_amenities ra ON ra.room_id = r.room_id
             JOIN amenities a ON a.amenity_id = ra.amenity_id
             WHERE r.room_type_id = rt.room_type_id) AS amenities
        FROM room_types rt
        ORDER BY rt.room_type_id
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/cancellation-reasons")
async def cancellation_reasons(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute("SELECT * FROM cancellation_reasons ORDER BY reason_id")
    return rows_to_dicts(await cur.fetchall())


@router.get("/services")
async def services(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT s.service_id, s.name, s.price, su.name AS unit
        FROM services s
        JOIN service_units su ON su.unit_id = s.unit_id
        ORDER BY s.service_id
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/rooms")
async def rooms(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT
            r.room_id, r.room_number, r.floor,
            rt.room_type_id, rt.name AS room_type, rt.capacity,
            rs.name AS status
        FROM rooms r
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        ORDER BY r.room_number
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/availability")
async def availability(
    checkin: date = Query(...),
    checkout: date = Query(...),
    guests: int = Query(1, ge=1),
    room_type_id: int | None = None,
    conn: AsyncConnection = Depends(get_db),
):
    if checkout <= checkin:
        raise HTTPException(status_code=400, detail="Дата выезда должна быть позже даты заезда")

    params: list = [checkin, checkout, checkin, checkout, guests]
    type_filter = ""
    if room_type_id:
        type_filter = "AND rt.room_type_id = %s"
        params.append(room_type_id)

    cur = await conn.execute(
        f"""
        SELECT * FROM (
            SELECT
                rt.room_type_id,
                rt.name,
                rt.capacity,
                rt.description,
                (SELECT MIN(rp.price_per_night)
                 FROM rate_plans rp
                 WHERE rp.room_type_id = rt.room_type_id
                   AND %s >= rp.season_start
                   AND %s - 1 <= rp.season_end) AS price_per_night,
                (SELECT COUNT(*)
                 FROM rooms r
                 WHERE r.room_type_id = rt.room_type_id
                   AND fn_room_available(r.room_id, %s, %s)) AS available_rooms,
                (SELECT COALESCE(json_agg(json_build_object(
                        'room_id', r.room_id,
                        'room_number', r.room_number,
                        'rate_id', rp.rate_id,
                        'price_per_night', rp.price_per_night
                    ) ORDER BY r.room_number), '[]'::json)
                 FROM rooms r
                 JOIN LATERAL (
                     SELECT rp.rate_id, rp.price_per_night
                     FROM rate_plans rp
                     WHERE rp.room_type_id = rt.room_type_id
                       AND %s >= rp.season_start
                       AND %s - 1 <= rp.season_end
                     ORDER BY rp.price_per_night
                     LIMIT 1
                 ) rp ON true
                 WHERE r.room_type_id = rt.room_type_id
                   AND fn_room_available(r.room_id, %s, %s)) AS rooms
            FROM room_types rt
            WHERE rt.capacity >= %s
            {type_filter}
        ) q
        WHERE q.available_rooms > 0
        ORDER BY q.price_per_night
        """,
        (
            checkin,
            checkout,
            checkin,
            checkout,
            checkin,
            checkout,
            checkin,
            checkout,
            *params[4:],
        ),
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/promo/{code}")
async def promo(code: str, checkin: date | None = None, conn: AsyncConnection = Depends(get_db)):
    target_date = checkin or date.today()
    cur = await conn.execute(
        """
        SELECT promo_id, code, discount_percent, valid_from, valid_to
        FROM promo_codes
        WHERE upper(code) = upper(%s)
          AND %s BETWEEN valid_from AND valid_to
        """,
        (code, target_date),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Промокод не действует")
    return row_to_dict(row)


async def find_or_create_guest(conn: AsyncConnection, payload: PublicBookingCreate) -> int:
    document = document_fields(payload.document_number)
    phone = phone_fields(payload.phone)

    cur = await conn.execute(
        "SELECT guest_id FROM guests WHERE document_number_hash = %s",
        (document["document_number_hash"],),
    )
    row = await cur.fetchone()
    if row:
        await conn.execute(
            """
            UPDATE guests
            SET full_name = %s,
                phone = COALESCE(%s, phone),
                phone_enc = COALESCE(%s, phone_enc),
                phone_hash = COALESCE(%s, phone_hash),
                email = COALESCE(%s, email),
                pdn_consent = pdn_consent OR %s
            WHERE guest_id = %s
            """,
            (
                payload.full_name,
                phone["phone"],
                phone["phone_enc"],
                phone["phone_hash"],
                payload.email,
                payload.pdn_consent,
                row["guest_id"],
            ),
        )
        return row["guest_id"]

    if not payload.pdn_consent:
        raise HTTPException(status_code=400, detail="Нужно согласие на обработку персональных данных")

    cur = await conn.execute(
        """
        INSERT INTO guests (
            full_name, document_number, document_number_enc, document_number_hash,
            phone, phone_enc, phone_hash, email, pdn_consent
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING guest_id
        """,
        (
            payload.full_name,
            document["document_number"],
            document["document_number_enc"],
            document["document_number_hash"],
            phone["phone"],
            phone["phone_enc"],
            phone["phone_hash"],
            payload.email,
            payload.pdn_consent,
        ),
    )
    return (await cur.fetchone())["guest_id"]


@router.post("/bookings")
async def create_public_booking(
    payload: PublicBookingCreate,
    request: Request,
    conn: AsyncConnection = Depends(get_db),
):
    if not payload.pdn_consent:
        raise HTTPException(status_code=400, detail="Нужно согласие на обработку персональных данных")

    guest_id = await find_or_create_guest(conn, payload)

    cur = await conn.execute(
        """
        SELECT r.room_id, r.room_type_id
        FROM rooms r
        WHERE r.room_id = %s
        """,
        (payload.room_id,),
    )
    room = await cur.fetchone()
    if not room:
        raise HTTPException(status_code=404, detail="Номер не найден")

    rate_id = payload.rate_id
    cur = await conn.execute(
        """
        SELECT rate_id
        FROM rate_plans
        WHERE room_type_id = %s
          AND %s >= season_start
          AND %s - 1 <= season_end
        ORDER BY price_per_night
        LIMIT 1
        """,
        (room["room_type_id"], payload.checkin_date, payload.checkout_date),
    )
    rate = await cur.fetchone()
    if not rate:
        raise HTTPException(status_code=400, detail="Нет тарифа на выбранные даты")
    if not rate_id:
        rate_id = rate["rate_id"]

    promo_id = None
    if payload.promo_code:
        cur = await conn.execute(
            """
            SELECT promo_id
            FROM promo_codes
            WHERE upper(code) = upper(%s)
              AND %s BETWEEN valid_from AND valid_to
            """,
            (payload.promo_code, payload.checkin_date),
        )
        promo = await cur.fetchone()
        if not promo:
            raise HTTPException(status_code=400, detail="Промокод не действует")
        promo_id = promo["promo_id"]

    try:
        cur = await conn.execute(
            """
            SELECT fn_create_booking(
                %s::integer, %s::integer, %s::integer, %s::date, %s::date,
                %s::integer, %s::varchar, %s::integer, %s::integer, NULL, %s::varchar,
                %s::time, %s::integer
            ) AS booking_id
            """,
            (
                guest_id,
                payload.room_id,
                rate_id,
                payload.checkin_date,
                payload.checkout_date,
                promo_id,
                payload.source,
                payload.adults,
                payload.children,
                request.client.host if request.client else "",
                payload.arrival_time,
                payload.hold_minutes,
            ),
        )
        booking_id = (await cur.fetchone())["booking_id"]
    except Exception as exc:
        await write_audit_event(
            user_id=None,
            table_name="bookings",
            action="ERROR",
            new_value={
                "guest_id": guest_id,
                "room_id": payload.room_id,
                "rate_id": rate_id,
                "checkin_date": str(payload.checkin_date),
                "checkout_date": str(payload.checkout_date),
            },
            error_message=str(exc)[:500],
            is_error=True,
            event_type="VALIDATION_ERROR",
            severity="ERROR",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=request.headers.get("x-request-id"),
        )
        raise HTTPException(status_code=400, detail=str(exc))

    if payload.payment_method in ("ONLINE", "CARD"):
        cur = await conn.execute(
            """
            SELECT fn_calculate_stay_price(%s::integer, %s::date, %s::date, %s::integer) AS total
            """,
            (rate_id, payload.checkin_date, payload.checkout_date, promo_id),
        )
        total = float((await cur.fetchone())["total"])
        amount = payload.payment_amount or total

        cur = await conn.execute(
            """
            INSERT INTO folios (booking_id, status)
            VALUES (%s, 'OPEN')
            ON CONFLICT (booking_id) DO UPDATE SET status = 'OPEN'
            RETURNING folio_id
            """,
            (booking_id,),
        )
        folio_id = (await cur.fetchone())["folio_id"]
        await conn.execute(
            """
            INSERT INTO payments (folio_id, amount, method, payment_type)
            VALUES (%s, %s, %s, 'DEPOSIT')
            """,
            (folio_id, amount, payload.payment_method),
        )
        await conn.execute(
            "CALL sp_confirm_booking(%s::integer, NULL, %s::varchar)",
            (booking_id, request.client.host if request.client else ""),
        )

    return await get_booking(conn, booking_id)

```

## `backend/app/api/guest.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from psycopg import AsyncConnection

from ..db import get_db
from ..deps import get_current_user, require_permission
from ..schemas import ServiceOrderCreate
from ..services.pdf import folio_pdf
from ..utils import get_booking, get_folio, rows_to_dicts

router = APIRouter(prefix="/guest", tags=["guest"])


def require_guest(user: dict = Depends(get_current_user)) -> dict:
    if user["role_code"] != "GUEST":
        raise HTTPException(status_code=403, detail="Доступно только гостю")
    if not user.get("guest_id"):
        raise HTTPException(status_code=403, detail="Профиль гостя не привязан к учётной записи")
    return user


@router.get("/dashboard")
async def dashboard(user: dict = Depends(require_guest), conn: AsyncConnection = Depends(get_db)):
    guest_id = user["guest_id"]
    cur = await conn.execute(
        """
        SELECT b.booking_id, b.checkin_date, b.checkout_date, b.status,
               r.room_number, rt.name AS room_type, rp.price_per_night
        FROM bookings b
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN rate_plans rp ON rp.rate_id = b.rate_id
        WHERE b.guest_id = %s
          AND b.status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND b.checkout_date >= CURRENT_DATE
        ORDER BY b.checkin_date
        LIMIT 1
        """,
        (guest_id,),
    )
    upcoming = await cur.fetchone()

    cur = await conn.execute(
        """
        SELECT b.booking_id, b.checkin_date, b.checkout_date, b.status,
               r.room_number, rt.name AS room_type
        FROM bookings b
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        WHERE b.guest_id = %s
        ORDER BY b.created_at DESC
        LIMIT 5
        """,
        (guest_id,),
    )
    recent = await cur.fetchall()

    cur = await conn.execute(
        """
        SELECT f.folio_id, f.status,
               fn_folio_charged(f.folio_id) AS charged_total,
               fn_folio_paid(f.folio_id) AS paid_total,
               fn_folio_balance(f.folio_id) AS balance
        FROM folios f
        JOIN bookings b ON b.booking_id = f.booking_id
        WHERE b.guest_id = %s
        ORDER BY f.folio_id DESC
        LIMIT 1
        """,
        (guest_id,),
    )
    folio = await cur.fetchone()

    cur = await conn.execute("SELECT service_id, name, price FROM services ORDER BY service_id")
    services = await cur.fetchall()

    return {
        "upcoming": upcoming,
        "recent_bookings": recent,
        "folio": folio,
        "recommended_services": services,
    }


@router.get("/bookings")
async def bookings(
    status: str | None = None,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    params: list = [user["guest_id"]]
    status_filter = ""
    if status:
        status_filter = "AND b.status = %s"
        params.append(status)
    cur = await conn.execute(
        f"""
        SELECT b.booking_id, b.checkin_date, b.checkout_date, b.status, b.source,
               r.room_number, rt.name AS room_type,
               fn_booking_balance(b.booking_id) AS balance
        FROM bookings b
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        WHERE b.guest_id = %s
        {status_filter}
        ORDER BY b.checkin_date DESC
        """,
        tuple(params),
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/bookings/{booking_id}")
async def booking_detail(
    booking_id: int,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")

    cur = await conn.execute(
        """
        SELECT * FROM check_ins WHERE booking_id = %s ORDER BY checkin_id DESC LIMIT 1
        """,
        (booking_id,),
    )
    checkin = await cur.fetchone()
    cur = await conn.execute(
        """
        SELECT * FROM check_outs WHERE booking_id = %s ORDER BY checkout_id DESC LIMIT 1
        """,
        (booking_id,),
    )
    checkout = await cur.fetchone()
    cur = await conn.execute(
        """
        SELECT so.order_id, so.quantity, so.ordered_at, s.name, s.price,
               so.quantity * s.price AS total
        FROM service_orders so
        JOIN services s ON s.service_id = so.service_id
        WHERE so.booking_id = %s
        ORDER BY so.order_id
        """,
        (booking_id,),
    )
    services = await cur.fetchall()
    cur = await conn.execute(
        """
        SELECT folio_id, status, opened_at, closed_at,
               fn_folio_charged(folio_id) AS charged_total,
               fn_folio_paid(folio_id) AS paid_total,
               fn_folio_balance(folio_id) AS balance
        FROM folios WHERE booking_id = %s ORDER BY folio_id DESC LIMIT 1
        """,
        (booking_id,),
    )
    folio = await cur.fetchone()

    timeline = [{"label": "Создана", "date": booking.get("created_at"), "done": True}]
    timeline.append(
        {
            "label": "Подтверждена",
            "date": None,
            "done": booking["status"] in ("CONFIRMED", "CHECKED_IN", "CHECKED_OUT"),
        }
    )
    timeline.append(
        {
            "label": "Заезд",
            "date": checkin["actual_checkin_at"] if checkin else None,
            "done": bool(checkin),
        }
    )
    timeline.append(
        {
            "label": "Выезд",
            "date": checkout["actual_checkout_at"] if checkout else None,
            "done": bool(checkout),
        }
    )

    return {
        "booking": booking,
        "services": services,
        "folio": folio,
        "timeline": timeline,
    }


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    request: Request,
    reason_id: int | None = Query(default=None),
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")
    if booking["status"] not in ("NEW", "CONFIRMED"):
        raise HTTPException(status_code=400, detail="Эту бронь нельзя отменить")
    await conn.execute(
        "CALL sp_cancel_booking(%s::integer, %s::integer, %s::integer, %s::varchar)",
        (booking_id, reason_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "CANCELLED"}


@router.get("/folios")
async def folios(user: dict = Depends(require_guest), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT f.folio_id, f.booking_id, f.status, f.opened_at, f.closed_at,
               fn_folio_charged(f.folio_id) AS charged_total,
               fn_folio_paid(f.folio_id) AS paid_total,
               fn_folio_balance(f.folio_id) AS balance
        FROM folios f
        JOIN bookings b ON b.booking_id = f.booking_id
        WHERE b.guest_id = %s
        ORDER BY f.folio_id DESC
        """,
        (user["guest_id"],),
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/folios/{folio_id}")
async def folio_detail(
    folio_id: int,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    folio = await get_folio(conn, folio_id)
    if folio.get("guest_id") != user["guest_id"]:
        cur = await conn.execute(
            "SELECT guest_id FROM bookings WHERE booking_id = %s",
            (folio["booking_id"],),
        )
        owner = await cur.fetchone()
        if not owner or owner["guest_id"] != user["guest_id"]:
            raise HTTPException(status_code=403, detail="Нет доступа к этому счёту")

    cur = await conn.execute(
        "SELECT * FROM folio_lines WHERE folio_id = %s ORDER BY line_id",
        (folio_id,),
    )
    charges = await cur.fetchall()
    cur = await conn.execute(
        "SELECT * FROM payments WHERE folio_id = %s ORDER BY payment_id",
        (folio_id,),
    )
    payments = await cur.fetchall()
    cur = await conn.execute(
        """
        SELECT rf.* FROM refunds rf
        JOIN payments p ON p.payment_id = rf.payment_id
        WHERE p.folio_id = %s ORDER BY rf.refund_id
        """,
        (folio_id,),
    )
    refunds = await cur.fetchall()
    return {"folio": folio, "charges": charges, "payments": payments, "refunds": refunds}


@router.get("/folios/{folio_id}/pdf")
async def folio_pdf_endpoint(
    folio_id: int,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    folio = await get_folio(conn, folio_id)
    cur = await conn.execute(
        "SELECT guest_id FROM bookings WHERE booking_id = %s", (folio["booking_id"],)
    )
    owner = await cur.fetchone()
    if not owner or owner["guest_id"] != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этому счёту")

    cur = await conn.execute(
        "SELECT * FROM folio_lines WHERE folio_id = %s ORDER BY line_id", (folio_id,)
    )
    charges = await cur.fetchall()
    cur = await conn.execute(
        "SELECT * FROM payments WHERE folio_id = %s ORDER BY payment_id", (folio_id,)
    )
    payments = await cur.fetchall()
    pdf = folio_pdf(folio, charges, payments)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="folio-{folio_id}.pdf"'},
    )


@router.post("/bookings/{booking_id}/services")
async def order_service(
    booking_id: int,
    payload: ServiceOrderCreate,
    request: Request,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")
    if booking["status"] != "CHECKED_IN":
        raise HTTPException(status_code=400, detail="Услуги доступны только во время проживания")
    cur = await conn.execute(
        "SELECT fn_add_service_order(%s::integer, %s::integer, %s::integer, %s::integer, %s::varchar) AS order_id",
        (
            booking_id,
            payload.service_id,
            payload.quantity,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    order_id = (await cur.fetchone())["order_id"]
    return {"order_id": order_id}

```

## `backend/app/api/manager.py`

```python
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from psycopg import AsyncConnection

from ..audit import write_audit_event
from ..crypto import document_fields, hash_value, normalize_document, normalize_phone, phone_fields
from ..db import get_db
from ..deps import require_permission
from ..schemas import (
    CheckInRequest,
    CheckOutRequest,
    GuestCreate,
    ManagerBookingCreate,
    HoldUpdateRequest,
    MoveBookingRequest,
    NightAuditRequest,
    PaymentCreate,
    RefundCreate,
    RoomStatusUpdate,
)
from ..services.pdf import folio_pdf
from ..utils import csv_response, get_booking, get_folio, row_to_dict, rows_to_dicts

router = APIRouter(prefix="/manager", tags=["manager"])


def booking_filters(
    status: str | None,
    date_from: date | None,
    date_to: date | None,
    search: str | None,
) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []
    if status:
        clauses.append("b.status = %s")
        params.append(status)
    if date_from:
        clauses.append("b.checkin_date >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("b.checkout_date <= %s")
        params.append(date_to)
    if search:
        like = f"%{search}%"
        clauses.append(
            "(g.full_name ILIKE %s OR g.document_number ILIKE %s OR r.room_number ILIKE %s OR CAST(b.booking_id AS TEXT) ILIKE %s)"
        )
        params.extend([like, like, like, like])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


@router.get("/dashboard")
async def dashboard(
    user: dict = Depends(require_permission("dashboard:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM v_dashboard_today")
    kpi = await cur.fetchone()

    cur = await conn.execute(
        """
        SELECT report_date, rooms_occupied, rooms_available, occupancy_pct
        FROM v_occupancy_daily
        WHERE report_date >= CURRENT_DATE - 14
        ORDER BY report_date
        """
    )
    occupancy = await cur.fetchall()

    cur = await conn.execute(
        """
        SELECT b.booking_id, g.full_name AS guest_name, r.room_number,
               b.checkin_date, b.checkout_date, b.status
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        WHERE b.checkin_date = CURRENT_DATE
          AND b.status IN ('NEW','CONFIRMED')
        ORDER BY r.room_number
        """
    )
    arrivals = await cur.fetchall()

    cur = await conn.execute(
        """
        SELECT b.booking_id, g.full_name AS guest_name, r.room_number,
               b.checkin_date, b.checkout_date, b.status
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        WHERE b.checkout_date = CURRENT_DATE
          AND b.status = 'CHECKED_IN'
        ORDER BY r.room_number
        """
    )
    departures = await cur.fetchall()

    cur = await conn.execute("SELECT * FROM v_room_status_today ORDER BY status")
    room_status = await cur.fetchall()

    cur = await conn.execute("SELECT * FROM v_payments_by_method")
    payments_by_method = await cur.fetchall()

    return {
        "kpi": kpi,
        "occupancy": occupancy,
        "arrivals": arrivals,
        "departures": departures,
        "room_status": room_status,
        "payments_by_method": payments_by_method,
    }


@router.get("/room-grid")
async def room_grid(
    start: date | None = None,
    end: date | None = None,
    user: dict = Depends(require_permission("rooms:view")),
    conn: AsyncConnection = Depends(get_db),
):
    start = start or date.today()
    end = end or (start + timedelta(days=7))
    cur = await conn.execute(
        """
        SELECT r.room_id, r.room_number, r.floor,
               rt.room_type_id, rt.name AS room_type, rt.capacity,
               rs.name AS status, br.name AS block_reason
        FROM rooms r
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        LEFT JOIN block_reasons br ON br.reason_id = r.block_reason_id
        ORDER BY r.room_number
        """
    )
    rooms = await cur.fetchall()

    cur = await conn.execute(
        """
        SELECT b.booking_id, b.room_id, b.checkin_date, b.checkout_date, b.status,
               g.full_name AS guest_name, b.adults, b.children
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        WHERE b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
          AND daterange(b.checkin_date, b.checkout_date, '[)')
              && daterange(%s, %s, '[)')
        ORDER BY b.checkin_date
        """,
        (start, end),
    )
    bookings = await cur.fetchall()
    return {"start": start, "end": end, "rooms": rooms, "bookings": bookings}


@router.get("/bookings")
async def bookings(
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: dict = Depends(require_permission("bookings:view")),
    conn: AsyncConnection = Depends(get_db),
):
    where, params = booking_filters(status, date_from, date_to, search)
    count_cur = await conn.execute(
        f"""
        SELECT COUNT(*) AS total
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        {where}
        """,
        tuple(params),
    )
    total = (await count_cur.fetchone())["total"]

    offset = (page - 1) * page_size
    cur = await conn.execute(
        f"""
        SELECT b.booking_id, b.checkin_date, b.checkout_date, b.status, b.source,
               b.created_at, g.full_name AS guest_name, g.document_number,
               r.room_number, rt.name AS room_type,
               rp.price_per_night,
               fn_booking_balance(b.booking_id) AS balance
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN rate_plans rp ON rp.rate_id = b.rate_id
        {where}
        ORDER BY b.checkin_date DESC, b.booking_id DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params + [page_size, offset]),
    )
    items = await cur.fetchall()
    return {"items": rows_to_dicts(items), "total": total, "page": page, "page_size": page_size}


@router.get("/bookings/export")
async def bookings_export(
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    user: dict = Depends(require_permission("bookings:view")),
    conn: AsyncConnection = Depends(get_db),
):
    where, params = booking_filters(status, date_from, date_to, search)
    cur = await conn.execute(
        f"""
        SELECT b.booking_id, g.full_name, g.document_number, g.phone,
               r.room_number, rt.name AS room_type,
               b.checkin_date, b.checkout_date, b.status, b.source,
               fn_booking_balance(b.booking_id) AS balance
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        {where}
        ORDER BY b.checkin_date DESC
        """,
        tuple(params),
    )
    return csv_response(rows_to_dicts(await cur.fetchall()), "bookings.csv")


@router.get("/bookings/{booking_id}")
async def booking_detail(
    booking_id: int,
    user: dict = Depends(require_permission("bookings:view")),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    cur = await conn.execute(
        "SELECT * FROM check_ins WHERE booking_id = %s ORDER BY checkin_id DESC LIMIT 1",
        (booking_id,),
    )
    checkin = await cur.fetchone()
    cur = await conn.execute(
        "SELECT * FROM check_outs WHERE booking_id = %s ORDER BY checkout_id DESC LIMIT 1",
        (booking_id,),
    )
    checkout = await cur.fetchone()
    cur = await conn.execute(
        """
        SELECT so.order_id, so.quantity, so.ordered_at, s.name, s.price,
               so.quantity * s.price AS total
        FROM service_orders so
        JOIN services s ON s.service_id = so.service_id
        WHERE so.booking_id = %s ORDER BY so.order_id
        """,
        (booking_id,),
    )
    services = await cur.fetchall()
    cur = await conn.execute(
        """
        SELECT folio_id, status, opened_at, closed_at,
               fn_folio_charged(folio_id) AS charged_total,
               fn_folio_paid(folio_id) AS paid_total,
               fn_folio_balance(folio_id) AS balance
        FROM folios WHERE booking_id = %s ORDER BY folio_id DESC LIMIT 1
        """,
        (booking_id,),
    )
    folio = await cur.fetchone()

    return {
        "booking": booking,
        "checkin": checkin,
        "checkout": checkout,
        "services": services,
        "folio": folio,
    }


@router.post("/bookings")
async def create_booking(
    payload: ManagerBookingCreate,
    request: Request,
    user: dict = Depends(require_permission("bookings:create")),
    conn: AsyncConnection = Depends(get_db),
):
    try:
        cur = await conn.execute(
            """
            SELECT fn_create_booking(
                %s::integer, %s::integer, %s::integer, %s::date, %s::date,
                %s::integer, %s::varchar, %s::integer, %s::integer, %s::integer, %s::varchar,
                %s::time, %s::integer
            ) AS booking_id
            """,
            (
                payload.guest_id,
                payload.room_id,
                payload.rate_id,
                payload.checkin_date,
                payload.checkout_date,
                payload.promo_id,
                payload.source,
                payload.adults,
                payload.children,
                user["user_id"],
                request.client.host if request.client else "",
                payload.arrival_time,
                payload.hold_minutes,
            ),
        )
        booking_id = (await cur.fetchone())["booking_id"]
    except Exception as exc:
        await write_audit_event(
            user_id=user["user_id"],
            table_name="bookings",
            action="ERROR",
            new_value={
                "guest_id": payload.guest_id,
                "room_id": payload.room_id,
                "rate_id": payload.rate_id,
                "checkin_date": str(payload.checkin_date),
                "checkout_date": str(payload.checkout_date),
            },
            error_message=str(exc)[:500],
            is_error=True,
            event_type="VALIDATION_ERROR",
            severity="ERROR",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=request.headers.get("x-request-id"),
        )
        raise HTTPException(status_code=400, detail=str(exc))
    return await get_booking(conn, booking_id)


@router.post("/bookings/{booking_id}/confirm")
async def confirm_booking(
    booking_id: int,
    request: Request,
    user: dict = Depends(require_permission("bookings:confirm")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_confirm_booking(%s::integer, %s::integer, %s::varchar)",
        (booking_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "CONFIRMED"}


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    request: Request,
    reason_id: int | None = Query(default=None),
    user: dict = Depends(require_permission("bookings:cancel")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_cancel_booking(%s::integer, %s::integer, %s::integer, %s::varchar)",
        (booking_id, reason_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "CANCELLED"}


@router.post("/bookings/{booking_id}/check-in")
async def check_in(
    booking_id: int,
    payload: CheckInRequest,
    request: Request,
    user: dict = Depends(require_permission("bookings:checkin")),
    conn: AsyncConnection = Depends(get_db),
):
    document = document_fields(payload.document_number)
    await conn.execute(
        """
        CALL sp_check_in_secure(
            %s::integer, %s::integer, %s::varchar, %s::text, %s::varchar,
            %s::numeric, %s::varchar, %s::varchar
        )
        """,
        (
            booking_id,
            user["user_id"],
            document["document_number"],
            document["document_number_enc"],
            document["document_number_hash"],
            payload.deposit_amount,
            payload.payment_method,
            request.client.host if request.client else "",
        ),
    )
    return {"ok": True, "status": "CHECKED_IN"}


@router.post("/bookings/{booking_id}/check-out")
async def check_out(
    booking_id: int,
    payload: CheckOutRequest,
    request: Request,
    user: dict = Depends(require_permission("bookings:checkout")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_check_out(%s::integer, %s::integer, %s::numeric, %s::varchar, %s::varchar)",
        (
            booking_id,
            user["user_id"],
            payload.payment_amount,
            payload.payment_method,
            request.client.host if request.client else "",
        ),
    )
    return {"ok": True, "status": "CHECKED_OUT"}


@router.post("/bookings/{booking_id}/move")
async def move_booking(
    booking_id: int,
    payload: MoveBookingRequest,
    user: dict = Depends(require_permission("bookings:update")),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    if booking["status"] in ("CANCELLED", "CHECKED_OUT", "NO_SHOW"):
        raise HTTPException(status_code=400, detail="Эту бронь нельзя перенести")
    availability_cur = await conn.execute(
        "SELECT fn_room_available(%s::integer, %s::date, %s::date, %s::integer) AS ok",
        (payload.room_id, payload.checkin_date, payload.checkout_date, booking_id),
    )
    availability_row = await availability_cur.fetchone()
    if not availability_row["ok"]:
        raise HTTPException(status_code=409, detail="Номер недоступен на выбранные даты")
    await conn.execute(
        """
        UPDATE bookings
        SET room_id = %s, checkin_date = %s, checkout_date = %s
        WHERE booking_id = %s
        """,
        (payload.room_id, payload.checkin_date, payload.checkout_date, booking_id),
    )
    return await get_booking(conn, booking_id)


@router.patch("/bookings/{booking_id}/hold")
async def update_hold(
    booking_id: int,
    payload: HoldUpdateRequest,
    user: dict = Depends(require_permission("bookings:update")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "SELECT checkin_date, arrival_time, status FROM bookings WHERE booking_id = %s",
        (booking_id,),
    )
    booking = await cur.fetchone()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    if booking["status"] in ("CANCELLED", "CHECKED_OUT", "NO_SHOW"):
        raise HTTPException(status_code=400, detail="Для этой брони удержание недоступно")

    arrival = payload.arrival_time or booking["arrival_time"] or time(14, 0)
    hold_minutes = payload.hold_minutes
    hold_until = datetime.combine(booking["checkin_date"], arrival) + timedelta(minutes=hold_minutes)

    await conn.execute(
        """
        UPDATE bookings
        SET arrival_time = %s, hold_minutes = %s, hold_until = %s
        WHERE booking_id = %s
        """,
        (arrival, hold_minutes, hold_until, booking_id),
    )
    return await get_booking(conn, booking_id)


@router.get("/guests")
async def guests(
    search: str | None = None,
    user: dict = Depends(require_permission("bookings:view")),
    conn: AsyncConnection = Depends(get_db),
):
    if search:
        like = f"%{search}%"
        document_hash = hash_value(normalize_document(search))
        phone_hash = hash_value(normalize_phone(search))
        cur = await conn.execute(
            """
            SELECT * FROM guests
            WHERE full_name ILIKE %s
               OR email ILIKE %s
               OR document_number_hash = %s
               OR phone_hash = %s
            ORDER BY full_name
            LIMIT 50
            """,
            (like, like, document_hash, phone_hash),
        )
    else:
        cur = await conn.execute("SELECT * FROM guests ORDER BY full_name LIMIT 50")
    return rows_to_dicts(await cur.fetchall())


@router.post("/guests")
async def create_guest(
    payload: GuestCreate,
    user: dict = Depends(require_permission("bookings:create")),
    conn: AsyncConnection = Depends(get_db),
):
    document = document_fields(payload.document_number)
    phone = phone_fields(payload.phone)
    cur = await conn.execute(
        """
        INSERT INTO guests (
            full_name, document_number, document_number_enc, document_number_hash,
            phone, phone_enc, phone_hash, email, pdn_consent
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            payload.full_name,
            document["document_number"],
            document["document_number_enc"],
            document["document_number_hash"],
            phone["phone"],
            phone["phone_enc"],
            phone["phone_hash"],
            payload.email,
            payload.pdn_consent,
        ),
    )
    return row_to_dict(await cur.fetchone())


@router.get("/rates")
async def rates(
    user: dict = Depends(require_permission("rates:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT rp.*, rt.name AS room_type
        FROM rate_plans rp
        JOIN room_types rt ON rt.room_type_id = rp.room_type_id
        ORDER BY rt.name, rp.season_start
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/rooms")
async def rooms(
    user: dict = Depends(require_permission("rooms:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT r.*, rt.name AS room_type, rs.name AS status
        FROM rooms r
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        ORDER BY r.room_number
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/room-statuses")
async def room_statuses(
    user: dict = Depends(require_permission("rooms:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM room_statuses ORDER BY status_id")
    return rows_to_dicts(await cur.fetchall())


@router.get("/cancellation-reasons")
async def cancellation_reasons(
    user: dict = Depends(require_permission("bookings:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM cancellation_reasons ORDER BY reason_id")
    return rows_to_dicts(await cur.fetchall())


@router.get("/folios")
async def folios(
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: dict = Depends(require_permission("folios:view")),
    conn: AsyncConnection = Depends(get_db),
):
    clauses: list[str] = []
    params: list = []
    if status:
        clauses.append("f.status = %s")
        params.append(status)
    if search:
        like = f"%{search}%"
        clauses.append("(g.full_name ILIKE %s OR r.room_number ILIKE %s OR CAST(f.folio_id AS TEXT) ILIKE %s)")
        params.extend([like, like, like])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur = await conn.execute(
        f"""
        SELECT COUNT(*) AS total
        FROM folios f
        JOIN bookings b ON b.booking_id = f.booking_id
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        {where}
        """,
        tuple(params),
    )
    total = (await cur.fetchone())["total"]
    offset = (page - 1) * page_size
    cur = await conn.execute(
        f"""
        SELECT f.folio_id, f.booking_id, f.status, f.opened_at, f.closed_at,
               g.full_name AS guest_name, r.room_number,
               fn_folio_charged(f.folio_id) AS charged_total,
               fn_folio_paid(f.folio_id) AS paid_total,
               fn_folio_balance(f.folio_id) AS balance
        FROM folios f
        JOIN bookings b ON b.booking_id = f.booking_id
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        {where}
        ORDER BY f.folio_id DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params + [page_size, offset]),
    )
    return {"items": rows_to_dicts(await cur.fetchall()), "total": total, "page": page, "page_size": page_size}


@router.get("/folios/{folio_id}")
async def folio_detail(
    folio_id: int,
    user: dict = Depends(require_permission("folios:view")),
    conn: AsyncConnection = Depends(get_db),
):
    folio = await get_folio(conn, folio_id)
    cur = await conn.execute(
        "SELECT * FROM folio_lines WHERE folio_id = %s ORDER BY line_id", (folio_id,)
    )
    charges = await cur.fetchall()
    cur = await conn.execute(
        "SELECT * FROM payments WHERE folio_id = %s ORDER BY payment_id", (folio_id,)
    )
    payments = await cur.fetchall()
    cur = await conn.execute(
        """
        SELECT rf.* FROM refunds rf
        JOIN payments p ON p.payment_id = rf.payment_id
        WHERE p.folio_id = %s ORDER BY rf.refund_id
        """,
        (folio_id,),
    )
    refunds = await cur.fetchall()
    return {"folio": folio, "charges": charges, "payments": payments, "refunds": refunds}


@router.get("/folios/{folio_id}/pdf")
async def folio_pdf_endpoint(
    folio_id: int,
    user: dict = Depends(require_permission("folios:view")),
    conn: AsyncConnection = Depends(get_db),
):
    folio = await get_folio(conn, folio_id)
    cur = await conn.execute(
        "SELECT * FROM folio_lines WHERE folio_id = %s ORDER BY line_id", (folio_id,)
    )
    charges = await cur.fetchall()
    cur = await conn.execute(
        "SELECT * FROM payments WHERE folio_id = %s ORDER BY payment_id", (folio_id,)
    )
    payments = await cur.fetchall()
    pdf = folio_pdf(folio, charges, payments)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="folio-{folio_id}.pdf"'},
    )


@router.post("/folios/{folio_id}/payments")
async def add_payment(
    folio_id: int,
    payload: PaymentCreate,
    request: Request,
    user: dict = Depends(require_permission("payments:create")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "SELECT fn_record_payment(%s::integer, %s::numeric, %s::varchar, %s::varchar, %s::integer, %s::varchar) AS payment_id",
        (
            folio_id,
            payload.amount,
            payload.method,
            payload.payment_type,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"payment_id": (await cur.fetchone())["payment_id"]}


@router.post("/payments/{payment_id}/refunds")
async def refund_payment(
    payment_id: int,
    payload: RefundCreate,
    request: Request,
    user: dict = Depends(require_permission("payments:refund")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "SELECT fn_refund_payment(%s::integer, %s::numeric, %s::varchar, %s::integer, %s::varchar) AS refund_id",
        (
            payment_id,
            payload.amount,
            payload.reason,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"refund_id": (await cur.fetchone())["refund_id"]}


@router.post("/folios/{folio_id}/close")
async def close_folio(
    folio_id: int,
    request: Request,
    user: dict = Depends(require_permission("folios:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        """
        UPDATE folios
        SET status = 'CLOSED', closed_at = now()
        WHERE folio_id = %s AND status = 'OPEN'
        """,
        (folio_id,),
    )
    return {"ok": True, "status": "CLOSED"}


@router.post("/night-audit")
async def night_audit(
    payload: NightAuditRequest,
    request: Request,
    user: dict = Depends(require_permission("bookings:night_audit")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_night_audit(%s::date, %s::integer, %s::varchar, NULL, NULL)",
        (
            payload.business_date,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    cur = await conn.execute(
        "SELECT * FROM business_days WHERE business_date = %s",
        (payload.business_date,),
    )
    return row_to_dict(await cur.fetchone())


@router.post("/rooms/{room_id}/status")
async def update_room_status(
    room_id: int,
    payload: RoomStatusUpdate,
    request: Request,
    user: dict = Depends(require_permission("rooms:update_status")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_set_room_status(%s::integer, %s::varchar, %s::integer, %s::integer, %s::varchar)",
        (
            room_id,
            payload.status_name,
            payload.reason_id,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"ok": True}

```

## `backend/app/api/housekeeping.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg import AsyncConnection

from ..db import get_db
from ..deps import require_permission
from ..schemas import (
    ConsumableWriteOff,
    HousekeepingTaskCreate,
    MaintenanceCreate,
    MaintenanceStatusUpdate,
    RoomStatusUpdate,
)
from ..utils import rows_to_dicts

router = APIRouter(prefix="/housekeeping", tags=["housekeeping"])


@router.get("/tasks")
async def tasks(
    status: str | None = None,
    floor: int | None = None,
    assignee_id: int | None = None,
    user: dict = Depends(require_permission("housekeeping:view")),
    conn: AsyncConnection = Depends(get_db),
):
    clauses: list[str] = []
    params: list = []
    if status:
        clauses.append("ht.status = %s")
        params.append(status)
    if floor is not None:
        clauses.append("r.floor = %s")
        params.append(floor)
    if assignee_id:
        clauses.append("ht.staff_id = %s")
        params.append(assignee_id)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur = await conn.execute(
        f"""
        SELECT ht.*, r.room_number, r.floor, rt.name AS room_type,
               rs.name AS room_status,
               u.full_name AS assignee_name
        FROM housekeeping_tasks ht
        JOIN rooms r ON r.room_id = ht.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        LEFT JOIN users u ON u.user_id = ht.staff_id
        {where}
        ORDER BY
            CASE ht.status WHEN 'IN_PROGRESS' THEN 0 WHEN 'ASSIGNED' THEN 1 WHEN 'DONE' THEN 2 ELSE 3 END,
            ht.priority DESC,
            ht.assigned_at DESC
        """,
        tuple(params),
    )
    return rows_to_dicts(await cur.fetchall())


@router.post("/tasks")
async def create_task(
    payload: HousekeepingTaskCreate,
    request: Request,
    user: dict = Depends(require_permission("housekeeping:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "SELECT fn_assign_housekeeping_task(%s::integer, %s::integer, %s::varchar, %s::varchar, %s::integer, %s::varchar) AS task_id",
        (
            payload.room_id,
            payload.staff_id,
            payload.task_type,
            payload.priority,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"task_id": (await cur.fetchone())["task_id"]}


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: int,
    request: Request,
    user: dict = Depends(require_permission("housekeeping:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_start_housekeeping_task(%s::integer, %s::integer, %s::varchar)",
        (task_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "IN_PROGRESS"}


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    request: Request,
    user: dict = Depends(require_permission("housekeeping:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_complete_housekeeping_task(%s::integer, %s::integer, %s::varchar)",
        (task_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "DONE"}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    request: Request,
    user: dict = Depends(require_permission("housekeeping:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_cancel_housekeeping_task(%s::integer, %s::integer, %s::varchar)",
        (task_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "CANCELLED"}


@router.post("/tasks/{task_id}/consumables")
async def write_off_consumable(
    task_id: int,
    payload: ConsumableWriteOff,
    request: Request,
    user: dict = Depends(require_permission("consumables:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "SELECT fn_write_off_consumable(%s::integer, %s::integer, %s::numeric, %s::integer, %s::varchar) AS usage_id",
        (
            task_id,
            payload.consumable_id,
            payload.quantity,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"usage_id": (await cur.fetchone())["usage_id"]}


@router.get("/consumables")
async def consumables(
    user: dict = Depends(require_permission("consumables:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM v_consumables_stock ORDER BY name")
    return rows_to_dicts(await cur.fetchall())


@router.get("/maintenance")
async def maintenance(
    status: str | None = None,
    user: dict = Depends(require_permission("maintenance:view")),
    conn: AsyncConnection = Depends(get_db),
):
    params: list = []
    status_filter = ""
    if status:
        status_filter = "WHERE mr.status = %s"
        params.append(status)
    cur = await conn.execute(
        f"""
        SELECT mr.*, r.room_number, r.floor,
               u.full_name AS assignee_name,
               ht.task_type
        FROM maintenance_requests mr
        JOIN rooms r ON r.room_id = mr.room_id
        LEFT JOIN users u ON u.user_id = mr.assigned_to
        LEFT JOIN housekeeping_tasks ht ON ht.task_id = mr.task_id
        {status_filter}
        ORDER BY
            CASE mr.priority WHEN 'URGENT' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'NORMAL' THEN 2 ELSE 3 END,
            mr.created_at DESC
        """,
        tuple(params),
    )
    return rows_to_dicts(await cur.fetchall())


@router.post("/maintenance")
async def create_maintenance(
    payload: MaintenanceCreate,
    request: Request,
    user: dict = Depends(require_permission("maintenance:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT fn_create_maintenance_request(
            %s::integer, %s::integer, %s::text, %s::varchar, %s::integer, %s::integer, %s::varchar
        ) AS request_id
        """,
        (
            payload.room_id,
            payload.task_id,
            payload.description,
            payload.priority,
            payload.assigned_to,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"request_id": (await cur.fetchone())["request_id"]}


@router.patch("/maintenance/{request_id}/status")
async def update_maintenance_status(
    request_id: int,
    payload: MaintenanceStatusUpdate,
    request: Request,
    user: dict = Depends(require_permission("maintenance:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_update_maintenance_status(%s::integer, %s::varchar, %s::integer, %s::varchar)",
        (request_id, payload.status, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": payload.status}


@router.get("/rooms")
async def rooms(
    user: dict = Depends(require_permission("rooms:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT r.room_id, r.room_number, r.floor, rt.name AS room_type,
               rs.name AS status, br.name AS block_reason
        FROM rooms r
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        LEFT JOIN block_reasons br ON br.reason_id = r.block_reason_id
        ORDER BY r.room_number
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.post("/rooms/{room_id}/status")
async def update_room_status(
    room_id: int,
    payload: RoomStatusUpdate,
    request: Request,
    user: dict = Depends(require_permission("rooms:update_status")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_set_room_status(%s::integer, %s::varchar, %s::integer, %s::integer, %s::varchar)",
        (
            room_id,
            payload.status_name,
            payload.reason_id,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"ok": True}


@router.get("/staff")
async def staff(
    user: dict = Depends(require_permission("housekeeping:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT u.user_id, u.full_name, u.email, r.name AS role_name
        FROM users u
        JOIN roles r ON r.role_id = u.role_id
        WHERE u.role_id = 3 AND u.is_active
        ORDER BY u.full_name
        """
    )
    return rows_to_dicts(await cur.fetchall())

```

## `backend/app/api/admin.py`

```python
from __future__ import annotations

import asyncio
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from psycopg import AsyncConnection, errors
from psycopg.types.json import Jsonb

from ..config import get_settings
from ..crypto import hash_value, normalize_phone, phone_fields
from ..db import get_db
from ..deps import get_current_user, require_permission
from ..schemas import BlockUserRequest, ResetPasswordRequest, RoleAssignRequest, RolePermissionsUpdate, UserCreate, UserUpdate
from ..security import hash_password
from ..services.backup import backup_path, run_backup_sync
from ..utils import csv_response, row_to_dict, rows_to_dicts

router = APIRouter(prefix="/admin", tags=["admin"])

DIRECTORIES: dict[str, dict[str, Any]] = {
    "room-types": {
        "table": "room_types",
        "pk": "room_type_id",
        "fields": ["name", "capacity", "description"],
        "permission": "rooms:manage",
    },
    "rooms": {
        "table": "rooms",
        "pk": "room_id",
        "fields": ["room_type_id", "status_id", "block_reason_id", "room_number", "floor"],
        "permission": "rooms:manage",
    },
    "amenities": {
        "table": "amenities",
        "pk": "amenity_id",
        "fields": ["name"],
        "permission": "rooms:manage",
    },
    "rate-plans": {
        "table": "rate_plans",
        "pk": "rate_id",
        "fields": [
            "room_type_id", "name", "season_start", "season_end",
            "price_per_night", "cancellation_terms",
        ],
        "permission": "rates:manage",
    },
    "services": {
        "table": "services",
        "pk": "service_id",
        "fields": ["unit_id", "name", "price"],
        "permission": "services:manage",
    },
    "promo-codes": {
        "table": "promo_codes",
        "pk": "promo_id",
        "fields": ["code", "discount_percent", "valid_from", "valid_to"],
        "permission": "promo:manage",
    },
    "cancellation-reasons": {
        "table": "cancellation_reasons",
        "pk": "reason_id",
        "fields": ["name"],
        "permission": "bookings:update",
    },
    "service-units": {
        "table": "service_units",
        "pk": "unit_id",
        "fields": ["name"],
        "permission": "services:manage",
    },
    "block-reasons": {
        "table": "block_reasons",
        "pk": "reason_id",
        "fields": ["name"],
        "permission": "rooms:manage",
    },
    "room-statuses": {
        "table": "room_statuses",
        "pk": "status_id",
        "fields": ["name"],
        "permission": "rooms:manage",
    },
    "consumables": {
        "table": "consumables",
        "pk": "consumable_id",
        "fields": ["name", "unit", "stock_quantity", "min_stock"],
        "permission": "consumables:manage",
    },
}


def directory_config(entity: str) -> dict[str, Any]:
    config = DIRECTORIES.get(entity)
    if not config:
        raise HTTPException(status_code=404, detail="Справочник не найден")
    return config


def check_directory_permission(user: dict, entity: str) -> None:
    permission = directory_config(entity)["permission"]
    if permission not in user["permissions"]:
        raise HTTPException(status_code=403, detail=f"Недостаточно прав: {permission}")


@router.get("/users")
async def users(
    search: str | None = None,
    role_id: int | None = None,
    status_filter: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: dict = Depends(require_permission("users:view")),
    conn: AsyncConnection = Depends(get_db),
):
    clauses: list[str] = []
    params: list = []
    if search:
        like = f"%{search}%"
        clauses.append("(u.full_name ILIKE %s OR u.email ILIKE %s OR u.phone_hash = %s)")
        params.extend([like, like, hash_value(normalize_phone(search))])
    if role_id:
        clauses.append("u.role_id = %s")
        params.append(role_id)
    if status_filter == "online":
        clauses.append("u.is_active AND u.last_seen_at >= now() - interval '5 minutes'")
    elif status_filter == "active":
        clauses.append("u.is_active")
    elif status_filter == "blocked":
        clauses.append("NOT u.is_active")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    count_cur = await conn.execute(f"SELECT COUNT(*) AS total FROM users u {where}", tuple(params))
    total = (await count_cur.fetchone())["total"]
    offset = (page - 1) * page_size
    cur = await conn.execute(
        f"""
        SELECT u.user_id, u.role_id, r.name AS role_name, u.full_name, u.email, u.phone,
               u.is_active, u.last_login_at, u.last_seen_at, u.created_at,
               COALESCE(u.is_active AND u.last_seen_at >= now() - interval '5 minutes', FALSE) AS is_online,
               u.block_reason, u.blocked_at,
               bu.full_name AS blocked_by_name,
               (SELECT count(*) FROM user_sessions s
                WHERE s.user_id = u.user_id
                  AND s.revoked_at IS NULL
                  AND s.expires_at > now()) AS active_sessions
        FROM users u
        JOIN roles r ON r.role_id = u.role_id
        LEFT JOIN users bu ON bu.user_id = u.blocked_by
        {where}
        ORDER BY u.user_id
        LIMIT %s OFFSET %s
        """,
        tuple(params + [page_size, offset]),
    )
    return {"items": rows_to_dicts(await cur.fetchall()), "total": total, "page": page, "page_size": page_size}


@router.post("/users")
async def create_user(
    payload: UserCreate,
    user: dict = Depends(require_permission("users:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT 1 FROM users WHERE lower(email) = lower(%s)", (payload.email,))
    if await cur.fetchone():
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    phone = phone_fields(payload.phone)
    cur = await conn.execute(
        """
        INSERT INTO users (
            role_id, full_name, email, phone, phone_enc, phone_hash, password_hash, is_active
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING user_id, role_id, full_name, email, phone, is_active
        """,
        (
            payload.role_id,
            payload.full_name,
            payload.email,
            phone["phone"],
            phone["phone_enc"],
            phone["phone_hash"],
            hash_password(payload.password),
            payload.is_active,
        ),
    )
    created = await cur.fetchone()
    await conn.execute(
        "INSERT INTO user_settings (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
        (created["user_id"],),
    )
    return row_to_dict(created)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    user: dict = Depends(require_permission("users:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    fields = payload.model_dump(exclude_unset=True)
    phone = fields.pop("phone", None)
    if phone is not None and "*" not in phone:
        fields.update(phone_fields(phone))
    if not fields:
        raise HTTPException(status_code=400, detail="Нет данных для изменения")
    sets: list[str] = []
    params: list = []
    for key, value in fields.items():
        sets.append(f"{key} = %s")
        params.append(value)
    params.append(user_id)
    cur = await conn.execute(
        f"UPDATE users SET {', '.join(sets)} WHERE user_id = %s RETURNING user_id, role_id, full_name, email, phone, is_active",
        tuple(params),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return row_to_dict(row)


@router.get("/users/stats")
async def user_stats(
    user: dict = Depends(require_permission("users:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE is_active) AS active,
            COUNT(*) FILTER (WHERE NOT is_active) AS blocked,
            COUNT(*) FILTER (
                WHERE is_active AND last_seen_at >= now() - interval '5 minutes'
            ) AS online
        FROM users
        """
    )
    summary = await cur.fetchone()
    cur = await conn.execute(
        """
        SELECT r.name AS role_name, COUNT(u.user_id) AS total,
               COUNT(*) FILTER (
                   WHERE u.is_active AND u.last_seen_at >= now() - interval '5 minutes'
               ) AS online
        FROM roles r
        LEFT JOIN users u ON u.role_id = r.role_id
        GROUP BY r.role_id, r.name
        ORDER BY r.role_id
        """
    )
    return {"summary": summary, "by_role": [dict(row) for row in await cur.fetchall()]}


@router.get("/users/block-reasons")
async def user_block_reasons(
    user: dict = Depends(require_permission("users:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM user_block_reasons ORDER BY reason_id")
    return rows_to_dicts(await cur.fetchall())


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    payload: BlockUserRequest,
    user: dict = Depends(require_permission("users:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    reason = (payload.custom_reason or "").strip()
    if payload.reason_id:
        cur = await conn.execute(
            "SELECT name FROM user_block_reasons WHERE reason_id = %s",
            (payload.reason_id,),
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Причина блокировки не найдена")
        reason = row["name"]
    if not reason:
        raise HTTPException(status_code=400, detail="Укажите причину блокировки")

    await conn.execute(
        """
        UPDATE users
        SET is_active = FALSE,
            block_reason = %s,
            blocked_at = now(),
            blocked_by = %s
        WHERE user_id = %s
        """,
        (reason, user["user_id"], user_id),
    )
    await conn.execute(
        "UPDATE user_sessions SET revoked_at = now() WHERE user_id = %s AND revoked_at IS NULL",
        (user_id,),
    )
    return {"ok": True, "reason": reason}


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    user: dict = Depends(require_permission("users:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        """
        UPDATE users
        SET is_active = TRUE,
            locked_until = NULL,
            failed_login_attempts = 0,
            block_reason = NULL,
            blocked_at = NULL,
            blocked_by = NULL
        WHERE user_id = %s
        """,
        (user_id,),
    )
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    user: dict = Depends(require_permission("users:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "UPDATE users SET password_hash = %s, password_changed_at = now() WHERE user_id = %s",
        (hash_password(payload.new_password), user_id),
    )
    return {"ok": True}


@router.patch("/users/{user_id}/role")
async def assign_role(
    user_id: int,
    payload: RoleAssignRequest,
    user: dict = Depends(require_permission("users:assign_roles")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute("UPDATE users SET role_id = %s WHERE user_id = %s", (payload.role_id, user_id))
    return {"ok": True}


@router.get("/roles")
async def roles(
    user: dict = Depends(require_permission("users:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT r.role_id, r.name,
               COALESCE(json_agg(p.code) FILTER (WHERE p.code IS NOT NULL), '[]'::json) AS permissions
        FROM roles r
        LEFT JOIN role_permissions rp ON rp.role_id = r.role_id
        LEFT JOIN permissions p ON p.permission_id = rp.permission_id
        GROUP BY r.role_id, r.name
        ORDER BY r.role_id
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/permissions")
async def permissions(
    user: dict = Depends(require_permission("users:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM permissions ORDER BY module, code")
    return rows_to_dicts(await cur.fetchall())


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: int,
    payload: RolePermissionsUpdate,
    user: dict = Depends(require_permission("roles:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))
    if payload.permission_codes:
        await conn.execute(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT %s, permission_id FROM permissions WHERE code = ANY(%s)
            ON CONFLICT DO NOTHING
            """,
            (role_id, payload.permission_codes),
        )
    return {"ok": True, "permissions": payload.permission_codes}


@router.get("/directories/{entity}")
async def list_directory(
    entity: str,
    search: str | None = None,
    user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_db),
):
    config = directory_config(entity)
    check_directory_permission(user, entity)
    params: tuple = ()
    where = ""
    if search:
        where = " WHERE to_jsonb(t)::text ILIKE %s"
        params = (f"%{search}%",)
    cur = await conn.execute(
        f"SELECT * FROM {config['table']} t {where} ORDER BY {config['pk']}",
        params,
    )
    return rows_to_dicts(await cur.fetchall())


@router.post("/directories/{entity}")
async def create_directory_item(
    entity: str,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_db),
):
    config = directory_config(entity)
    check_directory_permission(user, entity)
    fields = [field for field in config["fields"] if field in payload]
    if not fields:
        raise HTTPException(status_code=400, detail="Нет допустимых полей")
    placeholders = ", ".join(["%s"] * len(fields))
    cur = await conn.execute(
        f"INSERT INTO {config['table']} ({', '.join(fields)}) VALUES ({placeholders}) RETURNING *",
        tuple(payload[field] for field in fields),
    )
    return row_to_dict(await cur.fetchone())


@router.patch("/directories/{entity}/{item_id}")
async def update_directory_item(
    entity: str,
    item_id: int,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_db),
):
    config = directory_config(entity)
    check_directory_permission(user, entity)
    fields = [field for field in config["fields"] if field in payload]
    if not fields:
        raise HTTPException(status_code=400, detail="Нет допустимых полей")
    sets = ", ".join(f"{field} = %s" for field in fields)
    cur = await conn.execute(
        f"UPDATE {config['table']} SET {sets} WHERE {config['pk']} = %s RETURNING *",
        tuple(payload[field] for field in fields) + (item_id,),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return row_to_dict(row)


@router.delete("/directories/{entity}/{item_id}")
async def delete_directory_item(
    entity: str,
    item_id: int,
    user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_db),
):
    config = directory_config(entity)
    check_directory_permission(user, entity)
    try:
        cur = await conn.execute(
            f"DELETE FROM {config['table']} WHERE {config['pk']} = %s RETURNING {config['pk']}",
            (item_id,),
        )
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Запись не найдена")
    except errors.ForeignKeyViolation:
        raise HTTPException(status_code=409, detail="Запись используется и не может быть удалена")
    return {"ok": True}


@router.get("/audit")
async def audit(
    user_id: int | None = None,
    role_id: int | None = None,
    user_search: str | None = None,
    table_name: str | None = None,
    action: str | None = None,
    event_type: str | None = None,
    is_error: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: dict = Depends(require_permission("audit:view")),
    conn: AsyncConnection = Depends(get_db),
):
    clauses: list[str] = []
    params: list = []
    if user_id:
        clauses.append("a.user_id = %s")
        params.append(user_id)
    if role_id:
        clauses.append("r.role_id = %s")
        params.append(role_id)
    if user_search:
        like = f"%{user_search}%"
        clauses.append("(u.full_name ILIKE %s OR u.email ILIKE %s)")
        params.extend([like, like])
    if table_name:
        clauses.append("a.table_name = %s")
        params.append(table_name)
    if action:
        clauses.append("a.action = %s")
        params.append(action)
    if event_type:
        clauses.append("a.event_type = %s")
        params.append(event_type)
    if is_error is not None:
        clauses.append("a.is_error = %s")
        params.append(is_error)
    if date_from:
        clauses.append("a.changed_at >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("a.changed_at::date <= %s")
        params.append(date_to)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    joins = """
        LEFT JOIN users u ON u.user_id = a.user_id
        LEFT JOIN roles r ON r.role_id = u.role_id
    """
    count_cur = await conn.execute(
        f"SELECT COUNT(*) AS total FROM audit_log a {joins} {where}",
        tuple(params),
    )
    total = (await count_cur.fetchone())["total"]
    offset = (page - 1) * page_size
    cur = await conn.execute(
        f"""
        SELECT a.*, u.full_name AS user_name, r.name AS role_name
        FROM audit_log a
        {joins}
        {where}
        ORDER BY a.changed_at DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params + [page_size, offset]),
    )
    return {"items": rows_to_dicts(await cur.fetchall()), "total": total, "page": page, "page_size": page_size}


@router.get("/audit/export")
async def audit_export(
    user_id: int | None = None,
    role_id: int | None = None,
    user_search: str | None = None,
    table_name: str | None = None,
    action: str | None = None,
    event_type: str | None = None,
    is_error: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user: dict = Depends(require_permission("audit:export")),
    conn: AsyncConnection = Depends(get_db),
):
    clauses: list[str] = []
    params: list = []
    if user_id:
        clauses.append("a.user_id = %s")
        params.append(user_id)
    if role_id:
        clauses.append("r.role_id = %s")
        params.append(role_id)
    if user_search:
        like = f"%{user_search}%"
        clauses.append("(u.full_name ILIKE %s OR u.email ILIKE %s)")
        params.extend([like, like])
    if table_name:
        clauses.append("a.table_name = %s")
        params.append(table_name)
    if action:
        clauses.append("a.action = %s")
        params.append(action)
    if event_type:
        clauses.append("a.event_type = %s")
        params.append(event_type)
    if is_error is not None:
        clauses.append("a.is_error = %s")
        params.append(is_error)
    if date_from:
        clauses.append("a.changed_at >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("a.changed_at::date <= %s")
        params.append(date_to)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur = await conn.execute(
        f"""
        SELECT a.changed_at, u.full_name AS user_name, r.name AS role_name,
               a.table_name, a.record_id, a.action, a.event_type,
               a.is_error, a.error_message, a.old_value, a.new_value,
               a.ip_address, a.user_agent, a.request_id
        FROM audit_log a
        LEFT JOIN users u ON u.user_id = a.user_id
        LEFT JOIN roles r ON r.role_id = u.role_id
        {where}
        ORDER BY a.changed_at DESC
        """,
        tuple(params),
    )
    return csv_response(rows_to_dicts(await cur.fetchall()), "audit.csv")


@router.get("/backups")
async def list_backups(
    user: dict = Depends(require_permission("backup:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    path = backup_path()
    cur = await conn.execute(
        "SELECT key, value FROM system_settings WHERE key LIKE 'backup.%' ORDER BY key"
    )
    settings = {row["key"]: row["value"] for row in await cur.fetchall()}
    file_info = None
    if path.exists():
        stat = path.stat()
        file_info = {
            "filename": path.name,
            "size": stat.st_size,
            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    return {"file": file_info, "settings": settings}


@router.post("/backups")
async def create_backup(
    user: dict = Depends(require_permission("backup:manage")),
):
    result = await asyncio.to_thread(run_backup_sync)
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("error") or "Ошибка резервного копирования")
    return result


@router.get("/backups/download")
async def download_backup(
    user: dict = Depends(require_permission("backup:manage")),
):
    path = backup_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Резервная копия ещё не создана")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@router.post("/backups/restore")
async def restore_backup(
    user: dict = Depends(require_permission("backup:manage")),
):
    settings = get_settings()
    path = backup_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Резервная копия не найдена")
    result = await asyncio.to_thread(
        subprocess.run,
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--dbname",
            settings.database_admin_url,
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Ошибка pg_restore: {result.stderr[:500]}")
    return {"ok": True, "filename": path.name}


@router.get("/monitoring")
async def monitoring(
    user: dict = Depends(require_permission("monitoring:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT
            pg_database_size(current_database()) AS db_size,
            (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) AS active_connections,
            now() AS server_time,
            version() AS version
        """
    )
    summary = await cur.fetchone()
    cur = await conn.execute(
        """
        SELECT relname, n_live_tup, pg_total_relation_size(relid) AS size
        FROM pg_stat_user_tables
        ORDER BY size DESC
        LIMIT 10
        """
    )
    tables = await cur.fetchall()
    slow_queries: list[dict] = []
    try:
        async with conn.transaction():
            cur = await conn.execute(
                """
                SELECT query, calls, total_exec_time
                FROM pg_stat_statements
                ORDER BY total_exec_time DESC
                LIMIT 5
                """
            )
            slow_queries = list(await cur.fetchall())
    except Exception:
        slow_queries = []
    return {"summary": summary, "tables": tables, "slow_queries": slow_queries}


@router.get("/settings")
async def system_settings(
    user: dict = Depends(require_permission("settings:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM system_settings ORDER BY key")
    return rows_to_dicts(await cur.fetchall())


@router.put("/settings")
async def update_system_settings(
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(require_permission("settings:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    for key, value in payload.items():
        await conn.execute(
            """
            INSERT INTO system_settings (key, value, updated_at, updated_by)
            VALUES (%s, %s, now(), %s)
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = now(),
                updated_by = EXCLUDED.updated_by
            """,
            (key, Jsonb(value), user["user_id"]),
        )
    cur = await conn.execute("SELECT * FROM system_settings ORDER BY key")
    return rows_to_dicts(await cur.fetchall())


@router.get("/import-batches")
async def import_batches(
    user: dict = Depends(require_permission("settings:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT ib.*, u.full_name AS created_by_name
        FROM import_batches ib
        LEFT JOIN users u ON u.user_id = ib.created_by
        ORDER BY ib.import_id DESC
        LIMIT 50
        """
    )
    return rows_to_dicts(await cur.fetchall())

```

## `backend/app/api/reports.py`

```python
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import AsyncConnection

from ..db import get_db
from ..deps import require_permission
from ..utils import csv_response, rows_to_dicts

router = APIRouter(prefix="/reports", tags=["reports"])


def range_or_default(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    end = date_to or date.today()
    start = date_from or (end - timedelta(days=30))
    if end < start:
        raise HTTPException(status_code=400, detail="Некорректный период")
    return start, end


def maybe_csv(rows: list[dict], fmt: str, filename: str, user: dict):
    if fmt == "csv":
        if "reports:export" not in user["permissions"]:
            raise HTTPException(status_code=403, detail="Нет права на экспорт отчётов")
        return csv_response(rows, filename)
    return rows


@router.get("/occupancy")
async def occupancy(
    date_from: date | None = None,
    date_to: date | None = None,
    room_type_id: int | None = None,
    format: str = Query("json"),
    user: dict = Depends(require_permission("reports:view")),
    conn: AsyncConnection = Depends(get_db),
):
    start, end = range_or_default(date_from, date_to)
    if room_type_id:
        cur = await conn.execute(
            """
            SELECT report_date, room_type_id, room_type, rooms_total AS rooms_available,
                   rooms_occupied, occupancy_pct
            FROM v_occupancy_by_type
            WHERE report_date BETWEEN %s AND %s AND room_type_id = %s
            ORDER BY report_date
            """,
            (start, end, room_type_id),
        )
    else:
        cur = await conn.execute(
            """
            SELECT report_date, rooms_occupied, rooms_available, occupancy_pct
            FROM v_occupancy_daily
            WHERE report_date BETWEEN %s AND %s
            ORDER BY report_date
            """,
            (start, end),
        )
    series = rows_to_dicts(await cur.fetchall())
    if series:
        avg = round(sum(float(row["occupancy_pct"] or 0) for row in series) / len(series), 2)
        total_occupied = sum(int(row["rooms_occupied"] or 0) for row in series)
        total_available = sum(int(row["rooms_available"] or 0) for row in series)
    else:
        avg = 0
        total_occupied = 0
        total_available = 0
    payload = {
        "series": series,
        "summary": {
            "average_occupancy": avg,
            "room_nights_sold": total_occupied,
            "room_nights_available": total_available,
        },
    }
    if format == "csv":
        return maybe_csv(series, format, "occupancy.csv", user)
    return payload


@router.get("/adr-revpar")
async def adr_revpar(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = Query("json"),
    user: dict = Depends(require_permission("reports:view")),
    conn: AsyncConnection = Depends(get_db),
):
    start, end = range_or_default(date_from, date_to)
    cur = await conn.execute(
        """
        SELECT report_date, room_revenue, rooms_sold, rooms_available, adr, revpar
        FROM v_adr_revpar_daily
        WHERE report_date BETWEEN %s AND %s
        ORDER BY report_date
        """,
        (start, end),
    )
    series = rows_to_dicts(await cur.fetchall())
    revenue = sum(float(row["room_revenue"] or 0) for row in series)
    sold = sum(int(row["rooms_sold"] or 0) for row in series)
    available = sum(int(row["rooms_available"] or 0) for row in series)
    payload = {
        "series": series,
        "summary": {
            "room_revenue": round(revenue, 2),
            "adr": round(revenue / sold, 2) if sold else 0,
            "revpar": round(revenue / available, 2) if available else 0,
        },
    }
    if format == "csv":
        return maybe_csv(series, format, "adr-revpar.csv", user)
    return payload


@router.get("/cancellations")
async def cancellations(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = Query("json"),
    user: dict = Depends(require_permission("reports:view")),
    conn: AsyncConnection = Depends(get_db),
):
    start, end = range_or_default(date_from, date_to)
    cur = await conn.execute(
        """
        SELECT * FROM v_cancellations_monthly
        WHERE month BETWEEN %s AND %s
        ORDER BY month
        """,
        (start, end),
    )
    months = await cur.fetchall()
    cur = await conn.execute(
        """
        SELECT * FROM v_cancellation_reasons
        WHERE month BETWEEN %s AND %s
        ORDER BY month, bookings DESC
        """,
        (start, end),
    )
    reasons = await cur.fetchall()
    payload = {"months": rows_to_dicts(months), "reasons": rows_to_dicts(reasons)}
    if format == "csv":
        return maybe_csv(rows_to_dicts(months), format, "cancellations.csv", user)
    return payload


@router.get("/room-status")
async def room_status(
    format: str = Query("json"),
    user: dict = Depends(require_permission("reports:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM v_room_status_today ORDER BY status")
    rows = rows_to_dicts(await cur.fetchall())
    if format == "csv":
        return maybe_csv(rows, format, "room-status.csv", user)
    return {"items": rows}


@router.get("/consumables")
async def consumables(
    format: str = Query("json"),
    user: dict = Depends(require_permission("reports:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM v_consumables_stock ORDER BY name")
    rows = rows_to_dicts(await cur.fetchall())
    if format == "csv":
        return maybe_csv(rows, format, "consumables.csv", user)
    return {"items": rows}


@router.get("/revenue-by-service")
async def revenue_by_service(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = Query("json"),
    user: dict = Depends(require_permission("reports:view")),
    conn: AsyncConnection = Depends(get_db),
):
    start, end = range_or_default(date_from, date_to)
    cur = await conn.execute(
        """
        SELECT * FROM v_revenue_by_service
        WHERE month BETWEEN %s AND %s
        ORDER BY month, revenue DESC
        """,
        (start, end),
    )
    rows = rows_to_dicts(await cur.fetchall())
    if format == "csv":
        return maybe_csv(rows, format, "revenue-by-service.csv", user)
    return {"items": rows}

```

## `backend/app/api/imports.py`

```python
from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from ..db import get_db
from ..deps import require_permission
from ..schemas import ImportCommitRequest

router = APIRouter(prefix="/imports", tags=["imports"])

BANK_COLUMNS = {"date", "amount", "method", "booking_id", "folio_id", "external_ref"}
RATE_COLUMNS = {"room_type", "name", "season_start", "season_end", "price_per_night", "cancellation_terms"}
METHODS = {"CARD", "CASH", "BANK_TRANSFER", "ONLINE"}


def parse_date(value: str) -> str:
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("неверная дата")


def parse_amount(value: str) -> float:
    value = (value or "").strip().replace(" ", "").replace(",", ".")
    amount = float(value)
    if amount <= 0:
        raise ValueError("сумма должна быть больше нуля")
    return amount


def read_csv(upload: UploadFile, required: set[str]) -> list[dict[str, str]]:
    raw = upload.file.read()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8-sig", errors="replace")
    else:
        text = raw
    if not text.strip():
        raise HTTPException(status_code=400, detail="Файл пуст")
    delimiter = ";" if ";" in text.splitlines()[0] else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Не найдена строка заголовков")
    normalized = {name.strip() for name in reader.fieldnames}
    missing = required - normalized
    if missing:
        raise HTTPException(status_code=400, detail=f"Нет колонок: {', '.join(sorted(missing))}")
    return [{key.strip(): (value or "").strip() for key, value in row.items() if key} for row in reader]


@router.post("/bank-statement/preview")
async def bank_statement_preview(
    file: UploadFile = File(...),
    conn: AsyncConnection = Depends(get_db),
    user: dict = Depends(require_permission("imports:bank")),
):
    rows = read_csv(file, {"date", "amount", "method"})
    result = []
    valid = 0
    errors = 0
    for index, row in enumerate(rows, start=2):
        item = {"row": index, **row, "status": "ok", "error": None, "folio_id": None}
        try:
            item["date"] = parse_date(row["date"])
            item["amount"] = parse_amount(row["amount"])
            method = (row.get("method") or "").upper()
            if method not in METHODS:
                raise ValueError("недопустимый способ оплаты")
            item["method"] = method
            folio_id = None
            if row.get("folio_id"):
                folio_id = int(row["folio_id"])
            elif row.get("booking_id"):
                cur = await conn.execute(
                    """
                    SELECT folio_id FROM folios
                    WHERE booking_id = %s
                    ORDER BY folio_id DESC LIMIT 1
                    """,
                    (int(row["booking_id"]),),
                )
                folio = await cur.fetchone()
                if not folio:
                    raise ValueError("folio для брони не найден")
                folio_id = folio["folio_id"]
            else:
                raise ValueError("нужен booking_id или folio_id")
            cur = await conn.execute(
                "SELECT status FROM folios WHERE folio_id = %s",
                (folio_id,),
            )
            folio_row = await cur.fetchone()
            if not folio_row:
                raise ValueError("folio не найден")
            if folio_row["status"] != "OPEN":
                raise ValueError("folio закрыт")
            if row.get("external_ref"):
                cur = await conn.execute(
                    "SELECT 1 FROM payments WHERE external_ref = %s",
                    (row["external_ref"],),
                )
                if await cur.fetchone():
                    raise ValueError("платёж с таким external_ref уже существует")
            item["folio_id"] = folio_id
            valid += 1
        except (ValueError, TypeError) as exc:
            item["status"] = "error"
            item["error"] = str(exc)
            errors += 1
        result.append(item)
    return {"rows": result, "total": len(result), "valid": valid, "errors": errors}


@router.post("/bank-statement/commit")
async def bank_statement_commit(
    payload: ImportCommitRequest,
    conn: AsyncConnection = Depends(get_db),
    user: dict = Depends(require_permission("imports:bank")),
):
    valid_rows = [row for row in payload.rows if row.get("status") == "ok"]
    if not valid_rows:
        raise HTTPException(status_code=400, detail="Нет строк для загрузки")

    cur = await conn.execute(
        """
        INSERT INTO import_batches
            (import_type, filename, status, total_rows, success_rows, error_rows, created_by)
        VALUES ('BANK_STATEMENT', %s, 'PREVIEW', %s, %s, %s, %s)
        RETURNING import_id
        """,
        (payload.filename, len(payload.rows), len(valid_rows), len(payload.rows) - len(valid_rows), user["user_id"]),
    )
    import_id = (await cur.fetchone())["import_id"]

    for row in valid_rows:
        await conn.execute(
            """
            INSERT INTO payments (folio_id, amount, method, payment_type, external_ref)
            VALUES (%s, %s, %s, 'PAYMENT', %s)
            """,
            (
                int(row["folio_id"]),
                float(row["amount"]),
                row["method"],
                row.get("external_ref") or None,
            ),
        )

    await conn.execute(
        "UPDATE import_batches SET status = 'COMMITTED', committed_at = now() WHERE import_id = %s",
        (import_id,),
    )
    return {"ok": True, "import_id": import_id, "success_rows": len(valid_rows)}


@router.post("/rates/preview")
async def rates_preview(
    file: UploadFile = File(...),
    conn: AsyncConnection = Depends(get_db),
    user: dict = Depends(require_permission("imports:rates")),
):
    rows = read_csv(file, {"room_type", "name", "season_start", "season_end", "price_per_night"})
    result = []
    valid = 0
    errors = 0
    for index, row in enumerate(rows, start=2):
        item = {"row": index, **row, "status": "ok", "error": None, "room_type_id": None}
        try:
            cur = await conn.execute(
                "SELECT room_type_id FROM room_types WHERE lower(name) = lower(%s)",
                (row["room_type"],),
            )
            room_type = await cur.fetchone()
            if not room_type:
                raise ValueError("тип номера не найден")
            start = parse_date(row["season_start"])
            end = parse_date(row["season_end"])
            if end < start:
                raise ValueError("дата окончания раньше начала")
            price = parse_amount(row["price_per_night"])
            item.update(
                {
                    "room_type_id": room_type["room_type_id"],
                    "season_start": start,
                    "season_end": end,
                    "price_per_night": price,
                }
            )
            valid += 1
        except (ValueError, TypeError) as exc:
            item["status"] = "error"
            item["error"] = str(exc)
            errors += 1
        result.append(item)
    return {"rows": result, "total": len(result), "valid": valid, "errors": errors}


@router.post("/rates/commit")
async def rates_commit(
    payload: ImportCommitRequest,
    conn: AsyncConnection = Depends(get_db),
    user: dict = Depends(require_permission("imports:rates")),
):
    valid_rows = [row for row in payload.rows if row.get("status") == "ok"]
    if not valid_rows:
        raise HTTPException(status_code=400, detail="Нет строк для загрузки")

    cur = await conn.execute(
        """
        INSERT INTO import_batches
            (import_type, filename, status, total_rows, success_rows, error_rows, created_by)
        VALUES ('RATES', %s, 'PREVIEW', %s, %s, %s, %s)
        RETURNING import_id
        """,
        (payload.filename, len(payload.rows), len(valid_rows), len(payload.rows) - len(valid_rows), user["user_id"]),
    )
    import_id = (await cur.fetchone())["import_id"]

    for row in valid_rows:
        await conn.execute(
            """
            INSERT INTO rate_plans
                (room_type_id, name, season_start, season_end, price_per_night, cancellation_terms)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                int(row["room_type_id"]),
                row["name"],
                row["season_start"],
                row["season_end"],
                float(row["price_per_night"]),
                row.get("cancellation_terms") or None,
            ),
        )

    await conn.execute(
        "UPDATE import_batches SET status = 'COMMITTED', committed_at = now() WHERE import_id = %s",
        (import_id,),
    )
    return {"ok": True, "import_id": import_id, "success_rows": len(valid_rows)}

```

## `backend/app/services/pdf.py`

```python
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
]

BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
]


def _register_fonts() -> tuple[str, str]:
    regular = None
    bold = None
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            regular = path
            break
    for path in BOLD_CANDIDATES:
        if Path(path).exists():
            bold = path
            break
    if regular:
        pdfmetrics.registerFont(TTFont("SunStay", regular))
        if bold:
            pdfmetrics.registerFont(TTFont("SunStay-Bold", bold))
        else:
            bold = regular
        return "SunStay", "SunStay-Bold"
    return "Helvetica", "Helvetica-Bold"


def money(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"{number:,.2f} ₽".replace(",", " ")


def folio_pdf(folio: dict, charges: list[dict], payments: list[dict]) -> bytes:
    regular, bold = _register_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Счёт SunStay #{folio.get('folio_id')}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SunStayTitle",
        parent=styles["Title"],
        fontName=bold,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#123B36"),
        alignment=0,
    )
    body_style = ParagraphStyle(
        "SunStayBody",
        parent=styles["BodyText"],
        fontName=regular,
        fontSize=10,
        leading=14,
    )
    small_style = ParagraphStyle(
        "SunStaySmall",
        parent=body_style,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6E746D"),
    )
    table_style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), regular),
            ("FONTNAME", (0, 0), (-1, 0), bold),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3EEE6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1E2420")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E6DED2")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBF8F3")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )

    story = [
        Paragraph("SunStay", title_style),
        Paragraph("Бутик-отель · Санкт-Петербург, набережная реки Мойки, 12", small_style),
        Spacer(1, 6 * mm),
        Paragraph(f"Счёт Folio #{folio.get('folio_id')} от {str(folio.get('opened_at', ''))[:10]}", body_style),
        Spacer(1, 3 * mm),
    ]

    info_rows = [
        ["Гость", escape(str(folio.get("guest_name") or ""))],
        ["Документ", escape(str(folio.get("document_number") or ""))],
        ["Номер", escape(str(folio.get("room_number") or ""))],
        ["Период", f"{folio.get('checkin_date')} — {folio.get('checkout_date')}"],
        ["Статус", "Открыт" if folio.get("status") == "OPEN" else "Закрыт"],
    ]
    info_table = Table(info_rows, colWidths=[42 * mm, 120 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), bold),
                ("FONTNAME", (1, 0), (1, -1), regular),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([info_table, Spacer(1, 6 * mm)])

    charge_rows = [["Тип", "Описание", "Дата", "Сумма"]]
    for line in charges:
        charge_rows.append(
            [
                escape(str(line.get("line_type") or "")),
                escape(str(line.get("description") or "")),
                str(line.get("charge_date") or "")[:10],
                money(line.get("amount")),
            ]
        )
    if len(charge_rows) == 1:
        charge_rows.append(["", "Начислений нет", "", money(0)])
    charge_table = Table(charge_rows, colWidths=[24 * mm, 88 * mm, 26 * mm, 32 * mm], repeatRows=1)
    charge_table.setStyle(table_style)
    story.extend([Paragraph("Начисления", ParagraphStyle("H2", parent=body_style, fontName=bold, fontSize=12)), Spacer(1, 2 * mm), charge_table, Spacer(1, 5 * mm)])

    payment_rows = [["Дата", "Способ", "Тип", "Сумма"]]
    for payment in payments:
        payment_rows.append(
            [
                str(payment.get("paid_at") or "")[:10],
                escape(str(payment.get("method") or "")),
                escape(str(payment.get("payment_type") or "")),
                money(payment.get("amount")),
            ]
        )
    if len(payment_rows) == 1:
        payment_rows.append(["", "", "Платежей нет", money(0)])
    payment_table = Table(payment_rows, colWidths=[30 * mm, 40 * mm, 40 * mm, 40 * mm], repeatRows=1)
    payment_table.setStyle(table_style)
    story.extend([Paragraph("Платежи", ParagraphStyle("H3", parent=body_style, fontName=bold, fontSize=12)), Spacer(1, 2 * mm), payment_table, Spacer(1, 6 * mm)])

    totals = [
        ["Начислено", money(folio.get("charged_total"))],
        ["Оплачено", money(folio.get("paid_total"))],
        ["К оплате", money(folio.get("balance"))],
    ]
    totals_table = Table(totals, colWidths=[120 * mm, 42 * mm])
    totals_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), bold),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, 2), (-1, 2), 0.8, colors.HexColor("#123B36")),
                ("TOPPADDING", (0, 2), (-1, 2), 6),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Спасибо, что выбрали SunStay. Документ сформирован автоматически.", small_style))

    doc.build(story)
    return buffer.getvalue()

```

## `backend/app/services/backup.py`

```python
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from ..config import get_settings


def backup_path() -> Path:
    settings = get_settings()
    return Path(settings.backup_dir) / settings.backup_file_name


def run_backup_sync() -> dict:
    settings = get_settings()
    path = backup_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "pg_dump",
            "--dbname",
            settings.database_admin_url,
            "-Fc",
            "-f",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    status = "success" if result.returncode == 0 else "error"
    error = None if result.returncode == 0 else (result.stderr or "pg_dump failed")[:1000]

    with psycopg.connect(settings.database_admin_url) as conn:
        with conn.transaction():
            for key, value in (
                ("backup.last_run_at", datetime.now().isoformat()),
                ("backup.last_status", status),
                ("backup.last_error", error),
            ):
                conn.execute(
                    """
                    INSERT INTO system_settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = now()
                    """,
                    (key, Jsonb(value)),
                )

    return {
        "filename": path.name,
        "size": path.stat().st_size if path.exists() else 0,
        "status": status,
        "error": error,
    }

```

## `backend/tests/test_api.py`

```python
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def login(client: TestClient, email: str, password: str = "SunStay2026!") -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_manager_dashboard() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        response = client.get("/api/manager/dashboard", headers=auth_headers(session["access_token"]))
        assert response.status_code == 200
        data = response.json()
        assert "kpi" in data
        assert "occupancy" in data
        assert data["kpi"]["total_rooms"] >= 6


def test_public_availability_and_booking_list() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/public/availability",
            params={"checkin": "2026-12-20", "checkout": "2026-12-22", "guests": 2},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_guest_cannot_access_manager_api() -> None:
    with TestClient(app) as client:
        session = login(client, "guest.demo@sunstay.example")
        response = client.get("/api/manager/dashboard", headers=auth_headers(session["access_token"]))
        assert response.status_code == 403


def test_manager_cannot_access_admin_users() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        response = client.get("/api/admin/users", headers=auth_headers(session["access_token"]))
        assert response.status_code == 403


def test_reports_and_pdf() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/reports/occupancy", headers=headers)
        assert response.status_code == 200
        assert "series" in response.json()

        response = client.get("/api/manager/folios/1/pdf", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/pdf")
        assert response.content.startswith(b"%PDF")


def test_sql_injection_login_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "' OR 1=1 --", "password": "anything"},
        )
        assert response.status_code in (401, 422)


def test_admin_login_and_settings() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code == 200
        response = client.get("/api/admin/settings", headers=headers)
        assert response.status_code == 200


def test_admin_users_stats_reasons_and_masking() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])

        stats = client.get("/api/admin/users/stats", headers=headers)
        assert stats.status_code == 200
        payload = stats.json()
        assert payload["summary"]["total"] >= 5
        assert "online" in payload["summary"]

        reasons = client.get("/api/admin/users/block-reasons", headers=headers)
        assert reasons.status_code == 200
        assert len(reasons.json()) >= 4

        users = client.get("/api/admin/users", headers=headers, params={"page_size": 5})
        assert users.status_code == 200
        items = users.json()["items"]
        assert items
        assert "is_online" in items[0]
        assert "*" in (items[0]["phone"] or "")


def test_audit_filters_and_login_events() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get(
            "/api/admin/audit",
            headers=headers,
            params={"event_type": "LOGIN_SECURITY", "page_size": 5},
        )
        assert response.status_code == 200
        assert "items" in response.json()


def test_contacts_are_masked_in_manager_api() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/manager/bookings/2", headers=headers)
        assert response.status_code == 200
        booking = response.json()["booking"]
        assert "*" in booking["document_number"]
        assert "*" in booking["guest_phone"]
        assert "@" in booking["guest_email"]


def test_backup_status_and_schedule() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/admin/backups", headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert "settings" in payload
        assert payload["settings"]["backup.schedule_time"]

```

## `analytics/requirements.txt`

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
psycopg[binary,pool]==3.2.3
pydantic-settings==2.7.1
PyJWT==2.10.1
python-multipart==0.0.20

```

## `analytics/Dockerfile`

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

```

## `analytics/app/main.py`

```python
from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = __import__("os").getenv(
    "ANALYTICS_DATABASE_URL",
    "postgresql://sunstay_analytics:sunstay_analytics@localhost:5432/hotel",
)
JWT_SECRET = __import__("os").getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = __import__("os").getenv("JWT_ALGORITHM", "HS256")
CORS_ORIGINS = __import__("os").getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080,http://localhost"
).split(",")

pool: AsyncConnectionPool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={"row_factory": dict_row, "autocommit": True},
    )
    await pool.open()
    await pool.wait()
    yield
    await pool.close()


app = FastAPI(
    title="SunStay Analytics",
    description="Микросервис статистики и отчётности гостиницы SunStay.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in CORS_ORIGINS if item.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_conn():
    assert pool is not None
    async with pool.connection() as conn:
        yield conn


async def require_reports(request: Request) -> dict[str, Any]:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        payload = jwt.decode(
            header.split(" ", 1)[1],
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    if payload.get("role") not in ("MANAGER", "HOTEL_MANAGER", "DB_ADMIN"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return payload


def json_rows(rows):
    result = []
    for row in rows:
        item = {}
        for key, value in row.items():
            if isinstance(value, (date,)):
                value = value.isoformat()
            else:
                try:
                    value = float(value) if value.__class__.__name__ == "Decimal" else value
                except Exception:
                    pass
            item[key] = value
        result.append(item)
    return result


def csv_export(rows: list[dict], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    buffer.write("\ufeff")
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    content = buffer.getvalue().encode("utf-8")
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def period(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    end = date_to or date.today()
    start = date_from or (end - timedelta(days=30))
    if end < start:
        raise HTTPException(status_code=400, detail="Некорректный период")
    return start, end


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "analytics"}


@app.get("/api/reports/occupancy")
async def occupancy(
    date_from: date | None = None,
    date_to: date | None = None,
    room_type_id: int | None = None,
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    start, end = period(date_from, date_to)
    if room_type_id:
        cur = await conn.execute(
            """
            SELECT report_date, room_type_id, room_type, rooms_total AS rooms_available,
                   rooms_occupied, occupancy_pct
            FROM v_occupancy_by_type
            WHERE report_date BETWEEN %s AND %s AND room_type_id = %s
            ORDER BY report_date
            """,
            (start, end, room_type_id),
        )
    else:
        cur = await conn.execute(
            """
            SELECT report_date, rooms_occupied, rooms_available, occupancy_pct
            FROM v_occupancy_daily
            WHERE report_date BETWEEN %s AND %s
            ORDER BY report_date
            """,
            (start, end),
        )
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "occupancy.csv")
    avg = round(sum(float(row["occupancy_pct"] or 0) for row in rows) / len(rows), 2) if rows else 0
    return {
        "series": rows,
        "summary": {
            "average_occupancy": avg,
            "room_nights_sold": sum(int(row["rooms_occupied"] or 0) for row in rows),
            "room_nights_available": sum(int(row["rooms_available"] or 0) for row in rows),
        },
    }


@app.get("/api/reports/adr-revpar")
async def adr_revpar(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    start, end = period(date_from, date_to)
    cur = await conn.execute(
        """
        SELECT report_date, room_revenue, rooms_sold, rooms_available, adr, revpar
        FROM v_adr_revpar_daily
        WHERE report_date BETWEEN %s AND %s
        ORDER BY report_date
        """,
        (start, end),
    )
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "adr-revpar.csv")
    revenue = sum(float(row["room_revenue"] or 0) for row in rows)
    sold = sum(int(row["rooms_sold"] or 0) for row in rows)
    available = sum(int(row["rooms_available"] or 0) for row in rows)
    return {
        "series": rows,
        "summary": {
            "room_revenue": round(revenue, 2),
            "adr": round(revenue / sold, 2) if sold else 0,
            "revpar": round(revenue / available, 2) if available else 0,
        },
    }


@app.get("/api/reports/cancellations")
async def cancellations(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    start, end = period(date_from, date_to)
    cur = await conn.execute(
        "SELECT * FROM v_cancellations_monthly WHERE month BETWEEN %s AND %s ORDER BY month",
        (start, end),
    )
    months = json_rows(await cur.fetchall())
    cur = await conn.execute(
        "SELECT * FROM v_cancellation_reasons WHERE month BETWEEN %s AND %s ORDER BY month, bookings DESC",
        (start, end),
    )
    reasons = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(months, "cancellations.csv")
    return {"months": months, "reasons": reasons}


@app.get("/api/reports/room-status")
async def room_status(
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    cur = await conn.execute("SELECT * FROM v_room_status_today ORDER BY status")
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "room-status.csv")
    return {"items": rows}


@app.get("/api/reports/consumables")
async def consumables(
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    cur = await conn.execute("SELECT * FROM v_consumables_stock ORDER BY name")
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "consumables.csv")
    return {"items": rows}


@app.get("/api/reports/revenue-by-service")
async def revenue_by_service(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    start, end = period(date_from, date_to)
    cur = await conn.execute(
        "SELECT * FROM v_revenue_by_service WHERE month BETWEEN %s AND %s ORDER BY month, revenue DESC",
        (start, end),
    )
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "revenue-by-service.csv")
    return {"items": rows}

```

## `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: sunstay_db
    environment:
      POSTGRES_DB: hotel
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      TZ: Europe/Moscow
    ports:
      - "5432:5432"
    volumes:
      - sunstay_pgdata:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d:ro
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d hotel"]
      interval: 5s
      timeout: 5s
      retries: 30

  api:
    build:
      context: ./backend
    container_name: sunstay_api
    environment:
      DATABASE_URL: postgresql://sunstay_app:sunstay_app@db:5432/hotel
      DATABASE_ADMIN_URL: postgresql://postgres:postgres@db:5432/hotel
      ANALYTICS_DATABASE_URL: postgresql://sunstay_analytics:sunstay_analytics@db:5432/hotel
      JWT_SECRET: sunstay-dev-secret-change-in-production
      DATA_ENCRYPTION_KEY: bh9O5gpBkH-qPkJSoUkiWswjQyQqWcQ7ZHZU6BO_C9s=
      JWT_ALGORITHM: HS256
      CORS_ORIGINS: http://localhost:5173,http://localhost:8080,http://localhost
      BACKUP_DIR: /backups
      TZ: Europe/Moscow
    ports:
      - "8000:8000"
    volumes:
      - ./backups:/backups
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  analytics:
    build:
      context: ./analytics
    container_name: sunstay_analytics
    environment:
      ANALYTICS_DATABASE_URL: postgresql://sunstay_analytics:sunstay_analytics@db:5432/hotel
      JWT_SECRET: sunstay-dev-secret-change-in-production
      DATA_ENCRYPTION_KEY: bh9O5gpBkH-qPkJSoUkiWswjQyQqWcQ7ZHZU6BO_C9s=
      JWT_ALGORITHM: HS256
      CORS_ORIGINS: http://localhost:5173,http://localhost:8080,http://localhost
      TZ: Europe/Moscow
    ports:
      - "8001:8001"
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  web:
    build:
      context: ./frontend
    container_name: sunstay_web
    ports:
      - "8080:80"
    depends_on:
      - api
      - analytics
    restart: unless-stopped

  adminer:
    image: adminer:4
    container_name: sunstay_adminer
    ports:
      - "8081:8080"
    depends_on:
      db:
        condition: service_healthy

volumes:
  sunstay_pgdata:

```

## `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    client_max_body_size 10m;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript application/xml image/svg+xml;

    location /api/ {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /analytics/ {
        proxy_pass http://analytics:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

```
