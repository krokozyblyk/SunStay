from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from .db import get_pool
from .notifications import notify_guest
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
                SELECT b.booking_id, b.status, b.hold_until, b.guest_id,
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
                await notify_guest(
                    conn,
                    booking["guest_id"],
                    "BOOKING_CANCELLED",
                    "Бронь отменена",
                    "Истекло время ожидания подтверждения.",
                    f"/me/bookings/{booking['booking_id']}",
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
