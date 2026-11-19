-- =====================================================================================
--  SunStay: неделя 5 — расширенная серверная логика
--  Ограничения, функции, процедуры, триггеры, транзакционные операции.
-- =====================================================================================

BEGIN;

-- -------------------------------------------------------------------------------------
-- 1. Дополнительные поля и ограничения
-- -------------------------------------------------------------------------------------

ALTER TABLE bookings
    ADD COLUMN adults   INTEGER NOT NULL DEFAULT 1 CHECK (adults > 0),
    ADD COLUMN children INTEGER NOT NULL DEFAULT 0 CHECK (children >= 0);

ALTER TABLE check_ins
    ADD CONSTRAINT check_ins_booking_unique UNIQUE (booking_id);

ALTER TABLE check_outs
    ADD CONSTRAINT check_outs_booking_unique UNIQUE (booking_id);

ALTER TABLE folios
    ADD CONSTRAINT folios_booking_unique UNIQUE (booking_id);

ALTER TABLE folio_lines
    ADD COLUMN charge_date DATE,
    ADD COLUMN service_order_id INTEGER REFERENCES service_orders(order_id) ON DELETE SET NULL;

UPDATE folio_lines fl
SET charge_date = f.opened_at::date
FROM folios f
WHERE fl.folio_id = f.folio_id
  AND fl.line_type = 'ROOM'
  AND fl.charge_date IS NULL;

UPDATE folio_lines
SET charge_date = created_at::date
WHERE charge_date IS NULL;

CREATE UNIQUE INDEX uq_folio_room_charge
    ON folio_lines (folio_id, charge_date)
    WHERE line_type = 'ROOM' AND charge_date IS NOT NULL;

CREATE UNIQUE INDEX uq_folio_service_order
    ON folio_lines (service_order_id)
    WHERE service_order_id IS NOT NULL;

ALTER TABLE consumables
    ADD COLUMN min_stock NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (min_stock >= 0);

ALTER TABLE maintenance_requests
    ADD COLUMN priority VARCHAR(10) NOT NULL DEFAULT 'NORMAL'
        CHECK (priority IN ('LOW','NORMAL','HIGH','URGENT')),
    ADD COLUMN assigned_to INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT now();

ALTER TABLE housekeeping_tasks
    ADD COLUMN priority VARCHAR(10) NOT NULL DEFAULT 'NORMAL'
        CHECK (priority IN ('LOW','NORMAL','HIGH','URGENT'));

ALTER TABLE guests
    ADD COLUMN user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE SET NULL;

UPDATE guests SET user_id = 1 WHERE guest_id = 1;

ALTER TABLE payments
    ADD COLUMN external_ref VARCHAR(100);

CREATE UNIQUE INDEX uq_payments_external_ref
    ON payments (external_ref)
    WHERE external_ref IS NOT NULL;

ALTER TABLE audit_log
    ADD COLUMN user_agent VARCHAR(255),
    ADD COLUMN request_id VARCHAR(100);

ALTER TABLE bookings
    ADD CONSTRAINT bookings_no_overlap
    EXCLUDE USING gist (
        room_id WITH =,
        daterange(checkin_date, checkout_date, '[)') WITH &&
    )
    WHERE (status IN ('NEW','CONFIRMED','CHECKED_IN'));

CREATE TABLE business_days (
    business_date DATE PRIMARY KEY,
    closed_at     TIMESTAMP NOT NULL DEFAULT now(),
    closed_by     INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    totals        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE system_settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       JSONB NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT now(),
    updated_by  INTEGER REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE import_batches (
    import_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    import_type   VARCHAR(30) NOT NULL CHECK (import_type IN ('BANK_STATEMENT','RATES')),
    filename      VARCHAR(255),
    status        VARCHAR(20) NOT NULL DEFAULT 'PREVIEW'
        CHECK (status IN ('PREVIEW','COMMITTED','FAILED')),
    total_rows    INTEGER NOT NULL DEFAULT 0,
    success_rows  INTEGER NOT NULL DEFAULT 0,
    error_rows    INTEGER NOT NULL DEFAULT 0,
    errors        JSONB,
    created_by    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT now(),
    committed_at  TIMESTAMP
);

INSERT INTO system_settings (key, value) VALUES
    ('hotel.name',       '"SunStay"'::jsonb),
    ('hotel.address',    '"Санкт-Петербург, набережная реки Мойки, 12"'::jsonb),
    ('hotel.phone',      '"+7 (812) 490-70-00"'::jsonb),
    ('hotel.email',      '"welcome@sunstay-hotel.ru"'::jsonb),
    ('app.default_theme','"light"'::jsonb),
    ('app.default_language','"ru"'::jsonb)
ON CONFLICT (key) DO NOTHING;

COMMIT;

-- -------------------------------------------------------------------------------------
-- 2. Функции проверки и расчёта
-- -------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_room_available(
    p_room_id INTEGER,
    p_checkin DATE,
    p_checkout DATE,
    p_exclude_booking_id INTEGER DEFAULT NULL
) RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_available BOOLEAN;
BEGIN
    IF p_checkin IS NULL OR p_checkout IS NULL OR p_checkout <= p_checkin THEN
        RETURN FALSE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM rooms r
        JOIN room_statuses rs ON rs.status_id = r.status_id
        WHERE r.room_id = p_room_id
          AND rs.name <> 'БЛОКИРОВАН'
    ) THEN
        RETURN FALSE;
    END IF;

    SELECT NOT EXISTS (
        SELECT 1
        FROM bookings b
        WHERE b.room_id = p_room_id
          AND b.status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(b.checkin_date, b.checkout_date, '[)')
              && daterange(p_checkin, p_checkout, '[)')
          AND (p_exclude_booking_id IS NULL OR b.booking_id <> p_exclude_booking_id)
    ) INTO v_available;

    RETURN v_available;
END;
$$;

CREATE OR REPLACE FUNCTION fn_calculate_stay_price(
    p_rate_id INTEGER,
    p_checkin DATE,
    p_checkout DATE,
    p_promo_id INTEGER DEFAULT NULL
) RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_price NUMERIC(10,2);
    v_nights INTEGER;
    v_discount INTEGER;
    v_total NUMERIC(12,2);
BEGIN
    v_nights := p_checkout - p_checkin;
    IF v_nights <= 0 THEN
        RAISE EXCEPTION 'Дата выезда должна быть позже даты заезда';
    END IF;

    SELECT price_per_night INTO v_price
    FROM rate_plans
    WHERE rate_id = p_rate_id;

    IF v_price IS NULL THEN
        RAISE EXCEPTION 'Тариф % не найден', p_rate_id;
    END IF;

    v_total := v_price * v_nights;

    IF p_promo_id IS NOT NULL THEN
        SELECT discount_percent INTO v_discount
        FROM promo_codes
        WHERE promo_id = p_promo_id
          AND p_checkin BETWEEN valid_from AND valid_to;

        IF v_discount IS NOT NULL THEN
            v_total := v_total * (1 - v_discount / 100.0);
        END IF;
    END IF;

    RETURN ROUND(v_total, 2);
END;
$$;

CREATE OR REPLACE FUNCTION fn_folio_charged(p_folio_id INTEGER) RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(SUM(amount), 0)
    FROM folio_lines
    WHERE folio_id = p_folio_id;
$$;

CREATE OR REPLACE FUNCTION fn_folio_paid(p_folio_id INTEGER) RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT COALESCE((
        SELECT SUM(p.amount) FROM payments p WHERE p.folio_id = p_folio_id
    ), 0) - COALESCE((
        SELECT SUM(rf.amount)
        FROM refunds rf
        JOIN payments p2 ON p2.payment_id = rf.payment_id
        WHERE p2.folio_id = p_folio_id
    ), 0);
$$;

CREATE OR REPLACE FUNCTION fn_folio_balance(p_folio_id INTEGER) RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT fn_folio_charged(p_folio_id) - fn_folio_paid(p_folio_id);
$$;

CREATE OR REPLACE FUNCTION fn_booking_balance(p_booking_id INTEGER) RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(fn_folio_balance(f.folio_id), 0)
    FROM folios f
    WHERE f.booking_id = p_booking_id
    ORDER BY f.folio_id DESC
    LIMIT 1;
$$;

-- -------------------------------------------------------------------------------------
-- 3. Триггеры валидации, аудита и защиты
-- -------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_validate_booking() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_type INTEGER;
    v_capacity INTEGER;
    v_rate_type INTEGER;
BEGIN
    IF NEW.checkout_date <= NEW.checkin_date THEN
        RAISE EXCEPTION 'Дата выезда должна быть позже даты заезда';
    END IF;

    SELECT rt.room_type_id, rt.capacity
    INTO v_room_type, v_capacity
    FROM rooms r
    JOIN room_types rt ON rt.room_type_id = r.room_type_id
    WHERE r.room_id = NEW.room_id;

    IF v_room_type IS NULL OR v_capacity IS NULL THEN
        RAISE EXCEPTION 'Номер % не найден', NEW.room_id;
    END IF;

    SELECT room_type_id INTO v_rate_type
    FROM rate_plans
    WHERE rate_id = NEW.rate_id;

    IF v_rate_type IS NULL OR v_rate_type <> v_room_type THEN
        RAISE EXCEPTION 'Тариф не соответствует типу номера';
    END IF;

    IF NEW.adults + NEW.children > v_capacity THEN
        RAISE EXCEPTION 'Количество гостей превышает вместимость номера';
    END IF;

    IF NEW.status IN ('NEW','CONFIRMED','CHECKED_IN') THEN
        IF NOT EXISTS (
            SELECT 1
            FROM rate_plans rp
            WHERE rp.rate_id = NEW.rate_id
              AND NEW.checkin_date >= rp.season_start
              AND NEW.checkout_date - 1 <= rp.season_end
        ) THEN
            RAISE EXCEPTION 'Тариф не действует на выбранные даты';
        END IF;
    END IF;

    IF NEW.promo_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
            FROM promo_codes pc
            WHERE pc.promo_id = NEW.promo_id
              AND NEW.checkin_date BETWEEN pc.valid_from AND pc.valid_to
        ) THEN
            RAISE EXCEPTION 'Промокод не действует на выбранные даты';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_booking
BEFORE INSERT OR UPDATE ON bookings
FOR EACH ROW EXECUTE FUNCTION fn_validate_booking();

CREATE OR REPLACE FUNCTION fn_audit_row() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id INTEGER;
    v_ip VARCHAR(50);
    v_ua VARCHAR(255);
    v_request_id VARCHAR(100);
    v_record_id INTEGER;
    v_old TEXT;
    v_new TEXT;
BEGIN
    v_user_id := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;
    v_ip := NULLIF(current_setting('app.client_ip', true), '');
    v_ua := NULLIF(current_setting('app.user_agent', true), '');
    v_request_id := NULLIF(current_setting('app.request_id', true), '');

    IF TG_OP = 'DELETE' THEN
        v_record_id := (to_jsonb(OLD) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD)::TEXT;
        v_new := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD)::TEXT;
        v_new := to_jsonb(NEW)::TEXT;
    ELSE
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := NULL;
        v_new := to_jsonb(NEW)::TEXT;
    END IF;

    INSERT INTO audit_log (
        user_id, table_name, record_id, action,
        old_value, new_value, ip_address, user_agent, request_id
    ) VALUES (
        v_user_id, TG_TABLE_NAME, v_record_id, TG_OP,
        v_old, v_new, v_ip, v_ua, v_request_id
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_bookings
AFTER INSERT OR UPDATE OR DELETE ON bookings
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('booking_id');

CREATE TRIGGER trg_audit_rooms
AFTER INSERT OR UPDATE OR DELETE ON rooms
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('room_id');

CREATE TRIGGER trg_audit_users
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('user_id');

CREATE TRIGGER trg_audit_folios
AFTER INSERT OR UPDATE OR DELETE ON folios
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('folio_id');

CREATE TRIGGER trg_audit_payments
AFTER INSERT OR UPDATE OR DELETE ON payments
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('payment_id');

CREATE TRIGGER trg_audit_refunds
AFTER INSERT OR UPDATE OR DELETE ON refunds
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('refund_id');

CREATE TRIGGER trg_audit_rate_plans
AFTER INSERT OR UPDATE OR DELETE ON rate_plans
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('rate_id');

CREATE TRIGGER trg_audit_services
AFTER INSERT OR UPDATE OR DELETE ON services
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('service_id');

CREATE TRIGGER trg_audit_guests
AFTER INSERT OR UPDATE OR DELETE ON guests
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('guest_id');

CREATE TRIGGER trg_audit_housekeeping
AFTER INSERT OR UPDATE OR DELETE ON housekeeping_tasks
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('task_id');

CREATE TRIGGER trg_audit_maintenance
AFTER INSERT OR UPDATE OR DELETE ON maintenance_requests
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('request_id');

CREATE TRIGGER trg_audit_consumables
AFTER INSERT OR UPDATE OR DELETE ON consumables
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('consumable_id');

CREATE OR REPLACE FUNCTION fn_consumable_stock() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE consumables
        SET stock_quantity = stock_quantity - NEW.quantity
        WHERE consumable_id = NEW.consumable_id
          AND stock_quantity >= NEW.quantity;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Недостаточно расходного материала %', NEW.consumable_id;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE consumables
        SET stock_quantity = stock_quantity + OLD.quantity
        WHERE consumable_id = OLD.consumable_id;

        UPDATE consumables
        SET stock_quantity = stock_quantity - NEW.quantity
        WHERE consumable_id = NEW.consumable_id
          AND stock_quantity >= NEW.quantity;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Недостаточно расходного материала %', NEW.consumable_id;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        UPDATE consumables
        SET stock_quantity = stock_quantity + OLD.quantity
        WHERE consumable_id = OLD.consumable_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_consumable_stock
BEFORE INSERT OR UPDATE OR DELETE ON consumable_usage
FOR EACH ROW EXECUTE FUNCTION fn_consumable_stock();

CREATE OR REPLACE FUNCTION fn_prevent_closed_day() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_date DATE;
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

    IF v_date IS NOT NULL AND EXISTS (
        SELECT 1 FROM business_days
        WHERE business_date = v_date AND closed_at IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'Бизнес-день % закрыт. Изменения запрещены', v_date;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_closed_day_folio_lines
BEFORE INSERT OR UPDATE OR DELETE ON folio_lines
FOR EACH ROW EXECUTE FUNCTION fn_prevent_closed_day();

CREATE TRIGGER trg_prevent_closed_day_payments
BEFORE INSERT OR UPDATE OR DELETE ON payments
FOR EACH ROW EXECUTE FUNCTION fn_prevent_closed_day();

CREATE TRIGGER trg_prevent_closed_day_refunds
BEFORE INSERT OR UPDATE OR DELETE ON refunds
FOR EACH ROW EXECUTE FUNCTION fn_prevent_closed_day();

CREATE OR REPLACE FUNCTION fn_set_updated_at() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_maintenance_updated_at
BEFORE UPDATE ON maintenance_requests
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- -------------------------------------------------------------------------------------
-- 4. Транзакционные серверные операции
-- -------------------------------------------------------------------------------------

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
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_booking_id INTEGER;
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

    INSERT INTO bookings (
        guest_id, room_id, rate_id, promo_id,
        checkin_date, checkout_date, status, source,
        adults, children
    ) VALUES (
        p_guest_id, p_room_id, p_rate_id, p_promo_id,
        p_checkin, p_checkout, 'NEW', COALESCE(p_source, 'SITE'),
        COALESCE(p_adults, 1), COALESCE(p_children, 0)
    )
    RETURNING booking_id INTO v_booking_id;

    RETURN v_booking_id;
EXCEPTION
    WHEN exclusion_violation THEN
        RAISE EXCEPTION 'Номер уже забронирован на выбранные даты';
END;
$$;

CREATE OR REPLACE PROCEDURE sp_confirm_booking(
    p_booking_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE bookings
    SET status = 'CONFIRMED'
    WHERE booking_id = p_booking_id
      AND status = 'NEW';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Бронь % нельзя подтвердить: неверный статус', p_booking_id;
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_cancel_booking(
    p_booking_id INTEGER,
    p_reason_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE bookings
    SET status = 'CANCELLED',
        cancellation_reason_id = p_reason_id
    WHERE booking_id = p_booking_id
      AND status IN ('NEW','CONFIRMED');

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Бронь % нельзя отменить: неверный статус', p_booking_id;
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_check_in(
    p_booking_id INTEGER,
    p_manager_id INTEGER,
    p_document_number VARCHAR,
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

    IF EXISTS (
        SELECT 1
        FROM rooms r
        JOIN room_statuses rs ON rs.status_id = r.status_id
        WHERE r.room_id = v_room_id AND rs.name = 'БЛОКИРОВАН'
    ) THEN
        RAISE EXCEPTION 'Номер заблокирован';
    END IF;

    INSERT INTO check_ins (booking_id, manager_id, guest_document_number)
    VALUES (p_booking_id, p_manager_id, p_document_number);

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
    v_folio_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_manager_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT room_id INTO v_room_id
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

CREATE OR REPLACE FUNCTION fn_add_service_order(
    p_booking_id INTEGER,
    p_service_id INTEGER,
    p_quantity INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id INTEGER;
    v_folio_id INTEGER;
    v_price NUMERIC(10,2);
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT folio_id INTO v_folio_id
    FROM folios
    WHERE booking_id = p_booking_id AND status = 'OPEN'
    ORDER BY folio_id DESC
    LIMIT 1;

    IF v_folio_id IS NULL THEN
        RAISE EXCEPTION 'Открытый folio не найден';
    END IF;

    SELECT price INTO v_price FROM services WHERE service_id = p_service_id;

    INSERT INTO service_orders (booking_id, service_id, user_id, quantity)
    VALUES (p_booking_id, p_service_id, p_user_id, p_quantity)
    RETURNING order_id INTO v_order_id;

    INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date, service_order_id)
    VALUES (
        v_folio_id,
        'Услуга: ' || (SELECT name FROM services WHERE service_id = p_service_id),
        v_price * p_quantity,
        'SERVICE',
        CURRENT_DATE,
        v_order_id
    );

    RETURN v_order_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_record_payment(
    p_folio_id INTEGER,
    p_amount NUMERIC,
    p_method VARCHAR,
    p_type VARCHAR,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_payment_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    IF NOT EXISTS (SELECT 1 FROM folios WHERE folio_id = p_folio_id AND status = 'OPEN') THEN
        RAISE EXCEPTION 'Folio закрыт или не найден';
    END IF;

    INSERT INTO payments (folio_id, amount, method, payment_type)
    VALUES (p_folio_id, p_amount, p_method, COALESCE(p_type, 'PAYMENT'))
    RETURNING payment_id INTO v_payment_id;

    RETURN v_payment_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_refund_payment(
    p_payment_id INTEGER,
    p_amount NUMERIC,
    p_reason VARCHAR,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_refund_id INTEGER;
    v_payment_amount NUMERIC(10,2);
    v_refunded NUMERIC(10,2);
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT amount INTO v_payment_amount FROM payments WHERE payment_id = p_payment_id;

    SELECT COALESCE(SUM(amount), 0) INTO v_refunded
    FROM refunds
    WHERE payment_id = p_payment_id;

    IF p_amount > v_payment_amount - v_refunded THEN
        RAISE EXCEPTION 'Сумма возврата превышает остаток платежа';
    END IF;

    INSERT INTO refunds (payment_id, amount, reason)
    VALUES (p_payment_id, p_amount, p_reason)
    RETURNING refund_id INTO v_refund_id;

    RETURN v_refund_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_assign_housekeeping_task(
    p_room_id INTEGER,
    p_staff_id INTEGER,
    p_task_type VARCHAR,
    p_priority VARCHAR,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_task_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    INSERT INTO housekeeping_tasks (room_id, staff_id, task_type, status, priority)
    VALUES (p_room_id, p_staff_id, p_task_type, 'ASSIGNED', COALESCE(p_priority, 'NORMAL'))
    RETURNING task_id INTO v_task_id;

    RETURN v_task_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_start_housekeeping_task(
    p_task_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE housekeeping_tasks
    SET status = 'IN_PROGRESS'
    WHERE task_id = p_task_id AND status = 'ASSIGNED'
    RETURNING room_id INTO v_room_id;

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Задание % нельзя начать', p_task_id;
    END IF;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'В_УБОРКЕ';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_complete_housekeeping_task(
    p_task_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE housekeeping_tasks
    SET status = 'DONE', completed_at = now()
    WHERE task_id = p_task_id AND status IN ('ASSIGNED','IN_PROGRESS')
    RETURNING room_id INTO v_room_id;

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Задание % нельзя завершить', p_task_id;
    END IF;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'ЧИСТЫЙ_ГОТОВ';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_cancel_housekeeping_task(
    p_task_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE housekeeping_tasks
    SET status = 'CANCELLED'
    WHERE task_id = p_task_id AND status IN ('ASSIGNED','IN_PROGRESS');

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Задание % нельзя отменить', p_task_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION fn_write_off_consumable(
    p_task_id INTEGER,
    p_consumable_id INTEGER,
    p_quantity NUMERIC,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_usage_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    INSERT INTO consumable_usage (task_id, consumable_id, quantity)
    VALUES (p_task_id, p_consumable_id, p_quantity)
    RETURNING usage_id INTO v_usage_id;

    RETURN v_usage_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_create_maintenance_request(
    p_room_id INTEGER,
    p_task_id INTEGER,
    p_description TEXT,
    p_priority VARCHAR,
    p_assigned_to INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_request_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    INSERT INTO maintenance_requests (room_id, task_id, description, status, priority, assigned_to)
    VALUES (p_room_id, p_task_id, p_description, 'OPEN', COALESCE(p_priority, 'NORMAL'), p_assigned_to)
    RETURNING request_id INTO v_request_id;

    RETURN v_request_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_set_room_status(
    p_room_id INTEGER,
    p_status_name VARCHAR,
    p_reason_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = p_status_name;

    IF v_status_id IS NULL THEN
        RAISE EXCEPTION 'Статус номера % не найден', p_status_name;
    END IF;

    IF p_status_name = 'БЛОКИРОВАН' AND p_reason_id IS NULL THEN
        RAISE EXCEPTION 'Для блокировки номера нужно указать причину';
    END IF;

    UPDATE rooms
    SET status_id = v_status_id,
        block_reason_id = CASE WHEN p_status_name = 'БЛОКИРОВАН' THEN p_reason_id ELSE NULL END
    WHERE room_id = p_room_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_update_maintenance_status(
    p_request_id INTEGER,
    p_status VARCHAR,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE maintenance_requests
    SET status = p_status
    WHERE request_id = p_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Заявка % не найдена', p_request_id;
    END IF;
END;
$$;
