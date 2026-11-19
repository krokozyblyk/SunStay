-- =====================================================================================
--  SunStay: изображения, feature flags, идемпотентность
-- =====================================================================================

BEGIN;

ALTER TABLE room_types ADD COLUMN image_url TEXT;
ALTER TABLE services ADD COLUMN image_url TEXT;

UPDATE room_types SET image_url = 'images/room-standard.jpg' WHERE name = 'Стандарт';
UPDATE room_types SET image_url = 'images/room-comfort.jpg' WHERE name = 'Комфорт';
UPDATE room_types SET image_url = 'images/room-lux.jpg' WHERE name = 'Люкс';

UPDATE services SET image_url = 'images/service-breakfast.jpg' WHERE name ILIKE '%завтрак%';
UPDATE services SET image_url = 'images/service-spa.jpg' WHERE name ILIKE '%спа%' OR name ILIKE '%массаж%';
UPDATE services SET image_url = 'images/service-other.jpg' WHERE image_url IS NULL;

INSERT INTO system_settings (key, value)
VALUES
    ('feature.reviews', 'true'::jsonb),
    ('feature.waitlist', 'true'::jsonb),
    ('feature.loyalty', 'true'::jsonb),
    ('feature.special_requests', 'true'::jsonb)
ON CONFLICT (key) DO NOTHING;

CREATE TABLE idempotency_keys (
    key TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    endpoint VARCHAR(200) NOT NULL,
    response JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    expires_at TIMESTAMP NOT NULL DEFAULT now() + interval '24 hours'
);

CREATE INDEX idx_idempotency_expires ON idempotency_keys(expires_at);

COMMIT;
