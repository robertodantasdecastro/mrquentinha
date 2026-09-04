from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import (
    FIELD_ENCRYPTION_KEY,
    FIELD_ENCRYPTION_STRICT,
    FIELD_HASH_SALT,
    PAYMENTS_WEBHOOK_TOKEN,
    SECRET_KEY,
    env,
)

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", default=True)
SECURE_REFERRER_POLICY = env(
    "SECURE_REFERRER_POLICY",
    default="strict-origin-when-cross-origin",
)
X_FRAME_OPTIONS = env("X_FRAME_OPTIONS", default="DENY")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

ACCOUNTS_ALLOW_REQUEST_CLIENT_BASE_URL = False
ACCOUNTS_CLIENT_BASE_URL_HTTPS_ONLY = True
ACCOUNTS_CLIENT_BASE_URL_FALLBACK = "https://app.mrquentinha.com.br"

# Operacoes criticas do Portal permanecem bloqueadas em producao ate que cada
# fluxo tenha implementacao real, controles especificos e gate de liberacao.
PORTAL_CRITICAL_OPS_ENABLED = False


def _looks_insecure_secret(value: str, *, known_defaults: set[str]) -> bool:
    normalized = str(value or "").strip()
    lowered = normalized.lower()
    normalized_defaults = {str(item).strip().lower() for item in known_defaults}
    insecure_markers = (
        "change-me",
        "changeme",
        "default",
        "dev-only",
        "django-insecure",
    )
    return (
        len(normalized) < 32
        or any(lowered.startswith(item) for item in normalized_defaults)
        or any(marker in lowered for marker in insecure_markers)
    )


def _validate_production_secrets() -> None:
    invalid_categories: list[str] = []
    if _looks_insecure_secret(
        SECRET_KEY,
        known_defaults={"django-insecure-dev-only-change-me"},
    ):
        invalid_categories.append("SECRET_KEY")
    if len(str(FIELD_ENCRYPTION_KEY or "").strip()) < 32:
        invalid_categories.append("FIELD_ENCRYPTION_KEY")
    if len(str(FIELD_HASH_SALT or "").strip()) < 32:
        invalid_categories.append("FIELD_HASH_SALT")
    if not FIELD_ENCRYPTION_STRICT:
        invalid_categories.append("FIELD_ENCRYPTION_STRICT")
    if _looks_insecure_secret(
        PAYMENTS_WEBHOOK_TOKEN,
        known_defaults={"dev-mrquentinha-webhook-token"},
    ):
        invalid_categories.append("PAYMENTS_WEBHOOK_TOKEN")

    if invalid_categories:
        raise ImproperlyConfigured(
            "Configuracao de producao invalida nas categorias: "
            + ", ".join(invalid_categories)
        )


_validate_production_secrets()
