from __future__ import annotations

import hashlib

from django.conf import settings


def hash_sensitive_value(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    salt = str(getattr(settings, "FIELD_HASH_SALT", "") or "").strip()
    payload = f"{salt}:{normalized}".encode()
    return hashlib.sha256(payload).hexdigest()
