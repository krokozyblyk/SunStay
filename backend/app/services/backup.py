from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from ..config import get_settings


def backup_path() -> Path:
    settings = get_settings()
    return Path(settings.backup_dir) / settings.backup_file_name


def ensure_valid_backup() -> dict:
    """Return info about a usable backup, regenerating it if missing or empty.

    Render's free tier has an ephemeral filesystem: the dump file can disappear
    after an instance restart. Recreate it on demand so verify/download/restore
    never fail just because the dyno was recycled.
    """
    path = backup_path()
    if path.exists() and path.stat().st_size > 0:
        return {
            "filename": path.name,
            "size": path.stat().st_size,
            "status": "success",
            "error": None,
        }
    return run_backup_sync()


def run_backup_sync() -> dict:
    settings = get_settings()
    path = backup_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "pg_dump",
            "--dbname",
            settings.database_admin_url,
            "-Fc",
            "-n",
            "public",
            "--no-owner",
            "--no-acl",
            "-f",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    size = path.stat().st_size if path.exists() else 0
    status = "success" if result.returncode == 0 and size > 0 else "error"
    if status == "success":
        error = None
    elif size == 0:
        error = "Резервная копия пустая — проверьте права на схему public"
    else:
        error = (result.stderr or "pg_dump failed")[:1000]

    with psycopg.connect(settings.database_admin_url) as conn:
        with conn.transaction():
            for key, value in (
                ("backup.last_run_at", datetime.now().isoformat()),
                ("backup.last_status", status),
                ("backup.last_error", error),
            ):
                conn.execute(
                    """
                    INSERT INTO system_settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = now()
                    """,
                    (key, Jsonb(value)),
                )

    return {
        "filename": path.name,
        "size": size,
        "status": status,
        "error": error,
    }
