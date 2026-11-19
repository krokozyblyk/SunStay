from __future__ import annotations

from typing import Any

from psycopg import AsyncConnection


async def notify_user(
    conn: AsyncConnection,
    user_id: int,
    notification_type: str,
    title: str,
    body: str | None = None,
    link: str | None = None,
) -> None:
    await conn.execute(
        """
        INSERT INTO notifications (user_id, notification_type, title, body, link)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, notification_type, title, body, link),
    )


async def notify_guest(
    conn: AsyncConnection,
    guest_id: int,
    notification_type: str,
    title: str,
    body: str | None = None,
    link: str | None = None,
) -> bool:
    cur = await conn.execute("SELECT user_id FROM guests WHERE guest_id = %s", (guest_id,))
    row = await cur.fetchone()
    if not row or not row["user_id"]:
        return False
    await notify_user(conn, row["user_id"], notification_type, title, body, link)
    return True


async def notify_guest_by_booking(
    conn: AsyncConnection,
    booking: dict[str, Any],
    notification_type: str,
    title: str,
    body: str | None = None,
) -> bool:
    return await notify_guest(
        conn,
        booking["guest_id"],
        notification_type,
        title,
        body,
        f"/me/bookings/{booking['booking_id']}",
    )
