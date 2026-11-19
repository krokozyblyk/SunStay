-- =====================================================================================
--  SunStay: SQL-тесты серверной логики
--  Запуск: psql -U postgres -d hotel -f database/tests/week5_tests.sql
--  Все изменения откатываются.
-- =====================================================================================

\set ON_ERROR_STOP on
BEGIN;

DO $$
DECLARE
    v_booking_id INTEGER;
    v_folio_id INTEGER;
    v_payment_id INTEGER;
    v_order_id INTEGER;
    v_available BOOLEAN;
    v_price NUMERIC;
    v_status VARCHAR;
    v_charged NUMERIC;
    v_paid NUMERIC;
    v_audit_count INTEGER;
    v_task_count INTEGER;
    v_posted_count INTEGER;
    v_no_show_count INTEGER;
    v_room_lines INTEGER;
    v_closed_at TIMESTAMP;
    v_booking_id2 INTEGER;
    v_folio_id2 INTEGER;
    v_doc_masked VARCHAR;
    v_doc_enc TEXT;
    v_doc_hash VARCHAR;
BEGIN
    -- 1. Расчёт стоимости
    v_price := fn_calculate_stay_price(3, DATE '2026-12-20', DATE '2026-12-22', NULL);
    IF v_price <> 11200.00 THEN
        RAISE EXCEPTION 'Ожидалась цена 11200, получено %', v_price;
    END IF;

    -- 2. Доступность номера
    v_available := fn_room_available(4, DATE '2026-12-20', DATE '2026-12-22');
    IF NOT v_available THEN
        RAISE EXCEPTION 'Номер 4 должен быть доступен на 20–22.12.2026';
    END IF;

    -- 3. Создание брони
    SELECT fn_create_booking(1, 4, 3, DATE '2026-12-20', DATE '2026-12-22', NULL, 'SITE', 1, 0, 2, '127.0.0.1')
    INTO v_booking_id;

    IF v_booking_id IS NULL THEN
        RAISE EXCEPTION 'Бронь не создана';
    END IF;

    SELECT status INTO v_status FROM bookings WHERE booking_id = v_booking_id;
    IF v_status <> 'NEW' THEN
        RAISE EXCEPTION 'Ожидался статус NEW, получен %', v_status;
    END IF;

    v_available := fn_room_available(4, DATE '2026-12-20', DATE '2026-12-22');
    IF v_available THEN
        RAISE EXCEPTION 'После бронирования номер не должен быть доступен';
    END IF;

    -- 4. Подтверждение и заселение
    CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
    CALL sp_check_in(v_booking_id, 2, '4510 123456', 1000, 'CARD', '127.0.0.1');

    SELECT status INTO v_status FROM bookings WHERE booking_id = v_booking_id;
    IF v_status <> 'CHECKED_IN' THEN
        RAISE EXCEPTION 'Ожидался статус CHECKED_IN, получен %', v_status;
    END IF;

    SELECT folio_id INTO v_folio_id
    FROM folios WHERE booking_id = v_booking_id AND status = 'OPEN';
    IF v_folio_id IS NULL THEN
        RAISE EXCEPTION 'Folio не открыт при заселении';
    END IF;

    -- 5. Заказ услуги и платёж
    v_order_id := fn_add_service_order(v_booking_id, 1, 2, 2, '127.0.0.1');
    IF v_order_id IS NULL THEN
        RAISE EXCEPTION 'Заказ услуги не создан';
    END IF;

    v_payment_id := fn_record_payment(v_folio_id, 5000, 'CASH', 'PAYMENT', 2, '127.0.0.1');
    IF v_payment_id IS NULL THEN
        RAISE EXCEPTION 'Платёж не создан';
    END IF;

    v_paid := fn_folio_paid(v_folio_id);
    IF v_paid <> 6000.00 THEN
        RAISE EXCEPTION 'Ожидалось оплачено 6000, получено %', v_paid;
    END IF;

    PERFORM fn_refund_payment(v_payment_id, 1000, 'Тестовый возврат', 2, '127.0.0.1');

    v_paid := fn_folio_paid(v_folio_id);
    IF v_paid <> 5000.00 THEN
        RAISE EXCEPTION 'После возврата ожидалось 5000, получено %', v_paid;
    END IF;

    -- 6. Ночной аудит на текущую дату
    SELECT fn_create_booking(1, 1, 5, CURRENT_DATE, CURRENT_DATE + 1, NULL, 'SITE', 1, 0, 2, '127.0.0.1')
    INTO v_booking_id2;
    CALL sp_confirm_booking(v_booking_id2, 2, '127.0.0.1');
    SELECT document_number, document_number_enc, document_number_hash
    INTO v_doc_masked, v_doc_enc, v_doc_hash
    FROM guests WHERE guest_id = 1;
    CALL sp_check_in_secure(v_booking_id2, 2, v_doc_masked, v_doc_enc, v_doc_hash, 1000, 'CARD', '127.0.0.1');
    SELECT folio_id INTO v_folio_id2
    FROM folios WHERE booking_id = v_booking_id2 AND status = 'OPEN';

    CALL sp_night_audit(CURRENT_DATE, 2, '127.0.0.1', v_posted_count, v_no_show_count);
    UPDATE business_days SET closed_at = now() - interval '1 hour'
    WHERE business_date = CURRENT_DATE;

    SELECT count(*) INTO v_room_lines
    FROM folio_lines
    WHERE folio_id = v_folio_id2
      AND line_type = 'ROOM'
      AND charge_date = CURRENT_DATE;
    IF v_room_lines <> 1 THEN
        RAISE EXCEPTION 'Ночной аудит не начислил проживание за текущую дату';
    END IF;

    -- 7. Повторный аудит должен упасть
    BEGIN
        CALL sp_night_audit(CURRENT_DATE, 2, '127.0.0.1', v_posted_count, v_no_show_count);
        RAISE EXCEPTION 'Повторный ночной аудит должен завершиться ошибкой';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM NOT LIKE '%уже закрыт%' THEN
            RAISE;
        END IF;
    END;

    -- 8. Выселение
    CALL sp_check_out(v_booking_id, 2, 0, 'CARD', '127.0.0.1');

    SELECT status INTO v_status FROM bookings WHERE booking_id = v_booking_id;
    IF v_status <> 'CHECKED_OUT' THEN
        RAISE EXCEPTION 'Ожидался статус CHECKED_OUT, получен %', v_status;
    END IF;

    SELECT fn_folio_charged(v_folio_id) INTO v_charged;
    IF v_charged < 11200.00 THEN
        RAISE EXCEPTION 'После выселения начислено меньше стоимости проживания: %', v_charged;
    END IF;

    SELECT count(*) INTO v_task_count
    FROM housekeeping_tasks
    WHERE room_id = 4 AND task_type = 'POST_CHECKOUT';
    IF v_task_count = 0 THEN
        RAISE EXCEPTION 'Задание на уборку после выезда не создано';
    END IF;

    -- 9. Защита остатков расходников
    BEGIN
        PERFORM fn_write_off_consumable(1, 1, 999999, 2, '127.0.0.1');
        RAISE EXCEPTION 'Списание больше остатка должно завершиться ошибкой';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM NOT LIKE '%Недостаточно%' THEN
            RAISE;
        END IF;
    END;

    -- 10. Аудит
    SELECT count(*) INTO v_audit_count
    FROM audit_log
    WHERE table_name = 'bookings' AND record_id = v_booking_id;
    IF v_audit_count = 0 THEN
        RAISE EXCEPTION 'Записи аудита для брони не найдены';
    END IF;

    -- 11. Шифрование и маскирование контактов
    IF NOT EXISTS (
        SELECT 1 FROM guests
        WHERE guest_id = 1
          AND document_number_enc IS NOT NULL
          AND document_number LIKE '%*%'
          AND length(document_number_hash) = 64
          AND phone_enc IS NOT NULL
          AND phone LIKE '%*%'
          AND length(phone_hash) = 64
    ) THEN
        RAISE EXCEPTION 'Данные гостя не зашифрованы или не замаскированы';
    END IF;

    -- 12. Безопасное заселение по хэшу документа
    SELECT fn_create_booking(1, 5, 4, DATE '2026-12-25', DATE '2026-12-27', NULL, 'SITE', 1, 0, 2, '127.0.0.1')
    INTO v_booking_id;
    CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
    BEGIN
        CALL sp_check_in_secure(v_booking_id, 2, '**** 0000', 'wrong', encode(digest('0000 000000', 'sha256'), 'hex'), 1000, 'CARD', '127.0.0.1');
        RAISE EXCEPTION 'Заселение с неверным документом должно завершиться ошибкой';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM NOT ILIKE '%документ%' THEN
            RAISE;
        END IF;
    END;
    CALL sp_check_in_secure(v_booking_id, 2, v_doc_masked, v_doc_enc, v_doc_hash, 1000, 'CARD', '127.0.0.1');
    SELECT status INTO v_status FROM bookings WHERE booking_id = v_booking_id;
    IF v_status <> 'CHECKED_IN' THEN
        RAISE EXCEPTION 'Безопасное заселение не перевело бронь в CHECKED_IN';
    END IF;

    -- 13. Запрет закрытия будущего бизнес-дня
    BEGIN
        CALL sp_night_audit(CURRENT_DATE + 1, 2, '127.0.0.1', v_posted_count, v_no_show_count);
        RAISE EXCEPTION 'Закрытие будущего бизнес-дня должно завершиться ошибкой';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM NOT LIKE '%будущий%' THEN
            RAISE;
        END IF;
    END;

    -- 14. Закрытый день: платёж до закрытия запрещён, после закрытия разрешён
    SELECT closed_at INTO v_closed_at
    FROM business_days WHERE business_date = DATE '2026-11-17';
    IF v_closed_at IS NULL THEN
        RAISE EXCEPTION 'Для проверки закрытого дня нужен бизнес-день 17.11.2026';
    END IF;
    BEGIN
        INSERT INTO payments (folio_id, amount, method, payment_type, paid_at)
        VALUES (v_folio_id, 100, 'CASH', 'PAYMENT', v_closed_at - interval '1 hour');
        RAISE EXCEPTION 'Платёж до закрытия дня должен быть запрещён';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM NOT LIKE '%закрыт%' THEN
            RAISE;
        END IF;
    END;
    INSERT INTO payments (folio_id, amount, method, payment_type, paid_at)
    VALUES (v_folio_id, 100, 'CASH', 'PAYMENT', v_closed_at + interval '1 minute');
END;
$$;

ROLLBACK;
\echo 'SQL TESTS PASSED'
