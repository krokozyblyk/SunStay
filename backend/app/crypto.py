from __future__ import annotations

import hashlib
import re
from functools import lru_cache

from cryptography.fernet import Fernet

from .config import get_settings


@lru_cache
def _fernet() -> Fernet:
    return Fernet(get_settings().data_encryption_key.encode("utf-8"))


def normalize_phone(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_document(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "").upper()


def hash_value(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def encrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def mask_phone(value: str | None) -> str | None:
    digits = normalize_phone(value)
    if not digits:
        return None
    if len(digits) <= 2:
        return "+7 ***-**-**"
    return f"+7 ***-**-{digits[-2:]}"


def mask_document(value: str | None) -> str | None:
    normalized = normalize_document(value)
    if not normalized:
        return None
    if len(normalized) <= 4:
        return "****"
    return f"**** {normalized[-4:]}"


def phone_fields(value: str | None) -> dict[str, str | None]:
    normalized = normalize_phone(value)
    return {
        "phone": mask_phone(value),
        "phone_enc": encrypt_value(value),
        "phone_hash": hash_value(normalized) if normalized else None,
    }


def document_fields(value: str | None) -> dict[str, str | None]:
    normalized = normalize_document(value)
    return {
        "document_number": mask_document(value),
        "document_number_enc": encrypt_value(value),
        "document_number_hash": hash_value(normalized) if normalized else None,
    }


def checkin_document_fields(value: str | None) -> dict[str, str | None]:
    normalized = normalize_document(value)
    return {
        "guest_document_number": mask_document(value),
        "guest_document_number_enc": encrypt_value(value),
        "guest_document_number_hash": hash_value(normalized) if normalized else None,
    }
