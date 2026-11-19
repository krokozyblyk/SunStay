from __future__ import annotations

from datetime import date, datetime, time as dtime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from psycopg import AsyncConnection

from ..db import get_db
from ..deps import get_current_user, require_permission
from ..notifications import notify_guest_by_booking
from ..schemas import ChangeBookingRequest, ReviewCreate, ServiceOrderCreate, SpecialRequestsUpdate
from ..services.pdf import folio_pdf
from ..services.voucher import booking_voucher_pdf
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
               fn_booking_balance(b.booking_id) AS balance,
               rv.status AS review_status
        FROM bookings b
        JOIN rooms r ON r.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        LEFT JOIN reviews rv ON rv.booking_id = b.booking_id
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
    cur = await conn.execute(
        "SELECT review_id, rating, title, body, status, created_at FROM reviews WHERE booking_id = %s",
        (booking_id,),
    )
    review = await cur.fetchone()

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
        "review": review,
        "timeline": timeline,
    }


async def _setting_number(conn: AsyncConnection, key: str, default: float) -> float:
    cur = await conn.execute("SELECT value FROM system_settings WHERE key = %s", (key,))
    row = await cur.fetchone()
    try:
        return float(row["value"]) if row else default
    except (TypeError, ValueError):
        return default


async def _cancellation_quote(conn: AsyncConnection, booking: dict) -> dict:
    free_hours = await _setting_number(conn, "cancellation.free_hours", 48)
    half_hours = await _setting_number(conn, "cancellation.half_hours", 24)
    half_percent = await _setting_number(conn, "cancellation.half_percent", 50)

    checkin = date.fromisoformat(str(booking["checkin_date"])[:10])
    arrival = booking.get("arrival_time")
    hour, minute = 14, 0
    if arrival:
        parts = str(arrival)[:5].split(":")
        if len(parts) == 2:
            hour, minute = int(parts[0]), int(parts[1])
    checkin_at = datetime.combine(checkin, dtime(hour, minute))
    hours_left = max(0.0, (checkin_at - datetime.now()).total_seconds() / 3600)

    if hours_left >= free_hours:
        percent = 100
    elif hours_left >= half_hours:
        percent = half_percent
    else:
        percent = 0

    cur = await conn.execute(
        """
        SELECT COALESCE((
            SELECT fn_folio_paid(f.folio_id)
            FROM folios f WHERE f.booking_id = %s
            ORDER BY f.folio_id DESC LIMIT 1
        ), 0) AS paid
        """,
        (booking["booking_id"],),
    )
    paid = float((await cur.fetchone())["paid"] or 0)
    refund = round(paid * percent / 100, 2)
    return {
        "hours_left": round(hours_left, 1),
        "percent": percent,
        "paid": paid,
        "refund": refund,
        "free_hours": free_hours,
        "half_hours": half_hours,
        "half_percent": half_percent,
    }


async def _refund_booking(conn: AsyncConnection, booking_id: int, amount: float, user_id: int, ip: str) -> float:
    if amount <= 0:
        return 0
    cur = await conn.execute(
        """
        SELECT p.payment_id,
               p.amount - COALESCE((SELECT SUM(r.amount) FROM refunds r WHERE r.payment_id = p.payment_id), 0) AS available
        FROM payments p
        JOIN folios f ON f.folio_id = p.folio_id
        WHERE f.booking_id = %s
        ORDER BY p.payment_id DESC
        """,
        (booking_id,),
    )
    remaining = amount
    refunded = 0.0
    for row in await cur.fetchall():
        available = float(row["available"] or 0)
        if available <= 0:
            continue
        take = min(available, remaining)
        await conn.execute(
            "SELECT fn_refund_payment(%s::integer, %s::numeric, %s::varchar, %s::integer, %s::varchar)",
            (row["payment_id"], take, "Отмена брони", user_id, ip),
        )
        refunded += take
        remaining -= take
        if remaining <= 0.01:
            break
    return round(refunded, 2)


@router.get("/bookings/{booking_id}/cancellation-quote")
async def cancellation_quote(
    booking_id: int,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")
    if booking["status"] not in ("NEW", "CONFIRMED"):
        raise HTTPException(status_code=400, detail="Эту бронь нельзя отменить")
    return await _cancellation_quote(conn, booking)


@router.patch("/bookings/{booking_id}/requests")
async def update_special_requests(
    booking_id: int,
    payload: SpecialRequestsUpdate,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")
    if booking["status"] in ("CANCELLED", "CHECKED_OUT", "NO_SHOW"):
        raise HTTPException(status_code=400, detail="Для этой брони пожелания недоступны")
    await conn.execute(
        "UPDATE bookings SET special_requests = %s WHERE booking_id = %s",
        (payload.special_requests, booking_id),
    )
    return {"ok": True, "special_requests": payload.special_requests}


@router.get("/bookings/{booking_id}/price-breakdown")
async def price_breakdown(
    booking_id: int,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")
    checkin = date.fromisoformat(str(booking["checkin_date"])[:10])
    checkout = date.fromisoformat(str(booking["checkout_date"])[:10])
    nights = max(0, (checkout - checkin).days)
    rate_price = float(booking.get("price_per_night") or 0)
    room_total = round(rate_price * nights, 2)
    cur = await conn.execute(
        "SELECT fn_calculate_stay_price(%s::integer, %s::date, %s::date, %s::integer) AS total",
        (booking["rate_id"], booking["checkin_date"], booking["checkout_date"], booking.get("promo_id")),
    )
    promo_total = float((await cur.fetchone())["total"] or 0)
    promo_discount = round(max(0, room_total - promo_total), 2)
    cur = await conn.execute(
        """
        SELECT COALESCE(SUM(so.quantity * s.price), 0) AS services_total
        FROM service_orders so JOIN services s ON s.service_id = so.service_id
        WHERE so.booking_id = %s
        """,
        (booking_id,),
    )
    services_total = float((await cur.fetchone())["services_total"] or 0)
    cur = await conn.execute(
        """
        SELECT COALESCE(SUM(fl.amount), 0) AS discount_total
        FROM folio_lines fl JOIN folios f ON f.folio_id = fl.folio_id
        WHERE f.booking_id = %s AND fl.line_type = 'DISCOUNT'
        """,
        (booking_id,),
    )
    loyalty_discount = round(abs(float((await cur.fetchone())["discount_total"] or 0)), 2)
    total = round(room_total - promo_discount - loyalty_discount + services_total, 2)
    return {
        "nights": nights,
        "rate_name": booking.get("rate_name"),
        "price_per_night": rate_price,
        "room_total": room_total,
        "promo_discount": promo_discount,
        "loyalty_discount": loyalty_discount,
        "services_total": round(services_total, 2),
        "total": total,
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
    quote = await _cancellation_quote(conn, booking)
    ip = request.client.host if request.client else ""
    refunded = await _refund_booking(conn, booking_id, quote["refund"], user["user_id"], ip)
    await conn.execute(
        "CALL sp_cancel_booking(%s::integer, %s::integer, %s::integer, %s::varchar)",
        (booking_id, reason_id, user["user_id"], ip),
    )
    return {"ok": True, "status": "CANCELLED", "refunded": refunded, "quote": quote}


@router.post("/reviews")
async def create_review(
    payload: ReviewCreate,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, payload.booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")
    if booking["status"] != "CHECKED_OUT":
        raise HTTPException(status_code=400, detail="Отзыв можно оставить после выезда")

    cur = await conn.execute(
        """
        INSERT INTO reviews (booking_id, guest_id, rating, title, body)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (booking_id) DO NOTHING
        RETURNING review_id, status, created_at
        """,
        (
            payload.booking_id,
            user["guest_id"],
            payload.rating,
            payload.title,
            payload.body,
        ),
    )
    review = await cur.fetchone()
    if not review:
        raise HTTPException(status_code=409, detail="Отзыв по этой брони уже оставлен")
    return dict(review)


@router.get("/reviews")
async def my_reviews(user: dict = Depends(require_guest), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT review_id, booking_id, rating, title, body, status, created_at
        FROM reviews WHERE guest_id = %s ORDER BY created_at DESC
        """,
        (user["guest_id"],),
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/notifications")
async def notifications(
    limit: int = Query(30, ge=1, le=100),
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT notification_id, notification_type, title, body, link, read_at, created_at
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user["user_id"], limit),
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/notifications/unread-count")
async def unread_count(user: dict = Depends(require_guest), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        "SELECT count(*) AS count FROM notifications WHERE user_id = %s AND read_at IS NULL",
        (user["user_id"],),
    )
    return {"count": (await cur.fetchone())["count"]}


@router.post("/notifications/{notification_id}/read")
async def read_notification(
    notification_id: int,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "UPDATE notifications SET read_at = now() WHERE notification_id = %s AND user_id = %s",
        (notification_id, user["user_id"]),
    )
    return {"ok": True}


@router.post("/notifications/read-all")
async def read_all_notifications(user: dict = Depends(require_guest), conn: AsyncConnection = Depends(get_db)):
    await conn.execute(
        "UPDATE notifications SET read_at = now() WHERE user_id = %s AND read_at IS NULL",
        (user["user_id"],),
    )
    return {"ok": True}


@router.get("/loyalty")
async def loyalty(user: dict = Depends(require_guest), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        INSERT INTO loyalty_accounts (user_id, points_balance)
        VALUES (%s, 0)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user["user_id"],),
    )
    cur = await conn.execute(
        "SELECT points_balance FROM loyalty_accounts WHERE user_id = %s",
        (user["user_id"],),
    )
    balance = (await cur.fetchone())["points_balance"]
    cur = await conn.execute(
        """
        SELECT transaction_id, points, transaction_type, description, booking_id, created_at
        FROM loyalty_transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (user["user_id"],),
    )
    return {"points_balance": balance, "transactions": rows_to_dicts(await cur.fetchall())}


@router.post("/bookings/{booking_id}/change")
async def change_booking_dates(
    booking_id: int,
    payload: ChangeBookingRequest,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    if payload.checkout_date <= payload.checkin_date:
        raise HTTPException(status_code=400, detail="Дата выезда должна быть позже даты заезда")
    if payload.checkin_date < date.today():
        raise HTTPException(status_code=400, detail="Дата заезда уже прошла")

    booking = await get_booking(conn, booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")
    if booking["status"] not in ("NEW", "CONFIRMED"):
        raise HTTPException(status_code=400, detail="Даты можно изменить только для новой или подтверждённой брони")

    cur = await conn.execute(
        """
        SELECT 1
        FROM bookings b
        WHERE b.room_id = %s
          AND b.booking_id <> %s
          AND b.status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND b.checkin_date < %s
          AND b.checkout_date > %s
        LIMIT 1
        """,
        (booking["room_id"], booking_id, payload.checkout_date, payload.checkin_date),
    )
    if await cur.fetchone():
        raise HTTPException(status_code=409, detail="Номер занят на выбранные даты")

    cur = await conn.execute(
        """
        SELECT rate_id
        FROM rate_plans
        WHERE room_type_id = (SELECT room_type_id FROM rooms WHERE room_id = %s)
          AND %s >= season_start
          AND %s - 1 <= season_end
        ORDER BY price_per_night
        LIMIT 1
        """,
        (booking["room_id"], payload.checkin_date, payload.checkout_date),
    )
    rate = await cur.fetchone()
    if not rate:
        raise HTTPException(status_code=400, detail="Нет тарифа на выбранные даты")

    cur = await conn.execute(
        """
        UPDATE bookings
        SET checkin_date = %s,
            checkout_date = %s,
            rate_id = %s,
            hold_until = CASE
                WHEN arrival_time IS NOT NULL THEN (%s::date + arrival_time + (hold_minutes || ' minutes')::interval)
                ELSE (%s::date + (hold_minutes || ' minutes')::interval)
            END
        WHERE booking_id = %s
        RETURNING booking_id
        """,
        (
            payload.checkin_date,
            payload.checkout_date,
            rate["rate_id"],
            payload.checkin_date,
            payload.checkin_date,
            booking_id,
        ),
    )
    await notify_guest_by_booking(
        conn,
        booking,
        "BOOKING_CHANGED",
        "Даты бронирования изменены",
        f"Новые даты: {payload.checkin_date} — {payload.checkout_date}",
    )
    return await get_booking(conn, booking_id)


@router.get("/bookings/{booking_id}/voucher.pdf")
async def booking_voucher(
    booking_id: int,
    user: dict = Depends(require_guest),
    conn: AsyncConnection = Depends(get_db),
):
    booking = await get_booking(conn, booking_id)
    if booking.get("guest_id") != user["guest_id"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой брони")
    cur = await conn.execute(
        "SELECT full_name FROM guests WHERE guest_id = %s", (user["guest_id"],)
    )
    guest = await cur.fetchone()
    pdf = booking_voucher_pdf(booking, guest or {})
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="voucher-{booking_id}.pdf"'},
    )


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
