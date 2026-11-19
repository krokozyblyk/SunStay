from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from ..audit import write_audit_event
from ..crypto import document_fields, hash_value, normalize_document, normalize_phone, phone_fields
from ..db import get_db
from ..deps import require_permission
from ..events import publish, subscribe, unsubscribe
from ..notifications import notify_guest, notify_guest_by_booking
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
    BulkBookingAction,
    TemplateSendRequest,
    WaitlistUpdate,
    WaitlistConvertRequest,
    MassSendRequest,
)
from ..security import decode_access_token, role_code
from ..services.pdf import folio_pdf
from ..utils import csv_response, get_booking, get_folio, row_to_dict, rows_to_dicts

router = APIRouter(prefix="/manager", tags=["manager"])


async def _setting_number(conn: AsyncConnection, key: str, default: float) -> float:
    cur = await conn.execute("SELECT value FROM system_settings WHERE key = %s", (key,))
    row = await cur.fetchone()
    try:
        return float(row["value"]) if row else default
    except (TypeError, ValueError):
        return default


async def _award_loyalty_points(conn: AsyncConnection, booking: dict) -> int:
    cur = await conn.execute(
        "SELECT user_id FROM guests WHERE guest_id = %s", (booking["guest_id"],)
    )
    guest = await cur.fetchone()
    if not guest or not guest["user_id"]:
        return 0

    cur = await conn.execute(
        "SELECT fn_folio_paid(f.folio_id) AS paid FROM folios f WHERE f.booking_id = %s ORDER BY f.folio_id DESC LIMIT 1",
        (booking["booking_id"],),
    )
    folio = await cur.fetchone()
    paid = float(folio["paid"] or 0) if folio else 0
    percent = await _setting_number(conn, "loyalty.earn_percent", 5)
    points = int(paid * percent / 100)
    if points <= 0:
        return 0

    await conn.execute(
        """
        INSERT INTO loyalty_accounts (user_id, points_balance, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (user_id) DO UPDATE
        SET points_balance = loyalty_accounts.points_balance + EXCLUDED.points_balance,
            updated_at = now()
        """,
        (guest["user_id"], points),
    )
    await conn.execute(
        """
        INSERT INTO loyalty_transactions (user_id, points, transaction_type, description, booking_id)
        VALUES (%s, %s, 'EARN', %s, %s)
        """,
        (guest["user_id"], points, f"Начисление за проживание #{booking['booking_id']}", booking["booking_id"]),
    )
    return points


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
    booking = await get_booking(conn, booking_id)
    await notify_guest_by_booking(
        conn,
        booking,
        "BOOKING_CONFIRMED",
        "Бронь подтверждена",
        f"Ваша бронь #{booking_id} подтверждена. Заезд {booking['checkin_date']}, выезд {booking['checkout_date']}.",
    )
    await publish("bookings", {"id": booking_id, "status": "CONFIRMED"})
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
    await publish("bookings", {"id": booking_id, "status": "CANCELLED"})
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
    booking = await get_booking(conn, booking_id)
    await notify_guest_by_booking(
        conn,
        booking,
        "CHECKED_IN",
        "Счастливого проживания!",
        f"Вы заселены в номер {booking['room_number']}.",
    )
    await publish("bookings", {"id": booking_id, "status": "CHECKED_IN"})
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
    booking = await get_booking(conn, booking_id)
    await _award_loyalty_points(conn, booking)
    await notify_guest_by_booking(
        conn,
        booking,
        "CHECKED_OUT",
        "Спасибо за визит!",
        f"Счёт по брони #{booking_id} закрыт. Будем рады видеть вас снова.",
    )
    await publish("bookings", {"id": booking_id, "status": "CHECKED_OUT"})
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
    await publish("bookings", {"id": booking_id, "status": "MOVED"})
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
    idempotency_key = request.headers.get("idempotency-key")
    if idempotency_key:
        cur = await conn.execute(
            "SELECT response FROM idempotency_keys WHERE key = %s AND endpoint = 'manager.payments'",
            (idempotency_key,),
        )
        existing = await cur.fetchone()
        if existing and existing["response"]:
            return existing["response"]

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
    result = {"payment_id": (await cur.fetchone())["payment_id"]}
    if idempotency_key:
        await conn.execute(
            """
            INSERT INTO idempotency_keys (key, user_id, endpoint, response)
            VALUES (%s, %s, 'manager.payments', %s)
            ON CONFLICT (key) DO NOTHING
            """,
            (idempotency_key, user["user_id"], Jsonb(result)),
        )
    return result


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
    await publish("rooms", {"id": room_id, "status": payload.status_name})
    return {"ok": True}


@router.get("/waitlist")
async def waitlist(
    status: str | None = None,
    search: str | None = None,
    user: dict = Depends(require_permission("bookings:view")),
    conn: AsyncConnection = Depends(get_db),
):
    clauses: list[str] = []
    params: list = []
    if status:
        clauses.append("w.status = %s")
        params.append(status)
    if search:
        like = f"%{search}%"
        clauses.append("(w.guest_name ILIKE %s OR w.email ILIKE %s)")
        params.extend([like, like])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur = await conn.execute(
        f"""
        SELECT w.waitlist_id, w.guest_name, w.email, w.phone_masked,
               w.room_type_id, rt.name AS room_type,
               w.checkin_date, w.checkout_date, w.adults, w.children,
               w.note, w.status, w.created_at, w.notified_at,
               w.processed_at, u.full_name AS processed_by_name
        FROM waitlist_entries w
        LEFT JOIN room_types rt ON rt.room_type_id = w.room_type_id
        LEFT JOIN users u ON u.user_id = w.processed_by
        {where}
        ORDER BY w.status = 'WAITING' DESC, w.checkin_date, w.created_at
        """,
        tuple(params),
    )
    return rows_to_dicts(await cur.fetchall())


@router.patch("/waitlist/{waitlist_id}")
async def update_waitlist(
    waitlist_id: int,
    payload: WaitlistUpdate,
    request: Request,
    user: dict = Depends(require_permission("bookings:update")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        UPDATE waitlist_entries
        SET status = %s,
            note = COALESCE(%s, note),
            notified_at = CASE WHEN %s = 'NOTIFIED' THEN now() ELSE notified_at END,
            processed_by = %s,
            processed_at = CASE WHEN %s IN ('CONVERTED','CANCELLED') THEN now() ELSE processed_at END
        WHERE waitlist_id = %s
        RETURNING waitlist_id, status, note, notified_at, processed_at
        """,
        (
            payload.status,
            payload.note,
            payload.status,
            user["user_id"],
            payload.status,
            waitlist_id,
        ),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Запись листа ожидания не найдена")
    return dict(row)


@router.get("/search")
async def global_search(
    q: str = Query(min_length=1, max_length=100),
    user: dict = Depends(require_permission("bookings:view")),
    conn: AsyncConnection = Depends(get_db),
):
    like = f"%{q}%"
    bookings_cur = await conn.execute(
        """
        SELECT b.booking_id, b.checkin_date, b.checkout_date, b.status,
               g.full_name AS guest_name, r.room_number, rt.name AS room_type
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        WHERE g.full_name ILIKE %s OR g.email ILIKE %s OR r.room_number ILIKE %s
           OR CAST(b.booking_id AS TEXT) ILIKE %s
        ORDER BY b.booking_id DESC LIMIT 10
        """,
        (like, like, like, like),
    )
    guests_cur = await conn.execute(
        """
        SELECT g.guest_id, g.full_name, g.email, g.phone AS phone_masked,
               (SELECT count(*) FROM bookings b WHERE b.guest_id = g.guest_id) AS bookings_count
        FROM guests g
        WHERE g.full_name ILIKE %s OR g.email ILIKE %s
        ORDER BY g.guest_id DESC LIMIT 10
        """,
        (like, like),
    )
    rooms_cur = await conn.execute(
        """
        SELECT r.room_id, r.room_number, r.floor, rt.name AS room_type, rs.name AS status
        FROM rooms r
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        WHERE r.room_number ILIKE %s OR rt.name ILIKE %s
        ORDER BY r.room_number LIMIT 10
        """,
        (like, like),
    )
    return {
        "bookings": rows_to_dicts(await bookings_cur.fetchall()),
        "guests": rows_to_dicts(await guests_cur.fetchall()),
        "rooms": rows_to_dicts(await rooms_cur.fetchall()),
    }


@router.get("/floor-plan")
async def floor_plan(
    user: dict = Depends(require_permission("rooms:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT r.room_id, r.room_number, r.floor, rt.name AS room_type, rt.capacity,
               rs.name AS status,
               b.booking_id, b.checkin_date, b.checkout_date, b.status AS booking_status,
               g.full_name AS guest_name
        FROM rooms r
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        LEFT JOIN bookings b ON b.room_id = r.room_id
            AND b.status IN ('CONFIRMED','CHECKED_IN')
            AND CURRENT_DATE BETWEEN b.checkin_date AND b.checkout_date - 1
        LEFT JOIN guests g ON g.guest_id = b.guest_id
        ORDER BY r.floor, r.room_number
        """
    )
    rooms = rows_to_dicts(await cur.fetchall())
    floors: dict[int, list] = {}
    for room in rooms:
        floors.setdefault(room["floor"], []).append(room)
    return [{"floor": floor, "rooms": items} for floor, items in sorted(floors.items())]


@router.get("/events")
async def events(
    request: Request,
    token: str = Query(default=None),
    conn: AsyncConnection = Depends(get_db),
):
    user = None
    if token:
        try:
            payload = decode_access_token(token)
            uid = int(payload["sub"])
            cur = await conn.execute(
                """
                SELECT u.user_id, u.role_id, r.name AS role_name
                FROM users u JOIN roles r ON r.role_id = u.role_id
                WHERE u.user_id = %s AND u.is_active
                """,
                (uid,),
            )
            row = await cur.fetchone()
            if row:
                user = dict(row)
                user["role_code"] = role_code(row["role_name"])
        except Exception:
            user = None
    if not user or user["role_code"] == "GUEST":
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    async def generator():
        queue = subscribe()
        try:
            yield "data: " + json.dumps({"type": "connected"}, ensure_ascii=False) + "\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            unsubscribe(queue)

    return StreamingResponse(generator(), media_type="text/event-stream")


@router.post("/bookings/bulk")
async def bulk_booking_action(
    payload: BulkBookingAction,
    request: Request,
    user: dict = Depends(require_permission("bookings:update")),
    conn: AsyncConnection = Depends(get_db),
):
    results = []
    for booking_id in payload.ids:
        try:
            if payload.action == "confirm":
                await conn.execute(
                    "CALL sp_confirm_booking(%s::integer, %s::integer, %s::varchar)",
                    (booking_id, user["user_id"], request.client.host if request.client else ""),
                )
                results.append({"booking_id": booking_id, "status": "CONFIRMED"})
            else:
                await conn.execute(
                    "CALL sp_cancel_booking(%s::integer, NULL, %s::integer, %s::varchar)",
                    (booking_id, user["user_id"], request.client.host if request.client else ""),
                )
                results.append({"booking_id": booking_id, "status": "CANCELLED"})
        except Exception:
            results.append({"booking_id": booking_id, "error": True})
    await publish("bookings", {"action": payload.action, "ids": payload.ids})
    return {"results": results}


@router.get("/message-templates")
async def message_templates(
    user: dict = Depends(require_permission("bookings:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM message_templates ORDER BY name")
    return rows_to_dicts(await cur.fetchall())


@router.post("/guests/{guest_id}/notify")
async def notify_guest_manual(
    guest_id: int,
    payload: TemplateSendRequest,
    user: dict = Depends(require_permission("bookings:update")),
    conn: AsyncConnection = Depends(get_db),
):
    subject = payload.subject
    body = payload.body
    if payload.template_id:
        cur = await conn.execute(
            "SELECT * FROM message_templates WHERE template_id = %s", (payload.template_id,)
        )
        template = await cur.fetchone()
        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
        subject = subject or template["subject"]
        body = body or template["body"]
    if not subject or not body:
        raise HTTPException(status_code=400, detail="Укажите тему и текст сообщения")

    from ..notifications import notify_guest
    await notify_guest(conn, guest_id, "MANUAL", subject, body)
    return {"ok": True}

@router.post("/waitlist/{waitlist_id}/convert")
async def convert_waitlist(
    waitlist_id: int,
    payload: WaitlistConvertRequest,
    request: Request,
    user: dict = Depends(require_permission("bookings:create")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "SELECT * FROM waitlist_entries WHERE waitlist_id = %s AND status IN ('WAITING','NOTIFIED')",
        (waitlist_id,),
    )
    entry = await cur.fetchone()
    if not entry:
        raise HTTPException(status_code=404, detail="Заявка не найдена или уже обработана")

    checkin = payload.checkin_date or entry["checkin_date"]
    checkout = payload.checkout_date or entry["checkout_date"]
    document = document_fields(payload.document_number)

    cur = await conn.execute(
        "SELECT guest_id FROM guests WHERE document_number_hash = %s",
        (document["document_number_hash"],),
    )
    existing = await cur.fetchone()
    if existing:
        guest_id = existing["guest_id"]
    else:
        cur = await conn.execute(
            """
            INSERT INTO guests (
                full_name, document_number, document_number_enc, document_number_hash,
                phone, phone_enc, phone_hash, email, pdn_consent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING guest_id
            """,
            (
                entry["guest_name"],
                document["document_number"],
                document["document_number_enc"],
                document["document_number_hash"],
                entry["phone_masked"],
                entry["phone_enc"],
                entry["phone_hash"],
                entry["email"],
            ),
        )
        guest_id = (await cur.fetchone())["guest_id"]

    cur = await conn.execute(
        """
        SELECT fn_create_booking(
            %s::integer, %s::integer, %s::integer, %s::date, %s::date,
            NULL, 'PHONE', %s::integer, %s::integer, %s::integer, %s::varchar
        ) AS booking_id
        """,
        (
            guest_id,
            payload.room_id,
            payload.rate_id,
            checkin,
            checkout,
            entry["adults"],
            entry["children"],
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    booking_id = (await cur.fetchone())["booking_id"]
    await conn.execute(
        """
        UPDATE waitlist_entries
        SET status = 'CONVERTED', converted_booking_id = %s,
            processed_by = %s, processed_at = now()
        WHERE waitlist_id = %s
        """,
        (booking_id, user["user_id"], waitlist_id),
    )
    booking = await get_booking(conn, booking_id)
    await notify_guest_by_booking(
        conn,
        booking,
        "BOOKING_CREATED",
        "Бронь создана",
        f"Ваша бронь #{booking_id} создана по листу ожидания.",
    )
    await publish("bookings", {"id": booking_id, "status": "NEW"})
    return booking


@router.post("/notifications/send")
async def send_mass_notification(
    payload: MassSendRequest,
    user: dict = Depends(require_permission("bookings:update")),
    conn: AsyncConnection = Depends(get_db),
):
    subject = payload.subject
    body = payload.body
    if payload.template_id:
        cur = await conn.execute(
            "SELECT * FROM message_templates WHERE template_id = %s", (payload.template_id,)
        )
        template = await cur.fetchone()
        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
        subject = subject or template["subject"]
        body = body or template["body"]
    if not subject or not body:
        raise HTTPException(status_code=400, detail="Укажите тему и текст сообщения")

    sent = 0
    for guest_id in payload.guest_ids:
        if await notify_guest(conn, guest_id, "MANUAL", subject, body):
            sent += 1
    return {"ok": True, "sent": sent}
