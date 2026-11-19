-- =====================================================================================
--  SunStay: доработка check-out — гарантированное начисление всех ночей проживания
-- =====================================================================================

CREATE OR REPLACE PROCEDURE sp_check_out(
    p_booking_id INTEGER,
    p_manager_id INTEGER,
    p_payment_amount NUMERIC,
    p_payment_method VARCHAR,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_checkin DATE;
    v_checkout DATE;
    v_rate_id INTEGER;
    v_price NUMERIC(10,2);
    v_folio_id INTEGER;
    v_status_id INTEGER;
    d DATE;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_manager_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT room_id, checkin_date, checkout_date, rate_id
    INTO v_room_id, v_checkin, v_checkout, v_rate_id
    FROM bookings
    WHERE booking_id = p_booking_id
      AND status = 'CHECKED_IN';

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Выселение возможно только для заселённой брони';
    END IF;

    SELECT folio_id INTO v_folio_id
    FROM folios
    WHERE booking_id = p_booking_id AND status = 'OPEN'
    ORDER BY folio_id DESC
    LIMIT 1;

    IF v_folio_id IS NULL THEN
        RAISE EXCEPTION 'Открытый folio не найден';
    END IF;

    SELECT price_per_night INTO v_price
    FROM rate_plans
    WHERE rate_id = v_rate_id;

    FOR d IN
        SELECT generate_series(v_checkin, v_checkout - 1, interval '1 day')::date
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM folio_lines
            WHERE folio_id = v_folio_id
              AND line_type = 'ROOM'
              AND charge_date = d
        ) THEN
            INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date)
            VALUES (
                v_folio_id,
                'Проживание за ' || to_char(d, 'DD.MM.YYYY'),
                v_price,
                'ROOM',
                d
            );
        END IF;
    END LOOP;

    IF COALESCE(p_payment_amount, 0) > 0 THEN
        INSERT INTO payments (folio_id, amount, method, payment_type)
        VALUES (v_folio_id, p_payment_amount, COALESCE(p_payment_method, 'CARD'), 'PAYMENT');
    END IF;

    UPDATE folios
    SET status = 'CLOSED', closed_at = now()
    WHERE folio_id = v_folio_id;

    UPDATE bookings
    SET status = 'CHECKED_OUT'
    WHERE booking_id = p_booking_id;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'ГРЯЗНЫЙ';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;

    INSERT INTO housekeeping_tasks (room_id, staff_id, task_type, status, priority)
    VALUES (v_room_id, NULL, 'POST_CHECKOUT', 'ASSIGNED', 'HIGH');
END;
$$;
