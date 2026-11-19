-- =====================================================================================
--  SunStay: релевантные фото для услуг
-- =====================================================================================

BEGIN;

UPDATE services SET image_url = 'images/services/breakfast.jpg' WHERE name LIKE '%Завтрак%';
UPDATE services SET image_url = 'images/services/parking.jpg' WHERE name LIKE '%Парковка%';
UPDATE services SET image_url = 'images/services/transfer.jpg' WHERE name LIKE '%Трансфер%';
UPDATE services SET image_url = 'images/services/spa.jpg' WHERE name LIKE '%СПА%' OR name LIKE '%Спа%';

COMMIT;
