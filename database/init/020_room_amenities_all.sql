-- =====================================================================================
--  SunStay: удобства во всех номерах (чтобы фильтры поиска работали)
-- =====================================================================================

BEGIN;

INSERT INTO room_amenities (room_id, amenity_id)
SELECT r.room_id, a.amenity_id
FROM rooms r
CROSS JOIN amenities a
WHERE (a.name = 'Wi-Fi' OR a.name = 'Кондиционер')
  AND NOT EXISTS (
    SELECT 1 FROM room_amenities ra
    WHERE ra.room_id = r.room_id AND ra.amenity_id = a.amenity_id
  );

INSERT INTO room_amenities (room_id, amenity_id)
SELECT r.room_id, a.amenity_id
FROM rooms r
CROSS JOIN amenities a
WHERE r.room_type_id IN (2, 3)
  AND a.name IN ('Мини-бар', 'Сейф')
  AND NOT EXISTS (
    SELECT 1 FROM room_amenities ra
    WHERE ra.room_id = r.room_id AND ra.amenity_id = a.amenity_id
  );

INSERT INTO room_amenities (room_id, amenity_id)
SELECT r.room_id, a.amenity_id
FROM rooms r
CROSS JOIN amenities a
WHERE r.room_type_id = 3
  AND a.name = 'Балкон'
  AND NOT EXISTS (
    SELECT 1 FROM room_amenities ra
    WHERE ra.room_id = r.room_id AND ra.amenity_id = a.amenity_id
  );

INSERT INTO room_amenities (room_id, amenity_id)
SELECT r.room_id, a.amenity_id
FROM rooms r
CROSS JOIN amenities a
WHERE r.room_type_id = 1
  AND a.name = 'Сейф'
  AND (r.room_id % 3) = 0
  AND NOT EXISTS (
    SELECT 1 FROM room_amenities ra
    WHERE ra.room_id = r.room_id AND ra.amenity_id = a.amenity_id
  );

COMMIT;
