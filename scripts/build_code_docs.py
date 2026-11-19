from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SERVER_FILES = [
    "backend/requirements.txt",
    "backend/Dockerfile",
    "backend/app/main.py",
    "backend/app/config.py",
    "backend/app/db.py",
    "backend/app/security.py",
    "backend/app/crypto.py",
    "backend/app/audit.py",
    "backend/app/migrations.py",
    "backend/app/schedulers.py",
    "backend/app/deps.py",
    "backend/app/schemas.py",
    "backend/app/utils.py",
    "backend/app/api/auth.py",
    "backend/app/api/public.py",
    "backend/app/api/guest.py",
    "backend/app/api/manager.py",
    "backend/app/api/housekeeping.py",
    "backend/app/api/admin.py",
    "backend/app/api/reports.py",
    "backend/app/api/imports.py",
    "backend/app/services/pdf.py",
    "backend/app/services/backup.py",
    "backend/tests/test_api.py",
    "analytics/requirements.txt",
    "analytics/Dockerfile",
    "analytics/app/main.py",
    "docker-compose.yml",
    "frontend/nginx.conf",
]

DATABASE_FILES = [
    "database/init/000_extensions.sql",
    "database/init/001_hotel_db.sql",
    "database/init/002_week5.sql",
    "database/init/003_week6.sql",
    "database/init/004_week8_views.sql",
    "database/init/005_db_roles.sql",
    "database/init/006_fix_checkout.sql",
    "database/init/007_demo_current.sql",
    "database/init/008_security_features.sql",
    "database/init/008b_audit_function.sql",
    "database/init/009_encryption.sql",
    "database/init/010_secure_checkin_hold.sql",
    "database/init/011_closed_day_fix.sql",
    "database/tests/week5_tests.sql",
]


def collect_frontend() -> list[str]:
    files: list[str] = [
        "frontend/package.json",
        "frontend/vite.config.ts",
        "frontend/tailwind.config.js",
        "frontend/postcss.config.js",
        "frontend/index.html",
        "frontend/nginx.conf",
        "frontend/Dockerfile",
    ]
    for path in sorted((ROOT / "frontend" / "src").rglob("*")):
        if path.is_file() and path.suffix in {".ts", ".tsx", ".css"}:
            files.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    for path in sorted((ROOT / "frontend" / "scripts").glob("*")):
        if path.is_file():
            files.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return files


def write_doc(output: Path, title: str, files: list[str], intro: str) -> None:
    lines = [
        f"# {title}",
        "",
        f"> Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "",
        intro,
        "",
        "## Состав",
        "",
    ]
    for relative in files:
        lines.append(f"- `{relative}`")
    lines.append("")
    for relative in files:
        path = ROOT / relative
        if not path.exists():
            continue
        suffix = path.suffix.lower()
        language = {
            ".py": "python",
            ".sql": "sql",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".css": "css",
            ".json": "json",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".html": "html",
            ".conf": "nginx",
            ".mjs": "javascript",
            "": "text",
        }.get(suffix, "text")
        if path.name == "Dockerfile":
            language = "dockerfile"
        lines.extend([f"## `{relative}`", "", f"```{language}", path.read_text(encoding="utf-8"), "```", ""])
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    write_doc(
        ROOT / "backend" / "CODE_SERVER.md",
        "SunStay — текст серверной части",
        SERVER_FILES,
        "Полные листинги FastAPI-ядра, analytics-микросервиса, конфигурации Docker Compose, PDF-сервиса и API-тестов. "
        "Файл является приложением к проекту и не вставляется в пояснительную записку целиком.",
    )
    write_doc(
        ROOT / "database" / "CODE_DATABASE.md",
        "SunStay — текст скриптов базы данных",
        DATABASE_FILES,
        "Полные листинги инициализации PostgreSQL, миграций недель 5–8 и миграций безопасности, ролей БД, демонстрационных данных и SQL-тестов. "
        "Файл является приложением к проекту и не вставляется в пояснительную записку целиком.",
    )
    write_doc(
        ROOT / "frontend" / "CODE_FRONTEND.md",
        "SunStay — текст клиентской части",
        collect_frontend(),
        "Полные листинги React/TypeScript-приложения, дизайн-токенов, конфигурации Vite/Tailwind, Nginx и smoke-теста. "
        "Файл является приложением к проекту и не вставляется в пояснительную записку целиком.",
    )


if __name__ == "__main__":
    main()
