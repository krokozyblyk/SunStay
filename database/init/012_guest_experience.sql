-- =====================================================================================
--  SunStay: гостевой опыт — отзывы, лист ожидания, уведомления, курсы валют
-- =====================================================================================

BEGIN;

CREATE TABLE reviews (
    review_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id INTEGER NOT NULL UNIQUE REFERENCES bookings(booking_id) ON DELETE CASCADE,
    guest_id INTEGER NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(150),
    body TEXT NOT NULL CHECK (length(body) BETWEEN 10 AND 2000),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    moderated_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    moderated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_reviews_status ON reviews(status, created_at DESC);
CREATE INDEX idx_reviews_guest ON reviews(guest_id, created_at DESC);

CREATE TRIGGER trg_audit_reviews
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('review_id');

CREATE TABLE waitlist_entries (
    waitlist_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guest_name VARCHAR(200) NOT NULL,
    email VARCHAR(150),
    phone_masked VARCHAR(30),
    phone_enc TEXT,
    phone_hash VARCHAR(64),
    room_type_id INTEGER REFERENCES room_types(room_type_id) ON DELETE SET NULL,
    checkin_date DATE NOT NULL,
    checkout_date DATE NOT NULL,
    adults INTEGER NOT NULL DEFAULT 1 CHECK (adults BETWEEN 1 AND 10),
    children INTEGER NOT NULL DEFAULT 0 CHECK (children BETWEEN 0 AND 10),
    note TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'WAITING'
        CHECK (status IN ('WAITING', 'NOTIFIED', 'CONVERTED', 'CANCELLED')),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    notified_at TIMESTAMP,
    processed_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    processed_at TIMESTAMP,
    CHECK (checkout_date > checkin_date)
);

CREATE INDEX idx_waitlist_status ON waitlist_entries(status, checkin_date);
CREATE INDEX idx_waitlist_dates ON waitlist_entries(checkin_date, checkout_date);

CREATE TRIGGER trg_audit_waitlist
AFTER INSERT OR UPDATE OR DELETE ON waitlist_entries
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('waitlist_id');

CREATE TABLE notifications (
    notification_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT,
    link VARCHAR(255),
    read_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, read_at, created_at DESC);

INSERT INTO system_settings (key, value)
VALUES
    ('currency.usd_rate', '90'::jsonb),
    ('currency.eur_rate', '100'::jsonb)
ON CONFLICT (key) DO NOTHING;

INSERT INTO permissions (code, module, description)
VALUES ('reviews:moderate', 'reviews', 'Модерация отзывов гостей')
ON CONFLICT (code) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.name IN ('Управляющий отелем', 'Администратор БД')
  AND p.code = 'reviews:moderate'
ON CONFLICT DO NOTHING;

-- Демонстрационные одобренные отзывы по завершённым проживаниям.
WITH picked AS (
    SELECT b.booking_id, b.guest_id,
           row_number() OVER (ORDER BY b.booking_id) AS rn
    FROM bookings b
    WHERE b.status = 'CHECKED_OUT'
    ORDER BY b.booking_id
    LIMIT 3
)
INSERT INTO reviews (booking_id, guest_id, rating, title, body, status, created_at)
SELECT
    p.booking_id,
    p.guest_id,
    CASE p.rn WHEN 1 THEN 5 WHEN 2 THEN 4 ELSE 5 END,
    CASE p.rn
        WHEN 1 THEN 'Вернусь снова'
        WHEN 2 THEN 'Тихо и удобно'
        ELSE 'Отличный сервис'
    END,
    CASE p.rn
        WHEN 1 THEN 'Очень удобное расположение, внимательный персонал и спокойные номера. Завтрак свежий, всё продумано до мелочей.'
        WHEN 2 THEN 'Номер чистый, кровать удобная, интернет стабильный. Немного слышно улицу, но в целом отличный вариант для поездки.'
        ELSE 'Быстрое заселение, красивый интерьер и помощь с любыми вопросами. Отдельное спасибо команде за атмосферу.'
    END,
    'APPROVED',
    now() - (p.rn * interval '2 days')
FROM picked p
ON CONFLICT (booking_id) DO NOTHING;

COMMIT;
