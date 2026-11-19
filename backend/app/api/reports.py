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


@router.get("/forecast")
async def forecast(
    days: int = Query(30, ge=1, le=90),
    user: dict = Depends(require_permission("reports:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        WITH days AS (
            SELECT generate_series(CURRENT_DATE, CURRENT_DATE + (%s::integer - 1), interval '1 day')::date AS day
        ),
        total AS (SELECT count(*)::integer AS rooms FROM rooms)
        SELECT d.day,
               (SELECT COUNT(DISTINCT b.room_id)
                FROM bookings b
                WHERE b.status IN ('NEW','CONFIRMED','CHECKED_IN')
                  AND d.day >= b.checkin_date AND d.day < b.checkout_date) AS occupied_rooms,
               (SELECT COALESCE(SUM(rp.price_per_night), 0)
                FROM bookings b JOIN rate_plans rp ON rp.rate_id = b.rate_id
                WHERE b.status IN ('NEW','CONFIRMED','CHECKED_IN')
                  AND d.day >= b.checkin_date AND d.day < b.checkout_date) AS expected_revenue,
               t.rooms AS total_rooms
        FROM days d, total t
        ORDER BY d.day
        """,
        (days,),
    )
    rows = rows_to_dicts(await cur.fetchall())
    for row in rows:
        total_rooms = int(row["total_rooms"] or 0)
        row["occupancy_pct"] = round((int(row["occupied_rooms"] or 0) / total_rooms * 100), 2) if total_rooms else 0
    return {"series": rows}
