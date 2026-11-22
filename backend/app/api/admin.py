from __future__ import annotations

import asyncio
import hashlib
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from psycopg import AsyncConnection, errors
from psycopg.types.json import Jsonb

from ..config import get_settings
from ..crypto import hash_value, normalize_phone, phone_fields
from ..db import get_db
from ..deps import get_current_user, require_permission
from ..password_policy import validate_password
from ..schemas import (
    BlockUserRequest,
    ResetPasswordRequest,
    ReviewModerateRequest,
    RoleAssignRequest,
    RolePermissionsUpdate,
    UserCreate,
    UserUpdate,
)
from ..security import hash_password
from ..services.backup import backup_path, ensure_valid_backup, run_backup_sync
from ..utils import csv_response, row_to_dict, rows_to_dicts

router = APIRouter(prefix="/admin", tags=["admin"])

DIRECTORIES: dict[str, dict[str, Any]] = {
    "room-types": {
        "table": "room_types",
        "pk": "room_type_id",
        "fields": ["name", "capacity", "description", "image_url"],
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
        "fields": ["unit_id", "name", "price", "image_url"],
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
               u.is_active, u.last_login_at, u.last_seen_at, u.created_at, u.totp_enabled,
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
    await validate_password(conn, payload.password)
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

    cur = await conn.execute(
        "SELECT role_id FROM users WHERE user_id = %s", (user_id,)
    )
    target = await cur.fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if target["role_id"] == 5:
        raise HTTPException(status_code=403, detail="Нельзя отозвать доступ администратора БД")

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
    await validate_password(conn, payload.new_password)
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
    cur = await conn.execute(
        "SELECT role_id FROM users WHERE user_id = %s", (user_id,)
    )
    target = await cur.fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if target["role_id"] == 5:
        raise HTTPException(status_code=403, detail="Нельзя изменить роль администратора БД")
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


@router.get("/reviews")
async def reviews(
    status: str | None = None,
    search: str | None = None,
    user: dict = Depends(require_permission("reviews:moderate")),
    conn: AsyncConnection = Depends(get_db),
):
    clauses: list[str] = []
    params: list = []
    if status:
        clauses.append("r.status = %s")
        params.append(status)
    if search:
        like = f"%{search}%"
        clauses.append("(g.full_name ILIKE %s OR r.title ILIKE %s OR r.body ILIKE %s)")
        params.extend([like, like, like])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur = await conn.execute(
        f"""
        SELECT r.review_id, r.booking_id, r.rating, r.title, r.body, r.status,
               r.review_type, r.created_at, r.moderated_at, g.full_name AS guest_name,
               b.checkin_date, b.checkout_date, rm.room_number, rt.name AS room_type,
               u.full_name AS moderated_by_name
        FROM reviews r
        JOIN guests g ON g.guest_id = r.guest_id
        LEFT JOIN bookings b ON b.booking_id = r.booking_id
        LEFT JOIN rooms rm ON rm.room_id = b.room_id
        LEFT JOIN room_types rt ON rt.room_type_id = rm.room_type_id
        LEFT JOIN users u ON u.user_id = r.moderated_by
        {where}
        ORDER BY r.status = 'PENDING' DESC, r.created_at DESC
        """,
        tuple(params),
    )
    return rows_to_dicts(await cur.fetchall())


@router.patch("/reviews/{review_id}")
async def moderate_review(
    review_id: int,
    payload: ReviewModerateRequest,
    user: dict = Depends(require_permission("reviews:moderate")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        UPDATE reviews
        SET status = %s, moderated_by = %s, moderated_at = now()
        WHERE review_id = %s
        RETURNING review_id, status, moderated_by, moderated_at
        """,
        (payload.status, user["user_id"], review_id),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return dict(row)


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
    result = await asyncio.to_thread(ensure_valid_backup)
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("error") or "Не удалось создать резервную копию")
    path = backup_path()
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@router.post("/backups/restore")
async def restore_backup(
    user: dict = Depends(require_permission("backup:manage")),
):
    settings = get_settings()
    result = await asyncio.to_thread(ensure_valid_backup)
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("error") or "Не удалось создать резервную копию")
    path = backup_path()
    result = await asyncio.to_thread(
        subprocess.run,
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "-n",
            "public",
            "--no-owner",
            "--no-acl",
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


@router.get("/sessions")
async def sessions(
    user: dict = Depends(require_permission("users:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT s.session_id, s.user_id, u.full_name, u.email, r.name AS role_name,
               s.user_agent, s.ip_address, s.created_at, s.expires_at, s.revoked_at
        FROM user_sessions s
        JOIN users u ON u.user_id = s.user_id
        JOIN roles r ON r.role_id = u.role_id
        ORDER BY s.revoked_at NULLS FIRST, s.created_at DESC
        LIMIT 200
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: int,
    user: dict = Depends(require_permission("users:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "UPDATE user_sessions SET revoked_at = now() WHERE session_id = %s RETURNING session_id",
        (session_id,),
    )
    if not await cur.fetchone():
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return {"ok": True}


def _with_db(url: str, name: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(parts._replace(path="/" + name))


@router.post("/backups/verify")
async def verify_backup(user: dict = Depends(require_permission("backup:manage"))):
    ensured = await asyncio.to_thread(ensure_valid_backup)
    if ensured.get("status") != "success":
        raise HTTPException(status_code=500, detail=ensured.get("error") or "Не удалось создать резервную копию")
    path = backup_path()
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    result = await asyncio.to_thread(
        subprocess.run,
        ["pg_restore", "--list", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    preview = (result.stdout or "").splitlines()[:10]
    return {
        "ok": result.returncode == 0,
        "size": path.stat().st_size,
        "sha256": checksum,
        "preview": preview,
        "error": None if result.returncode == 0 else (result.stderr or "")[:500],
    }


@router.post("/backups/test-restore")
async def test_restore(user: dict = Depends(require_permission("backup:manage"))):
    ensured = await asyncio.to_thread(ensure_valid_backup)
    if ensured.get("status") != "success":
        raise HTTPException(status_code=500, detail=ensured.get("error") or "Не удалось создать резервную копию")
    path = backup_path()
    settings = get_settings()
    admin_url = settings.database_admin_url
    temp_db = "hotel_restore_check"

    def run() -> dict:
        subprocess.run(["psql", admin_url, "-c", f"DROP DATABASE IF EXISTS {temp_db};"], capture_output=True, text=True, timeout=60)
        created = subprocess.run(["psql", admin_url, "-c", f"CREATE DATABASE {temp_db};"], capture_output=True, text=True, timeout=60)
        if created.returncode != 0:
            return {"ok": False, "error": (created.stderr or "")[:500]}
        temp_url = _with_db(admin_url, temp_db)
        restored = subprocess.run(
            ["pg_restore", "-n", "public", "--no-owner", "--no-acl", "--dbname", temp_url, str(path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        tables = subprocess.run(
            ["psql", temp_url, "-t", "-A", "-c", "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        bookings = subprocess.run(
            ["psql", temp_url, "-t", "-A", "-c", "SELECT count(*) FROM bookings;"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        subprocess.run(["psql", admin_url, "-c", f"DROP DATABASE IF EXISTS {temp_db};"], capture_output=True, text=True, timeout=60)
        table_count = (tables.stdout or "").strip()
        booking_count = (bookings.stdout or "").strip()
        ok = bool(table_count.isdigit() and booking_count.isdigit() and int(table_count) > 0)
        return {
            "ok": ok,
            "tables": table_count,
            "bookings": booking_count,
            "error": None if ok else (restored.stderr or "")[:500],
        }

    return await asyncio.to_thread(run)
