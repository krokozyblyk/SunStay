from __future__ import annotations

import json
from typing import Any

from .db import get_pool


def _json_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


async def write_audit_event(
    *,
    user_id: int | None,
    table_name: str,
    record_id: int | None = None,
    action: str = "ERROR",
    old_value: Any = None,
    new_value: Any = None,
    error_message: str | None = None,
    is_error: bool = False,
    event_type: str = "DATA_CHANGE",
    severity: str = "INFO",
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    try:
        async with get_pool().connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO audit_log (
                        user_id, table_name, record_id, action,
                        old_value, new_value, ip_address, user_agent, request_id,
                        is_error, error_message, event_type, severity
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        table_name,
                        record_id,
                        action,
                        _json_text(old_value),
                        _json_text(new_value),
                        ip_address,
                        user_agent,
                        request_id,
                        is_error,
                        error_message,
                        event_type,
                        severity,
                    ),
                )
    except Exception:
        # Аудит не должен ломать основную операцию.
        pass
