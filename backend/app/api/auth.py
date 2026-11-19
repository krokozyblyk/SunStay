from __future__ import annotations

import hashlib
import json
import secrets
import uuid

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from ..audit import write_audit_event
from ..crypto import document_fields, encrypt_value, phone_fields
from ..db import get_db, get_pool
from ..deps import get_current_user
from ..password_policy import validate_password
from ..schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SettingsUpdate,
    ChangePasswordRequest,
    TwoFactorDisableRequest,
    TwoFactorEnableRequest,
    TwoFactorVerifyRequest,
)
from ..security import (
    create_access_token,
    create_2fa_token,
    decode_2fa_token,
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
            u.password_hash, u.is_active, u.failed_login_attempts, u.totp_enabled,
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

    if user["totp_enabled"]:
        return {
            "requires_2fa": True,
            "twofa_token": create_2fa_token(user["user_id"]),
        }

    await log_attempt(
        payload.email, ip, True, user=user,
        user_agent=ua, request_id=rid,
    )
    return await issue_tokens(conn, user)


def _generate_recovery_codes() -> tuple[list[str], list[str]]:
    codes = [secrets.token_urlsafe(9) for _ in range(10)]
    hashed = [hashlib.sha256(code.encode("utf-8")).hexdigest() for code in codes]
    return codes, hashed


async def _totp_secret(user_id: int, conn: AsyncConnection) -> str | None:
    cur = await conn.execute("SELECT totp_secret_enc FROM users WHERE user_id = %s", (user_id,))
    row = await cur.fetchone()
    if not row or not row["totp_secret_enc"]:
        return None
    from ..crypto import decrypt_value
    return decrypt_value(row["totp_secret_enc"])


@router.post("/2fa/verify")
async def verify_2fa(payload: TwoFactorVerifyRequest, request: Request, conn: AsyncConnection = Depends(get_db)):
    try:
        claims = decode_2fa_token(payload.twofa_token)
        user_id = int(claims["sub"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Код подтверждения истёк, войдите заново")

    cur = await conn.execute(
        """
        SELECT u.*, r.name AS role_name, g.guest_id
        FROM users u JOIN roles r ON r.role_id = u.role_id
        LEFT JOIN guests g ON g.user_id = u.user_id
        WHERE u.user_id = %s
        """,
        (user_id,),
    )
    user = await cur.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    secret = await _totp_secret(user_id, conn)
    if not secret:
        raise HTTPException(status_code=400, detail="Двухфакторная аутентификация не настроена")

    code_valid = pyotp.TOTP(secret).verify(payload.code, valid_window=1)
    recovery_valid = False
    if not code_valid:
        recovery_codes = user.get("totp_recovery_codes") or []
        code_hash = hashlib.sha256(payload.code.strip().encode("utf-8")).hexdigest()
        if code_hash in recovery_codes:
            recovery_valid = True
            remaining = [c for c in recovery_codes if c != code_hash]
            await conn.execute(
                "UPDATE users SET totp_recovery_codes = %s WHERE user_id = %s",
                (Jsonb(remaining), user_id),
            )

    if not code_valid and not recovery_valid:
        raise HTTPException(status_code=401, detail="Неверный код")

    ip = request.client.host if request.client else ""
    await log_attempt(user["email"], ip, True, user=user, user_agent=request.headers.get("user-agent"), request_id=request.headers.get("x-request-id") or str(uuid.uuid4()))
    return await issue_tokens(conn, user)


@router.post("/2fa/setup")
async def setup_2fa(user: dict = Depends(get_current_user), conn: AsyncConnection = Depends(get_db)):
    if user["role_code"] not in ("DB_ADMIN", "HOTEL_MANAGER"):
        raise HTTPException(status_code=403, detail="2FA доступна только администратору БД и управляющему отелем")
    secret = pyotp.random_base32()
    await conn.execute(
        "UPDATE users SET totp_secret_enc = %s, totp_enabled = FALSE WHERE user_id = %s",
        (encrypt_value(secret), user["user_id"]),
    )
    uri = pyotp.TOTP(secret).provisioning_uri(name=user["email"], issuer_name="SunStay")
    return {"secret": secret, "otpauth_uri": uri}


@router.post("/2fa/enable")
async def enable_2fa(payload: TwoFactorEnableRequest, user: dict = Depends(get_current_user), conn: AsyncConnection = Depends(get_db)):
    secret = await _totp_secret(user["user_id"], conn)
    if not secret:
        raise HTTPException(status_code=400, detail="Сначала создайте секрет")
    if not pyotp.TOTP(secret).verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Неверный код")
    codes, hashed = _generate_recovery_codes()
    await conn.execute(
        "UPDATE users SET totp_enabled = TRUE, totp_recovery_codes = %s WHERE user_id = %s",
        (Jsonb(hashed), user["user_id"]),
    )
    return {"ok": True, "recovery_codes": codes}


@router.post("/2fa/disable")
async def disable_2fa(payload: TwoFactorDisableRequest, user: dict = Depends(get_current_user), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute("SELECT password_hash FROM users WHERE user_id = %s", (user["user_id"],))
    row = await cur.fetchone()
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Неверный пароль")
    await conn.execute(
        "UPDATE users SET totp_enabled = FALSE, totp_secret_enc = NULL, totp_recovery_codes = NULL WHERE user_id = %s",
        (user["user_id"],),
    )
    return {"ok": True}


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

    await validate_password(conn, payload.password)

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


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT password_hash FROM users WHERE user_id = %s", (user["user_id"],))
    row = await cur.fetchone()
    if not row or not verify_password(payload.old_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")
    await validate_password(conn, payload.new_password)
    await conn.execute(
        "UPDATE users SET password_hash = %s, password_changed_at = now() WHERE user_id = %s",
        (hash_password(payload.new_password), user["user_id"]),
    )
    await conn.execute(
        "UPDATE user_sessions SET revoked_at = now() WHERE user_id = %s AND revoked_at IS NULL",
        (user["user_id"],),
    )
    return {"ok": True}


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
