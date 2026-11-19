-- =====================================================================================
--  SunStay: шифрование чувствительных контактов
--  Открытые значения заменяются маскированными, полные — шифруются в *_enc,
--  для поиска и уникальности используются *_hash.
-- =====================================================================================

BEGIN;

ALTER TABLE guests
    ADD COLUMN phone_enc TEXT,
    ADD COLUMN document_number_enc TEXT,
    ADD COLUMN phone_hash VARCHAR(64),
    ADD COLUMN document_number_hash VARCHAR(64);

DO $$
DECLARE
    c RECORD;
BEGIN
    FOR c IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'guests'::regclass
          AND contype = 'u'
    LOOP
        IF c.conname = 'guests_document_number_key' THEN
            EXECUTE format('ALTER TABLE guests DROP CONSTRAINT %I', c.conname);
        END IF;
    END LOOP;
END;
$$;

CREATE UNIQUE INDEX uq_guests_document_hash
    ON guests(document_number_hash)
    WHERE document_number_hash IS NOT NULL;

CREATE INDEX idx_guests_phone_hash
    ON guests(phone_hash);

ALTER TABLE users
    ADD COLUMN phone_enc TEXT,
    ADD COLUMN phone_hash VARCHAR(64);

CREATE INDEX idx_users_phone_hash
    ON users(phone_hash);

ALTER TABLE check_ins
    ADD COLUMN guest_document_number_enc TEXT,
    ADD COLUMN guest_document_number_hash VARCHAR(64);

CREATE INDEX idx_check_ins_document_hash
    ON check_ins(guest_document_number_hash);

COMMIT;
