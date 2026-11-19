-- =====================================================================================
--  SunStay: уникальное фото для КАЖДОГО номера
-- =====================================================================================

BEGIN;

WITH numbered AS (
    SELECT room_id, row_number() OVER (ORDER BY room_id) AS n
    FROM rooms
)
UPDATE rooms r
SET image_url = 'images/unique/room-' || lpad(n.n::text, 3, '0') || '.jpg'
FROM numbered n
WHERE r.room_id = n.room_id;

COMMIT;
