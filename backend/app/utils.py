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
            r.image_url AS room_image,
            r.description AS room_description,
            r.variant_name AS room_variant,
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
