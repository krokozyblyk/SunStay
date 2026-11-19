-- =====================================================================================
--  SunStay: безопасное заселение и удержание брони
-- =====================================================================================

DROP FUNCTION IF EXISTS fn_create_booking(INTEGER, INTEGER, INTEGER, DATE, DATE, INTEGER, VARCHAR, INTEGER, INTEGER, INTEGER, VARCHAR);

CREATE OR REPLACE FUNCTION fn_create_booking(
    p_guest_id INTEGER,
    p_room_id INTEGER,
    p_rate_id INTEGER,
    p_checkin DATE,
    p_checkout DATE,
    p_promo_id INTEGER,
    p_source VARCHAR,
    p_adults INTEGER,
    p_children INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR,
    p_arrival_time TIME DEFAULT NULL,
    p_hold_minutes INTEGER DEFAULT 60
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_booking_id INTEGER;
    v_arrival TIME;
    v_hold_until TIMESTAMPTZ;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    IF NOT fn_room_available(p_room_id, p_checkin, p_checkout) THEN
        RAISE EXCEPTION 'Номер недоступен на выбранные даты';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM guests WHERE guest_id = p_guest_id AND pdn_consent = TRUE
    ) THEN
        RAISE EXCEPTION 'Нет согласия гостя на обработку персональных данных';
    END IF;

    v_arrival := COALESCE(p_arrival_time, TIME '14:00');
    v_hold_until := (p_checkin::timestamp + v_arrival)
        + make_interval(mins => COALESCE(p_hold_minutes, 60));

    INSERT INTO bookings (
        guest_id, room_id, rate_id, promo_id,
        checkin_date, checkout_date, status, source,
        adults, children, arrival_time, hold_minutes, hold_until
    ) VALUES (
        p_guest_id, p_room_id, p_rate_id, p_promo_id,
        p_checkin, p_checkout, 'NEW', COALESCE(p_source, 'SITE'),
        COALESCE(p_adults, 1), COALESCE(p_children, 0),
        v_arrival, COALESCE(p_hold_minutes, 60), v_hold_until
    )
    RETURNING booking_id INTO v_booking_id;

    RETURN v_booking_id;
EXCEPTION
    WHEN exclusion_violation THEN
        RAISE EXCEPTION 'Номер уже забронирован на выбранные даты';
END;
$$;

CREATE OR REPLACE PROCEDURE sp_check_in_secure(
    p_booking_id INTEGER,
    p_manager_id INTEGER,
    p_document_masked VARCHAR,
    p_document_enc TEXT,
    p_document_hash VARCHAR,
    p_deposit_amount NUMERIC,
    p_payment_method VARCHAR,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_folio_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_manager_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT room_id INTO v_room_id
    FROM bookings
    WHERE booking_id = p_booking_id
      AND status = 'CONFIRMED';

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Заселение возможно только для подтверждённой брони';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        WHERE b.booking_id = p_booking_id
          AND g.document_number_hash = p_document_hash
    ) THEN
        RAISE EXCEPTION 'Документ не совпадает с данными гостя';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM rooms r
        JOIN room_statuses rs ON rs.status_id = r.status_id
        WHERE r.room_id = v_room_id AND rs.name = 'БЛОКИРОВАН'
    ) THEN
        RAISE EXCEPTION 'Номер заблокирован';
    END IF;

    INSERT INTO check_ins (
        booking_id, manager_id, guest_document_number,
        guest_document_number_enc, guest_document_number_hash
    ) VALUES (
        p_booking_id, p_manager_id, p_document_masked,
        p_document_enc, p_document_hash
    );

    UPDATE bookings SET status = 'CHECKED_IN' WHERE booking_id = p_booking_id;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'ЗАСЕЛЁН';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;

    INSERT INTO folios (booking_id, status)
    VALUES (p_booking_id, 'OPEN')
    ON CONFLICT (booking_id) DO NOTHING;

    SELECT folio_id INTO v_folio_id
    FROM folios
    WHERE booking_id = p_booking_id
    ORDER BY folio_id DESC
    LIMIT 1;

    IF COALESCE(p_deposit_amount, 0) > 0 THEN
        INSERT INTO payments (folio_id, amount, method, payment_type)
        VALUES (v_folio_id, p_deposit_amount, COALESCE(p_payment_method, 'CARD'), 'DEPOSIT');
    END IF;
END;
$$;
