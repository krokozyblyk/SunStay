-- =====================================================================================
--  SunStay: вместимость номеров, статус 2FA, нормы расходников
-- =====================================================================================

BEGIN;

ALTER TABLE rooms ADD COLUMN IF NOT EXISTS capacity INTEGER;
UPDATE rooms SET capacity = CASE
  WHEN room_type_id = 1 THEN
    CASE WHEN room_number IN ('1','101','102','103') THEN 2
         WHEN room_number BETWEEN '110' AND '113' THEN 1
         WHEN room_number BETWEEN '114' AND '119' THEN 2
         WHEN room_number BETWEEN '120' AND '124' THEN 3
         WHEN room_number BETWEEN '125' AND '129' THEN 4
         ELSE 2 END
  WHEN room_type_id = 2 THEN
    CASE WHEN room_number IN ('201','202') THEN 2
         WHEN room_number BETWEEN '210' AND '214' THEN 2
         WHEN room_number BETWEEN '215' AND '219' THEN 3
         WHEN room_number BETWEEN '220' AND '229' THEN 4
         ELSE 3 END
  WHEN room_type_id = 3 THEN
    CASE WHEN room_number = '301' THEN 4
         WHEN room_number BETWEEN '310' AND '314' THEN 3
         WHEN room_number BETWEEN '315' AND '317' THEN 4
         ELSE 4 END
  ELSE 2
END;

ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_setup_requested BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE consumables ADD COLUMN IF NOT EXISTS max_stock NUMERIC(10,2) NOT NULL DEFAULT 0;
UPDATE consumables SET max_stock = 120, stock_quantity = 120, min_stock = 30 WHERE name LIKE '%Полотенце%';
UPDATE consumables SET max_stock = 100, stock_quantity = 100, min_stock = 25 WHERE name LIKE '%Шампунь%';
UPDATE consumables SET max_stock = 300, stock_quantity = 300, min_stock = 75 WHERE name LIKE '%туалетной бумаги%' OR name LIKE '%бумага%';
UPDATE consumables SET max_stock = 40, stock_quantity = 40, min_stock = 10 WHERE name LIKE '%Моющее%';

COMMIT;
