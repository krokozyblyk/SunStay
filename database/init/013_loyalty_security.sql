-- =====================================================================================
--  SunStay: лояльность, шаблоны сообщений, 2FA, политика паролей
-- =====================================================================================

BEGIN;

CREATE TABLE loyalty_accounts (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    points_balance INTEGER NOT NULL DEFAULT 0 CHECK (points_balance >= 0),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE loyalty_transactions (
    transaction_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    points INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('EARN', 'REDEEM', 'ADJUST')),
    description VARCHAR(255),
    booking_id INTEGER REFERENCES bookings(booking_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_loyalty_tx_user ON loyalty_transactions(user_id, created_at DESC);

CREATE TABLE message_templates (
    template_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    subject VARCHAR(200),
    body TEXT NOT NULL,
    template_type VARCHAR(30) NOT NULL DEFAULT 'NOTIFICATION',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

ALTER TABLE users
    ADD COLUMN totp_secret_enc TEXT,
    ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN totp_recovery_codes JSONB;

INSERT INTO system_settings (key, value)
VALUES
    ('password.min_length', '8'::jsonb),
    ('password.require_uppercase', 'true'::jsonb),
    ('password.require_digit', 'true'::jsonb),
    ('password.require_special', 'false'::jsonb),
    ('loyalty.earn_percent', '5'::jsonb),
    ('loyalty.redeem_max_percent', '30'::jsonb)
ON CONFLICT (key) DO NOTHING;

INSERT INTO message_templates (name, subject, body, template_type)
VALUES
    ('Подтверждение брони', 'Ваша бронь подтверждена', 'Уважаемый гость, ваша бронь #{{booking_id}} подтверждена. Заезд {{checkin}}, выезд {{checkout}}.', 'NOTIFICATION'),
    ('Напоминание о заезде', 'Напоминание о заезде', 'Напоминаем, что ваш заезд {{checkin}} в SunStay. Будем рады вас видеть!', 'NOTIFICATION'),
    ('Счёт готов', 'Ваш счёт готов', 'Ваш счёт по брони #{{booking_id}} готов к оплате.', 'NOTIFICATION')
ON CONFLICT (name) DO NOTHING;

COMMIT;
