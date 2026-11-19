$ErrorActionPreference = "Stop"

docker compose exec -T db pg_dump -U postgres -d hotel -Fc -f "/backups/sunstay_latest.dump"
docker compose exec -T db psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS hotel_restore_test;"
docker compose exec -T db psql -U postgres -d postgres -c "CREATE DATABASE hotel_restore_test;"
docker compose exec -T db pg_restore -U postgres -d hotel_restore_test --no-owner "/backups/sunstay_latest.dump"

$tables = docker compose exec -T db psql -U postgres -d hotel_restore_test -t -A -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"
$bookings = docker compose exec -T db psql -U postgres -d hotel_restore_test -t -A -c "SELECT count(*) FROM bookings;"

Write-Output "Восстановлено таблиц: $($tables.Trim())"
Write-Output "Восстановлено броней: $($bookings.Trim())"

docker compose exec -T db psql -U postgres -d postgres -c "DROP DATABASE hotel_restore_test;"
Write-Output "Тест restore завершён успешно"
