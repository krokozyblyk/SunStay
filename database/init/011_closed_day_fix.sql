-- =====================================================================================
--  SunStay: закрытие бизнес-дня — разрешаем платежи после закрытия,
--  но запрещаем закрывать будущие даты.
-- =====================================================================================

CREATE OR REPLACE FUNCTION fn_prevent_closed_day() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_date DATE;
    v_closed_at TIMESTAMP;
BEGIN
    IF current_setting('app.bypass_closed_day', true) = 'on' THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;

    IF TG_OP = 'DELETE' THEN
        IF TG_TABLE_NAME = 'folio_lines' THEN
            v_date := COALESCE(OLD.charge_date, OLD.created_at::date);
        ELSIF TG_TABLE_NAME = 'payments' THEN
            v_date := OLD.paid_at::date;
        ELSIF TG_TABLE_NAME = 'refunds' THEN
            v_date := OLD.refunded_at::date;
        END IF;
    ELSE
        IF TG_TABLE_NAME = 'folio_lines' THEN
            v_date := COALESCE(NEW.charge_date, NEW.created_at::date);
        ELSIF TG_TABLE_NAME = 'payments' THEN
            v_date := NEW.paid_at::date;
        ELSIF TG_TABLE_NAME = 'refunds' THEN
            v_date := NEW.refunded_at::date;
        END IF;
    END IF;

    IF v_date IS NOT NULL THEN
        SELECT closed_at INTO v_closed_at
        FROM business_days
        WHERE business_date = v_date;
    END IF;

    IF v_closed_at IS NOT NULL THEN
        IF TG_TABLE_NAME = 'payments' THEN
            IF TG_OP = 'DELETE' OR (TG_OP IN ('INSERT', 'UPDATE') AND NEW.paid_at <= v_closed_at) THEN
                RAISE EXCEPTION 'Бизнес-день % закрыт. Изменения запрещены', v_date;
            END IF;
        ELSIF TG_TABLE_NAME = 'refunds' THEN
            IF TG_OP = 'DELETE' OR (TG_OP IN ('INSERT', 'UPDATE') AND NEW.refunded_at <= v_closed_at) THEN
                RAISE EXCEPTION 'Бизнес-день % закрыт. Изменения запрещены', v_date;
            END IF;
        ELSE
            RAISE EXCEPTION 'Бизнес-день % закрыт. Изменения запрещены', v_date;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_night_audit(
    p_business_date DATE,
    p_user_id INTEGER,
    p_ip VARCHAR,
    OUT p_posted_count INTEGER,
    OUT p_no_show_count INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    r RECORD;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    IF p_business_date > CURRENT_DATE THEN
        RAISE EXCEPTION 'Нельзя закрыть будущий бизнес-день %', p_business_date;
    END IF;

    IF EXISTS (SELECT 1 FROM business_days WHERE business_date = p_business_date) THEN
        RAISE EXCEPTION 'Бизнес-день % уже закрыт', p_business_date;
    END IF;

    p_posted_count := 0;

    FOR r IN
        SELECT b.booking_id, f.folio_id, rp.price_per_night
        FROM bookings b
        JOIN folios f ON f.booking_id = b.booking_id AND f.status = 'OPEN'
        JOIN rate_plans rp ON rp.rate_id = b.rate_id
        WHERE b.status = 'CHECKED_IN'
          AND p_business_date >= b.checkin_date
          AND p_business_date < b.checkout_date
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM folio_lines fl
            WHERE fl.folio_id = r.folio_id
              AND fl.line_type = 'ROOM'
              AND fl.charge_date = p_business_date
        ) THEN
            INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date)
            VALUES (
                r.folio_id,
                'Проживание за ' || to_char(p_business_date, 'DD.MM.YYYY'),
                r.price_per_night,
                'ROOM',
                p_business_date
            );
            p_posted_count := p_posted_count + 1;
        END IF;
    END LOOP;

    UPDATE bookings
    SET status = 'NO_SHOW'
    WHERE status = 'CONFIRMED'
      AND checkin_date = p_business_date;

    GET DIAGNOSTICS p_no_show_count = ROW_COUNT;

    INSERT INTO business_days (business_date, closed_by, totals)
    VALUES (
        p_business_date,
        p_user_id,
        jsonb_build_object(
            'posted_count', p_posted_count,
            'no_show_count', p_no_show_count
        )
    );
END;
$$;
