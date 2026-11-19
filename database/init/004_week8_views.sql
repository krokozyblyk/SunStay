-- =====================================================================================
--  SunStay: неделя 8 — представления для статистики и отчётности
-- =====================================================================================

CREATE OR REPLACE VIEW v_occupancy_daily AS
WITH bounds AS (
    SELECT MIN(checkin_date) AS min_date,
           MAX(checkout_date) AS max_date
    FROM bookings
), dates AS (
    SELECT generate_series(min_date, max_date - 1, interval '1 day')::date AS report_date
    FROM bounds
), totals AS (
    SELECT COUNT(*)::numeric AS rooms_total FROM rooms
)
SELECT
    d.report_date,
    COALESCE(COUNT(DISTINCT b.room_id), 0) AS rooms_occupied,
    t.rooms_total AS rooms_available,
    ROUND(COALESCE(COUNT(DISTINCT b.room_id), 0) / NULLIF(t.rooms_total, 0) * 100, 2) AS occupancy_pct
FROM dates d
CROSS JOIN totals t
LEFT JOIN bookings b
    ON b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
   AND d.report_date >= b.checkin_date
   AND d.report_date < b.checkout_date
GROUP BY d.report_date, t.rooms_total
ORDER BY d.report_date;

CREATE OR REPLACE VIEW v_occupancy_by_type AS
WITH bounds AS (
    SELECT MIN(checkin_date) AS min_date,
           MAX(checkout_date) AS max_date
    FROM bookings
), dates AS (
    SELECT generate_series(min_date, max_date - 1, interval '1 day')::date AS report_date
    FROM bounds
), room_totals AS (
    SELECT rt.room_type_id, rt.name, COUNT(r.room_id)::numeric AS rooms_total
    FROM room_types rt
    LEFT JOIN rooms r ON r.room_type_id = rt.room_type_id
    GROUP BY rt.room_type_id, rt.name
)
SELECT
    d.report_date,
    rt.room_type_id,
    rt.name AS room_type,
    rt.rooms_total,
    COALESCE(COUNT(DISTINCT b.room_id), 0) AS rooms_occupied,
    ROUND(COALESCE(COUNT(DISTINCT b.room_id), 0) / NULLIF(rt.rooms_total, 0) * 100, 2) AS occupancy_pct
FROM dates d
CROSS JOIN room_totals rt
LEFT JOIN rooms r ON r.room_type_id = rt.room_type_id
LEFT JOIN bookings b
    ON b.room_id = r.room_id
   AND b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
   AND d.report_date >= b.checkin_date
   AND d.report_date < b.checkout_date
GROUP BY d.report_date, rt.room_type_id, rt.name, rt.rooms_total
ORDER BY d.report_date, rt.name;

CREATE OR REPLACE VIEW v_adr_revpar_daily AS
WITH bounds AS (
    SELECT MIN(checkin_date) AS min_date,
           MAX(checkout_date) AS max_date
    FROM bookings
), dates AS (
    SELECT generate_series(min_date, max_date - 1, interval '1 day')::date AS report_date
    FROM bounds
), revenue AS (
    SELECT
        d.report_date,
        SUM(rp.price_per_night) AS room_revenue
    FROM dates d
    JOIN bookings b
        ON b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
       AND d.report_date >= b.checkin_date
       AND d.report_date < b.checkout_date
    JOIN rate_plans rp ON rp.rate_id = b.rate_id
    GROUP BY d.report_date
), sold AS (
    SELECT d.report_date, COUNT(DISTINCT b.room_id)::numeric AS rooms_sold
    FROM dates d
    LEFT JOIN bookings b
        ON b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
       AND d.report_date >= b.checkin_date
       AND d.report_date < b.checkout_date
    GROUP BY d.report_date
), total_rooms AS (
    SELECT COUNT(*)::numeric AS rooms_available FROM rooms
)
SELECT
    d.report_date,
    COALESCE(r.room_revenue, 0) AS room_revenue,
    COALESCE(s.rooms_sold, 0) AS rooms_sold,
    tr.rooms_available,
    ROUND(COALESCE(r.room_revenue, 0) / NULLIF(s.rooms_sold, 0), 2) AS adr,
    ROUND(COALESCE(r.room_revenue, 0) / NULLIF(tr.rooms_available, 0), 2) AS revpar
FROM dates d
CROSS JOIN total_rooms tr
LEFT JOIN revenue r ON r.report_date = d.report_date
LEFT JOIN sold s ON s.report_date = d.report_date
ORDER BY d.report_date;

CREATE OR REPLACE VIEW v_cancellations_monthly AS
SELECT
    date_trunc('month', checkin_date)::date AS month,
    COUNT(*) AS total_bookings,
    COUNT(*) FILTER (WHERE status = 'CANCELLED') AS cancelled,
    COUNT(*) FILTER (WHERE status = 'NO_SHOW') AS no_show,
    ROUND(COUNT(*) FILTER (WHERE status = 'CANCELLED')::numeric / NULLIF(COUNT(*), 0) * 100, 2) AS cancellation_pct,
    ROUND(COUNT(*) FILTER (WHERE status = 'NO_SHOW')::numeric / NULLIF(COUNT(*), 0) * 100, 2) AS no_show_pct
FROM bookings
GROUP BY date_trunc('month', checkin_date)::date
ORDER BY month;

CREATE OR REPLACE VIEW v_cancellation_reasons AS
SELECT
    date_trunc('month', b.checkin_date)::date AS month,
    COALESCE(cr.name, 'Без причины') AS reason,
    COUNT(*) AS bookings
FROM bookings b
LEFT JOIN cancellation_reasons cr ON cr.reason_id = b.cancellation_reason_id
WHERE b.status = 'CANCELLED'
GROUP BY date_trunc('month', b.checkin_date)::date, COALESCE(cr.name, 'Без причины')
ORDER BY month, bookings DESC;

CREATE OR REPLACE VIEW v_room_status_today AS
SELECT
    rs.name AS status,
    COUNT(r.room_id) AS rooms,
    ROUND(COUNT(r.room_id)::numeric / NULLIF((SELECT COUNT(*) FROM rooms), 0) * 100, 2) AS percent
FROM room_statuses rs
LEFT JOIN rooms r ON r.status_id = rs.status_id
GROUP BY rs.name
ORDER BY rs.name;

CREATE OR REPLACE VIEW v_consumables_stock AS
SELECT
    c.consumable_id,
    c.name,
    c.unit,
    c.stock_quantity,
    c.min_stock,
    (c.stock_quantity < c.min_stock) AS deficit,
    COALESCE(SUM(cu.quantity), 0) AS used_total,
    COALESCE(SUM(cu.quantity) FILTER (WHERE ht.assigned_at >= now() - interval '30 days'), 0) AS used_30d
FROM consumables c
LEFT JOIN consumable_usage cu ON cu.consumable_id = c.consumable_id
LEFT JOIN housekeeping_tasks ht ON ht.task_id = cu.task_id
GROUP BY c.consumable_id, c.name, c.unit, c.stock_quantity, c.min_stock
ORDER BY c.name;

CREATE OR REPLACE VIEW v_revenue_by_service AS
SELECT
    date_trunc('month', so.ordered_at)::date AS month,
    s.service_id,
    s.name AS service,
    SUM(so.quantity) AS quantity,
    SUM(so.quantity * s.price) AS revenue
FROM service_orders so
JOIN services s ON s.service_id = so.service_id
GROUP BY date_trunc('month', so.ordered_at)::date, s.service_id, s.name
ORDER BY month, revenue DESC;

CREATE OR REPLACE VIEW v_payments_by_method AS
SELECT
    method,
    COUNT(*) AS payments,
    SUM(amount) AS total
FROM payments
GROUP BY method
ORDER BY total DESC;

CREATE OR REPLACE VIEW v_dashboard_today AS
SELECT
    (SELECT COUNT(DISTINCT room_id)
     FROM bookings
     WHERE CURRENT_DATE >= checkin_date
       AND CURRENT_DATE < checkout_date
       AND status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')) AS occupied_rooms,
    (SELECT COUNT(*) FROM rooms) AS total_rooms,
    (SELECT ROUND(COUNT(DISTINCT room_id)::numeric / NULLIF((SELECT COUNT(*) FROM rooms), 0) * 100, 2)
     FROM bookings
     WHERE CURRENT_DATE >= checkin_date
       AND CURRENT_DATE < checkout_date
       AND status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')) AS occupancy_pct,
    (SELECT COUNT(*) FROM bookings WHERE checkin_date = CURRENT_DATE AND status IN ('NEW','CONFIRMED')) AS arrivals_today,
    (SELECT COUNT(*) FROM bookings WHERE checkout_date = CURRENT_DATE AND status = 'CHECKED_IN') AS departures_today,
    (SELECT COALESCE(SUM(amount), 0) FROM folio_lines WHERE line_type = 'ROOM' AND charge_date = CURRENT_DATE) AS room_revenue_today,
    (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE paid_at::date = CURRENT_DATE) AS payments_today,
    (SELECT ROUND(SUM(rp.price_per_night) / NULLIF(COUNT(*), 0), 2)
     FROM bookings b
     JOIN rate_plans rp ON rp.rate_id = b.rate_id
     WHERE CURRENT_DATE >= b.checkin_date
       AND CURRENT_DATE < b.checkout_date
       AND b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')) AS adr_today,
    (SELECT ROUND(SUM(rp.price_per_night) / NULLIF((SELECT COUNT(*) FROM rooms), 0), 2)
     FROM bookings b
     JOIN rate_plans rp ON rp.rate_id = b.rate_id
     WHERE CURRENT_DATE >= b.checkin_date
       AND CURRENT_DATE < b.checkout_date
       AND b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')) AS revpar_today;
