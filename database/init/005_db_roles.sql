-- =====================================================================================
--  SunStay: роли базы данных для приложения и аналитики
-- =====================================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sunstay_app') THEN
        CREATE ROLE sunstay_app LOGIN PASSWORD 'sunstay_app' NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sunstay_analytics') THEN
        CREATE ROLE sunstay_analytics LOGIN PASSWORD 'sunstay_analytics' NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;

    EXECUTE format('GRANT CONNECT ON DATABASE %I TO sunstay_app', current_database());
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO sunstay_analytics', current_database());
END;
$$;

GRANT USAGE ON SCHEMA public TO sunstay_app;
GRANT USAGE ON SCHEMA public TO sunstay_analytics;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sunstay_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sunstay_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO sunstay_app;
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA public TO sunstay_app;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO sunstay_analytics;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sunstay_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO sunstay_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO sunstay_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO sunstay_analytics;
