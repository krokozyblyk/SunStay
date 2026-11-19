from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg import AsyncConnection

from ..audit import write_audit_event
from ..crypto import document_fields, phone_fields
from ..db import get_db
from ..deps import get_optional_user
from ..notifications import notify_guest_by_booking
from ..schemas import PublicBookingCreate, WaitlistCreate
from ..utils import get_booking, row_to_dict, rows_to_dicts

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/config")
async def public_config(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute("SELECT key, value FROM system_settings WHERE key LIKE 'feature.%'")
    flags = {row["key"].replace("feature.", ""): bool(row["value"]) for row in await cur.fetchall()}
    return {"features": flags}


@router.get("/room-types")
async def room_types(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT
            rt.room_type_id,
            rt.name,
            rt.capacity,
            rt.description,
            rt.image_url,
            (SELECT MIN(rp.price_per_night)
             FROM rate_plans rp
             WHERE rp.room_type_id = rt.room_type_id) AS min_price,
            (SELECT COUNT(*) FROM rooms r WHERE r.room_type_id = rt.room_type_id) AS rooms_count,
            (SELECT COALESCE(json_agg(DISTINCT a.name), '[]'::json)
             FROM rooms r
             JOIN room_amenities ra ON ra.room_id = r.room_id
             JOIN amenities a ON a.amenity_id = ra.amenity_id
             WHERE r.room_type_id = rt.room_type_id) AS amenities
        FROM room_types rt
        ORDER BY rt.room_type_id
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/cancellation-reasons")
async def cancellation_reasons(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute("SELECT * FROM cancellation_reasons ORDER BY reason_id")
    return rows_to_dicts(await cur.fetchall())


@router.get("/services")
async def services(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT s.service_id, s.name, s.price, s.image_url, su.name AS unit
        FROM services s
        JOIN service_units su ON su.unit_id = s.unit_id
        ORDER BY s.service_id
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/rooms")
async def rooms(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT
            r.room_id, r.room_number, r.floor,
            rt.room_type_id, rt.name AS room_type, rt.capacity,
            rs.name AS status
        FROM rooms r
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        ORDER BY r.room_number
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/calendar")
async def calendar(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    room_type_id: int | None = None,
    conn: AsyncConnection = Depends(get_db),
):
    today = date.today()
    if month:
        try:
            first = date.fromisoformat(f"{month}-01")
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат месяца")
    else:
        first = today.replace(day=1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    last = next_month - timedelta(days=1)

    cur = await conn.execute(
        """
        WITH days AS (
            SELECT generate_series(%s::date, %s::date, interval '1 day')::date AS day
        ),
        types AS (
            SELECT room_type_id FROM room_types
            WHERE %s::integer IS NULL OR room_type_id = %s::integer
        )
        SELECT
            d.day,
            (SELECT MIN(rp.price_per_night)
             FROM rate_plans rp
             JOIN types t ON t.room_type_id = rp.room_type_id
             WHERE d.day BETWEEN rp.season_start AND rp.season_end) AS min_price,
            (SELECT COUNT(*)
             FROM rooms r
             JOIN types t ON t.room_type_id = r.room_type_id
             WHERE fn_room_available(r.room_id, d.day, d.day + 1)) AS available_rooms
        FROM days d
        ORDER BY d.day
        """,
        (first, last, room_type_id, room_type_id),
    )
    rows = []
    for row in await cur.fetchall():
        item = dict(row)
        item["is_past"] = item["day"] < today
        item["min_price"] = float(item["min_price"] or 0)
        rows.append(item)
    return {"month": first.strftime("%Y-%m"), "days": rows}


@router.get("/reviews")
async def public_reviews(limit: int = Query(6, ge=1, le=30), conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        """
        SELECT
            r.review_id, r.rating, r.title, r.body, r.created_at,
            split_part(g.full_name, ' ', 1) || ' ' ||
                COALESCE(left(split_part(g.full_name, ' ', 2), 1) || '.', '') AS guest_name,
            rt.name AS room_type
        FROM reviews r
        JOIN guests g ON g.guest_id = r.guest_id
        JOIN bookings b ON b.booking_id = r.booking_id
        JOIN rooms rm ON rm.room_id = b.room_id
        JOIN room_types rt ON rt.room_type_id = rm.room_type_id
        WHERE r.status = 'APPROVED'
        ORDER BY r.created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/currencies")
async def currencies(conn: AsyncConnection = Depends(get_db)):
    cur = await conn.execute(
        "SELECT key, value FROM system_settings WHERE key IN ('currency.usd_rate','currency.eur_rate')"
    )
    values = {row["key"]: row["value"] for row in await cur.fetchall()}
    return {
        "base": "RUB",
        "rates": {
            "RUB": 1,
            "USD": float(values.get("currency.usd_rate") or 90),
            "EUR": float(values.get("currency.eur_rate") or 100),
        },
    }


@router.post("/waitlist")
async def create_waitlist(
    payload: WaitlistCreate,
    conn: AsyncConnection = Depends(get_db),
):
    if payload.checkout_date <= payload.checkin_date:
        raise HTTPException(status_code=400, detail="Дата выезда должна быть позже даты заезда")
    if payload.checkin_date < date.today():
        raise HTTPException(status_code=400, detail="Дата заезда уже прошла")

    phone = phone_fields(payload.phone)
    cur = await conn.execute(
        """
        INSERT INTO waitlist_entries (
            guest_name, email, phone_masked, phone_enc, phone_hash,
            room_type_id, checkin_date, checkout_date, adults, children, note
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING waitlist_id, status, created_at
        """,
        (
            payload.full_name,
            payload.email,
            phone["phone"],
            phone["phone_enc"],
            phone["phone_hash"],
            payload.room_type_id,
            payload.checkin_date,
            payload.checkout_date,
            payload.adults,
            payload.children,
            payload.note,
        ),
    )
    return dict(await cur.fetchone())


@router.get("/availability")
async def availability(
    checkin: date = Query(...),
    checkout: date = Query(...),
    guests: int = Query(1, ge=1),
    room_type_id: int | None = None,
    conn: AsyncConnection = Depends(get_db),
):
    if checkout <= checkin:
        raise HTTPException(status_code=400, detail="Дата выезда должна быть позже даты заезда")

    params: list = [checkin, checkout, checkin, checkout, guests]
    type_filter = ""
    if room_type_id:
        type_filter = "AND rt.room_type_id = %s"
        params.append(room_type_id)

    cur = await conn.execute(
        f"""
        SELECT * FROM (
            SELECT
                rt.room_type_id,
                rt.name,
                rt.capacity,
                rt.description,
                rt.image_url,
                (SELECT MIN(rp.price_per_night)
                 FROM rate_plans rp
                 WHERE rp.room_type_id = rt.room_type_id
                   AND %s >= rp.season_start
                   AND %s - 1 <= rp.season_end) AS price_per_night,
                (SELECT COUNT(*)
                 FROM rooms r
                 WHERE r.room_type_id = rt.room_type_id
                   AND fn_room_available(r.room_id, %s, %s)) AS available_rooms,
                (SELECT COALESCE(json_agg(json_build_object(
                        'room_id', r.room_id,
                        'room_number', r.room_number,
                        'rate_id', rp.rate_id,
                        'price_per_night', rp.price_per_night
                    ) ORDER BY r.room_number), '[]'::json)
                 FROM rooms r
                 JOIN LATERAL (
                     SELECT rp.rate_id, rp.price_per_night
                     FROM rate_plans rp
                     WHERE rp.room_type_id = rt.room_type_id
                       AND %s >= rp.season_start
                       AND %s - 1 <= rp.season_end
                     ORDER BY rp.price_per_night
                     LIMIT 1
                 ) rp ON true
                 WHERE r.room_type_id = rt.room_type_id
                   AND fn_room_available(r.room_id, %s, %s)) AS rooms
            FROM room_types rt
            WHERE rt.capacity >= %s
            {type_filter}
        ) q
        WHERE q.available_rooms > 0
        ORDER BY q.price_per_night
        """,
        (
            checkin,
            checkout,
            checkin,
            checkout,
            checkin,
            checkout,
            checkin,
            checkout,
            *params[4:],
        ),
    )
    return rows_to_dicts(await cur.fetchall())


@router.get("/promo/{code}")
async def promo(code: str, checkin: date | None = None, conn: AsyncConnection = Depends(get_db)):
    target_date = checkin or date.today()
    cur = await conn.execute(
        """
        SELECT promo_id, code, discount_percent, valid_from, valid_to
        FROM promo_codes
        WHERE upper(code) = upper(%s)
          AND %s BETWEEN valid_from AND valid_to
        """,
        (code, target_date),
    )
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Промокод не действует")
    return row_to_dict(row)


async def _redeem_points(
    conn: AsyncConnection,
    user: dict,
    requested: int,
    total: float,
) -> int:
    cur = await conn.execute(
        "SELECT value FROM system_settings WHERE key = 'loyalty.redeem_max_percent'"
    )
    row = await cur.fetchone()
    try:
        max_percent = float(row["value"]) if row else 30
    except (TypeError, ValueError):
        max_percent = 30
    cap = total * max_percent / 100

    cur = await conn.execute(
        "SELECT points_balance FROM loyalty_accounts WHERE user_id = %s", (user["user_id"],)
    )
    account = await cur.fetchone()
    balance = int(account["points_balance"]) if account else 0

    points = min(int(requested), balance, int(cap))
    if points <= 0:
        return 0

    await conn.execute(
        """
        UPDATE loyalty_accounts
        SET points_balance = points_balance - %s, updated_at = now()
        WHERE user_id = %s
        """,
        (points, user["user_id"]),
    )
    await conn.execute(
        """
        INSERT INTO loyalty_transactions (user_id, points, transaction_type, description)
        VALUES (%s, %s, 'REDEEM', %s)
        """,
        (user["user_id"], points, "Списание баллов при бронировании"),
    )
    return points


async def find_or_create_guest(conn: AsyncConnection, payload: PublicBookingCreate) -> int:
    document = document_fields(payload.document_number)
    phone = phone_fields(payload.phone)

    cur = await conn.execute(
        "SELECT guest_id FROM guests WHERE document_number_hash = %s",
        (document["document_number_hash"],),
    )
    row = await cur.fetchone()
    if row:
        await conn.execute(
            """
            UPDATE guests
            SET full_name = %s,
                phone = COALESCE(%s, phone),
                phone_enc = COALESCE(%s, phone_enc),
                phone_hash = COALESCE(%s, phone_hash),
                email = COALESCE(%s, email),
                pdn_consent = pdn_consent OR %s
            WHERE guest_id = %s
            """,
            (
                payload.full_name,
                phone["phone"],
                phone["phone_enc"],
                phone["phone_hash"],
                payload.email,
                payload.pdn_consent,
                row["guest_id"],
            ),
        )
        return row["guest_id"]

    if not payload.pdn_consent:
        raise HTTPException(status_code=400, detail="Нужно согласие на обработку персональных данных")

    cur = await conn.execute(
        """
        INSERT INTO guests (
            full_name, document_number, document_number_enc, document_number_hash,
            phone, phone_enc, phone_hash, email, pdn_consent
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING guest_id
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
    return (await cur.fetchone())["guest_id"]


@router.post("/bookings")
async def create_public_booking(
    payload: PublicBookingCreate,
    request: Request,
    conn: AsyncConnection = Depends(get_db),
    user: dict | None = Depends(get_optional_user),
):
    if not payload.pdn_consent:
        raise HTTPException(status_code=400, detail="Нужно согласие на обработку персональных данных")

    guest_id = await find_or_create_guest(conn, payload)

    cur = await conn.execute(
        """
        SELECT r.room_id, r.room_type_id
        FROM rooms r
        WHERE r.room_id = %s
        """,
        (payload.room_id,),
    )
    room = await cur.fetchone()
    if not room:
        raise HTTPException(status_code=404, detail="Номер не найден")

    rate_id = payload.rate_id
    cur = await conn.execute(
        """
        SELECT rate_id
        FROM rate_plans
        WHERE room_type_id = %s
          AND %s >= season_start
          AND %s - 1 <= season_end
        ORDER BY price_per_night
        LIMIT 1
        """,
        (room["room_type_id"], payload.checkin_date, payload.checkout_date),
    )
    rate = await cur.fetchone()
    if not rate:
        raise HTTPException(status_code=400, detail="Нет тарифа на выбранные даты")
    if not rate_id:
        rate_id = rate["rate_id"]

    promo_id = None
    if payload.promo_code:
        cur = await conn.execute(
            """
            SELECT promo_id
            FROM promo_codes
            WHERE upper(code) = upper(%s)
              AND %s BETWEEN valid_from AND valid_to
            """,
            (payload.promo_code, payload.checkin_date),
        )
        promo = await cur.fetchone()
        if not promo:
            raise HTTPException(status_code=400, detail="Промокод не действует")
        promo_id = promo["promo_id"]

    try:
        cur = await conn.execute(
            """
            SELECT fn_create_booking(
                %s::integer, %s::integer, %s::integer, %s::date, %s::date,
                %s::integer, %s::varchar, %s::integer, %s::integer, NULL, %s::varchar,
                %s::time, %s::integer
            ) AS booking_id
            """,
            (
                guest_id,
                payload.room_id,
                rate_id,
                payload.checkin_date,
                payload.checkout_date,
                promo_id,
                payload.source,
                payload.adults,
                payload.children,
                request.client.host if request.client else "",
                payload.arrival_time,
                payload.hold_minutes,
            ),
        )
        booking_id = (await cur.fetchone())["booking_id"]
        if payload.special_requests:
            await conn.execute(
                "UPDATE bookings SET special_requests = %s WHERE booking_id = %s",
                (payload.special_requests, booking_id),
            )
    except Exception as exc:
        await write_audit_event(
            user_id=None,
            table_name="bookings",
            action="ERROR",
            new_value={
                "guest_id": guest_id,
                "room_id": payload.room_id,
                "rate_id": rate_id,
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

    if payload.payment_method in ("ONLINE", "CARD"):
        cur = await conn.execute(
            """
            SELECT fn_calculate_stay_price(%s::integer, %s::date, %s::date, %s::integer) AS total
            """,
            (rate_id, payload.checkin_date, payload.checkout_date, promo_id),
        )
        total = float((await cur.fetchone())["total"])
        points_used = 0
        if payload.points_to_use > 0 and user and user["role_code"] == "GUEST":
            points_used = await _redeem_points(conn, user, payload.points_to_use, total)
        amount = (payload.payment_amount or total) - points_used
        if amount < 0:
            amount = 0

        cur = await conn.execute(
            """
            INSERT INTO folios (booking_id, status)
            VALUES (%s, 'OPEN')
            ON CONFLICT (booking_id) DO UPDATE SET status = 'OPEN'
            RETURNING folio_id
            """,
            (booking_id,),
        )
        folio_id = (await cur.fetchone())["folio_id"]
        if points_used > 0:
            await conn.execute(
                """
                INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date)
                VALUES (%s, %s, %s, 'DISCOUNT', CURRENT_DATE)
                """,
                (folio_id, f"Списание бонусных баллов", -points_used),
            )
        await conn.execute(
            """
            INSERT INTO payments (folio_id, amount, method, payment_type)
            VALUES (%s, %s, %s, 'DEPOSIT')
            """,
            (folio_id, amount, payload.payment_method),
        )
        await conn.execute(
            "CALL sp_confirm_booking(%s::integer, NULL, %s::varchar)",
            (booking_id, request.client.host if request.client else ""),
        )

    booking = await get_booking(conn, booking_id)
    await notify_guest_by_booking(
        conn,
        booking,
        "BOOKING_CREATED",
        "Бронь создана",
        f"Ваша бронь #{booking_id} создана. Заезд {booking['checkin_date']}.",
    )
    return booking
