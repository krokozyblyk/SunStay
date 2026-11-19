from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from psycopg import AsyncConnection

from ..db import get_db
from ..deps import get_current_user
from ..utils import rows_to_dicts

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    limit: int = Query(30, ge=1, le=100),
    user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT notification_id, notification_type, title, body, link, read_at, created_at
        FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT %s
        """,
        (user["user_id"], limit),
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/unread-count")
async def unread_count(user: dict = Depends(get_current_user), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        "SELECT count(*) AS count FROM notifications WHERE user_id = %s AND read_at IS NULL",
        (user["user_id"],),
    )
    return {"count": (await cur.fetchone())["count"]}


@router.post("/{notification_id}/read")
async def read_notification(
    notification_id: int,
    user: dict = Depends(get_current_user),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "UPDATE notifications SET read_at = now() WHERE notification_id = %s AND user_id = %s",
        (notification_id, user["user_id"]),
    )
    return {"ok": True}


@router.post("/read-all")
async def read_all(user: dict = Depends(get_current_user), conn: AsyncConnection = Depends(get_db)):
    await conn.execute(
        "UPDATE notifications SET read_at = now() WHERE user_id = %s AND read_at IS NULL",
        (user["user_id"],),
    )
    return {"ok": True}
