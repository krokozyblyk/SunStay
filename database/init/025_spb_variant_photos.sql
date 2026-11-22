-- =====================================================================================
--  SunStay: уникальные фото номеров из отелей Санкт-Петербурга
--  Каждый номер получает отдельный файл, подходящий к его варианту.
-- =====================================================================================

BEGIN;

WITH ranked AS (
    SELECT
        r.room_id,
        rt.name AS type_name,
        COALESCE(r.variant_name, '') AS variant,
        row_number() OVER (
            PARTITION BY rt.name, COALESCE(r.variant_name, '')
            ORDER BY r.room_id
        ) AS rn
    FROM rooms r
    JOIN room_types rt ON rt.room_type_id = r.room_type_id
)
UPDATE rooms r
SET image_url = 'images/spb/' || CASE
    WHEN ranked.type_name = 'Стандарт' AND ranked.variant = 'Классика' THEN
        CASE WHEN ranked.rn <= 8 THEN 'standard-classic-' || ranked.rn || '.jpg'
             ELSE 'standard-cozy-' || (ranked.rn - 8) || '.jpg' END
    WHEN ranked.type_name = 'Стандарт' AND ranked.variant = 'Панорама' THEN
        CASE WHEN ranked.rn <= 8 THEN 'standard-panorama-' || ranked.rn || '.jpg'
             ELSE 'standard-cozy-' || (ranked.rn - 4) || '.jpg' END
    WHEN ranked.type_name = 'Стандарт' THEN
        'standard-cozy-8.jpg'

    WHEN ranked.type_name = 'Комфорт' AND ranked.variant = 'Бизнес' THEN
        'comfort-business-' || ranked.rn || '.jpg'
    WHEN ranked.type_name = 'Комфорт' AND ranked.variant = 'Городской вид' THEN
        CASE WHEN ranked.rn <= 8 THEN 'comfort-city-' || ranked.rn || '.jpg'
             ELSE 'comfort-business-' || (ranked.rn - 6) || '.jpg' END
    WHEN ranked.type_name = 'Комфорт' AND ranked.variant = 'Простор' THEN
        CASE WHEN ranked.rn <= 7 THEN 'comfort-spacious-' || ranked.rn || '.jpg'
             ELSE 'comfort-business-' || (ranked.rn - 2) || '.jpg' END

    WHEN ranked.type_name = 'Люкс' AND ranked.variant = 'Классик' THEN
        'lux-classic-' || ranked.rn || '.jpg'
    WHEN ranked.type_name = 'Люкс' AND ranked.variant = 'Панорамный' THEN
        CASE WHEN ranked.rn <= 3 THEN 'lux-panorama-' || ranked.rn || '.jpg'
             ELSE 'lux-president-' || (ranked.rn - 2) || '.jpg' END
    WHEN ranked.type_name = 'Люкс' AND ranked.variant = 'Президентский' THEN
        'lux-president-' || (ranked.rn + 2) || '.jpg'

    ELSE 'standard-cozy-8.jpg'
END
FROM ranked
WHERE r.room_id = ranked.room_id
  AND r.image_url NOT LIKE 'images/spb/%';

COMMIT;
