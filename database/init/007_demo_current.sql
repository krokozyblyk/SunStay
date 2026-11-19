-- =====================================================================================
--  SunStay: демонстрационные брони на текущую неделю
--  Выполняется после основной схемы и наполнения.
-- =====================================================================================

UPDATE users
SET full_name = 'Иванов Иван Иванович'
WHERE user_id = 1
  AND full_name = 'Гостевой аккаунт (демо)';

INSERT INTO rate_plans (room_type_id, name, season_start, season_end, price_per_night, cancellation_terms)
SELECT 1, 'Стандарт — межсезонье', '2026-10-01', '2026-12-31', 4000.00, 'Бесплатная отмена за 24 часа'
WHERE NOT EXISTS (SELECT 1 FROM rate_plans WHERE name = 'Стандарт — межсезонье');

DO $$
DECLARE
    v_booking_id INTEGER;
    v_rate_standard INTEGER;
BEGIN
    SELECT rate_id INTO v_rate_standard
    FROM rate_plans
    WHERE room_type_id = 1
      AND CURRENT_DATE BETWEEN season_start AND season_end
    ORDER BY price_per_night
    LIMIT 1;

    IF v_rate_standard IS NULL THEN
        RAISE EXCEPTION 'Не найден тариф для Стандарта на текущую дату';
    END IF;

    -- 101: подтверждённая бронь на 2 ночи
    IF NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE room_id = 1
          AND status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(checkin_date, checkout_date, '[)')
              && daterange(CURRENT_DATE, CURRENT_DATE + 2, '[)')
    ) THEN
        SELECT fn_create_booking(2, 1, v_rate_standard, CURRENT_DATE, CURRENT_DATE + 2, NULL, 'SITE', 1, 0, 2, '127.0.0.1')
        INTO v_booking_id;
        CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
    END IF;

    -- 102: подтверждённая бронь на 3 ночи
    IF NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE room_id = 2
          AND status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(checkin_date, checkout_date, '[)')
              && daterange(CURRENT_DATE, CURRENT_DATE + 3, '[)')
    ) THEN
        SELECT fn_create_booking(1, 2, v_rate_standard, CURRENT_DATE, CURRENT_DATE + 3, NULL, 'PHONE', 1, 0, 2, '127.0.0.1')
        INTO v_booking_id;
        CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
    END IF;

    -- 201: подтверждённая бронь на 2 ночи
    IF NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE room_id = 3
          AND status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(checkin_date, checkout_date, '[)')
              && daterange(CURRENT_DATE, CURRENT_DATE + 2, '[)')
    ) THEN
        SELECT fn_create_booking(4, 3, 3, CURRENT_DATE, CURRENT_DATE + 2, NULL, 'OTA', 1, 0, 2, '127.0.0.1')
        INTO v_booking_id;
        CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
    END IF;

    -- 202: заселённый гость на 3 ночи
    IF NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE room_id = 4
          AND status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(checkin_date, checkout_date, '[)')
              && daterange(CURRENT_DATE, CURRENT_DATE + 3, '[)')
    ) THEN
        SELECT fn_create_booking(3, 4, 3, CURRENT_DATE, CURRENT_DATE + 3, NULL, 'SITE', 1, 1, 2, '127.0.0.1')
        INTO v_booking_id;
        CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
        CALL sp_check_in(v_booking_id, 2, '4512 789012', 5000, 'CARD', '127.0.0.1');
    END IF;
END;
$$;

-- Демонстрационная история проживаний за последние две недели
DO $$
DECLARE
    v_std INTEGER;
    v_comf INTEGER;
    v_lux INTEGER;
BEGIN
    SELECT rate_id INTO v_std
    FROM rate_plans
    WHERE room_type_id = 1
      AND CURRENT_DATE BETWEEN season_start AND season_end
    ORDER BY price_per_night
    LIMIT 1;

    SELECT rate_id INTO v_comf
    FROM rate_plans
    WHERE room_type_id = 2
      AND CURRENT_DATE BETWEEN season_start AND season_end
    ORDER BY price_per_night
    LIMIT 1;

    SELECT rate_id INTO v_lux
    FROM rate_plans
    WHERE room_type_id = 3
      AND CURRENT_DATE BETWEEN season_start AND season_end
    ORDER BY price_per_night
    LIMIT 1;

    IF v_std IS NULL OR v_comf IS NULL OR v_lux IS NULL THEN
        RETURN;
    END IF;

    INSERT INTO bookings (guest_id, room_id, rate_id, checkin_date, checkout_date, status, source, adults, children)
    VALUES
        (2, 1, v_std, CURRENT_DATE - 15, CURRENT_DATE - 13, 'CHECKED_OUT', 'SITE', 1, 0),
        (4, 1, v_std, CURRENT_DATE - 10, CURRENT_DATE - 8,  'CHECKED_OUT', 'PHONE', 2, 0),
        (2, 1, v_std, CURRENT_DATE - 5,  CURRENT_DATE - 3,  'CHECKED_OUT', 'OTA', 1, 1),
        (1, 2, v_std, CURRENT_DATE - 14, CURRENT_DATE - 12, 'CHECKED_OUT', 'SITE', 1, 0),
        (3, 2, v_std, CURRENT_DATE - 9,  CURRENT_DATE - 7,  'CHECKED_OUT', 'WALK_IN', 1, 0),
        (4, 2, v_std, CURRENT_DATE - 4,  CURRENT_DATE - 2,  'CHECKED_OUT', 'SITE', 2, 0),
        (2, 3, v_comf, CURRENT_DATE - 15, CURRENT_DATE - 14, 'CHECKED_OUT', 'SITE', 2, 0),
        (3, 3, v_comf, CURRENT_DATE - 11, CURRENT_DATE - 9,  'CHECKED_OUT', 'OTA', 1, 0),
        (1, 3, v_comf, CURRENT_DATE - 6,  CURRENT_DATE - 4,  'CHECKED_OUT', 'PHONE', 1, 1),
        (4, 4, v_comf, CURRENT_DATE - 13, CURRENT_DATE - 11, 'CHECKED_OUT', 'SITE', 2, 0),
        (1, 4, v_comf, CURRENT_DATE - 8,  CURRENT_DATE - 6,  'CHECKED_OUT', 'OTA', 1, 0),
        (2, 4, v_comf, CURRENT_DATE - 3,  CURRENT_DATE - 1,  'CHECKED_OUT', 'SITE', 1, 0),
        (3, 5, v_lux, CURRENT_DATE - 12, CURRENT_DATE - 10, 'CHECKED_OUT', 'SITE', 2, 1),
        (4, 5, v_lux, CURRENT_DATE - 7,  CURRENT_DATE - 5,  'CHECKED_OUT', 'PHONE', 1, 0),
        (1, 5, v_lux, CURRENT_DATE - 2,  CURRENT_DATE - 1,  'CHECKED_OUT', 'OTA', 2, 0),
        (1, 2, v_std, CURRENT_DATE - 15, CURRENT_DATE - 14, 'CHECKED_OUT', 'SITE', 1, 0),
        (2, 3, v_comf, CURRENT_DATE - 14, CURRENT_DATE - 12, 'CHECKED_OUT', 'SITE', 2, 0),
        (3, 4, v_comf, CURRENT_DATE - 15, CURRENT_DATE - 13, 'CHECKED_OUT', 'OTA', 1, 0),
        (4, 5, v_lux, CURRENT_DATE - 15, CURRENT_DATE - 12, 'CHECKED_OUT', 'SITE', 1, 0),
        (3, 2, v_std, CURRENT_DATE - 12, CURRENT_DATE - 10, 'CHECKED_OUT', 'PHONE', 1, 0),
        (4, 1, v_std, CURRENT_DATE - 13, CURRENT_DATE - 10, 'CHECKED_OUT', 'SITE', 2, 0),
        (1, 3, v_comf, CURRENT_DATE - 9,  CURRENT_DATE - 6,  'CHECKED_OUT', 'SITE', 1, 1),
        (2, 4, v_comf, CURRENT_DATE - 6,  CURRENT_DATE - 3,  'CHECKED_OUT', 'OTA', 2, 0),
        (3, 5, v_lux, CURRENT_DATE - 5,  CURRENT_DATE - 2,  'CHECKED_OUT', 'SITE', 1, 0)
    ON CONFLICT DO NOTHING;

    INSERT INTO bookings (guest_id, room_id, rate_id, checkin_date, checkout_date, status, source, adults, children, cancellation_reason_id)
    VALUES
        (3, 1, v_std, CURRENT_DATE - 16, CURRENT_DATE - 14, 'CANCELLED', 'SITE', 1, 0, 1),
        (2, 3, v_comf, CURRENT_DATE - 12, CURRENT_DATE - 10, 'CANCELLED', 'SITE', 1, 0, 2),
        (4, 5, v_lux, CURRENT_DATE - 6, CURRENT_DATE - 4, 'NO_SHOW', 'PHONE', 1, 0, NULL)
    ON CONFLICT DO NOTHING;
END;
$$;

-- Демонстрационное начисление проживания за текущую ночь
INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date)
SELECT
    f.folio_id,
    'Проживание за ' || to_char(CURRENT_DATE, 'DD.MM.YYYY'),
    rp.price_per_night,
    'ROOM',
    CURRENT_DATE
FROM folios f
JOIN bookings b ON b.booking_id = f.booking_id
JOIN rate_plans rp ON rp.rate_id = b.rate_id
WHERE f.status = 'OPEN'
  AND b.status = 'CHECKED_IN'
  AND CURRENT_DATE >= b.checkin_date
  AND CURRENT_DATE < b.checkout_date
  AND NOT EXISTS (
      SELECT 1
      FROM folio_lines fl
      WHERE fl.folio_id = f.folio_id
        AND fl.line_type = 'ROOM'
        AND fl.charge_date = CURRENT_DATE
  );

-- Актуальные статусы номеров для демонстрации
UPDATE rooms SET status_id = (SELECT status_id FROM room_statuses WHERE name = 'ЗАБРОНИРОВАН')
WHERE room_id IN (1, 2)
  AND NOT EXISTS (
      SELECT 1 FROM bookings b
      WHERE b.room_id = rooms.room_id
        AND b.status = 'CHECKED_IN'
        AND CURRENT_DATE >= b.checkin_date
        AND CURRENT_DATE < b.checkout_date
  );

UPDATE rooms SET status_id = (SELECT status_id FROM room_statuses WHERE name = 'ЧИСТЫЙ_ГОТОВ')
WHERE room_id = 3
  AND NOT EXISTS (
      SELECT 1 FROM bookings b
      WHERE b.room_id = rooms.room_id
        AND b.status = 'CHECKED_IN'
        AND CURRENT_DATE >= b.checkin_date
        AND CURRENT_DATE < b.checkout_date
  );

UPDATE rooms SET status_id = (SELECT status_id FROM room_statuses WHERE name = 'СВОБОДЕН')
WHERE room_id = 5
  AND NOT EXISTS (
      SELECT 1 FROM bookings b
      WHERE b.room_id = rooms.room_id
        AND b.status = 'CHECKED_IN'
        AND CURRENT_DATE >= b.checkin_date
        AND CURRENT_DATE < b.checkout_date
  );
