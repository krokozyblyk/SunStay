from __future__ import annotations

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
