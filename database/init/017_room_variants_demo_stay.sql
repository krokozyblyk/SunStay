-- =====================================================================================
--  SunStay: варианты номеров и демо-заселение гостя
-- =====================================================================================

BEGIN;

ALTER TABLE rooms ADD COLUMN IF NOT EXISTS variant_name VARCHAR(100);
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS image_url TEXT;
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS description TEXT;

UPDATE rooms SET
  variant_name = CASE rt.name
    WHEN 'Стандарт' THEN CASE WHEN room_number IN ('101','102','103','1') THEN 'Классика'
                              WHEN room_number BETWEEN '110' AND '119' THEN 'Классика'
                              WHEN room_number BETWEEN '120' AND '129' THEN 'Панорама'
                              ELSE 'Уют' END
    WHEN 'Комфорт' THEN CASE WHEN room_number IN ('201','202') THEN 'Бизнес'
                             WHEN room_number BETWEEN '210' AND '219' THEN 'Городской вид'
                             WHEN room_number BETWEEN '220' AND '229' THEN 'Простор'
                             ELSE 'Городской вид' END
    WHEN 'Люкс' THEN CASE WHEN room_number = '301' THEN 'Президентский'
                          WHEN room_number BETWEEN '310' AND '314' THEN 'Панорамный'
                          WHEN room_number BETWEEN '315' AND '317' THEN 'Классик'
                          ELSE 'Панорамный' END
  END,
  image_url = CASE rt.name
    WHEN 'Стандарт' THEN CASE WHEN room_number IN ('101','102','103','1') OR room_number BETWEEN '110' AND '119' THEN 'images/variants/standard-classic.jpg'
                              WHEN room_number BETWEEN '120' AND '129' THEN 'images/variants/standard-panorama.jpg'
                              ELSE 'images/variants/standard-cozy.jpg' END
    WHEN 'Комфорт' THEN CASE WHEN room_number IN ('201','202') THEN 'images/variants/comfort-business.jpg'
                             WHEN room_number BETWEEN '210' AND '219' THEN 'images/variants/comfort-city.jpg'
                             WHEN room_number BETWEEN '220' AND '229' THEN 'images/variants/comfort-spacious.jpg'
                             ELSE 'images/variants/comfort-city.jpg' END
    WHEN 'Люкс' THEN CASE WHEN room_number = '301' THEN 'images/variants/lux-president.jpg'
                          WHEN room_number BETWEEN '310' AND '314' THEN 'images/variants/lux-panorama.jpg'
                          WHEN room_number BETWEEN '315' AND '317' THEN 'images/variants/lux-classic.jpg'
                          ELSE 'images/variants/lux-panorama.jpg' END
  END,
  description = CASE rt.name
    WHEN 'Стандарт' THEN CASE WHEN room_number BETWEEN '120' AND '129' THEN 'Светлый номер с панорамным окном и рабочим столом.'
                              WHEN room_number BETWEEN '110' AND '119' THEN 'Уютный номер с классическим интерьером и удобной кроватью.'
                              ELSE 'Компактный номер с продуманным светом и мягкими тканями.' END
    WHEN 'Комфорт' THEN CASE WHEN room_number IN ('201','202') THEN 'Номер повышенной комфортности с отдельной рабочей зоной.'
                             WHEN room_number BETWEEN '220' AND '229' THEN 'Просторный номер с креслами и увеличенной ванной.'
                             ELSE 'Номер с видом на город, мягким диваном и кофе-станцией.' END
    WHEN 'Люкс' THEN CASE WHEN room_number = '301' THEN 'Президентский люкс с гостиной, кабинетом и панорамным видом.'
                          WHEN room_number BETWEEN '315' AND '317' THEN 'Классический люкс с просторной спальней и гостиной.'
                          ELSE 'Панорамный люкс с видом на набережную и отдельной гостиной.' END
  END
FROM room_types rt
WHERE rt.room_type_id = rooms.room_type_id;

-- Демо-гость уже заселен: 18.11 — 20.12
DO $$
DECLARE
  v_booking_id INTEGER;
  v_folio_id INTEGER;
  v_room_id INTEGER;
  v_guest_id INTEGER;
  v_doc_enc TEXT;
  v_doc_hash VARCHAR(64);
  v_doc_masked VARCHAR(50);
BEGIN
  SELECT guest_id, document_number, document_number_enc, document_number_hash
  INTO v_guest_id, v_doc_masked, v_doc_enc, v_doc_hash
  FROM guests WHERE guest_id = 1;

  SELECT room_id INTO v_room_id FROM rooms WHERE room_number = '111' LIMIT 1;

  IF NOT EXISTS (
    SELECT 1 FROM bookings
    WHERE guest_id = 1 AND status = 'CHECKED_IN' AND checkin_date = DATE '2026-11-18'
  ) THEN
    SELECT fn_create_booking(
      v_guest_id, v_room_id, 5, DATE '2026-11-18', DATE '2026-12-20',
      NULL, 'SITE', 2, 0, NULL, '127.0.0.1'
    ) INTO v_booking_id;

    UPDATE bookings
    SET status = 'CHECKED_IN',
        special_requests = 'Ранний заезд, высокий этаж'
    WHERE booking_id = v_booking_id;

    INSERT INTO check_ins (
      booking_id, manager_id, guest_document_number,
      guest_document_number_enc, guest_document_number_hash, actual_checkin_at
    ) VALUES (v_booking_id, 2, v_doc_masked, v_doc_enc, v_doc_hash, TIMESTAMP '2026-11-18 14:05:00');

    INSERT INTO folios (booking_id, status, opened_at)
    VALUES (v_booking_id, 'OPEN', TIMESTAMP '2026-11-18 14:05:00')
    RETURNING folio_id INTO v_folio_id;

    INSERT INTO folio_lines (folio_id, description, amount, line_type)
    VALUES (v_folio_id, 'Проживание с 18.11 по 20.12', 47840, 'ROOM');

    INSERT INTO service_orders (booking_id, service_id, user_id, quantity)
    VALUES (v_booking_id, 4, 1, 1);
  END IF;
END $$;

COMMIT;
