-- =====================================================================================
--  SunStay: безопасность, аудит, блокировки, удержание брони, бэкапы
-- =====================================================================================

BEGIN;

ALTER TABLE users
    ADD COLUMN last_seen_at TIMESTAMPTZ,
    ADD COLUMN block_reason TEXT,
    ADD COLUMN blocked_at TIMESTAMPTZ,
    ADD COLUMN blocked_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

CREATE TABLE user_block_reasons (
    reason_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name      VARCHAR(150) NOT NULL UNIQUE
);

INSERT INTO user_block_reasons (name) VALUES
    ('Нарушение правил'),
    ('Подозрительная активность'),
    ('Неактуальная учётная запись'),
    ('По заявлению сотрудника')
ON CONFLICT (name) DO NOTHING;

ALTER TABLE audit_log
    ADD COLUMN is_error BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN error_message TEXT,
    ADD COLUMN severity VARCHAR(10) NOT NULL DEFAULT 'INFO',
    ADD COLUMN event_type VARCHAR(30) NOT NULL DEFAULT 'DATA_CHANGE';

ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS audit_log_action_check;
ALTER TABLE audit_log
    ADD CONSTRAINT audit_log_action_check CHECK (
        action IN (
            'INSERT', 'UPDATE', 'DELETE',
            'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGIN_BLOCKED',
            'ERROR', 'AUTO_RELEASE'
        )
    );

CREATE INDEX idx_audit_error ON audit_log(is_error) WHERE is_error;
CREATE INDEX idx_audit_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at);
CREATE INDEX idx_users_last_seen ON users(last_seen_at);

ALTER TABLE bookings
    ADD COLUMN arrival_time TIME,
    ADD COLUMN hold_minutes INTEGER NOT NULL DEFAULT 60
        CHECK (hold_minutes BETWEEN 5 AND 1440),
    ADD COLUMN hold_until TIMESTAMPTZ;

CREATE INDEX idx_bookings_hold_until
    ON bookings(hold_until)
    WHERE hold_until IS NOT NULL;

INSERT INTO cancellation_reasons (name)
SELECT 'Истекло время ожидания'
WHERE NOT EXISTS (
    SELECT 1 FROM cancellation_reasons WHERE name = 'Истекло время ожидания'
);

INSERT INTO system_settings (key, value) VALUES
    ('backup.enabled', 'true'::jsonb),
    ('backup.schedule_time', '"03:00"'::jsonb),
    ('backup.last_run_at', 'null'::jsonb),
    ('backup.last_status', '"never"'::jsonb),
    ('backup.last_error', 'null'::jsonb)
ON CONFLICT (key) DO NOTHING;

COMMIT;

CREATE OR REPLACE FUNCTION fn_audit_row() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id INTEGER;
    v_ip VARCHAR(50);
    v_ua VARCHAR(255);
    v_request_id VARCHAR(100);
    v_record_id INTEGER;
    v_old JSONB;
    v_new JSONB;
BEGIN
    v_user_id := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;
    v_ip := NULLIF(current_setting('app.client_ip', true), '');
    v_ua := NULLIF(current_setting('app.user_agent', true), '');
    v_request_id := NULLIF(current_setting('app.request_id', true), '');

    -- Не засоряем аудит обновлениями last_seen_at при каждом запросе.
    IF TG_TABLE_NAME = 'users' AND TG_OP = 'UPDATE' THEN
        IF (to_jsonb(OLD) - 'last_seen_at') = (to_jsonb(NEW) - 'last_seen_at') THEN
            RETURN NEW;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        v_record_id := (to_jsonb(OLD) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD);
        v_new := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD);
        v_new := to_jsonb(NEW);
    ELSE
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := NULL;
        v_new := to_jsonb(NEW);
    END IF;

    -- Не сохраняем в аудит шифротекст и хэши чувствительных полей.
    IF v_old IS NOT NULL THEN
        v_old := v_old
            - 'phone_enc' - 'document_number_enc' - 'guest_document_number_enc'
            - 'phone_hash' - 'document_number_hash' - 'guest_document_number_hash'
            - 'password_hash';
    END IF;
    IF v_new IS NOT NULL THEN
        v_new := v_new
            - 'phone_enc' - 'document_number_enc' - 'guest_document_number_enc'
            - 'phone_hash' - 'document_number_hash' - 'guest_document_number_hash'
            - 'password_hash';
    END IF;

    INSERT INTO audit_log (
        user_id, table_name, record_id, action,
        old_value, new_value, ip_address, user_agent, request_id,
        is_error, event_type, severity
    ) VALUES (
        v_user_id, TG_TABLE_NAME, v_record_id, TG_OP,
        v_old::TEXT, v_new::TEXT, v_ip, v_ua, v_request_id,
        FALSE, 'DATA_CHANGE', 'INFO'
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;
