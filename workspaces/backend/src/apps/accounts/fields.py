from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core import signing
from django.db import models

try:
    from cryptography.fernet import Fernet, InvalidToken  # type: ignore
except Exception:  # pragma: no cover - fallback em ambientes sem dependencia
    Fernet = None
    InvalidToken = Exception

_ENCRYPTION_PREFIX = "enc::"


def _get_fernet() -> Fernet:
    key = str(getattr(settings, "FIELD_ENCRYPTION_KEY", "") or "").strip()
    if not key:
        if bool(getattr(settings, "FIELD_ENCRYPTION_STRICT", False)):
            raise RuntimeError(
                "FIELD_ENCRYPTION_KEY nao configurada para criptografia."
            )
        return None
    if Fernet is None:
        if bool(getattr(settings, "FIELD_ENCRYPTION_STRICT", False)):
            raise RuntimeError(
                "Dependencia cryptography nao disponivel para criptografia."
            )
        return None
    return Fernet(key.encode())


def _encrypt_value(raw_value: str) -> str:
    fernet = _get_fernet()
    if fernet is None:
        sealed = signing.dumps(raw_value, salt="mrq-field-seal")
        return f"{_ENCRYPTION_PREFIX}{sealed}"
    token = fernet.encrypt(raw_value.encode("utf-8"))
    return f"{_ENCRYPTION_PREFIX}{token.decode('utf-8')}"


def _decrypt_value(raw_value: str) -> str:
    if not raw_value.startswith(_ENCRYPTION_PREFIX):
        return raw_value
    token = raw_value[len(_ENCRYPTION_PREFIX) :]
    fernet = _get_fernet()
    try:
        if fernet is None:
            return signing.loads(token, salt="mrq-field-seal")
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return raw_value


class EncryptedTextField(models.TextField):
    def get_prep_value(self, value: Any) -> Any:
        prepared = super().get_prep_value(value)
        if prepared is None:
            return prepared
        text_value = str(prepared)
        if not text_value:
            return text_value
        if text_value.startswith(_ENCRYPTION_PREFIX):
            return text_value
        return _encrypt_value(text_value)

    def from_db_value(self, value: Any, expression, connection) -> Any:
        if value is None:
            return value
        text_value = str(value)
        if not text_value:
            return text_value
        return _decrypt_value(text_value)

    def to_python(self, value: Any) -> Any:
        if value is None:
            return value
        text_value = str(value)
        if not text_value:
            return text_value
        return _decrypt_value(text_value)
