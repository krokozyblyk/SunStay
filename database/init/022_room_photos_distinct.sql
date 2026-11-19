-- =====================================================================================
--  SunStay: разные фото для номеров (4 варианта на категорию)
-- =====================================================================================

BEGIN;

UPDATE rooms SET image_url = CASE room_type_id
  WHEN 1 THEN 'images/rooms/standard-' || (((room_id - 1) % 4) + 1) || '.jpg'
  WHEN 2 THEN 'images/rooms/comfort-' || (((room_id - 1) % 4) + 1) || '.jpg'
  WHEN 3 THEN 'images/rooms/lux-' || (((room_id - 1) % 4) + 1) || '.jpg'
  ELSE image_url
END
WHERE room_type_id IN (1, 2, 3);

UPDATE room_types SET image_url = CASE room_type_id
  WHEN 1 THEN 'images/rooms/standard-4.jpg'
  WHEN 2 THEN 'images/rooms/comfort-4.jpg'
  WHEN 3 THEN 'images/rooms/lux-4.jpg'
  ELSE image_url
END
WHERE room_type_id IN (1, 2, 3);

COMMIT;
