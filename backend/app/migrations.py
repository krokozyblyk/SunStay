from __future__ import annotations

import logging

from .crypto import checkin_document_fields, document_fields, phone_fields
from .db import get_pool

logger = logging.getLogger("sunstay.migrations")


async def encrypt_sensitive_data() -> None:
    """Идемпотентно шифрует существующие открытые контакты и маскирует их."""
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.transaction():
            guests = await conn.execute(
                """
                SELECT guest_id, phone, phone_enc, document_number, document_number_enc
                FROM guests
                WHERE phone_enc IS NULL OR document_number_enc IS NULL
                """
            )
            for guest in await guests.fetchall():
                guest_id = guest["guest_id"]
                phone = guest["phone"]
                document = guest["document_number"]
                if phone and guest["phone_enc"] is None and "*" not in phone:
                    values = phone_fields(phone)
                    await conn.execute(
                        "UPDATE guests SET phone = %s, phone_enc = %s, phone_hash = %s WHERE guest_id = %s",
                        (values["phone"], values["phone_enc"], values["phone_hash"], guest_id),
                    )
                if document and guest["document_number_enc"] is None and "*" not in document:
                    values = document_fields(document)
                    await conn.execute(
                        """
                        UPDATE guests
                        SET document_number = %s, document_number_enc = %s, document_number_hash = %s
                        WHERE guest_id = %s
                        """,
                        (
                            values["document_number"],
                            values["document_number_enc"],
                            values["document_number_hash"],
                            guest_id,
                        ),
                    )

            users = await conn.execute(
                "SELECT user_id, phone, phone_enc FROM users WHERE phone_enc IS NULL AND phone IS NOT NULL"
            )
            for user in await users.fetchall():
                phone = user["phone"]
                if phone and "*" not in phone:
                    values = phone_fields(phone)
                    await conn.execute(
                        "UPDATE users SET phone = %s, phone_enc = %s, phone_hash = %s WHERE user_id = %s",
                        (values["phone"], values["phone_enc"], values["phone_hash"], user["user_id"]),
                    )

            checkins = await conn.execute(
                """
                SELECT checkin_id, guest_document_number, guest_document_number_enc
                FROM check_ins
                WHERE guest_document_number_enc IS NULL AND guest_document_number IS NOT NULL
                """
            )
            for checkin in await checkins.fetchall():
                document = checkin["guest_document_number"]
                if document and "*" not in document:
                    values = checkin_document_fields(document)
                    await conn.execute(
                        """
                        UPDATE check_ins
                        SET guest_document_number = %s,
                            guest_document_number_enc = %s,
                            guest_document_number_hash = %s
                        WHERE checkin_id = %s
                        """,
                        (
                            values["guest_document_number"],
                            values["guest_document_number_enc"],
                            values["guest_document_number_hash"],
                            checkin["checkin_id"],
                        ),
                    )

    logger.info("Sensitive contact encryption migration completed")
