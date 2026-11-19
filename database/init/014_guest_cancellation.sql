-- =====================================================================================
--  SunStay: особые пожелания и политика отмены
-- =====================================================================================

BEGIN;

ALTER TABLE bookings
    ADD COLUMN special_requests TEXT;

ALTER TABLE waitlist_entries
    ADD COLUMN converted_booking_id INTEGER REFERENCES bookings(booking_id) ON DELETE SET NULL;

INSERT INTO system_settings (key, value)
VALUES
    ('cancellation.free_hours', '48'::jsonb),
    ('cancellation.half_hours', '24'::jsonb),
    ('cancellation.half_percent', '50'::jsonb)
ON CONFLICT (key) DO NOTHING;

COMMIT;
