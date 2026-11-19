$ErrorActionPreference = "Stop"

docker compose exec -T db pg_restore -U postgres -d hotel --clean --if-exists --no-owner "/backups/sunstay_latest.dump"

Write-Output "База восстановлена из backups/sunstay_latest.dump"
