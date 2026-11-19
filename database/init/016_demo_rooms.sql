-- =====================================================================================
--  SunStay: 48 демонстрационных номеров
-- =====================================================================================

BEGIN;

-- Стандарт: 20 номеров (110–129), этажи 1–2
INSERT INTO rooms (room_number, room_type_id, status_id, floor)
SELECT '1' || lpad(i::text, 2, '0'), 1, 6, CASE WHEN i <= 19 THEN 1 ELSE 2 END
FROM generate_series(10, 29) AS i
ON CONFLICT (room_number) DO NOTHING;

-- Комфорт: 20 номеров (210–229), этажи 2–3
INSERT INTO rooms (room_number, room_type_id, status_id, floor)
SELECT '2' || lpad(i::text, 2, '0'), 2, 6, CASE WHEN i <= 19 THEN 2 ELSE 3 END
FROM generate_series(10, 29) AS i
ON CONFLICT (room_number) DO NOTHING;

-- Люкс: 8 номеров (310–317), этаж 3–4
INSERT INTO rooms (room_number, room_type_id, status_id, floor)
SELECT '3' || lpad(i::text, 2, '0'), 3, 6, CASE WHEN i <= 14 THEN 3 ELSE 4 END
FROM generate_series(10, 17) AS i
ON CONFLICT (room_number) DO NOTHING;

COMMIT;
