from __future__ import annotations

from urllib.parse import urljoin

from apps.portal.services import ensure_portal_config, get_payment_providers_config

SUPPORTED_PAYMENT_PROVIDERS = {"mock", "mercadopago", "efi", "asaas"}
SUPPORTED_PAYMENT_CHANNELS = {"web", "mobile"}


def get_payment_settings() -> dict:
    return get_payment_providers_config(public=False)


def get_provider_settings(provider_name: str) -> dict:
    normalized_provider = (provider_name or "").strip().lower()
    if not normalized_provider:
        return {}

    config = get_payment_settings()
    provider_settings = config.get(normalized_provider)
    if not isinstance(provider_settings, dict):
        return {}

    return provider_settings


def _normalize_channel(channel: str | None) -> str:
    normalized_channel = (channel or "").strip().lower()
    if normalized_channel in SUPPORTED_PAYMENT_CHANNELS:
        return normalized_channel
    return "web"


def resolve_provider_for_method(payment_method: str, channel: str | None = None) -> str:
    normalized_method = (payment_method or "").strip().upper()
    config = get_payment_settings()

    enabled_providers_raw = config.get("enabled_providers", [])
    enabled_providers = [
        str(item).strip().lower()
        for item in enabled_providers_raw
        if str(item).strip().lower() in SUPPORTED_PAYMENT_PROVIDERS
    ]
    if not enabled_providers:
        enabled_providers = ["mock"]

    frontend_provider = config.get("frontend_provider", {})
    channel_key = _normalize_channel(channel)
    channel_provider = "mock"
    if isinstance(frontend_provider, dict):
        channel_provider_raw = str(frontend_provider.get(channel_key, "mock"))
        channel_provider_raw = channel_provider_raw.strip().lower()
        if channel_provider_raw in SUPPORTED_PAYMENT_PROVIDERS:
            channel_provider = channel_provider_raw

    method_provider_order = config.get("method_provider_order", {})
    method_candidates_raw = method_provider_order.get(normalized_method, [])
    method_candidates = [
        str(item).strip().lower() for item in method_candidates_raw if str(item).strip()
    ]

    default_provider = str(config.get("default_provider", "mock")).strip().lower()
    candidate_order = [
        channel_provider,
        *method_candidates,
        default_provider,
        "mock",
    ]

    for candidate in candidate_order:
        if candidate in enabled_providers and candidate in SUPPORTED_PAYMENT_PROVIDERS:
            return candidate

    return "mock"


def build_provider_webhook_url(provider_name: str) -> str:
    config = ensure_portal_config()
    base = str(config.backend_base_url or config.api_base_url).strip()
    if not base:
        return f"/api/v1/orders/payments/webhook/{provider_name}/"

    normalized_base = base.rstrip("/") + "/"
    return urljoin(
        normalized_base,
        f"api/v1/orders/payments/webhook/{provider_name}/",
    )
