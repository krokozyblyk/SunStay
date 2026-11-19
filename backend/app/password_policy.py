from __future__ import annotations

from fastapi import HTTPException
from psycopg import AsyncConnection


async def validate_password(conn: AsyncConnection, password: str) -> None:
    cur = await conn.execute(
        "SELECT key, value FROM system_settings WHERE key LIKE 'password.%'"
    )
    settings = {row["key"]: row["value"] for row in await cur.fetchall()}

    def flag(key: str, default: bool) -> bool:
        value = settings.get(key)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "t")

    min_length = int(settings.get("password.min_length") or 8)
    require_upper = flag("password.require_uppercase", True)
    require_digit = flag("password.require_digit", True)
    require_special = flag("password.require_special", False)

    problems: list[str] = []
    if len(password) < min_length:
        problems.append(f"не короче {min_length} символов")
    if require_upper and not any(c.isupper() for c in password):
        problems.append("заглавная буква")
    if require_digit and not any(c.isdigit() for c in password):
        problems.append("цифра")
    if require_special and not any(not c.isalnum() for c in password):
        problems.append("специальный символ")

    if problems:
        raise HTTPException(status_code=400, detail="Пароль должен содержать: " + ", ".join(problems))
