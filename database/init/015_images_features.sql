-- =====================================================================================
--  SunStay: изображения, feature flags, идемпотентность
-- =====================================================================================

BEGIN;

ALTER TABLE room_types ADD COLUMN image_url TEXT;
ALTER TABLE services ADD COLUMN image_url TEXT;

UPDATE room_types SET image_url = 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=80' WHERE name = 'Стандарт';
UPDATE room_types SET image_url = 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80' WHERE name = 'Комфорт';
UPDATE room_types SET image_url = 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80' WHERE name = 'Люкс';

UPDATE services SET image_url = 'https://images.unsplash.com/photo-1533777857889-4be7c70b33f7?auto=format&fit=crop&w=900&q=80' WHERE name ILIKE '%завтрак%';
UPDATE services SET image_url = 'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=900&q=80' WHERE name ILIKE '%спа%' OR name ILIKE '%массаж%';
UPDATE services SET image_url = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80' WHERE image_url IS NULL;

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
