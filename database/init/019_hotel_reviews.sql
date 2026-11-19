-- =====================================================================================
--  SunStay: отзывы об отеле
-- =====================================================================================

BEGIN;

ALTER TABLE reviews ALTER COLUMN booking_id DROP NOT NULL;
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS review_type VARCHAR(20) NOT NULL DEFAULT 'BOOKING';
UPDATE reviews SET review_type = 'BOOKING' WHERE review_type IS NULL;

CREATE INDEX IF NOT EXISTS idx_reviews_type ON reviews(review_type, status, created_at DESC);

COMMIT;
