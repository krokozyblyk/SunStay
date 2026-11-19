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
