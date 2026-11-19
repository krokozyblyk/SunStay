$ErrorActionPreference = "Stop"

docker compose exec -T db pg_dump -U postgres -d hotel -Fc -f "/backups/sunstay_latest.dump"

Write-Output "Резервная копия обновлена: backups/sunstay_latest.dump"
