import hashlib
import json
import os
import re
import signal
import subprocess
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib import error as urllib_error
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import (
    MobileRelease,
    MobileReleaseStatus,
    PortalConfig,
    PortalPage,
    PortalSection,
)
from .selectors import (
    get_latest_published_mobile_release,
    get_portal_singleton,
    list_sections_by_template_page,
)

PortalChannel = Literal["portal", "client", "admin"]
CHANNEL_PORTAL: PortalChannel = "portal"
CHANNEL_CLIENT: PortalChannel = "client"
CHANNEL_ADMIN: PortalChannel = "admin"
PROJECT_ROOT = Path(__file__).resolve().parents[5]
OPS_RUNTIME_DIR = PROJECT_ROOT / ".runtime" / "ops"
OPS_PID_DIR = OPS_RUNTIME_DIR / "pids"
OPS_LOG_DIR = OPS_RUNTIME_DIR / "logs"
CLOUDFLARED_LOCAL_BIN = PROJECT_ROOT / ".runtime" / "bin" / "cloudflared"
CLOUDFLARE_PID_FILE = OPS_PID_DIR / "cloudflare.pid"
CLOUDFLARE_LOG_FILE = OPS_LOG_DIR / "cloudflare.log"
CLOUDFLARE_DEV_URL_PATTERN = re.compile(r"https?://[a-zA-Z0-9-]+\.trycloudflare\.com")
CLOUDFLARE_DEV_RESERVED_HOSTS = {
    "api.trycloudflare.com",
}
CLOUDFLARE_DEV_SERVICE_SPECS = (
    {"key": "portal", "name": "Portal Web", "port": 3000},
    {"key": "client", "name": "Client Web", "port": 3001},
    {"key": "admin", "name": "Admin Web", "port": 3002},
    {"key": "api", "name": "Backend API", "port": 8000},
)
CLOUDFLARE_DEV_CONNECTIVITY_PATHS = {
    "portal": "/",
    "client": "/",
    "admin": "/",
    "api": "/api/v1/health",
}

DEFAULT_PORTAL_TEMPLATE_ITEMS = [
    {"id": "classic", "label": "Classic"},
    {"id": "letsfit-clean", "label": "LetsFit Clean"},
]

DEFAULT_CLIENT_TEMPLATE_ITEMS = [
    {"id": "client-classic", "label": "Cliente Classico"},
    {"id": "client-quentinhas", "label": "Cliente Quentinhas"},
    {"id": "client-vitrine-fit", "label": "Cliente Vitrine Fit"},
]

DEFAULT_ADMIN_TEMPLATE_ITEMS = [
    {"id": "admin-classic", "label": "Admin Classico"},
    {"id": "admin-adminkit", "label": "Admin Operations Kit"},
    {"id": "admin-admindek", "label": "Admin Dek Prime"},
]

DEFAULT_AUTH_PROVIDERS_SETTINGS = {
    "google": {
        "enabled": False,
        "web_client_id": "",
        "ios_client_id": "",
        "android_client_id": "",
        "client_secret": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uri_web": (
            "https://www.mrquentinha.com.br/conta/oauth/google/callback"
        ),
        "redirect_uri_mobile": "mrquentinha://oauth/google/callback",
        "scope": "openid email profile",
    },
    "apple": {
        "enabled": False,
        "service_id": "",
        "team_id": "",
        "key_id": "",
        "private_key": "",
        "auth_uri": "https://appleid.apple.com/auth/authorize",
        "token_uri": "https://appleid.apple.com/auth/token",
        "redirect_uri_web": (
            "https://www.mrquentinha.com.br/conta/oauth/apple/callback"
        ),
        "redirect_uri_mobile": "mrquentinha://oauth/apple/callback",
        "scope": "name email",
    },
}


def _default_auth_providers_payload() -> dict:
    return deepcopy(DEFAULT_AUTH_PROVIDERS_SETTINGS)


DEFAULT_PAYMENT_PROVIDERS_SETTINGS = {
    "default_provider": "mock",
    "enabled_providers": ["mock"],
    "frontend_provider": {
        "web": "mock",
        "mobile": "mock",
    },
    "method_provider_order": {
        "PIX": ["mock"],
        "CARD": ["mock"],
        "VR": ["mock"],
    },
    "receiver": {
        "person_type": "CNPJ",
        "document": "",
        "name": "",
        "email": "",
    },
    "mercadopago": {
        "enabled": False,
        "api_base_url": "https://api.mercadopago.com",
        "access_token": "",
        "webhook_secret": "",
        "sandbox": True,
    },
    "efi": {
        "enabled": False,
        "api_base_url": "https://cobrancas-h.api.efipay.com.br",
        "client_id": "",
        "client_secret": "",
        "webhook_secret": "",
        "sandbox": True,
    },
    "asaas": {
        "enabled": False,
        "api_base_url": "https://sandbox.asaas.com/api/v3",
        "api_key": "",
        "webhook_secret": "",
        "sandbox": True,
    },
}


def _default_payment_providers_payload() -> dict:
    return deepcopy(DEFAULT_PAYMENT_PROVIDERS_SETTINGS)


DEFAULT_EMAIL_SETTINGS = {
    "enabled": False,
    "backend": "django.core.mail.backends.smtp.EmailBackend",
    "host": "",
    "port": 587,
    "username": "",
    "password": "",
    "use_tls": True,
    "use_ssl": False,
    "timeout_seconds": 15,
    "from_name": "Mr Quentinha",
    "from_email": "noreply@mrquentinha.local",
    "reply_to_email": "",
    "test_recipient": "",
}


def _default_email_settings_payload() -> dict:
    return deepcopy(DEFAULT_EMAIL_SETTINGS)


DEFAULT_CLOUDFLARE_SETTINGS = {
    "enabled": False,
    "mode": "hybrid",
    "dev_mode": False,
    "scheme": "https",
    "root_domain": "mrquentinha.com.br",
    "subdomains": {
        "portal": "www",
        "client": "app",
        "admin": "admin",
        "api": "api",
    },
    "tunnel_name": "mrquentinha",
    "tunnel_id": "",
    "tunnel_token": "",
    "account_id": "",
    "zone_id": "",
    "api_token": "",
    "auto_apply_routes": True,
    "last_action_at": "",
    "last_status_message": "Cloudflare desativado.",
    "runtime": {
        "state": "inactive",
        "last_started_at": "",
        "last_stopped_at": "",
        "last_error": "",
        "run_command": "",
    },
    "dev_urls": {
        "portal": "",
        "client": "",
        "admin": "",
        "api": "",
    },
    "local_snapshot": {},
}


def _default_cloudflare_settings_payload() -> dict:
    return deepcopy(DEFAULT_CLOUDFLARE_SETTINGS)


DEFAULT_CONFIG_PAYLOAD = {
    "active_template": "classic",
    "available_templates": DEFAULT_PORTAL_TEMPLATE_ITEMS,
    "client_active_template": "client-classic",
    "client_available_templates": DEFAULT_CLIENT_TEMPLATE_ITEMS,
    "admin_active_template": "admin-classic",
    "admin_available_templates": DEFAULT_ADMIN_TEMPLATE_ITEMS,
    "site_name": "Mr Quentinha",
    "site_title": "Mr Quentinha | Marmitas do dia",
    "meta_description": "Marmitas saudaveis com entrega agendada.",
    "primary_color": "#FF6A00",
    "secondary_color": "#1F2937",
    "dark_bg_color": "#0F172A",
    "android_download_url": "https://www.mrquentinha.com.br/app#android",
    "ios_download_url": "https://www.mrquentinha.com.br/app#ios",
    "qr_target_url": "https://www.mrquentinha.com.br/app",
    "api_base_url": "https://10.211.55.21:8000",
    "local_hostname": "mrquentinha",
    "local_network_ip": "10.211.55.21",
    "root_domain": "mrquentinha.local",
    "portal_domain": "www.mrquentinha.local",
    "client_domain": "app.mrquentinha.local",
    "admin_domain": "admin.mrquentinha.local",
    "api_domain": "api.mrquentinha.local",
    "portal_base_url": "https://10.211.55.21:3000",
    "client_base_url": "https://10.211.55.21:3001",
    "admin_base_url": "https://10.211.55.21:3002",
    "backend_base_url": "https://10.211.55.21:8000",
    "proxy_base_url": "https://10.211.55.21:8088",
    "cors_allowed_origins": [
        "https://10.211.55.21:3000",
        "https://10.211.55.21:3001",
        "https://10.211.55.21:3002",
        "http://mrquentinha:3000",
        "http://mrquentinha:3001",
        "http://mrquentinha:3002",
        "http://10.211.55.21:3000",
        "http://10.211.55.21:3001",
        "http://10.211.55.21:3002",
    ],
    "cloudflare_settings": _default_cloudflare_settings_payload(),
    "auth_providers": _default_auth_providers_payload(),
    "payment_providers": _default_payment_providers_payload(),
    "email_settings": _default_email_settings_payload(),
    "is_published": False,
}

DEFAULT_SECTION_FIXTURES = [
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Comida caseira pronta para o seu dia",
        "sort_order": 10,
        "body_json": {
            "kicker": "Mr Quentinha",
            "headline": "Marmitas equilibradas com entrega planejada",
            "subheadline": "Escolha seu cardapio e receba sem complicacao.",
            "cta_primary": {"label": "Ver cardapio", "href": "/cardapio"},
            "cta_secondary": {"label": "Baixar app", "href": "/app"},
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "benefits",
        "title": "Por que escolher o Mr Quentinha",
        "sort_order": 20,
        "body_json": {
            "items": [
                "Entrega agendada",
                "Cardapio variado",
                "Preparo padronizado",
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "categories",
        "title": "Categorias",
        "sort_order": 30,
        "body_json": {
            "items": [
                {"name": "Dia a dia", "description": "Praticidade com sabor"},
                {"name": "Fit", "description": "Foco em equilibrio"},
                {"name": "Premium", "description": "Proteina reforcada"},
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "faq",
        "title": "Perguntas frequentes",
        "sort_order": 40,
        "body_json": {
            "items": [
                {
                    "question": "Como faco o pedido?",
                    "answer": "Escolha data, prato e confirme no app ou web.",
                },
                {
                    "question": "Como armazenar?",
                    "answer": "Conserve refrigerado e aqueca quando for consumir.",
                },
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "footer",
        "title": "Atendimento",
        "sort_order": 50,
        "body_json": {
            "phone": "(11) 90000-0000",
            "email": "contato@mrquentinha.com.br",
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Hero LetsFit",
        "sort_order": 10,
        "body_json": {
            "kicker": "Plano inteligente",
            "headline": "Sua semana organizada com marmitas prontas",
            "subheadline": "Escolha kits e acompanhe seu pedido em tempo real.",
            "background_image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
            "cta_primary": {"label": "Montar kit", "href": "/cardapio"},
            "cta_secondary": {"label": "Como funciona", "href": "/como-funciona"},
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "benefits",
        "title": "Beneficios",
        "sort_order": 20,
        "body_json": {
            "items": [
                {"text": "Pronto em 5 min", "icon": "clock"},
                {"text": "Entrega agendada", "icon": "truck"},
                {"text": "Ingredientes selecionados", "icon": "check"},
                {"text": "Pagamento no app", "icon": "card"},
            ]
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "categories",
        "title": "Categorias letsfit",
        "sort_order": 30,
        "body_json": {
            "items": [
                {
                    "name": "Dia a dia",
                    "description": "Comida caseira equilibrada para todos os dias.",
                    "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
                },
                {
                    "name": "Low carb",
                    "description": "Opcao com menos carboidrato e foco em proteina.",
                    "image_url": "https://images.unsplash.com/photo-1603569283847-aa295f0d016a",
                },
                {
                    "name": "Vegetariano",
                    "description": (
                        "Receitas leves com legumes, graos e proteina vegetal."
                    ),
                    "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd",
                },
                {
                    "name": "Kits semanais",
                    "description": "Pacotes fechados para a semana inteira.",
                    "image_url": "https://images.unsplash.com/photo-1579113800032-c38bd7635818",
                },
            ]
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "kit",
        "title": "Monte seu kit",
        "sort_order": 40,
        "body_json": {
            "kicker": "Nao sabe o que escolher?",
            "headline": "Monte seu kit para a semana",
            "description": (
                "Selecione dias e objetivo. "
                "O sistema sugere combinacoes do cardapio do dia."
            ),
            "cta_label": "Simular kit personalizado",
            "cta_href": "/cardapio",
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "how_to_heat",
        "title": "Conservacao e aquecimento",
        "sort_order": 45,
        "body_json": {
            "title": "Facil de preparar e armazenar",
            "subheadline": "As embalagens vao do freezer ao micro-ondas com seguranca.",
            "cards": [
                {
                    "tone": "cold",
                    "title": "Conservacao",
                    "description": (
                        "Geladeira por ate 3 dias ou freezer por ate 30 dias."
                    ),
                },
                {
                    "tone": "hot",
                    "title": "Aquecimento",
                    "description": (
                        "No micro-ondas por 5 a 7 minutos "
                        "apos abrir um respiro na embalagem."
                    ),
                },
            ],
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "faq",
        "title": "FAQ",
        "sort_order": 50,
        "body_json": {
            "items": [
                {
                    "question": "Como agendar a entrega?",
                    "answer": "No checkout, selecione a data de entrega disponivel.",
                },
                {
                    "question": "Aceita VR/VA?",
                    "answer": (
                        "Aceitamos VR e VA conforme rede habilitada no pagamento."
                    ),
                },
                {
                    "question": "A comida chega congelada?",
                    "answer": (
                        "Voce escolhe entre entrega fresca para o dia "
                        "ou ultracongelada."
                    ),
                },
            ]
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "footer",
        "title": "Contato",
        "sort_order": 60,
        "body_json": {
            "phone": "(11) 90000-0000",
            "email": "atendimento@mrquentinha.com.br",
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Web Cliente Classico",
        "sort_order": 10,
        "body_json": {
            "headline": "Cardapio do dia com entrega organizada",
            "subheadline": "Monte seu pedido rapido e acompanhe status em tempo real.",
        },
    },
    {
        "template_id": "client-quentinhas",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Web Cliente Quentinhas",
        "sort_order": 10,
        "body_json": {
            "headline": "Sua quentinha favorita chegou no estilo Mr Quentinha",
            "subheadline": (
                "Visual inspirado em vitrines digitais de quentinhas, com foco em "
                "praticidade e conversao."
            ),
            "badge": "Entrega agendada",
        },
    },
    {
        "template_id": "client-vitrine-fit",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Web Cliente Vitrine Fit",
        "sort_order": 10,
        "body_json": {
            "headline": "Monte sua semana com vitrine visual de marmitas",
            "subheadline": (
                "Template inspirado em lojas de marmitas com foco em foto, "
                "descoberta rapida e conversao."
            ),
            "badge": "Fotos reais e menu por data",
        },
    },
    {
        "template_id": "client-vitrine-fit",
        "page": PortalPage.HOME,
        "key": "benefits",
        "title": "Diferenciais da vitrine",
        "sort_order": 20,
        "body_json": {
            "items": [
                {"text": "Fotos em destaque", "icon": "image"},
                {"text": "Busca por data", "icon": "calendar"},
                {"text": "Checkout em poucos cliques", "icon": "cart"},
                {"text": "Acompanhamento em tempo real", "icon": "timeline"},
            ]
        },
    },
    {
        "template_id": "client-vitrine-fit",
        "page": PortalPage.HOME,
        "key": "categories",
        "title": "Colecoes",
        "sort_order": 30,
        "body_json": {
            "items": [
                {"name": "Mais pedidas", "description": "Top picks da semana"},
                {"name": "Fit proteico", "description": "Alta proteina e equilibrio"},
                {"name": "Leves", "description": "Opcoes com menor teor calorico"},
                {"name": "Kits", "description": "Combos para rotina completa"},
            ]
        },
    },
]


CONFIG_MUTABLE_FIELDS = [
    "active_template",
    "available_templates",
    "client_active_template",
    "client_available_templates",
    "admin_active_template",
    "admin_available_templates",
    "site_name",
    "site_title",
    "meta_description",
    "primary_color",
    "secondary_color",
    "dark_bg_color",
    "android_download_url",
    "ios_download_url",
    "qr_target_url",
    "api_base_url",
    "local_hostname",
    "local_network_ip",
    "root_domain",
    "portal_domain",
    "client_domain",
    "admin_domain",
    "api_domain",
    "portal_base_url",
    "client_base_url",
    "admin_base_url",
    "backend_base_url",
    "proxy_base_url",
    "cors_allowed_origins",
    "cloudflare_settings",
    "auth_providers",
    "payment_providers",
    "email_settings",
    "is_published",
    "published_at",
]


def _extract_template_ids(available_templates: list) -> set[str]:
    template_ids: set[str] = set()

    for item in available_templates:
        if isinstance(item, dict):
            template_id = str(item.get("id", "")).strip()
        else:
            template_id = str(item).strip()

        if template_id:
            template_ids.add(template_id)

    return template_ids


def _merge_default_template_items(
    *,
    current_items: object,
    default_items: list[dict],
) -> list[dict]:
    merged: list[dict] = []
    known_ids: set[str] = set()

    if isinstance(current_items, list):
        for item in current_items:
            if isinstance(item, dict):
                template_id = str(item.get("id", "")).strip()
                label = str(item.get("label", "")).strip() or template_id
            else:
                template_id = str(item).strip()
                label = template_id

            if not template_id or template_id in known_ids:
                continue

            known_ids.add(template_id)
            merged.append({"id": template_id, "label": label})

    for item in default_items:
        template_id = str(item.get("id", "")).strip()
        if not template_id or template_id in known_ids:
            continue

        known_ids.add(template_id)
        merged.append(
            {
                "id": template_id,
                "label": str(item.get("label", "")).strip() or template_id,
            }
        )

    return merged


def _normalize_auth_providers(raw_value: object | None) -> dict:
    normalized = _default_auth_providers_payload()
    if not isinstance(raw_value, dict):
        return normalized

    for provider in ("google", "apple"):
        source_config = raw_value.get(provider)
        if not isinstance(source_config, dict):
            continue

        provider_defaults = normalized[provider]
        for key in provider_defaults:
            if key not in source_config:
                continue
            provider_defaults[key] = source_config[key]

    return normalized


def _build_public_auth_providers(raw_value: object | None) -> dict:
    normalized = _normalize_auth_providers(raw_value)

    google = normalized["google"]
    apple = normalized["apple"]

    return {
        "google": {
            "enabled": bool(google.get("enabled")),
            "web_client_id": str(google.get("web_client_id", "")).strip(),
            "ios_client_id": str(google.get("ios_client_id", "")).strip(),
            "android_client_id": str(google.get("android_client_id", "")).strip(),
            "auth_uri": str(google.get("auth_uri", "")).strip(),
            "token_uri": str(google.get("token_uri", "")).strip(),
            "redirect_uri_web": str(google.get("redirect_uri_web", "")).strip(),
            "redirect_uri_mobile": str(google.get("redirect_uri_mobile", "")).strip(),
            "scope": str(google.get("scope", "")).strip(),
            "configured": bool(
                str(google.get("web_client_id", "")).strip()
                and str(google.get("client_secret", "")).strip()
            ),
        },
        "apple": {
            "enabled": bool(apple.get("enabled")),
            "service_id": str(apple.get("service_id", "")).strip(),
            "team_id": str(apple.get("team_id", "")).strip(),
            "key_id": str(apple.get("key_id", "")).strip(),
            "auth_uri": str(apple.get("auth_uri", "")).strip(),
            "token_uri": str(apple.get("token_uri", "")).strip(),
            "redirect_uri_web": str(apple.get("redirect_uri_web", "")).strip(),
            "redirect_uri_mobile": str(apple.get("redirect_uri_mobile", "")).strip(),
            "scope": str(apple.get("scope", "")).strip(),
            "configured": bool(
                str(apple.get("service_id", "")).strip()
                and str(apple.get("private_key", "")).strip()
                and str(apple.get("team_id", "")).strip()
                and str(apple.get("key_id", "")).strip()
            ),
        },
    }


def _normalize_payment_providers(raw_value: object | None) -> dict:
    normalized = _default_payment_providers_payload()
    allowed_providers = {"mock", "mercadopago", "efi", "asaas"}
    if not isinstance(raw_value, dict):
        return normalized

    if "default_provider" in raw_value:
        normalized["default_provider"] = (
            str(raw_value.get("default_provider", "")).strip() or "mock"
        )

    enabled = raw_value.get("enabled_providers")
    if isinstance(enabled, list):
        normalized["enabled_providers"] = [
            str(item).strip().lower() for item in enabled if str(item).strip()
        ] or ["mock"]
        normalized["enabled_providers"] = [
            item
            for item in normalized["enabled_providers"]
            if item in allowed_providers
        ] or ["mock"]

    frontend_provider = raw_value.get("frontend_provider")
    if isinstance(frontend_provider, dict):
        web_provider = (
            str(frontend_provider.get("web", "mock")).strip().lower() or "mock"
        )
        mobile_provider = (
            str(frontend_provider.get("mobile", "mock")).strip().lower() or "mock"
        )
        normalized["frontend_provider"] = {
            "web": web_provider if web_provider in allowed_providers else "mock",
            "mobile": (
                mobile_provider if mobile_provider in allowed_providers else "mock"
            ),
        }

    method_order = raw_value.get("method_provider_order")
    if isinstance(method_order, dict):
        for method in ("PIX", "CARD", "VR"):
            source = method_order.get(method)
            if not isinstance(source, list):
                continue
            normalized["method_provider_order"][method] = [
                str(item).strip().lower() for item in source if str(item).strip()
            ] or ["mock"]
            normalized["method_provider_order"][method] = [
                item
                for item in normalized["method_provider_order"][method]
                if item in allowed_providers
            ] or ["mock"]

    receiver = raw_value.get("receiver")
    if isinstance(receiver, dict):
        normalized["receiver"] = {
            "person_type": (
                str(receiver.get("person_type", "CNPJ")).strip().upper() or "CNPJ"
            ),
            "document": str(receiver.get("document", "")).strip(),
            "name": str(receiver.get("name", "")).strip(),
            "email": str(receiver.get("email", "")).strip(),
        }

    for provider in ("mercadopago", "efi", "asaas"):
        provider_source = raw_value.get(provider)
        if not isinstance(provider_source, dict):
            continue
        provider_defaults = normalized[provider]
        for key in provider_defaults:
            if key not in provider_source:
                continue
            provider_defaults[key] = provider_source[key]

    if normalized["default_provider"] not in normalized["enabled_providers"]:
        normalized["enabled_providers"].append(normalized["default_provider"])

    for channel in ("web", "mobile"):
        channel_provider = normalized["frontend_provider"].get(channel, "mock")
        if channel_provider not in normalized["enabled_providers"]:
            normalized["enabled_providers"].append(channel_provider)

    return normalized


def _build_public_payment_providers(raw_value: object | None) -> dict:
    normalized = _normalize_payment_providers(raw_value)
    mercadopago = normalized["mercadopago"]
    efi = normalized["efi"]
    asaas = normalized["asaas"]

    return {
        "default_provider": normalized["default_provider"],
        "enabled_providers": normalized["enabled_providers"],
        "frontend_provider": normalized["frontend_provider"],
        "method_provider_order": normalized["method_provider_order"],
        "receiver": {
            "person_type": normalized["receiver"]["person_type"],
            "document": normalized["receiver"]["document"],
            "name": normalized["receiver"]["name"],
            "email": normalized["receiver"]["email"],
        },
        "mercadopago": {
            "enabled": bool(mercadopago.get("enabled")),
            "api_base_url": str(mercadopago.get("api_base_url", "")).strip(),
            "sandbox": bool(mercadopago.get("sandbox", True)),
            "configured": bool(str(mercadopago.get("access_token", "")).strip()),
        },
        "efi": {
            "enabled": bool(efi.get("enabled")),
            "api_base_url": str(efi.get("api_base_url", "")).strip(),
            "sandbox": bool(efi.get("sandbox", True)),
            "configured": bool(
                str(efi.get("client_id", "")).strip()
                and str(efi.get("client_secret", "")).strip()
            ),
        },
        "asaas": {
            "enabled": bool(asaas.get("enabled")),
            "api_base_url": str(asaas.get("api_base_url", "")).strip(),
            "sandbox": bool(asaas.get("sandbox", True)),
            "configured": bool(str(asaas.get("api_key", "")).strip()),
        },
    }


def _safe_validate_email(value: str) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        return ""
    try:
        validate_email(candidate)
    except ValidationError:
        return ""
    return candidate


def _normalize_email_settings(raw_value: object | None) -> dict:
    normalized = _default_email_settings_payload()
    if not isinstance(raw_value, dict):
        return normalized

    normalized["enabled"] = bool(raw_value.get("enabled", False))
    backend = str(
        raw_value.get(
            "backend",
            "django.core.mail.backends.smtp.EmailBackend",
        )
    ).strip()
    normalized["backend"] = backend or "django.core.mail.backends.smtp.EmailBackend"
    normalized["host"] = str(raw_value.get("host", "")).strip()
    normalized["username"] = str(raw_value.get("username", "")).strip()
    normalized["password"] = str(raw_value.get("password", "")).strip()
    normalized["use_tls"] = bool(raw_value.get("use_tls", True))
    normalized["use_ssl"] = bool(raw_value.get("use_ssl", False))

    try:
        port = int(raw_value.get("port", normalized["port"]))
    except (TypeError, ValueError):
        port = int(normalized["port"])
    normalized["port"] = max(1, min(port, 65535))

    try:
        timeout_seconds = int(
            raw_value.get("timeout_seconds", normalized["timeout_seconds"])
        )
    except (TypeError, ValueError):
        timeout_seconds = int(normalized["timeout_seconds"])
    normalized["timeout_seconds"] = max(1, min(timeout_seconds, 120))

    normalized["from_name"] = (
        str(raw_value.get("from_name", normalized["from_name"])).strip()
        or normalized["from_name"]
    )
    normalized["from_email"] = _safe_validate_email(
        str(raw_value.get("from_email", normalized["from_email"])).strip()
        or normalized["from_email"]
    )
    normalized["reply_to_email"] = _safe_validate_email(
        str(raw_value.get("reply_to_email", "")).strip()
    )
    normalized["test_recipient"] = _safe_validate_email(
        str(raw_value.get("test_recipient", "")).strip()
    )

    if normalized["use_tls"] and normalized["use_ssl"]:
        normalized["use_ssl"] = False

    return normalized


def resolve_portal_email_delivery_options() -> dict:
    config = ensure_portal_config()
    email_settings = _normalize_email_settings(config.email_settings)

    from_email_address = (
        email_settings["from_email"] or str(settings.DEFAULT_FROM_EMAIL).strip()
    )
    from_name = str(email_settings.get("from_name", "")).strip()
    from_email = from_email_address
    if from_name:
        from_email = f"{from_name} <{from_email_address}>"

    reply_to_email = str(email_settings.get("reply_to_email", "")).strip()
    reply_to = [reply_to_email] if reply_to_email else []
    connection = None

    if bool(email_settings.get("enabled", False)):
        host = str(email_settings.get("host", "")).strip()
        if not host:
            raise ValidationError(
                "SMTP habilitado sem host configurado em Email (Web Admin)."
            )

        connection = get_connection(
            backend=str(email_settings.get("backend", "")).strip()
            or "django.core.mail.backends.smtp.EmailBackend",
            fail_silently=True,
            host=host,
            port=int(email_settings.get("port", 587)),
            username=str(email_settings.get("username", "")).strip() or None,
            password=str(email_settings.get("password", "")).strip() or None,
            use_tls=bool(email_settings.get("use_tls", True)),
            use_ssl=bool(email_settings.get("use_ssl", False)),
            timeout=int(email_settings.get("timeout_seconds", 15)),
        )

    return {
        "settings": email_settings,
        "connection": connection,
        "from_email": from_email,
        "reply_to": reply_to,
    }


def send_portal_test_email(*, to_email: str, initiated_by: str = "") -> dict:
    delivery = resolve_portal_email_delivery_options()
    email_settings = delivery["settings"]

    target_email = (
        _safe_validate_email(to_email)
        or _safe_validate_email(email_settings.get("test_recipient", ""))
        or _safe_validate_email(email_settings.get("from_email", ""))
    )
    if not target_email:
        raise ValidationError("Informe um destinatario valido para o teste de e-mail.")

    initiated_by_label = str(initiated_by or "").strip() or "sistema"
    subject = "[Mr Quentinha] Teste de configuracao de e-mail"
    body = (
        "Este e um e-mail de teste enviado pelo Web Admin do Mr Quentinha.\n\n"
        f"Iniciado por: {initiated_by_label}\n"
        f"Data: {timezone.now().isoformat()}\n"
        f"SMTP customizado ativo: {'sim' if email_settings.get('enabled') else 'nao'}\n"
    )
    html_body = (
        "<p>Este e um e-mail de teste enviado pelo <strong>Web Admin</strong> do "
        "Mr Quentinha.</p>"
        f"<p><strong>Iniciado por:</strong> {initiated_by_label}<br/>"
        f"<strong>Data:</strong> {timezone.now().isoformat()}<br/>"
        f"<strong>SMTP customizado ativo:</strong> "
        f"{'sim' if email_settings.get('enabled') else 'nao'}</p>"
    )

    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=str(delivery["from_email"]),
        to=[target_email],
        reply_to=delivery["reply_to"] or None,
        connection=delivery["connection"],
    )
    message.attach_alternative(html_body, "text/html")
    sent_count = int(message.send(fail_silently=True) or 0)

    if sent_count <= 0:
        raise ValidationError(
            "Falha ao enviar e-mail de teste. Revise as credenciais SMTP."
        )

    return {
        "ok": True,
        "detail": "E-mail de teste enviado com sucesso.",
        "to_email": target_email,
        "custom_provider_enabled": bool(email_settings.get("enabled", False)),
    }


def _normalize_cloudflare_mode(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"local_only", "cloudflare_only", "hybrid"}:
        return normalized
    return "hybrid"


def _normalize_cloudflare_settings(raw_value: object | None) -> dict:
    normalized = _default_cloudflare_settings_payload()
    if not isinstance(raw_value, dict):
        return normalized

    normalized["enabled"] = bool(raw_value.get("enabled", False))
    normalized["mode"] = _normalize_cloudflare_mode(raw_value.get("mode"))
    normalized["dev_mode"] = bool(raw_value.get("dev_mode", False))
    scheme = str(raw_value.get("scheme", "https")).strip().lower()
    normalized["scheme"] = "https" if scheme not in {"http", "https"} else scheme
    normalized["root_domain"] = (
        str(raw_value.get("root_domain", "")).strip() or normalized["root_domain"]
    )
    normalized["tunnel_name"] = (
        str(raw_value.get("tunnel_name", "")).strip() or normalized["tunnel_name"]
    )
    normalized["tunnel_id"] = str(raw_value.get("tunnel_id", "")).strip()
    normalized["tunnel_token"] = str(raw_value.get("tunnel_token", "")).strip()
    normalized["account_id"] = str(raw_value.get("account_id", "")).strip()
    normalized["zone_id"] = str(raw_value.get("zone_id", "")).strip()
    normalized["api_token"] = str(raw_value.get("api_token", "")).strip()
    normalized["auto_apply_routes"] = bool(raw_value.get("auto_apply_routes", True))
    normalized["last_action_at"] = str(raw_value.get("last_action_at", "")).strip()
    normalized["last_status_message"] = (
        str(raw_value.get("last_status_message", "")).strip()
        or "Cloudflare desativado."
    )

    source_subdomains = raw_value.get("subdomains")
    if isinstance(source_subdomains, dict):
        for channel in ("portal", "client", "admin", "api"):
            source_value = source_subdomains.get(channel)
            if source_value is None:
                continue
            normalized["subdomains"][channel] = str(source_value).strip().lower()

    source_runtime = raw_value.get("runtime")
    if isinstance(source_runtime, dict):
        for key in ("state", "last_started_at", "last_stopped_at", "last_error"):
            if key in source_runtime:
                normalized["runtime"][key] = str(source_runtime.get(key, "")).strip()
        if "run_command" in source_runtime:
            normalized["runtime"]["run_command"] = str(
                source_runtime.get("run_command", "")
            ).strip()

    source_dev_urls = raw_value.get("dev_urls")
    if isinstance(source_dev_urls, dict):
        for channel in ("portal", "client", "admin", "api"):
            normalized["dev_urls"][channel] = str(
                source_dev_urls.get(channel, "")
            ).strip()

    source_snapshot = raw_value.get("local_snapshot")
    if isinstance(source_snapshot, dict):
        normalized["local_snapshot"] = {
            str(key): source_snapshot[key]
            for key in source_snapshot
            if isinstance(key, str)
        }

    return normalized


def _join_cloudflare_domain(*, subdomain: str, root_domain: str) -> str:
    clean_root = root_domain.strip().lower().strip(".")
    clean_subdomain = subdomain.strip().lower().strip(".")
    if not clean_root:
        return ""
    if clean_subdomain in {"", "@", "root"}:
        return clean_root
    return f"{clean_subdomain}.{clean_root}"


def _extract_hostname_from_url(value: str) -> str:
    parsed = urlparse(str(value or "").strip())
    return str(parsed.hostname or "").strip().lower()


def _normalize_cloudflare_dev_urls(settings: dict) -> dict[str, str]:
    dev_urls = settings.get("dev_urls")
    output: dict[str, str] = {
        "portal": "",
        "client": "",
        "admin": "",
        "api": "",
    }
    if not isinstance(dev_urls, dict):
        return output

    for channel in output:
        raw_url = str(dev_urls.get(channel, "")).strip().rstrip("/")
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            output[channel] = raw_url
    return output


def _has_complete_cloudflare_dev_urls(dev_urls: dict[str, str]) -> bool:
    return all(bool(dev_urls.get(channel, "").strip()) for channel in dev_urls)


def _extract_cloudflare_dev_urls_from_runtime_payload(
    runtime_payload: dict,
) -> dict[str, str]:
    source_urls = runtime_payload.get("dev_urls")
    normalized = {
        "portal": "",
        "client": "",
        "admin": "",
        "api": "",
    }
    if not isinstance(source_urls, dict):
        return normalized

    for channel in normalized:
        normalized[channel] = str(source_urls.get(channel, "")).strip().rstrip("/")
    return normalized


def _build_cloudflare_preview_payload(config: PortalConfig, settings: dict) -> dict:
    normalized = _normalize_cloudflare_settings(settings)
    dev_mode = bool(normalized.get("dev_mode", False))
    scheme = normalized["scheme"]
    root_domain = normalized["root_domain"]
    subdomains = normalized["subdomains"]

    if dev_mode:
        dev_urls = _normalize_cloudflare_dev_urls(normalized)
        portal_base_url = dev_urls["portal"]
        client_base_url = dev_urls["client"]
        admin_base_url = dev_urls["admin"]
        api_base_url = dev_urls["api"]
        portal_domain = _extract_hostname_from_url(portal_base_url)
        client_domain = _extract_hostname_from_url(client_base_url)
        admin_domain = _extract_hostname_from_url(admin_base_url)
        api_domain = _extract_hostname_from_url(api_base_url)
    else:
        portal_domain = _join_cloudflare_domain(
            subdomain=subdomains["portal"],
            root_domain=root_domain,
        )
        client_domain = _join_cloudflare_domain(
            subdomain=subdomains["client"],
            root_domain=root_domain,
        )
        admin_domain = _join_cloudflare_domain(
            subdomain=subdomains["admin"],
            root_domain=root_domain,
        )
        api_domain = _join_cloudflare_domain(
            subdomain=subdomains["api"],
            root_domain=root_domain,
        )

        portal_base_url = f"{scheme}://{portal_domain}" if portal_domain else ""
        client_base_url = f"{scheme}://{client_domain}" if client_domain else ""
        admin_base_url = f"{scheme}://{admin_domain}" if admin_domain else ""
        api_base_url = f"{scheme}://{api_domain}" if api_domain else ""

    cors_origins = [
        origin
        for origin in [portal_base_url, client_base_url, admin_base_url]
        if origin
    ]

    ingress_rules = [
        f"{portal_domain} -> http://127.0.0.1:3000",
        f"{client_domain} -> http://127.0.0.1:3001",
        f"{admin_domain} -> http://127.0.0.1:3002",
        f"{api_domain} -> http://127.0.0.1:8000",
    ]
    run_command = ""
    if dev_mode:
        run_command = (
            "cloudflared tunnel --url http://127.0.0.1:<porta> --no-autoupdate "
            "(um processo por servico)"
        )
    elif normalized["tunnel_token"]:
        run_command = "cloudflared tunnel run --token <token-configurado-no-admin>"
    elif normalized["tunnel_name"]:
        run_command = f"cloudflared tunnel run {normalized['tunnel_name']}"

    return {
        "mode": normalized["mode"],
        "dev_mode": dev_mode,
        "scheme": scheme,
        "root_domain": root_domain,
        "domains": {
            "portal": portal_domain,
            "client": client_domain,
            "admin": admin_domain,
            "api": api_domain,
        },
        "urls": {
            "portal_base_url": portal_base_url,
            "client_base_url": client_base_url,
            "admin_base_url": admin_base_url,
            "api_base_url": api_base_url,
            "backend_base_url": api_base_url,
        },
        "cors_allowed_origins": cors_origins,
        "tunnel": {
            "name": normalized["tunnel_name"],
            "id": normalized["tunnel_id"],
            "configured": dev_mode
            or bool(normalized["tunnel_token"] or normalized["tunnel_id"]),
            "run_command": run_command,
        },
        "ingress_rules": ingress_rules,
        "coexistence_note": (
            "Modo hybrid permite acesso local e Cloudflare ao mesmo tempo."
            if not dev_mode
            else "Modo dev usa dominios aleatorios trycloudflare.com por servico."
        ),
        "generated_at": timezone.now().isoformat(),
    }


def _build_public_cloudflare_settings(config: PortalConfig) -> dict:
    normalized = _normalize_cloudflare_settings(config.cloudflare_settings)
    preview = _build_cloudflare_preview_payload(config, normalized)
    return {
        "enabled": normalized["enabled"],
        "mode": normalized["mode"],
        "dev_mode": bool(normalized.get("dev_mode", False)),
        "scheme": normalized["scheme"],
        "root_domain": normalized["root_domain"],
        "subdomains": normalized["subdomains"],
        "last_action_at": normalized["last_action_at"],
        "last_status_message": normalized["last_status_message"],
        "runtime": {
            "state": str(normalized["runtime"].get("state", "inactive")).strip()
            or "inactive",
            "last_started_at": str(
                normalized["runtime"].get("last_started_at", "")
            ).strip(),
            "last_stopped_at": str(
                normalized["runtime"].get("last_stopped_at", "")
            ).strip(),
            "last_error": str(normalized["runtime"].get("last_error", "")).strip(),
        },
        "dev_urls": _normalize_cloudflare_dev_urls(normalized),
        "domains": preview["domains"],
        "urls": preview["urls"],
        "coexistence_supported": True,
    }


def _build_local_connectivity_snapshot(config: PortalConfig) -> dict:
    return {
        "local_hostname": config.local_hostname,
        "local_network_ip": config.local_network_ip,
        "root_domain": config.root_domain,
        "portal_domain": config.portal_domain,
        "client_domain": config.client_domain,
        "admin_domain": config.admin_domain,
        "api_domain": config.api_domain,
        "api_base_url": config.api_base_url,
        "portal_base_url": config.portal_base_url,
        "client_base_url": config.client_base_url,
        "admin_base_url": config.admin_base_url,
        "backend_base_url": config.backend_base_url,
        "proxy_base_url": config.proxy_base_url,
        "cors_allowed_origins": list(config.cors_allowed_origins),
    }


def _ensure_ops_runtime_dirs() -> None:
    OPS_PID_DIR.mkdir(parents=True, exist_ok=True)
    OPS_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_cloudflared_binary() -> str:
    override = str(os.environ.get("MQ_CLOUDFLARED_BIN", "")).strip()
    if override:
        return override
    if CLOUDFLARED_LOCAL_BIN.exists() and os.access(CLOUDFLARED_LOCAL_BIN, os.X_OK):
        return str(CLOUDFLARED_LOCAL_BIN)
    return "cloudflared"


def _read_pid_from_file(pid_file: Path) -> int | None:
    if not pid_file.exists():
        return None

    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None

    try:
        os.kill(pid, 0)
        return pid
    except OSError:
        return None


def _read_cloudflare_pid() -> int | None:
    return _read_pid_from_file(CLOUDFLARE_PID_FILE)


def _cloudflare_dev_pid_file(key: str) -> Path:
    return OPS_PID_DIR / f"cloudflare-dev-{key}.pid"


def _cloudflare_dev_log_file(key: str) -> Path:
    return OPS_LOG_DIR / f"cloudflare-dev-{key}.log"


def _tail_log_file(log_file: Path, *, lines: int = 80) -> list[str]:
    if lines <= 0:
        return []
    if not log_file.exists():
        return []

    try:
        content = log_file.read_text(encoding="utf-8")
    except OSError:
        return []

    return [line for line in content.splitlines()[-lines:] if line.strip()]


def _tail_cloudflare_log(*, lines: int = 80) -> list[str]:
    return _tail_log_file(CLOUDFLARE_LOG_FILE, lines=lines)


def _read_cloudflare_dev_url_from_log(log_file: Path) -> str:
    if not log_file.exists():
        return ""
    try:
        content = log_file.read_text(encoding="utf-8")
    except OSError:
        return ""

    matches = CLOUDFLARE_DEV_URL_PATTERN.findall(content)
    valid_matches: list[str] = []
    for raw_match in matches:
        normalized = str(raw_match).strip().rstrip("/")
        if not normalized:
            continue

        parsed = urlparse(normalized)
        host = str(parsed.hostname or "").strip().lower()
        if not host or host in CLOUDFLARE_DEV_RESERVED_HOSTS:
            continue
        if not host.endswith(".trycloudflare.com"):
            continue
        if parsed.scheme not in {"http", "https"}:
            continue

        valid_matches.append(normalized)

    if not valid_matches:
        return ""
    return valid_matches[-1]


def _stop_pid_file(pid_file: Path) -> None:
    pid = _read_pid_from_file(pid_file)
    if pid is not None:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    if pid_file.exists():
        try:
            pid_file.unlink()
        except OSError:
            pass


def _stop_cloudflare_dev_tunnels() -> None:
    for service in CLOUDFLARE_DEV_SERVICE_SPECS:
        _stop_pid_file(_cloudflare_dev_pid_file(service["key"]))


def _check_cloudflare_dev_service_connectivity(*, key: str, base_url: str) -> dict:
    cleaned_base_url = str(base_url).strip().rstrip("/")
    checked_at = timezone.now().isoformat()
    if not cleaned_base_url:
        return {
            "connectivity": "unknown",
            "http_status": None,
            "latency_ms": None,
            "checked_url": "",
            "checked_at": checked_at,
            "error": "",
        }

    check_path = CLOUDFLARE_DEV_CONNECTIVITY_PATHS.get(key, "/")
    check_url = f"{cleaned_base_url}{check_path}"
    start = time.monotonic()
    request = Request(
        check_url,
        method="GET",
        headers={"User-Agent": "mrquentinha-cloudflare-monitor/1.0"},
    )

    try:
        with urlopen(request, timeout=6) as response:
            status_code = int(response.getcode())
            latency_ms = int((time.monotonic() - start) * 1000)
            connectivity = "online" if status_code < 500 else "offline"
            return {
                "connectivity": connectivity,
                "http_status": status_code,
                "latency_ms": latency_ms,
                "checked_url": check_url,
                "checked_at": checked_at,
                "error": "",
            }
    except urllib_error.HTTPError as exc:
        status_code = int(exc.code)
        latency_ms = int((time.monotonic() - start) * 1000)
        connectivity = "online" if status_code < 500 else "offline"
        return {
            "connectivity": connectivity,
            "http_status": status_code,
            "latency_ms": latency_ms,
            "checked_url": check_url,
            "checked_at": checked_at,
            "error": str(exc),
        }
    except (urllib_error.URLError, TimeoutError, OSError) as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        return {
            "connectivity": "offline",
            "http_status": None,
            "latency_ms": latency_ms,
            "checked_url": check_url,
            "checked_at": checked_at,
            "error": str(exc),
        }


def _build_cloudflare_dev_runtime_payload(settings: dict) -> dict:
    normalized = _normalize_cloudflare_settings(settings)
    services: list[dict] = []
    dev_urls = _normalize_cloudflare_dev_urls(normalized)

    states: list[str] = []
    aggregated_log_lines: list[str] = []
    first_pid: int | None = None

    for service in CLOUDFLARE_DEV_SERVICE_SPECS:
        key = service["key"]
        pid_file = _cloudflare_dev_pid_file(key)
        log_file = _cloudflare_dev_log_file(key)
        pid = _read_pid_from_file(pid_file)
        url = _read_cloudflare_dev_url_from_log(log_file) or dev_urls.get(key, "")
        connectivity = _check_cloudflare_dev_service_connectivity(key=key, base_url=url)
        running = pid is not None
        if first_pid is None and pid is not None:
            first_pid = pid
        states.append("running" if running else "offline")

        tail_lines = _tail_log_file(log_file, lines=8)
        for line in tail_lines:
            aggregated_log_lines.append(f"[{key}] {line}")

        services.append(
            {
                "key": key,
                "name": service["name"],
                "port": service["port"],
                "pid": pid,
                "url": url,
                "log_file": str(log_file),
                "running": running,
                "connectivity": connectivity["connectivity"],
                "http_status": connectivity["http_status"],
                "latency_ms": connectivity["latency_ms"],
                "checked_url": connectivity["checked_url"],
                "checked_at": connectivity["checked_at"],
                "error": connectivity["error"],
            }
        )

    if all(state == "running" for state in states):
        state = "active"
    elif any(state == "running" for state in states):
        state = "partial"
    else:
        state = "inactive"

    runtime = normalized.get("runtime", {})
    if runtime.get("state") == "error":
        state = "error"

    return {
        "state": state,
        "pid": first_pid,
        "log_file": str(OPS_LOG_DIR / "cloudflare-dev-*.log"),
        "last_started_at": str(runtime.get("last_started_at", "")).strip(),
        "last_stopped_at": str(runtime.get("last_stopped_at", "")).strip(),
        "last_error": str(runtime.get("last_error", "")).strip(),
        "run_command": str(runtime.get("run_command", "")).strip(),
        "last_log_lines": aggregated_log_lines[-40:],
        "dev_mode": True,
        "dev_urls": {item["key"]: item["url"] for item in services},
        "dev_services": services,
    }


def _build_cloudflare_run_command(settings: dict) -> list[str]:
    tunnel_token = str(settings.get("tunnel_token", "")).strip()
    tunnel_name = str(settings.get("tunnel_name", "")).strip()
    cloudflared_bin = _resolve_cloudflared_binary()

    if tunnel_token:
        return [cloudflared_bin, "tunnel", "run", "--token", tunnel_token]
    if tunnel_name:
        return [cloudflared_bin, "tunnel", "run", tunnel_name]

    raise ValidationError(
        "Defina tunnel_token ou tunnel_name para iniciar runtime do Cloudflare."
    )


def _format_command_for_display(command: list[str]) -> str:
    parts: list[str] = []
    for item in command:
        clean = str(item).strip()
        if " " in clean:
            parts.append(f'"{clean}"')
        else:
            parts.append(clean)
    return " ".join(parts)


def _build_cloudflare_runtime_payload(config: PortalConfig) -> dict:
    settings = _normalize_cloudflare_settings(config.cloudflare_settings)
    if bool(settings.get("dev_mode", False)):
        return _build_cloudflare_dev_runtime_payload(settings)

    pid = _read_cloudflare_pid()
    runtime = settings.get("runtime", {})
    state = "active" if pid else "inactive"
    if runtime.get("state") == "error":
        state = "error"

    return {
        "state": state,
        "pid": pid,
        "log_file": str(CLOUDFLARE_LOG_FILE),
        "last_started_at": str(runtime.get("last_started_at", "")).strip(),
        "last_stopped_at": str(runtime.get("last_stopped_at", "")).strip(),
        "last_error": str(runtime.get("last_error", "")).strip(),
        "run_command": str(runtime.get("run_command", "")).strip(),
        "last_log_lines": _tail_cloudflare_log(lines=40),
    }


def _resolve_api_base_url(config: PortalConfig) -> str:
    api_url = str(config.api_base_url or "").strip()
    if api_url:
        return api_url

    backend_url = str(config.backend_base_url or "").strip()
    if backend_url:
        return backend_url

    return DEFAULT_CONFIG_PAYLOAD["api_base_url"]


def _resolve_public_host(config: PortalConfig) -> str:
    parsed = urlparse(_resolve_api_base_url(config))
    if parsed.hostname:
        return parsed.hostname

    if str(config.local_network_ip).strip():
        return str(config.local_network_ip).strip()

    return str(config.local_hostname).strip() or "mrquentinha"


def _resolve_download_base_url(config: PortalConfig) -> str:
    parsed = urlparse(_resolve_api_base_url(config))
    scheme = parsed.scheme or "https"
    host = _resolve_public_host(config)
    return f"{scheme}://{host}:3000"


def build_mobile_download_urls(config: PortalConfig) -> dict[str, str]:
    base_url = _resolve_download_base_url(config)
    return {
        "android": f"{base_url}/app/downloads/android.apk",
        "ios": f"{base_url}/app/downloads/ios",
    }


def _seed_missing_sections(config: PortalConfig) -> None:
    for fixture in DEFAULT_SECTION_FIXTURES:
        PortalSection.objects.get_or_create(
            config=config,
            template_id=fixture["template_id"],
            page=fixture["page"],
            key=fixture["key"],
            defaults={
                "title": fixture["title"],
                "body_json": fixture["body_json"],
                "is_enabled": True,
                "sort_order": fixture["sort_order"],
            },
        )


def _ensure_connection_defaults(config: PortalConfig) -> None:
    fallback_fields = [
        "api_base_url",
        "local_hostname",
        "root_domain",
        "portal_domain",
        "client_domain",
        "admin_domain",
        "api_domain",
        "portal_base_url",
        "client_base_url",
        "admin_base_url",
        "backend_base_url",
        "proxy_base_url",
    ]

    update_fields: list[str] = []
    for field_name in fallback_fields:
        current_value = getattr(config, field_name)
        if str(current_value).strip():
            continue

        setattr(config, field_name, DEFAULT_CONFIG_PAYLOAD[field_name])
        update_fields.append(field_name)

    if str(config.api_base_url).strip() and not str(config.backend_base_url).strip():
        config.backend_base_url = config.api_base_url
        update_fields.append("backend_base_url")

    if str(config.backend_base_url).strip() and not str(config.api_base_url).strip():
        config.api_base_url = config.backend_base_url
        update_fields.append("api_base_url")

    if not config.cors_allowed_origins:
        config.cors_allowed_origins = DEFAULT_CONFIG_PAYLOAD["cors_allowed_origins"]
        update_fields.append("cors_allowed_origins")

    merged_portal_templates = _merge_default_template_items(
        current_items=config.available_templates,
        default_items=DEFAULT_PORTAL_TEMPLATE_ITEMS,
    )
    if config.available_templates != merged_portal_templates:
        config.available_templates = merged_portal_templates
        update_fields.append("available_templates")

    merged_client_templates = _merge_default_template_items(
        current_items=config.client_available_templates,
        default_items=DEFAULT_CLIENT_TEMPLATE_ITEMS,
    )
    if config.client_available_templates != merged_client_templates:
        config.client_available_templates = merged_client_templates
        update_fields.append("client_available_templates")

    merged_admin_templates = _merge_default_template_items(
        current_items=config.admin_available_templates,
        default_items=DEFAULT_ADMIN_TEMPLATE_ITEMS,
    )
    if config.admin_available_templates != merged_admin_templates:
        config.admin_available_templates = merged_admin_templates
        update_fields.append("admin_available_templates")

    normalized_auth_providers = _normalize_auth_providers(config.auth_providers)
    if config.auth_providers != normalized_auth_providers:
        config.auth_providers = normalized_auth_providers
        update_fields.append("auth_providers")

    normalized_payment_providers = _normalize_payment_providers(
        config.payment_providers
    )
    if config.payment_providers != normalized_payment_providers:
        config.payment_providers = normalized_payment_providers
        update_fields.append("payment_providers")

    normalized_email_settings = _normalize_email_settings(config.email_settings)
    if config.email_settings != normalized_email_settings:
        config.email_settings = normalized_email_settings
        update_fields.append("email_settings")

    normalized_cloudflare_settings = _normalize_cloudflare_settings(
        config.cloudflare_settings
    )
    if config.cloudflare_settings != normalized_cloudflare_settings:
        config.cloudflare_settings = normalized_cloudflare_settings
        update_fields.append("cloudflare_settings")

    if update_fields:
        update_fields.append("updated_at")
        config.save(update_fields=update_fields)


def ensure_portal_config() -> PortalConfig:
    config = get_portal_singleton()
    if config is not None:
        _ensure_connection_defaults(config)
        _seed_missing_sections(config)
        return config

    config = PortalConfig.objects.create(
        singleton_key=PortalConfig.SINGLETON_KEY,
        **DEFAULT_CONFIG_PAYLOAD,
    )
    _ensure_connection_defaults(config)
    _seed_missing_sections(config)
    return config


@transaction.atomic
def save_portal_config(
    *,
    payload: dict,
    instance: PortalConfig | None = None,
) -> tuple[PortalConfig, bool]:
    payload = payload.copy()
    if "auth_providers" in payload:
        payload["auth_providers"] = _normalize_auth_providers(payload["auth_providers"])
    if "payment_providers" in payload:
        payload["payment_providers"] = _normalize_payment_providers(
            payload["payment_providers"]
        )
    if "email_settings" in payload:
        payload["email_settings"] = _normalize_email_settings(payload["email_settings"])
    if "cloudflare_settings" in payload:
        payload["cloudflare_settings"] = _normalize_cloudflare_settings(
            payload["cloudflare_settings"]
        )
    if "api_base_url" in payload and "backend_base_url" not in payload:
        payload["backend_base_url"] = payload["api_base_url"]
    if "backend_base_url" in payload and "api_base_url" not in payload:
        payload["api_base_url"] = payload["backend_base_url"]

    config = instance or get_portal_singleton()
    created = False

    if config is None:
        config = PortalConfig(
            singleton_key=PortalConfig.SINGLETON_KEY,
            **DEFAULT_CONFIG_PAYLOAD,
        )
        created = True

    update_fields: list[str] = []
    for field_name in CONFIG_MUTABLE_FIELDS:
        if field_name not in payload:
            continue

        new_value = payload[field_name]
        if getattr(config, field_name) == new_value:
            continue

        setattr(config, field_name, new_value)
        update_fields.append(field_name)

    available_templates = payload.get("available_templates", config.available_templates)
    active_template = payload.get("active_template", config.active_template)
    client_available_templates = payload.get(
        "client_available_templates",
        config.client_available_templates,
    )
    client_active_template = payload.get(
        "client_active_template",
        config.client_active_template,
    )
    admin_available_templates = payload.get(
        "admin_available_templates",
        config.admin_available_templates,
    )
    admin_active_template = payload.get(
        "admin_active_template",
        config.admin_active_template,
    )

    if available_templates and active_template not in _extract_template_ids(
        available_templates
    ):
        raise ValidationError("active_template precisa existir em available_templates.")

    if (
        client_available_templates
        and client_active_template
        not in _extract_template_ids(client_available_templates)
    ):
        raise ValidationError(
            "client_active_template precisa existir em client_available_templates."
        )

    if (
        admin_available_templates
        and admin_active_template
        not in _extract_template_ids(admin_available_templates)
    ):
        raise ValidationError(
            "admin_active_template precisa existir em admin_available_templates."
        )

    if created:
        config.save()
        return config, True

    if update_fields:
        update_fields.append("updated_at")
        config.save(update_fields=update_fields)

    return config, False


@transaction.atomic
def publish_portal_config() -> PortalConfig:
    config = ensure_portal_config()
    now = timezone.now()

    update_fields: list[str] = []
    if not config.is_published:
        config.is_published = True
        update_fields.append("is_published")

    if config.published_at is None:
        config.published_at = now
        update_fields.append("published_at")

    if update_fields:
        update_fields.append("updated_at")
        config.save(update_fields=update_fields)

    return config


def _resolve_templates(config: PortalConfig, *, channel: PortalChannel) -> list[dict]:
    if channel == CHANNEL_CLIENT:
        if config.client_available_templates:
            return config.client_available_templates
        return DEFAULT_CLIENT_TEMPLATE_ITEMS

    if channel == CHANNEL_ADMIN:
        if config.admin_available_templates:
            return config.admin_available_templates
        return DEFAULT_ADMIN_TEMPLATE_ITEMS

    if config.available_templates:
        return config.available_templates
    return DEFAULT_PORTAL_TEMPLATE_ITEMS


def _resolve_active_template(config: PortalConfig, *, channel: PortalChannel) -> str:
    if channel == CHANNEL_CLIENT:
        return config.client_active_template
    if channel == CHANNEL_ADMIN:
        return config.admin_active_template
    return config.active_template


def build_public_portal_payload(
    *,
    page: str = PortalPage.HOME,
    channel: PortalChannel = CHANNEL_PORTAL,
) -> dict:
    if channel not in {CHANNEL_PORTAL, CHANNEL_CLIENT, CHANNEL_ADMIN}:
        raise ValidationError("Canal invalido para configuracao publica.")

    config = ensure_portal_config()
    mobile_download_urls = build_mobile_download_urls(config)
    active_template = _resolve_active_template(config, channel=channel)
    sections = list_sections_by_template_page(
        config=config,
        template_id=active_template,
        page=page,
        enabled_only=True,
    )

    return {
        "channel": channel,
        "active_template": active_template,
        "available_templates": _resolve_templates(config, channel=channel),
        "client_active_template": config.client_active_template,
        "client_available_templates": _resolve_templates(
            config,
            channel=CHANNEL_CLIENT,
        ),
        "admin_active_template": config.admin_active_template,
        "admin_available_templates": _resolve_templates(
            config,
            channel=CHANNEL_ADMIN,
        ),
        "site_name": config.site_name,
        "site_title": config.site_title,
        "meta_description": config.meta_description,
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "dark_bg_color": config.dark_bg_color,
        "android_download_url": config.android_download_url,
        "ios_download_url": config.ios_download_url,
        "qr_target_url": config.qr_target_url,
        "api_base_url": _resolve_api_base_url(config),
        "local_hostname": config.local_hostname,
        "local_network_ip": config.local_network_ip,
        "root_domain": config.root_domain,
        "portal_domain": config.portal_domain,
        "client_domain": config.client_domain,
        "admin_domain": config.admin_domain,
        "api_domain": config.api_domain,
        "portal_base_url": config.portal_base_url,
        "client_base_url": config.client_base_url,
        "admin_base_url": config.admin_base_url,
        "backend_base_url": config.backend_base_url,
        "proxy_base_url": config.proxy_base_url,
        "cors_allowed_origins": config.cors_allowed_origins,
        "cloudflare": _build_public_cloudflare_settings(config),
        "auth_providers": _build_public_auth_providers(config.auth_providers),
        "payment_providers": _build_public_payment_providers(config.payment_providers),
        "host_publico": _resolve_public_host(config),
        "app_download_android_url": mobile_download_urls["android"],
        "app_download_ios_url": mobile_download_urls["ios"],
        "is_published": config.is_published,
        "updated_at": config.updated_at,
        "page": page,
        "sections": [
            {
                "id": section.id,
                "template_id": section.template_id,
                "page": section.page,
                "key": section.key,
                "title": section.title,
                "body_json": section.body_json,
                "sort_order": section.sort_order,
                "updated_at": section.updated_at,
            }
            for section in sections
        ],
    }


def get_payment_providers_config(*, public: bool = False) -> dict:
    config = ensure_portal_config()
    if public:
        return _build_public_payment_providers(config.payment_providers)
    return _normalize_payment_providers(config.payment_providers)


def _serialize_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def build_portal_version_payload() -> dict:
    config = ensure_portal_config()
    portal_sections_qs = PortalSection.objects.filter(
        config=config,
        template_id=config.active_template,
    )
    client_sections_qs = PortalSection.objects.filter(
        config=config,
        template_id=config.client_active_template,
    )

    latest_section = max(
        filter(
            None,
            [
                portal_sections_qs.aggregate(latest=Max("updated_at"))["latest"],
                client_sections_qs.aggregate(latest=Max("updated_at"))["latest"],
            ],
        ),
        default=None,
    )
    timestamps = [ts for ts in [config.updated_at, latest_section] if ts is not None]
    resolved_updated_at = max(timestamps) if timestamps else config.updated_at

    fingerprint_payload = {
        "active_template": config.active_template,
        "client_active_template": config.client_active_template,
        "admin_active_template": config.admin_active_template,
        "config_updated_at": _serialize_dt(config.updated_at),
        "sections": {
            "portal": [
                {
                    "id": row["id"],
                    "updated_at": _serialize_dt(row["updated_at"]),
                }
                for row in portal_sections_qs.order_by("id").values("id", "updated_at")
            ],
            "client": [
                {
                    "id": row["id"],
                    "updated_at": _serialize_dt(row["updated_at"]),
                }
                for row in client_sections_qs.order_by("id").values("id", "updated_at")
            ],
            "admin": [
                {
                    "id": row["id"],
                    "updated_at": _serialize_dt(row["updated_at"]),
                }
                for row in PortalSection.objects.filter(
                    config=config,
                    template_id=config.admin_active_template,
                )
                .order_by("id")
                .values("id", "updated_at")
            ],
        },
    }
    digest = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {
        "updated_at": _serialize_dt(resolved_updated_at),
        "hash": digest,
        "etag": digest,
    }


@transaction.atomic
def create_mobile_release(
    *,
    payload: dict,
    created_by=None,
) -> MobileRelease:
    config = ensure_portal_config()
    requested_config_id = payload.get("config")
    if isinstance(requested_config_id, PortalConfig):
        requested_config_id = requested_config_id.id
    if requested_config_id is not None and int(requested_config_id) != config.id:
        raise ValidationError("config invalido para criacao da release.")

    release = MobileRelease.objects.create(
        config=config,
        release_version=str(payload.get("release_version", "")).strip(),
        build_number=int(payload.get("build_number", 1)),
        update_policy=payload.get("update_policy", "OPTIONAL"),
        is_critical_update=bool(payload.get("is_critical_update", False)),
        min_supported_version=str(payload.get("min_supported_version", "")).strip(),
        recommended_version=str(payload.get("recommended_version", "")).strip(),
        release_notes=str(payload.get("release_notes", "")).strip(),
        metadata=payload.get("metadata", {}),
        created_by=created_by,
    )
    return release


@transaction.atomic
def compile_mobile_release(release: MobileRelease) -> MobileRelease:
    config = ensure_portal_config()
    download_urls = build_mobile_download_urls(config)
    now = timezone.now()

    release.status = MobileReleaseStatus.SIGNED
    release.api_base_url_snapshot = _resolve_api_base_url(config)
    release.host_publico_snapshot = _resolve_public_host(config)
    release.android_download_url = download_urls["android"]
    release.ios_download_url = download_urls["ios"]
    if not release.min_supported_version:
        release.min_supported_version = release.release_version
    if not release.recommended_version:
        release.recommended_version = release.release_version
    release.build_log = "\n".join(
        [
            "Pipeline executado via Portal CMS (modo inicial).",
            "Etapas: build Android + build iOS + testes + assinatura.",
            (
                "Observacao: publicacao iOS depende de canal oficial "
                "(TestFlight/App Store/Enterprise)."
            ),
            f"Compilado em: {now.isoformat()}",
        ]
    )
    release.metadata = {
        **(release.metadata or {}),
        "compiled_at": now.isoformat(),
        "compiled_by": "portal-admin",
    }
    release.save(
        update_fields=[
            "status",
            "api_base_url_snapshot",
            "host_publico_snapshot",
            "android_download_url",
            "ios_download_url",
            "min_supported_version",
            "recommended_version",
            "build_log",
            "metadata",
            "updated_at",
        ]
    )
    return release


@transaction.atomic
def publish_mobile_release(release: MobileRelease) -> MobileRelease:
    allowed_statuses = {
        MobileReleaseStatus.SIGNED,
        MobileReleaseStatus.PUBLISHED,
    }
    if release.status not in allowed_statuses:
        raise ValidationError("Release precisa estar assinado antes de publicar.")

    now = timezone.now()
    update_fields: list[str] = []
    if release.status != MobileReleaseStatus.PUBLISHED:
        release.status = MobileReleaseStatus.PUBLISHED
        update_fields.append("status")
    if release.published_at is None:
        release.published_at = now
        update_fields.append("published_at")

    if update_fields:
        update_fields.append("updated_at")
        release.save(update_fields=update_fields)

    return release


def build_latest_mobile_release_payload() -> dict:
    config = ensure_portal_config()
    release = get_latest_published_mobile_release(config=config)
    download_urls = build_mobile_download_urls(config)

    if release is None:
        return {
            "release_version": "",
            "build_number": 0,
            "status": "DRAFT",
            "update_policy": "OPTIONAL",
            "is_critical_update": False,
            "min_supported_version": "",
            "recommended_version": "",
            "api_base_url": _resolve_api_base_url(config),
            "host_publico": _resolve_public_host(config),
            "android_download_url": download_urls["android"],
            "ios_download_url": download_urls["ios"],
            "published_at": None,
            "release_notes": "",
        }

    return {
        "release_version": release.release_version,
        "build_number": release.build_number,
        "status": release.status,
        "update_policy": release.update_policy,
        "is_critical_update": release.is_critical_update,
        "min_supported_version": release.min_supported_version,
        "recommended_version": release.recommended_version,
        "api_base_url": release.api_base_url_snapshot or _resolve_api_base_url(config),
        "host_publico": release.host_publico_snapshot or _resolve_public_host(config),
        "android_download_url": (
            release.android_download_url or download_urls["android"]
        ),
        "ios_download_url": release.ios_download_url or download_urls["ios"],
        "published_at": release.published_at,
        "release_notes": release.release_notes,
    }


def build_cloudflare_preview(
    *,
    overrides: dict | None = None,
) -> dict:
    config = ensure_portal_config()
    base_settings = _normalize_cloudflare_settings(config.cloudflare_settings)
    if isinstance(overrides, dict):
        base_settings = _normalize_cloudflare_settings({**base_settings, **overrides})
    return _build_cloudflare_preview_payload(config, base_settings)


def _append_unique_origins(origins: list[str], extra: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()

    for item in [*origins, *extra]:
        normalized = str(item).strip().rstrip("/")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)

    return output


def _build_cloudflare_dev_run_command_display() -> str:
    return (
        "cloudflared tunnel --url http://127.0.0.1:<porta> --no-autoupdate "
        "(portal/client/admin/api)"
    )


def _apply_cloudflare_dev_urls_to_config(
    *,
    config: PortalConfig,
    settings: dict,
    dev_urls: dict[str, str],
) -> list[str]:
    normalized_dev_urls = _normalize_cloudflare_dev_urls({"dev_urls": dev_urls})
    urls = {
        "portal": normalized_dev_urls["portal"].strip().rstrip("/"),
        "client": normalized_dev_urls["client"].strip().rstrip("/"),
        "admin": normalized_dev_urls["admin"].strip().rstrip("/"),
        "api": normalized_dev_urls["api"].strip().rstrip("/"),
    }

    mode = _normalize_cloudflare_mode(settings.get("mode"))
    local_snapshot = settings.get("local_snapshot", {})
    local_origins = local_snapshot.get("cors_allowed_origins", [])
    if not isinstance(local_origins, list):
        local_origins = []

    update_fields: list[str] = []

    if urls["portal"]:
        config.portal_base_url = urls["portal"]
        config.portal_domain = _extract_hostname_from_url(urls["portal"])
        update_fields.extend(["portal_base_url", "portal_domain"])
    if urls["client"]:
        config.client_base_url = urls["client"]
        config.client_domain = _extract_hostname_from_url(urls["client"])
        update_fields.extend(["client_base_url", "client_domain"])
    if urls["admin"]:
        config.admin_base_url = urls["admin"]
        config.admin_domain = _extract_hostname_from_url(urls["admin"])
        update_fields.extend(["admin_base_url", "admin_domain"])
    if urls["api"]:
        config.api_base_url = urls["api"]
        config.backend_base_url = urls["api"]
        config.api_domain = _extract_hostname_from_url(urls["api"])
        update_fields.extend(["api_base_url", "backend_base_url", "api_domain"])

    cloud_origins = [urls["portal"], urls["client"], urls["admin"]]
    cloud_origins = [origin for origin in cloud_origins if origin]
    if cloud_origins:
        if mode == "cloudflare_only":
            cors_origins = _append_unique_origins([], cloud_origins)
        else:
            cors_origins = _append_unique_origins(local_origins, cloud_origins)
        config.cors_allowed_origins = cors_origins
        update_fields.append("cors_allowed_origins")

    return update_fields


@transaction.atomic
def toggle_cloudflare_mode(
    *,
    enabled: bool,
    overrides: dict | None = None,
) -> tuple[PortalConfig, dict]:
    config = ensure_portal_config()
    settings = _normalize_cloudflare_settings(config.cloudflare_settings)
    if isinstance(overrides, dict):
        settings = _normalize_cloudflare_settings({**settings, **overrides})

    now_iso = timezone.now().isoformat()
    preview = _build_cloudflare_preview_payload(config, settings)
    update_fields: list[str] = []

    if enabled:
        if not settings.get("local_snapshot"):
            settings["local_snapshot"] = _build_local_connectivity_snapshot(config)

        mode = _normalize_cloudflare_mode(settings.get("mode"))
        if mode == "local_only":
            mode = "hybrid"
            settings["mode"] = mode

        if bool(settings.get("dev_mode", False)):
            settings["runtime"]["state"] = "inactive"
            settings["runtime"][
                "run_command"
            ] = _build_cloudflare_dev_run_command_display()
            dev_urls = _normalize_cloudflare_dev_urls(settings)
            if settings.get("auto_apply_routes", True):
                update_fields.extend(
                    _apply_cloudflare_dev_urls_to_config(
                        config=config,
                        settings=settings,
                        dev_urls=dev_urls,
                    )
                )
            settings["last_status_message"] = (
                "Cloudflare DEV habilitado. "
                "Inicie o runtime para gerar URLs aleatorias."
            )
        else:
            urls = preview["urls"]
            domains = preview["domains"]
            cloud_origins = preview["cors_allowed_origins"]
            local_snapshot = settings.get("local_snapshot", {})
            local_origins = local_snapshot.get("cors_allowed_origins", [])
            if not isinstance(local_origins, list):
                local_origins = []

            if mode == "cloudflare_only":
                cors_origins = _append_unique_origins([], cloud_origins)
            else:
                cors_origins = _append_unique_origins(local_origins, cloud_origins)

            config.root_domain = settings["root_domain"]
            config.portal_domain = str(domains.get("portal", "")).strip()
            config.client_domain = str(domains.get("client", "")).strip()
            config.admin_domain = str(domains.get("admin", "")).strip()
            config.api_domain = str(domains.get("api", "")).strip()
            config.portal_base_url = str(urls.get("portal_base_url", "")).strip()
            config.client_base_url = str(urls.get("client_base_url", "")).strip()
            config.admin_base_url = str(urls.get("admin_base_url", "")).strip()
            config.api_base_url = str(urls.get("api_base_url", "")).strip()
            config.backend_base_url = str(urls.get("backend_base_url", "")).strip()
            config.cors_allowed_origins = cors_origins

            update_fields.extend(
                [
                    "root_domain",
                    "portal_domain",
                    "client_domain",
                    "admin_domain",
                    "api_domain",
                    "portal_base_url",
                    "client_base_url",
                    "admin_base_url",
                    "api_base_url",
                    "backend_base_url",
                    "cors_allowed_origins",
                ]
            )

        settings["enabled"] = True
        settings["last_action_at"] = now_iso
        if not bool(settings.get("dev_mode", False)):
            settings["last_status_message"] = (
                "Cloudflare ativo com roteamento automatico para todos os frontends."
            )
            settings["runtime"]["state"] = "active"
            settings["runtime"]["last_started_at"] = now_iso
            settings["runtime"]["last_error"] = ""
            settings["runtime"]["run_command"] = preview["tunnel"]["run_command"]
    else:
        _stop_pid_file(CLOUDFLARE_PID_FILE)
        _stop_cloudflare_dev_tunnels()

        snapshot = settings.get("local_snapshot", {})
        if not isinstance(snapshot, dict):
            snapshot = {}

        for field_name in (
            "local_hostname",
            "local_network_ip",
            "root_domain",
            "portal_domain",
            "client_domain",
            "admin_domain",
            "api_domain",
            "api_base_url",
            "portal_base_url",
            "client_base_url",
            "admin_base_url",
            "backend_base_url",
            "proxy_base_url",
        ):
            if field_name in snapshot:
                setattr(config, field_name, snapshot[field_name])
                update_fields.append(field_name)

        snapshot_origins = snapshot.get("cors_allowed_origins")
        if isinstance(snapshot_origins, list):
            config.cors_allowed_origins = _append_unique_origins(snapshot_origins, [])
            update_fields.append("cors_allowed_origins")

        settings["enabled"] = False
        settings["last_action_at"] = now_iso
        settings["last_status_message"] = (
            "Cloudflare desativado e modo local restaurado."
        )
        settings["runtime"]["state"] = "inactive"
        settings["runtime"]["last_stopped_at"] = now_iso
        settings["runtime"]["run_command"] = ""
        settings["dev_urls"] = {
            "portal": "",
            "client": "",
            "admin": "",
            "api": "",
        }

    normalized_settings = _normalize_cloudflare_settings(settings)
    config.cloudflare_settings = normalized_settings
    update_fields.append("cloudflare_settings")

    if update_fields:
        update_fields = list(dict.fromkeys([*update_fields, "updated_at"]))
        config.save(update_fields=update_fields)

    return config, preview


@transaction.atomic
def manage_cloudflare_runtime(
    *,
    action: str,
) -> tuple[PortalConfig, dict]:
    normalized_action = str(action or "").strip().lower()
    is_refresh_action = normalized_action == "refresh"
    if normalized_action not in {"start", "stop", "status", "refresh"}:
        raise ValidationError("Acao invalida para runtime Cloudflare.")

    config = ensure_portal_config()
    settings = _normalize_cloudflare_settings(config.cloudflare_settings)
    runtime = settings.get("runtime", {})
    _ensure_ops_runtime_dirs()
    now_iso = timezone.now().isoformat()

    dev_mode = bool(settings.get("dev_mode", False))
    if dev_mode:
        if normalized_action == "refresh":
            _stop_cloudflare_dev_tunnels()
            settings["dev_urls"] = {
                "portal": "",
                "client": "",
                "admin": "",
                "api": "",
            }
            runtime["state"] = "inactive"
            runtime["last_stopped_at"] = now_iso
            runtime["run_command"] = ""
            settings["runtime"] = runtime
            settings["last_action_at"] = now_iso
            settings["last_status_message"] = (
                "Runtime DEV reiniciado para gerar novos dominios."
            )
            normalized_action = "start"

        if normalized_action == "start":
            try:
                for service in CLOUDFLARE_DEV_SERVICE_SPECS:
                    key = service["key"]
                    port = int(service["port"])
                    pid_file = _cloudflare_dev_pid_file(key)
                    log_file = _cloudflare_dev_log_file(key)
                    existing_pid = _read_pid_from_file(pid_file)

                    if existing_pid is None:
                        cloudflared_bin = _resolve_cloudflared_binary()
                        command = [
                            cloudflared_bin,
                            "tunnel",
                            "--url",
                            f"http://127.0.0.1:{port}",
                            "--no-autoupdate",
                        ]
                        try:
                            log_handle = open(log_file, "w", encoding="utf-8")
                        except OSError as exc:
                            raise ValidationError(
                                f"Falha ao abrir log do tunnel DEV ({key})."
                            ) from exc

                        try:
                            proc = subprocess.Popen(
                                command,
                                cwd=PROJECT_ROOT,
                                stdout=log_handle,
                                stderr=log_handle,
                                stdin=subprocess.DEVNULL,
                                start_new_session=True,
                            )
                        except FileNotFoundError as exc:
                            log_handle.close()
                            raise ValidationError(
                                "Binario cloudflared nao encontrado no servidor."
                            ) from exc
                        except OSError as exc:
                            log_handle.close()
                            raise ValidationError(
                                f"Falha ao iniciar tunnel DEV ({key})."
                            ) from exc
                        finally:
                            log_handle.close()

                        pid_file.write_text(str(proc.pid), encoding="utf-8")
                    wait_deadline = time.monotonic() + 25.0
                    service_url = _read_cloudflare_dev_url_from_log(log_file)
                    while not service_url and time.monotonic() < wait_deadline:
                        time.sleep(0.5)
                        service_url = _read_cloudflare_dev_url_from_log(log_file)

                    if not service_url:
                        raise ValidationError(
                            f"Tunnel DEV ({key}) iniciou sem URL publica. "
                            f"Verifique {log_file}."
                        )

                    settings["dev_urls"][key] = service_url

                runtime["state"] = "active"
                runtime["last_started_at"] = now_iso
                runtime["last_error"] = ""
                runtime["run_command"] = _build_cloudflare_dev_run_command_display()
                settings["runtime"] = runtime
                settings["last_action_at"] = now_iso
                if is_refresh_action:
                    settings["last_status_message"] = (
                        "Cloudflare DEV atualizou dominios aleatorios por servico."
                    )
                else:
                    settings["last_status_message"] = (
                        "Cloudflare DEV ativo com URLs aleatorias por servico."
                    )

                update_fields: list[str] = []
                if settings.get("enabled", False) and settings.get(
                    "auto_apply_routes", True
                ):
                    update_fields.extend(
                        _apply_cloudflare_dev_urls_to_config(
                            config=config,
                            settings=settings,
                            dev_urls=_normalize_cloudflare_dev_urls(settings),
                        )
                    )
                settings["enabled"] = True
                config.cloudflare_settings = _normalize_cloudflare_settings(settings)
                update_fields.extend(["cloudflare_settings", "updated_at"])
                config.save(update_fields=list(dict.fromkeys(update_fields)))
                return config, _build_cloudflare_runtime_payload(config)
            except ValidationError:
                _stop_cloudflare_dev_tunnels()
                runtime["state"] = "error"
                runtime["last_error"] = (
                    "Falha ao iniciar Cloudflare DEV. Verifique os logs por servico."
                )
                settings["runtime"] = runtime
                settings["last_action_at"] = now_iso
                config.cloudflare_settings = _normalize_cloudflare_settings(settings)
                config.save(update_fields=["cloudflare_settings", "updated_at"])
                raise

        if normalized_action == "stop":
            _stop_cloudflare_dev_tunnels()
            runtime["state"] = "inactive"
            runtime["last_stopped_at"] = now_iso
            runtime["run_command"] = ""
            settings["runtime"] = runtime
            settings["last_action_at"] = now_iso
            settings["last_status_message"] = (
                "Cloudflare DEV parado pelo painel administrativo."
            )
            settings["dev_urls"] = {
                "portal": "",
                "client": "",
                "admin": "",
                "api": "",
            }
            config.cloudflare_settings = _normalize_cloudflare_settings(settings)
            config.save(update_fields=["cloudflare_settings", "updated_at"])
            return config, _build_cloudflare_runtime_payload(config)

        # status (dev)
        runtime_payload = _build_cloudflare_runtime_payload(config)
        observed_dev_urls = _extract_cloudflare_dev_urls_from_runtime_payload(
            runtime_payload
        )
        current_dev_urls = _normalize_cloudflare_dev_urls(settings)
        update_fields: list[str] = []

        if observed_dev_urls != current_dev_urls:
            settings["dev_urls"] = observed_dev_urls
            settings["last_action_at"] = now_iso
            settings["last_status_message"] = (
                "Cloudflare DEV atualizou dominios aleatorios por servico."
            )
            if settings.get("enabled", False) and settings.get(
                "auto_apply_routes", True
            ):
                update_fields.extend(
                    _apply_cloudflare_dev_urls_to_config(
                        config=config,
                        settings=settings,
                        dev_urls=observed_dev_urls,
                    )
                )

        runtime["state"] = runtime_payload["state"]
        settings["runtime"] = runtime
        config.cloudflare_settings = _normalize_cloudflare_settings(settings)
        update_fields.extend(["cloudflare_settings", "updated_at"])
        config.save(update_fields=list(dict.fromkeys(update_fields)))
        return config, runtime_payload

    current_pid = _read_cloudflare_pid()
    if current_pid is None and CLOUDFLARE_PID_FILE.exists():
        try:
            CLOUDFLARE_PID_FILE.unlink()
        except OSError:
            pass

    if normalized_action == "refresh":
        if current_pid is not None:
            try:
                os.kill(current_pid, signal.SIGTERM)
            except OSError:
                pass
            if CLOUDFLARE_PID_FILE.exists():
                try:
                    CLOUDFLARE_PID_FILE.unlink()
                except OSError:
                    pass
        current_pid = None
        normalized_action = "start"

    if normalized_action == "start":
        if current_pid is not None:
            runtime["state"] = "active"
            runtime["last_error"] = ""
            settings["runtime"] = runtime
            config.cloudflare_settings = _normalize_cloudflare_settings(settings)
            config.save(update_fields=["cloudflare_settings", "updated_at"])
            return config, _build_cloudflare_runtime_payload(config)

        command = _build_cloudflare_run_command(settings)
        try:
            log_handle = open(CLOUDFLARE_LOG_FILE, "a", encoding="utf-8")
        except OSError as exc:
            raise ValidationError("Falha ao abrir log do Cloudflare runtime.") from exc

        try:
            proc = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=log_handle,
                stderr=log_handle,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except FileNotFoundError as exc:
            log_handle.close()
            raise ValidationError(
                "Binario cloudflared nao encontrado no servidor."
            ) from exc
        except OSError as exc:
            log_handle.close()
            raise ValidationError(
                "Falha ao iniciar processo cloudflared no servidor."
            ) from exc

        log_handle.close()
        CLOUDFLARE_PID_FILE.write_text(str(proc.pid), encoding="utf-8")

        runtime["state"] = "active"
        runtime["last_started_at"] = now_iso
        runtime["last_error"] = ""
        runtime["run_command"] = _format_command_for_display(command)
        settings["runtime"] = runtime
        settings["last_action_at"] = now_iso
        settings["last_status_message"] = (
            "Tunnel Cloudflare iniciado pelo painel administrativo."
        )
        config.cloudflare_settings = _normalize_cloudflare_settings(settings)
        config.save(update_fields=["cloudflare_settings", "updated_at"])
        return config, _build_cloudflare_runtime_payload(config)

    if normalized_action == "stop":
        if current_pid is not None:
            try:
                os.kill(current_pid, signal.SIGTERM)
            except OSError:
                pass
        if CLOUDFLARE_PID_FILE.exists():
            try:
                CLOUDFLARE_PID_FILE.unlink()
            except OSError:
                pass

        runtime["state"] = "inactive"
        runtime["last_stopped_at"] = now_iso
        settings["runtime"] = runtime
        settings["last_action_at"] = now_iso
        settings["last_status_message"] = (
            "Tunnel Cloudflare parado pelo painel administrativo."
        )
        config.cloudflare_settings = _normalize_cloudflare_settings(settings)
        config.save(update_fields=["cloudflare_settings", "updated_at"])
        return config, _build_cloudflare_runtime_payload(config)

    # status
    runtime_payload = _build_cloudflare_runtime_payload(config)
    runtime["state"] = runtime_payload["state"]
    settings["runtime"] = runtime
    config.cloudflare_settings = _normalize_cloudflare_settings(settings)
    config.save(update_fields=["cloudflare_settings", "updated_at"])
    return config, runtime_payload


@transaction.atomic
def seed_portal_defaults() -> dict:
    config, created = save_portal_config(payload=DEFAULT_CONFIG_PAYLOAD)
    created_sections = 0
    updated_sections = 0

    for fixture in DEFAULT_SECTION_FIXTURES:
        defaults = {
            "title": fixture["title"],
            "body_json": fixture["body_json"],
            "is_enabled": True,
            "sort_order": fixture["sort_order"],
        }
        section, section_created = PortalSection.objects.update_or_create(
            config=config,
            template_id=fixture["template_id"],
            page=fixture["page"],
            key=fixture["key"],
            defaults=defaults,
        )

        if section_created:
            created_sections += 1
        else:
            updated_sections += 1

    return {
        "config_created": created,
        "config_id": config.id,
        "sections_created": created_sections,
        "sections_updated": updated_sections,
    }
