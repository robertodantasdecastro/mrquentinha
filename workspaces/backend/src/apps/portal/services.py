import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
from urllib import error as urllib_error
from urllib.parse import urlencode, urlparse
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
CLOUDFLARE_API_BASE_URL = "https://api.cloudflare.com/client/v4"
CLOUDFLARE_API_TIMEOUT_SECONDS = 12
CLOUDFLARE_API_DOC_LINKS = (
    {
        "label": "Verificar token API",
        "url": (
            "https://developers.cloudflare.com/api/resources/user/"
            "subresources/tokens/methods/verify/"
        ),
    },
    {
        "label": "Listar zonas",
        "url": "https://developers.cloudflare.com/api/resources/zones/methods/list/",
    },
    {
        "label": "Listar registros DNS",
        "url": (
            "https://developers.cloudflare.com/api/resources/dns/"
            "subresources/records/methods/list/"
        ),
    },
)

DEFAULT_PORTAL_TEMPLATE_ITEMS = [
    {"id": "classic", "label": "Classic"},
    {"id": "letsfit-clean", "label": "LetsFit Clean"},
    {"id": "editorial-jp", "label": "Editorial JP"},
]

DEFAULT_CLIENT_TEMPLATE_ITEMS = [
    {"id": "client-classic", "label": "Cliente Classico"},
    {"id": "client-quentinhas", "label": "Cliente Quentinhas"},
    {"id": "client-vitrine-fit", "label": "Cliente Vitrine Fit"},
    {"id": "client-editorial-jp", "label": "Cliente Editorial JP"},
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
    "dev_url_mode": "random",
    "dev_official_domain": "dev.mrquentinha.com.br",
    "dev_manual_urls": {
        "portal": "https://portal-mrquentinha.trycloudflare.com",
        "client": "https://cliente-mrquentinha.trycloudflare.com",
        "admin": "https://admin-mrquentinha.trycloudflare.com",
        "api": "https://api-mrquentinha.trycloudflare.com",
    },
    "local_snapshot": {},
}


def _default_cloudflare_settings_payload() -> dict:
    return deepcopy(DEFAULT_CLOUDFLARE_SETTINGS)


INSTALLER_WORKFLOW_VERSION = "2026.02.28"
INSTALLER_ALLOWED_STACKS = {"vm", "docker"}
INSTALLER_ALLOWED_ENVS = {"dev", "prod"}
INSTALLER_ALLOWED_TARGETS = {"local", "ssh", "aws", "gcp"}
INSTALLER_ALLOWED_SSH_AUTH_MODES = {"key", "password"}
INSTALLER_ALLOWED_CLOUD_PROVIDERS = {"aws", "gcp"}
INSTALLER_ALLOWED_AWS_AUTH_MODES = {"profile", "access_key"}
INSTALLER_SAFE_REMOTE_PATH_RE = re.compile(r"^[A-Za-z0-9_./$-]+$")
INSTALLER_SAFE_GIT_REF_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
SSL_ALLOWED_DOMAIN_RE = re.compile(r"^[A-Za-z0-9.-]+$")
DBOPS_ALLOWED_LABEL_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
INSTALLER_RUNTIME_DIR = PROJECT_ROOT / ".runtime" / "install"
INSTALLER_JOBS_DIR = INSTALLER_RUNTIME_DIR / "jobs"
DBOPS_RUNTIME_DIR = PROJECT_ROOT / ".runtime" / "db_ops"
DBOPS_KEYS_DIR = DBOPS_RUNTIME_DIR / "keys"
DBOPS_SYNC_DIR = DBOPS_RUNTIME_DIR / "sync"
DBOPS_TUNNEL_PID_FILE = DBOPS_RUNTIME_DIR / "ssh_tunnel.pid"
DBOPS_TUNNEL_LOG_FILE = DBOPS_RUNTIME_DIR / "ssh_tunnel.log"
AWS_COST_DEFAULT_EC2_HOURLY_USD = 0.0416
AWS_COST_EBS_GB_MONTH_USD = 0.10
AWS_COST_EIP_MONTH_USD = 3.60
AWS_COST_ROUTE53_HOSTED_ZONE_MONTH_USD = 0.50
AWS_COST_ROUTE53_QUERIES_MONTH_USD = 0.40
AWS_COST_DATA_TRANSFER_MONTH_USD = 5.00
AWS_COST_EC2_HOURLY_BY_INSTANCE = {
    "t3.nano": 0.0052,
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "t3.large": 0.0832,
    "t4g.nano": 0.0042,
    "t4g.micro": 0.0084,
    "t4g.small": 0.0168,
    "t4g.medium": 0.0336,
    "t4g.large": 0.0672,
}

DEFAULT_DATABASE_OPS_SETTINGS = {
    "tunnel": {
        "enabled": False,
        "local_bind_host": "127.0.0.1",
        "local_port": 55432,
        "remote_db_host": "127.0.0.1",
        "remote_db_port": 5432,
        "status": "inactive",
        "pid": None,
        "last_started_at": "",
        "last_stopped_at": "",
        "last_error": "",
    },
    "psql": {
        "last_command": "",
        "last_executed_at": "",
    },
    "django_sync": {
        "last_dump_file": "",
        "last_synced_at": "",
        "last_synced_by": "",
    },
}


def _default_database_ops_settings_payload() -> dict:
    return deepcopy(DEFAULT_DATABASE_OPS_SETTINGS)


DEFAULT_INSTALLER_SETTINGS = {
    "workflow_version": INSTALLER_WORKFLOW_VERSION,
    "last_synced_at": "",
    "last_sync_note": "Workflow do instalador ainda nao sincronizado nesta instancia.",
    "requires_review": False,
    "operation_mode": "dev",
    "lifecycle": {
        "enforce_sync_memory": True,
        "enforce_quality_gate": True,
        "enforce_installer_workflow_check": True,
    },
    "wizard": {
        "autosave_enabled": True,
        "last_completed_step": "mode",
        "draft": {
            "mode": "dev",
            "stack": "vm",
            "target": "local",
            "start_after_install": False,
        },
    },
    "jobs": {
        "last_job_id": "",
        "last_job_status": "idle",
        "last_job_started_at": "",
        "last_job_finished_at": "",
        "last_job_summary": "",
    },
    "api_public_access": {
        "enabled": False,
        "preferred_endpoint": "public_ip",
        "public_ip_base_url": "http://44.192.27.104",
        "aws_dns_base_url": "http://ec2-44-192-27-104.compute-1.amazonaws.com",
    },
    "database_ops": _default_database_ops_settings_payload(),
}


def _default_installer_settings_payload() -> dict:
    return deepcopy(DEFAULT_INSTALLER_SETTINGS)


def _normalize_mobile_api_public_url(raw_value: object) -> str:
    value = str(raw_value or "").strip().rstrip("/")
    if not value:
        return ""

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return ""

    hostname = str(parsed.hostname or "").strip().lower()
    if not hostname:
        return ""

    if hostname.endswith("mrquentinha.com.br"):
        # Requisito operacional: endpoint mobile publico nao deve usar dominio custom.
        return ""

    return value


def _normalize_api_public_access_settings(raw_value: object | None) -> dict:
    defaults = deepcopy(DEFAULT_INSTALLER_SETTINGS["api_public_access"])
    if not isinstance(raw_value, dict):
        return defaults

    preferred_endpoint = (
        str(raw_value.get("preferred_endpoint", defaults["preferred_endpoint"]))
        .strip()
        .lower()
    )
    if preferred_endpoint not in {"public_ip", "aws_dns"}:
        preferred_endpoint = defaults["preferred_endpoint"]

    public_ip_base_url = _normalize_mobile_api_public_url(
        raw_value.get("public_ip_base_url", defaults["public_ip_base_url"])
    )
    aws_dns_base_url = _normalize_mobile_api_public_url(
        raw_value.get("aws_dns_base_url", defaults["aws_dns_base_url"])
    )

    if not public_ip_base_url:
        public_ip_base_url = defaults["public_ip_base_url"]
    if not aws_dns_base_url:
        aws_dns_base_url = defaults["aws_dns_base_url"]

    return {
        "enabled": bool(raw_value.get("enabled", defaults["enabled"])),
        "preferred_endpoint": preferred_endpoint,
        "public_ip_base_url": public_ip_base_url,
        "aws_dns_base_url": aws_dns_base_url,
    }


def _normalize_operation_mode(raw_value: object | None) -> str:
    normalized = str(raw_value or "").strip().lower()
    if normalized in {"production", "producao"}:
        return "prod"
    if normalized in {"dev", "prod", "hybrid"}:
        return normalized
    return "dev"


def _normalize_database_ops_settings(raw_value: object | None) -> dict:
    defaults = _default_database_ops_settings_payload()
    if not isinstance(raw_value, dict):
        return defaults

    tunnel = raw_value.get("tunnel")
    merged_tunnel = defaults["tunnel"]
    if isinstance(tunnel, dict):
        merged_tunnel["enabled"] = bool(tunnel.get("enabled", merged_tunnel["enabled"]))
        merged_tunnel["local_bind_host"] = (
            str(tunnel.get("local_bind_host", merged_tunnel["local_bind_host"])).strip()
            or merged_tunnel["local_bind_host"]
        )
        try:
            local_port = int(tunnel.get("local_port", merged_tunnel["local_port"]))
        except (TypeError, ValueError):
            local_port = int(merged_tunnel["local_port"])
        merged_tunnel["local_port"] = max(1024, min(local_port, 65535))
        merged_tunnel["remote_db_host"] = (
            str(tunnel.get("remote_db_host", merged_tunnel["remote_db_host"])).strip()
            or merged_tunnel["remote_db_host"]
        )
        try:
            remote_db_port = int(
                tunnel.get("remote_db_port", merged_tunnel["remote_db_port"])
            )
        except (TypeError, ValueError):
            remote_db_port = int(merged_tunnel["remote_db_port"])
        merged_tunnel["remote_db_port"] = max(1, min(remote_db_port, 65535))
        merged_tunnel["status"] = (
            str(tunnel.get("status", merged_tunnel["status"])).strip() or "inactive"
        )
        pid_value = tunnel.get("pid")
        if isinstance(pid_value, int) and pid_value > 0:
            merged_tunnel["pid"] = pid_value
        else:
            merged_tunnel["pid"] = None
        merged_tunnel["last_started_at"] = str(
            tunnel.get("last_started_at", merged_tunnel["last_started_at"])
        ).strip()
        merged_tunnel["last_stopped_at"] = str(
            tunnel.get("last_stopped_at", merged_tunnel["last_stopped_at"])
        ).strip()
        merged_tunnel["last_error"] = str(
            tunnel.get("last_error", merged_tunnel["last_error"])
        ).strip()

    psql = raw_value.get("psql")
    merged_psql = defaults["psql"]
    if isinstance(psql, dict):
        merged_psql["last_command"] = str(
            psql.get("last_command", merged_psql["last_command"])
        ).strip()
        merged_psql["last_executed_at"] = str(
            psql.get("last_executed_at", merged_psql["last_executed_at"])
        ).strip()

    django_sync = raw_value.get("django_sync")
    merged_django_sync = defaults["django_sync"]
    if isinstance(django_sync, dict):
        merged_django_sync["last_dump_file"] = str(
            django_sync.get("last_dump_file", merged_django_sync["last_dump_file"])
        ).strip()
        merged_django_sync["last_synced_at"] = str(
            django_sync.get("last_synced_at", merged_django_sync["last_synced_at"])
        ).strip()
        merged_django_sync["last_synced_by"] = str(
            django_sync.get("last_synced_by", merged_django_sync["last_synced_by"])
        ).strip()

    return {
        "tunnel": merged_tunnel,
        "psql": merged_psql,
        "django_sync": merged_django_sync,
    }


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
    "installer_settings": _default_installer_settings_payload(),
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
        "template_id": "classic",
        "page": PortalPage.SUPORTE,
        "key": "hero",
        "title": "Suporte Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Central de suporte",
            "headline": "Suporte para vendas, pedidos e operacao",
            "subheadline": (
                "Clientes devem abrir chamados no app; equipes operacionais podem "
                "usar os canais institucionais."
            ),
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.SUPORTE,
        "key": "channels",
        "title": "Canais de suporte",
        "sort_order": 20,
        "body_json": {
            "items": [
                {
                    "title": "Suporte cliente",
                    "description": "Abertura de chamado autenticado no app.",
                    "value": "app.mrquentinha.com.br/suporte",
                },
                {
                    "title": "Suporte operacional",
                    "description": "Atendimento comercial e operacional.",
                    "value": "suporte@mrquentinha.com.br",
                },
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.WIKI,
        "key": "hero",
        "title": "Wiki Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Wiki operacional",
            "headline": "Base de conhecimento do ecossistema",
            "subheadline": (
                "Documentacao de operacao comercial, suporte e conformidade."
            ),
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.WIKI,
        "key": "topics",
        "title": "Topicos de wiki",
        "sort_order": 20,
        "body_json": {
            "items": [
                {"title": "Operacao comercial", "href": "/app"},
                {"title": "Suporte e chamados", "href": "/suporte"},
                {"title": "Compliance", "href": "/lgpd"},
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.CARDAPIO,
        "key": "hero",
        "title": "Cardapio Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "API ao vivo",
            "headline": "Cardapio do dia",
            "subheadline": (
                "Selecione a data para consultar itens e precos atualizados "
                "direto do backend."
            ),
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.APP,
        "key": "hero",
        "title": "App Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Canal de vendas",
            "headline": "App e Web Cliente no mesmo fluxo comercial",
            "subheadline": (
                "A venda acontece no app.mrquentinha.com.br com pedido, "
                "pagamento e acompanhamento em tempo real."
            ),
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.SOBRE,
        "key": "hero",
        "title": "Sobre Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Quem somos",
            "headline": "Muito prazer, somos o Mr Quentinha",
            "subheadline": (
                "Comida caseira com processo operacional e tecnologia para venda, "
                "suporte e gestao."
            ),
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.COMO_FUNCIONA,
        "key": "hero",
        "title": "Como funciona Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Jornada completa",
            "headline": "Como funciona o ecossistema Mr Quentinha",
            "subheadline": (
                "Portal institucional, web cliente e operacao administrativa "
                "em um fluxo integrado."
            ),
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.COMO_FUNCIONA,
        "key": "steps",
        "title": "Etapas da jornada",
        "sort_order": 20,
        "body_json": {
            "items": [
                {
                    "title": "Voce escolhe",
                    "description": "Use o cardapio por data e finalize no app.",
                },
                {
                    "title": "Nos produzimos",
                    "description": "A cozinha opera com lote, estoque e qualidade.",
                },
                {
                    "title": "Voce acompanha",
                    "description": "Pedido, pagamento e suporte no mesmo login.",
                },
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.CONTATO,
        "key": "hero",
        "title": "Contato Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Fale com o Mr Quentinha",
            "headline": "Contato institucional e comercial",
            "subheadline": (
                "Parcerias, implantacao e suporte operacional centralizados."
            ),
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.CONTATO,
        "key": "channels",
        "title": "Canais de contato",
        "sort_order": 20,
        "body_json": {
            "items": [
                {
                    "title": "Comercial e parcerias",
                    "description": "Implantacao e evolucao de operacao.",
                    "value": "contato@mrquentinha.com.br",
                },
                {
                    "title": "Suporte operacional",
                    "description": "Demandas de producao, pedidos e atendimento.",
                    "value": "suporte@mrquentinha.com.br",
                },
                {
                    "title": "Horario",
                    "description": "Segunda a sexta, das 08h as 18h.",
                    "value": "Sao Paulo - SP",
                },
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.PRIVACIDADE,
        "key": "hero",
        "title": "Privacidade Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Privacidade e seguranca",
            "headline": "Politica de Privacidade",
            "subheadline": (
                "Transparencia sobre coleta, uso e protecao de dados pessoais "
                "no ecossistema."
            ),
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.TERMOS,
        "key": "hero",
        "title": "Termos Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Termos e condicoes",
            "headline": "Termos de Uso",
            "subheadline": "Condicoes para uso do portal, web client e app.",
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.LGPD,
        "key": "hero",
        "title": "LGPD Portal Classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "LGPD em pratica",
            "headline": "LGPD e seus direitos",
            "subheadline": (
                "Direitos do titular, bases legais e operacao de conformidade."
            ),
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
        "template_id": "letsfit-clean",
        "page": PortalPage.SUPORTE,
        "key": "hero",
        "title": "Suporte LetsFit",
        "sort_order": 10,
        "body_json": {
            "kicker": "Ajuda rapida",
            "headline": "Suporte para clientes e operacao",
            "subheadline": (
                "Atendimento multicanal para jornada de compra, pedidos e uso da "
                "plataforma."
            ),
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.SUPORTE,
        "key": "channels",
        "title": "Canais LetsFit",
        "sort_order": 20,
        "body_json": {
            "items": [
                {
                    "title": "App do cliente",
                    "description": "Canal principal para suporte com historico.",
                    "value": "app.mrquentinha.com.br/suporte",
                },
                {
                    "title": "Canal institucional",
                    "description": "Demandas comerciais e operacionais.",
                    "value": "contato@mrquentinha.com.br",
                },
            ]
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.WIKI,
        "key": "hero",
        "title": "Wiki LetsFit",
        "sort_order": 10,
        "body_json": {
            "kicker": "Documentacao viva",
            "headline": "Wiki operacional e de suporte",
            "subheadline": (
                "Guia rapido para rotinas de venda, atendimento e governanca."
            ),
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.WIKI,
        "key": "topics",
        "title": "Topicos LetsFit",
        "sort_order": 20,
        "body_json": {
            "items": [
                {"title": "Vendas no app", "href": "/app"},
                {"title": "Fluxo de suporte", "href": "/suporte"},
                {"title": "Privacidade e LGPD", "href": "/privacidade"},
            ]
        },
    },
    {
        "template_id": "editorial-jp",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Hero Editorial JP",
        "sort_order": 10,
        "body_json": {
            "kicker": "Edicao semanal",
            "headline": "Cardapio autoral com ritmo de loja editorial",
            "subheadline": (
                "Layout em blocos largos, foco em curadoria e CTA direto para a "
                "area de vendas."
            ),
            "cta_primary": {"label": "Comprar no app", "href": "/app"},
            "cta_secondary": {"label": "Ver cardapio", "href": "/cardapio"},
        },
    },
    {
        "template_id": "editorial-jp",
        "page": PortalPage.HOME,
        "key": "benefits",
        "title": "Diferenciais editorial",
        "sort_order": 20,
        "body_json": {
            "items": [
                {"text": "Curadoria por objetivo alimentar", "icon": "spark"},
                {"text": "Vendas no app com jornada curta", "icon": "cart"},
                {"text": "Suporte e wiki conectados", "icon": "support"},
                {"text": "Operacao em tempo real", "icon": "chart"},
            ]
        },
    },
    {
        "template_id": "editorial-jp",
        "page": PortalPage.HOME,
        "key": "categories",
        "title": "Linhas editoriais",
        "sort_order": 30,
        "body_json": {
            "items": [
                {
                    "name": "Performance",
                    "description": "Marmitas com proteina reforcada para alta rotina.",
                    "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd",
                },
                {
                    "name": "Rotina",
                    "description": (
                        "Opcao equilibrada para almoco e jantar do dia a dia."
                    ),
                    "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
                },
                {
                    "name": "Leves",
                    "description": (
                        "Selecao com menor densidade calorica e alta saciedade."
                    ),
                    "image_url": "https://images.unsplash.com/photo-1490645935967-10de6ba17061",
                },
                {
                    "name": "Kits da semana",
                    "description": "Pacotes prontos para conversao rapida no app.",
                    "image_url": "https://images.unsplash.com/photo-1467003909585-2f8a72700288",
                },
            ]
        },
    },
    {
        "template_id": "editorial-jp",
        "page": PortalPage.SUPORTE,
        "key": "hero",
        "title": "Suporte Editorial JP",
        "sort_order": 10,
        "body_json": {
            "kicker": "Suporte em duas frentes",
            "headline": "Atendimento para cliente e operacao",
            "subheadline": (
                "Clientes no app, time operacional em canais institucionais."
            ),
        },
    },
    {
        "template_id": "editorial-jp",
        "page": PortalPage.SUPORTE,
        "key": "channels",
        "title": "Canais editorial",
        "sort_order": 20,
        "body_json": {
            "items": [
                {
                    "title": "Suporte cliente (app)",
                    "description": "Abertura de chamados autenticados e historico.",
                    "value": "app.mrquentinha.com.br/suporte",
                },
                {
                    "title": "Suporte operacional",
                    "description": (
                        "Comercial, duvidas de implantacao e jornada de loja."
                    ),
                    "value": "suporte@mrquentinha.com.br",
                },
            ]
        },
    },
    {
        "template_id": "editorial-jp",
        "page": PortalPage.WIKI,
        "key": "hero",
        "title": "Wiki Editorial JP",
        "sort_order": 10,
        "body_json": {
            "kicker": "Base editorial",
            "headline": "Wiki de apoio para operacao e vendas",
            "subheadline": (
                "Conteudo curto e acionavel para manter padrao de atendimento."
            ),
        },
    },
    {
        "template_id": "editorial-jp",
        "page": PortalPage.WIKI,
        "key": "topics",
        "title": "Topicos editorial",
        "sort_order": 20,
        "body_json": {
            "items": [
                {"title": "Curadoria e cardapio", "href": "/cardapio"},
                {"title": "Conversao no app", "href": "/app"},
                {"title": "Atendimento e SLA", "href": "/suporte"},
            ]
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
        "template_id": "client-classic",
        "page": PortalPage.CARDAPIO,
        "key": "hero",
        "title": "Cardapio cliente classico",
        "sort_order": 10,
        "body_json": {
            "badge": "Pedido por data",
            "headline": "Selecione suas marmitas",
            "subheadline": "Consulte disponibilidade e monte seu carrinho.",
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.PEDIDOS,
        "key": "hero",
        "title": "Pedidos cliente classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Meus pedidos",
            "headline": "Acompanhe seu historico",
            "subheadline": (
                "Do login ao recebimento: status de preparo, entrega e confirmacao."
            ),
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.CONTA,
        "key": "hero",
        "title": "Conta cliente classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Conta",
            "headline": "Acesse ou crie sua conta",
            "subheadline": ("Centralize login, cadastro, preferencias e atendimento."),
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.SUPORTE,
        "key": "hero",
        "title": "Suporte cliente classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Atendimento",
            "headline": "Suporte do cliente",
            "subheadline": (
                "Abra chamados, acompanhe respostas e mantenha historico no login."
            ),
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.WIKI,
        "key": "hero",
        "title": "Wiki cliente classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Wiki",
            "headline": "Base de ajuda do cliente",
            "subheadline": "Guias rapidos para compra, pedidos, conta e suporte.",
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.WIKI,
        "key": "groups",
        "title": "Grupos da wiki cliente",
        "sort_order": 20,
        "body_json": {
            "items": [
                {
                    "title": "Conta e acesso",
                    "description": "Cadastro, login e seguranca.",
                    "links": [
                        {"label": "Minha conta", "href": "/conta"},
                        {"label": "Privacidade", "href": "/privacidade"},
                        {"label": "Termos", "href": "/termos"},
                    ],
                },
                {
                    "title": "Pedidos e pagamento",
                    "description": "Compra, pagamento e acompanhamento.",
                    "links": [
                        {"label": "Cardapio", "href": "/cardapio"},
                        {"label": "Meus pedidos", "href": "/pedidos"},
                        {"label": "Suporte", "href": "/suporte"},
                    ],
                },
                {
                    "title": "Compliance",
                    "description": "LGPD, privacidade e governanca de dados.",
                    "links": [
                        {"label": "LGPD", "href": "/lgpd"},
                        {"label": "Privacidade", "href": "/privacidade"},
                        {"label": "Suporte", "href": "/suporte"},
                    ],
                },
            ]
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.PRIVACIDADE,
        "key": "hero",
        "title": "Privacidade cliente classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Privacidade e seguranca",
            "headline": "Politica de Privacidade",
            "subheadline": (
                "Coleta, uso e protecao de dados pessoais no ecossistema "
                "Mr Quentinha."
            ),
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.TERMOS,
        "key": "hero",
        "title": "Termos cliente classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "Termos e condicoes",
            "headline": "Termos de Uso",
            "subheadline": "Condicoes para uso do web client e aplicativo.",
        },
    },
    {
        "template_id": "client-classic",
        "page": PortalPage.LGPD,
        "key": "hero",
        "title": "LGPD cliente classico",
        "sort_order": 10,
        "body_json": {
            "kicker": "LGPD em pratica",
            "headline": "LGPD e seus direitos",
            "subheadline": (
                "Direitos do titular, bases legais e processos de atendimento."
            ),
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
    {
        "template_id": "client-editorial-jp",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Web Cliente Editorial JP",
        "sort_order": 10,
        "body_json": {
            "headline": "Area de vendas com visual editorial e foco em conversao",
            "subheadline": (
                "Cards amplos, tipografia de impacto e suporte conectado ao login."
            ),
            "badge": "Checkout acelerado",
        },
    },
    {
        "template_id": "client-editorial-jp",
        "page": PortalPage.HOME,
        "key": "benefits",
        "title": "Diferenciais cliente editorial",
        "sort_order": 20,
        "body_json": {
            "items": [
                {"text": "Navegacao por colecoes", "icon": "grid"},
                {"text": "Resumo da jornada em uma tela", "icon": "timeline"},
                {"text": "Suporte integrado por conta", "icon": "support"},
                {"text": "Checkout com pagamentos online", "icon": "card"},
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
    "installer_settings",
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


def _normalize_installer_settings(raw_value: object | None) -> dict:
    normalized = _default_installer_settings_payload()
    if not isinstance(raw_value, dict):
        return normalized

    normalized["workflow_version"] = (
        str(raw_value.get("workflow_version", "")).strip() or INSTALLER_WORKFLOW_VERSION
    )
    normalized["last_synced_at"] = str(raw_value.get("last_synced_at", "")).strip()
    normalized["last_sync_note"] = (
        str(raw_value.get("last_sync_note", "")).strip() or normalized["last_sync_note"]
    )
    normalized["requires_review"] = bool(raw_value.get("requires_review", False))
    normalized["operation_mode"] = _normalize_operation_mode(
        raw_value.get("operation_mode", normalized["operation_mode"])
    )

    lifecycle = raw_value.get("lifecycle")
    if isinstance(lifecycle, dict):
        normalized["lifecycle"] = {
            "enforce_sync_memory": bool(
                lifecycle.get(
                    "enforce_sync_memory",
                    normalized["lifecycle"]["enforce_sync_memory"],
                )
            ),
            "enforce_quality_gate": bool(
                lifecycle.get(
                    "enforce_quality_gate",
                    normalized["lifecycle"]["enforce_quality_gate"],
                )
            ),
            "enforce_installer_workflow_check": bool(
                lifecycle.get(
                    "enforce_installer_workflow_check",
                    normalized["lifecycle"]["enforce_installer_workflow_check"],
                )
            ),
        }

    wizard = raw_value.get("wizard")
    if isinstance(wizard, dict):
        merged_wizard = normalized["wizard"]
        merged_wizard["autosave_enabled"] = bool(
            wizard.get("autosave_enabled", merged_wizard["autosave_enabled"])
        )
        merged_wizard["last_completed_step"] = (
            str(
                wizard.get(
                    "last_completed_step",
                    merged_wizard.get("last_completed_step", "mode"),
                )
            ).strip()
            or "mode"
        )
        draft_value = wizard.get("draft", {})
        if isinstance(draft_value, dict):
            merged_wizard["draft"] = draft_value
        normalized["wizard"] = merged_wizard

    jobs = raw_value.get("jobs")
    if isinstance(jobs, dict):
        merged_jobs = normalized["jobs"]
        merged_jobs["last_job_id"] = str(jobs.get("last_job_id", "")).strip()
        merged_jobs["last_job_status"] = (
            str(jobs.get("last_job_status", "")).strip() or "idle"
        )
        merged_jobs["last_job_started_at"] = str(
            jobs.get("last_job_started_at", "")
        ).strip()
        merged_jobs["last_job_finished_at"] = str(
            jobs.get("last_job_finished_at", "")
        ).strip()
        merged_jobs["last_job_summary"] = str(jobs.get("last_job_summary", "")).strip()
        normalized["jobs"] = merged_jobs

    normalized["api_public_access"] = _normalize_api_public_access_settings(
        raw_value.get("api_public_access")
    )
    normalized["database_ops"] = _normalize_database_ops_settings(
        raw_value.get("database_ops")
    )

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


def _normalize_cloudflare_dev_url_mode(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"random", "manual", "official"}:
        return normalized
    return "random"


def _normalize_cloudflare_manual_dev_urls(raw_value: object | None) -> dict[str, str]:
    output: dict[str, str] = {
        "portal": "",
        "client": "",
        "admin": "",
        "api": "",
    }
    if not isinstance(raw_value, dict):
        return output

    for channel in output:
        raw_url = str(raw_value.get(channel, "")).strip().rstrip("/")
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            output[channel] = raw_url
    return output


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
    normalized["dev_url_mode"] = _normalize_cloudflare_dev_url_mode(
        raw_value.get("dev_url_mode")
    )
    normalized["dev_official_domain"] = str(
        raw_value.get("dev_official_domain", normalized.get("dev_official_domain", ""))
    ).strip()
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
    source_manual_dev_urls = raw_value.get("dev_manual_urls")
    if isinstance(source_manual_dev_urls, dict):
        for channel in ("portal", "client", "admin", "api"):
            normalized["dev_manual_urls"][channel] = str(
                source_manual_dev_urls.get(channel, "")
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


def _build_cloudflare_official_dev_urls(settings: dict) -> dict[str, str]:
    dev_domain = str(settings.get("dev_official_domain", "")).strip().lower().strip(".")
    scheme = str(settings.get("scheme", "https")).strip().lower()
    if scheme not in {"http", "https"}:
        scheme = "https"

    output: dict[str, str] = {
        "portal": "",
        "client": "",
        "admin": "",
        "api": "",
    }
    if not dev_domain:
        return output

    for spec in CLOUDFLARE_DEV_SERVICE_SPECS:
        channel = str(spec.get("key", "")).strip()
        port = int(spec.get("port", 0) or 0)
        if channel in output and port > 0:
            output[channel] = f"{scheme}://{dev_domain}:{port}"
    return output


def _resolve_cloudflare_active_dev_urls(settings: dict) -> dict[str, str]:
    manual_urls = _normalize_cloudflare_manual_dev_urls(settings.get("dev_manual_urls"))
    dev_url_mode = _normalize_cloudflare_dev_url_mode(settings.get("dev_url_mode"))
    if dev_url_mode == "manual" and _has_complete_cloudflare_dev_urls(manual_urls):
        return manual_urls
    if dev_url_mode == "official":
        official_urls = _build_cloudflare_official_dev_urls(settings)
        if _has_complete_cloudflare_dev_urls(official_urls):
            return official_urls
    return _normalize_cloudflare_dev_urls(settings)


def _has_complete_cloudflare_dev_urls(dev_urls: dict[str, str]) -> bool:
    return all(bool(dev_urls.get(channel, "").strip()) for channel in dev_urls)


def _extract_cloudflare_dev_urls_from_runtime_payload(
    runtime_payload: dict,
) -> dict[str, str]:
    source_urls = runtime_payload.get("observed_dev_urls")
    if not isinstance(source_urls, dict):
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
    dev_url_mode = _normalize_cloudflare_dev_url_mode(normalized.get("dev_url_mode"))
    scheme = normalized["scheme"]
    root_domain = normalized["root_domain"]
    subdomains = normalized["subdomains"]

    if dev_mode:
        dev_urls = _resolve_cloudflare_active_dev_urls(normalized)
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
        "dev_url_mode": dev_url_mode,
        "dev_manual_urls": _normalize_cloudflare_manual_dev_urls(
            normalized.get("dev_manual_urls")
        ),
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
            else (
                "Modo dev usando URLs manuais/estaveis definidas pelo operador."
                if dev_url_mode == "manual"
                else (
                    "Modo dev usando dominio oficial com portas por servico."
                    if dev_url_mode == "official"
                    else (
                        "Modo dev usa dominios aleatorios "
                        "trycloudflare.com por servico."
                    )
                )
            )
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
        "dev_url_mode": _normalize_cloudflare_dev_url_mode(
            normalized.get("dev_url_mode")
        ),
        "dev_official_domain": str(normalized.get("dev_official_domain", "")).strip(),
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
        "dev_manual_urls": _normalize_cloudflare_manual_dev_urls(
            normalized.get("dev_manual_urls")
        ),
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
    observed_dev_urls = _normalize_cloudflare_dev_urls(normalized)
    active_dev_urls = _resolve_cloudflare_active_dev_urls(normalized)
    manual_dev_urls = _normalize_cloudflare_manual_dev_urls(
        normalized.get("dev_manual_urls")
    )
    dev_url_mode = _normalize_cloudflare_dev_url_mode(normalized.get("dev_url_mode"))

    states: list[str] = []
    aggregated_log_lines: list[str] = []
    first_pid: int | None = None

    for service in CLOUDFLARE_DEV_SERVICE_SPECS:
        key = service["key"]
        pid_file = _cloudflare_dev_pid_file(key)
        log_file = _cloudflare_dev_log_file(key)
        pid = _read_pid_from_file(pid_file)
        observed_url = _read_cloudflare_dev_url_from_log(
            log_file
        ) or observed_dev_urls.get(key, "")
        display_url = observed_url or active_dev_urls.get(key, "")
        observed_dev_urls[key] = observed_url
        connectivity = _check_cloudflare_dev_service_connectivity(
            key=key, base_url=display_url
        )
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
                "url": display_url,
                "observed_url": observed_url,
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
        "dev_url_mode": dev_url_mode,
        "dev_manual_urls": manual_dev_urls,
        "dev_urls": active_dev_urls,
        "observed_dev_urls": observed_dev_urls,
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


def _resolve_mobile_api_base_url(config: PortalConfig) -> str:
    installer_settings = _normalize_installer_settings(config.installer_settings)
    public_access = installer_settings.get("api_public_access", {})
    if bool(public_access.get("enabled", False)):
        preferred_endpoint = str(
            public_access.get("preferred_endpoint", "public_ip")
        ).strip()
        candidates: list[str] = []
        if preferred_endpoint == "aws_dns":
            candidates = [
                str(public_access.get("aws_dns_base_url", "")).strip(),
                str(public_access.get("public_ip_base_url", "")).strip(),
            ]
        else:
            candidates = [
                str(public_access.get("public_ip_base_url", "")).strip(),
                str(public_access.get("aws_dns_base_url", "")).strip(),
            ]
        for candidate in candidates:
            normalized = _normalize_mobile_api_public_url(candidate)
            if normalized:
                return normalized

    return _resolve_api_base_url(config)


def _resolve_public_host(config: PortalConfig) -> str:
    parsed = urlparse(_resolve_api_base_url(config))
    if parsed.hostname:
        return parsed.hostname

    if str(config.local_network_ip).strip():
        return str(config.local_network_ip).strip()

    return str(config.local_hostname).strip() or "mrquentinha"


def _resolve_mobile_public_host(config: PortalConfig) -> str:
    parsed = urlparse(_resolve_mobile_api_base_url(config))
    if parsed.hostname:
        return parsed.hostname
    return _resolve_public_host(config)


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

    normalized_installer_settings = _normalize_installer_settings(
        config.installer_settings
    )
    if config.installer_settings != normalized_installer_settings:
        config.installer_settings = normalized_installer_settings
        update_fields.append("installer_settings")

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
    if "installer_settings" in payload:
        payload["installer_settings"] = _normalize_installer_settings(
            payload["installer_settings"]
        )
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


def _resolve_fallback_template_id(
    *,
    channel: PortalChannel,
    active_template: str,
) -> str | None:
    if channel == CHANNEL_CLIENT and active_template != "client-classic":
        return "client-classic"
    if channel == CHANNEL_ADMIN and active_template != "admin-classic":
        return "admin-classic"
    if channel == CHANNEL_PORTAL and active_template != "classic":
        return "classic"
    return None


def _resolve_sections_for_payload(
    *,
    config: PortalConfig,
    page: str,
    channel: PortalChannel,
    active_template: str,
) -> list[PortalSection]:
    primary_sections = list(
        list_sections_by_template_page(
            config=config,
            template_id=active_template,
            page=page,
            enabled_only=True,
        )
    )
    fallback_template = _resolve_fallback_template_id(
        channel=channel,
        active_template=active_template,
    )
    if fallback_template is None:
        return primary_sections

    fallback_sections = list(
        list_sections_by_template_page(
            config=config,
            template_id=fallback_template,
            page=page,
            enabled_only=True,
        )
    )
    if primary_sections:
        return primary_sections
    return fallback_sections


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
    sections = _resolve_sections_for_payload(
        config=config,
        page=page,
        channel=channel,
        active_template=active_template,
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
    release.api_base_url_snapshot = _resolve_mobile_api_base_url(config)
    release.host_publico_snapshot = _resolve_mobile_public_host(config)
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
            "api_base_url": _resolve_mobile_api_base_url(config),
            "host_publico": _resolve_mobile_public_host(config),
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
        "api_base_url": release.api_base_url_snapshot
        or _resolve_mobile_api_base_url(config),
        "host_publico": release.host_publico_snapshot
        or _resolve_mobile_public_host(config),
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


def _cloudflare_api_extract_errors(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []

    raw_errors = payload.get("errors")
    if not isinstance(raw_errors, list):
        return []

    errors: list[str] = []
    for item in raw_errors:
        if isinstance(item, dict):
            code = str(item.get("code", "")).strip()
            message = str(item.get("message", "")).strip()
            if code and message:
                errors.append(f"{code}: {message}")
            elif message:
                errors.append(message)
        elif isinstance(item, str) and item.strip():
            errors.append(item.strip())
    return errors


def _cloudflare_api_request(
    *,
    token: str,
    path: str,
    query: dict[str, str] | None = None,
) -> dict:
    query_string = ""
    if isinstance(query, dict):
        clean_query = {
            str(key): str(value)
            for key, value in query.items()
            if str(value).strip()
        }
        if clean_query:
            query_string = urlencode(clean_query)

    url = f"{CLOUDFLARE_API_BASE_URL}{path}"
    if query_string:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query_string}"

    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=CLOUDFLARE_API_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body or "{}")
            errors = _cloudflare_api_extract_errors(payload)
            return {
                "ok": bool(payload.get("success", False) and not errors),
                "status": int(response.status),
                "payload": payload,
                "errors": errors,
            }
    except urllib_error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            payload = {}
        errors = _cloudflare_api_extract_errors(payload)
        if not errors:
            errors = [f"HTTP {exc.code} ao consultar Cloudflare API."]
        return {
            "ok": False,
            "status": int(exc.code),
            "payload": payload,
            "errors": errors,
        }
    except (urllib_error.URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "status": 0,
            "payload": {},
            "errors": [f"Falha de conectividade com Cloudflare API: {exc}"],
        }


def _build_cloudflare_api_guide_payload() -> dict:
    return {
        "required_permissions": [
            "User -> API Tokens -> Read",
            "Zone -> Zone -> Read",
            "Zone -> DNS -> Read",
            "Zone -> DNS -> Edit (para aplicar/alterar registros)",
        ],
        "steps": [
            "1. Criar API Token no Cloudflare com escopo minimo de leitura.",
            "2. Verificar token via endpoint /user/tokens/verify.",
            "3. Resolver Zone ID (manual ou automatico por root_domain).",
            "4. Validar se os registros DNS esperados existem (portal/client/admin/api).",
            "5. Em producao, confirmar proxied=true apenas quando realmente usar proxy Cloudflare.",
        ],
        "docs": list(CLOUDFLARE_API_DOC_LINKS),
    }


def inspect_cloudflare_api_status(*, overrides: dict | None = None) -> dict:
    config = ensure_portal_config()
    settings = _normalize_cloudflare_settings(config.cloudflare_settings)
    if isinstance(overrides, dict):
        settings = _normalize_cloudflare_settings({**settings, **overrides})

    token = str(settings.get("api_token", "")).strip()
    zone_id_input = str(settings.get("zone_id", "")).strip()
    account_id = str(settings.get("account_id", "")).strip()

    preview = _build_cloudflare_preview_payload(config, settings)
    expected_domains = {
        channel: str(preview.get("domains", {}).get(channel, "")).strip().lower()
        for channel in ("portal", "client", "admin", "api")
    }

    result = {
        "checked_at": timezone.now().isoformat(),
        "configured": bool(token),
        "mode": str(settings.get("mode", "hybrid")).strip().lower() or "hybrid",
        "dev_mode": bool(settings.get("dev_mode", False)),
        "expected_domains": expected_domains,
        "token": {
            "configured": bool(token),
            "valid": False,
            "status": "missing" if not token else "pending",
            "expires_on": "",
            "not_before": "",
            "id": "",
            "errors": [],
        },
        "zone": {
            "configured": bool(zone_id_input),
            "resolved": False,
            "id": zone_id_input,
            "name": "",
            "status": "not_checked",
            "errors": [],
        },
        "dns": {
            "checked": False,
            "records": {
                "portal": {"domain": expected_domains["portal"], "found": False, "type": "", "content": "", "proxied": None},
                "client": {"domain": expected_domains["client"], "found": False, "type": "", "content": "", "proxied": None},
                "admin": {"domain": expected_domains["admin"], "found": False, "type": "", "content": "", "proxied": None},
                "api": {"domain": expected_domains["api"], "found": False, "type": "", "content": "", "proxied": None},
            },
            "missing": [],
            "errors": [],
        },
        "tunnel": {
            "checked": False,
            "account_id": account_id,
            "total": 0,
            "errors": [],
        },
        "guide": _build_cloudflare_api_guide_payload(),
    }

    if not token:
        result["token"]["errors"] = [
            "Informe API Token para diagnosticar Cloudflare via API."
        ]
        return result

    token_check = _cloudflare_api_request(token=token, path="/user/tokens/verify")
    token_payload = token_check.get("payload", {})
    token_info = token_payload.get("result", {}) if isinstance(token_payload, dict) else {}
    result["token"]["errors"] = token_check.get("errors", [])
    if token_check.get("ok") and isinstance(token_info, dict):
        result["token"]["valid"] = True
        result["token"]["status"] = str(token_info.get("status", "active")).strip() or "active"
        result["token"]["expires_on"] = str(token_info.get("expires_on", "")).strip()
        result["token"]["not_before"] = str(token_info.get("not_before", "")).strip()
        result["token"]["id"] = str(token_info.get("id", "")).strip()
    else:
        result["token"]["status"] = "invalid"
        return result

    resolved_zone_id = zone_id_input
    root_domain = str(settings.get("root_domain", "")).strip().lower().strip(".")
    if resolved_zone_id:
        zone_check = _cloudflare_api_request(
            token=token,
            path=f"/zones/{resolved_zone_id}",
        )
        zone_payload = zone_check.get("payload", {})
        zone_info = zone_payload.get("result", {}) if isinstance(zone_payload, dict) else {}
    else:
        zone_check = _cloudflare_api_request(
            token=token,
            path="/zones",
            query={"name": root_domain, "status": "active", "per_page": "1", "page": "1"},
        )
        zone_payload = zone_check.get("payload", {})
        zone_list = zone_payload.get("result", []) if isinstance(zone_payload, dict) else []
        zone_info = zone_list[0] if isinstance(zone_list, list) and zone_list else {}
        resolved_zone_id = str(zone_info.get("id", "")).strip()

    result["zone"]["errors"] = zone_check.get("errors", [])
    result["zone"]["id"] = resolved_zone_id
    result["zone"]["name"] = str(zone_info.get("name", "")).strip()
    result["zone"]["status"] = str(zone_info.get("status", "")).strip() or (
        "active" if resolved_zone_id else "missing"
    )
    result["zone"]["resolved"] = bool(resolved_zone_id)

    if not resolved_zone_id:
        if not result["zone"]["errors"]:
            result["zone"]["errors"] = [
                "Nao foi possivel resolver Zone ID com os dados informados."
            ]
        return result

    for channel, hostname in expected_domains.items():
        if not hostname:
            continue

        dns_check = _cloudflare_api_request(
            token=token,
            path=f"/zones/{resolved_zone_id}/dns_records",
            query={"name": hostname, "per_page": "10", "page": "1"},
        )
        if not dns_check.get("ok"):
            result["dns"]["errors"].extend(dns_check.get("errors", []))
            continue

        dns_payload = dns_check.get("payload", {})
        records = dns_payload.get("result", []) if isinstance(dns_payload, dict) else []
        if not isinstance(records, list) or not records:
            continue

        picked = records[0] if isinstance(records[0], dict) else {}
        result["dns"]["records"][channel] = {
            "domain": hostname,
            "found": True,
            "type": str(picked.get("type", "")).strip(),
            "content": str(picked.get("content", "")).strip(),
            "proxied": bool(picked.get("proxied", False))
            if picked.get("proxied") is not None
            else None,
        }

    result["dns"]["checked"] = True
    missing = [
        channel
        for channel, payload in result["dns"]["records"].items()
        if not bool(payload.get("found"))
    ]
    result["dns"]["missing"] = missing

    if account_id:
        tunnel_check = _cloudflare_api_request(
            token=token,
            path=f"/accounts/{account_id}/cfd_tunnel",
            query={"is_deleted": "false", "per_page": "50", "page": "1"},
        )
        result["tunnel"]["checked"] = True
        result["tunnel"]["errors"] = tunnel_check.get("errors", [])
        if tunnel_check.get("ok"):
            tunnel_payload = tunnel_check.get("payload", {})
            tunnel_items = (
                tunnel_payload.get("result", [])
                if isinstance(tunnel_payload, dict)
                else []
            )
            if isinstance(tunnel_items, list):
                result["tunnel"]["total"] = len(tunnel_items)

    return result


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
            dev_urls = _resolve_cloudflare_active_dev_urls(settings)
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
                    routing_dev_urls = _resolve_cloudflare_active_dev_urls(settings)
                    update_fields.extend(
                        _apply_cloudflare_dev_urls_to_config(
                            config=config,
                            settings=settings,
                            dev_urls=routing_dev_urls,
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
                routing_dev_urls = _resolve_cloudflare_active_dev_urls(settings)
                update_fields.extend(
                    _apply_cloudflare_dev_urls_to_config(
                        config=config,
                        settings=settings,
                        dev_urls=routing_dev_urls,
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


def apply_ssl_certificates(*, payload: dict | None) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    email = str(payload.get("email", "")).strip()
    raw_domains = payload.get("domains", [])
    dry_run = bool(payload.get("dry_run", False))

    if not email:
        raise ValidationError("Informe o e-mail para o certificado SSL.")

    domains: list[str] = []
    if isinstance(raw_domains, str):
        domains = [item.strip() for item in raw_domains.split(",") if item.strip()]
    elif isinstance(raw_domains, list):
        domains = [str(item).strip() for item in raw_domains if str(item).strip()]

    if not domains:
        raise ValidationError("Informe pelo menos um dominio para SSL.")

    for domain in domains:
        if not SSL_ALLOWED_DOMAIN_RE.fullmatch(domain):
            raise ValidationError(f"Dominio invalido: {domain}")

    script_path = PROJECT_ROOT / "scripts" / "ops_ssl_cert.sh"
    if not script_path.exists():
        raise ValidationError("Script de certificados nao encontrado.")

    env = os.environ.copy()
    env["MRQ_SSL_EMAIL"] = email
    env["MRQ_SSL_DOMAINS"] = ",".join(domains)
    env["MRQ_SSL_DRY_RUN"] = "1" if dry_run else "0"

    process = subprocess.run(
        ["bash", str(script_path)],
        env=env,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )

    return {
        "ok": process.returncode == 0,
        "exit_code": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


@transaction.atomic
def save_database_ssh_settings(*, payload: dict | None) -> PortalConfig:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    if bool(context.get("local_db_ops")):
        raise ValidationError(
            "SSH/tunnel nao e necessario neste ambiente (EC2 com banco local)."
        )
    payload = payload if isinstance(payload, dict) else {}
    ssh_settings = _validate_dbops_ssh_settings(payload)
    return _save_dbops_ssh_in_installer_settings(
        config=config,
        ssh_settings=ssh_settings,
        completed_step="database-ssh",
    )


def validate_database_ssh_connectivity(*, payload: dict | None = None) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    if bool(context.get("local_db_ops")):
        return {
            "ok": True,
            "check": {
                "name": "ssh_not_required",
                "status": "ok",
                "detail": "SSH nao requerido neste ambiente (EC2 com banco local).",
            },
            "ssh": {},
            "runtime": context,
        }
    incoming = payload if isinstance(payload, dict) else {}
    source_settings = incoming if incoming else _extract_dbops_ssh_from_config(config)
    ssh_settings = _validate_dbops_ssh_settings(source_settings)
    check = _run_ssh_connectivity_probe(ssh_settings=ssh_settings)
    return {
        "ok": True,
        "check": check,
        "ssh": _sanitize_installer_payload({"ssh": ssh_settings}).get("ssh", {}),
    }


@transaction.atomic
def upload_database_ssh_key(
    *,
    filename: str,
    content: str,
) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    if bool(context.get("local_db_ops")):
        raise ValidationError(
            "Upload de chave SSH nao se aplica neste ambiente (EC2 com banco local)."
        )
    normalized_filename = os.path.basename(str(filename or "").strip())
    if not normalized_filename:
        raise ValidationError("Arquivo .pem invalido (nome vazio).")
    if not normalized_filename.lower().endswith(".pem"):
        raise ValidationError("Arquivo invalido: envie uma chave com extensao .pem.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", normalized_filename):
        raise ValidationError(
            "Arquivo .pem invalido: nome contem caracteres proibidos."
        )

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise ValidationError("Conteudo da chave .pem vazio.")
    if "BEGIN" not in normalized_content or "PRIVATE KEY" not in normalized_content:
        raise ValidationError(
            "Conteudo da chave .pem invalido (cabecalho de chave privada ausente)."
        )

    _ensure_dbops_runtime_dirs()
    key_path = DBOPS_KEYS_DIR / normalized_filename
    try:
        key_path.write_text(normalized_content + "\n", encoding="utf-8")
        os.chmod(key_path, 0o600)
    except OSError as exc:
        raise ValidationError(
            "Falha ao salvar chave .pem no servidor backend."
        ) from exc

    return {
        "ok": True,
        "key_path": str(key_path),
        "filename": normalized_filename,
    }


def _local_db_backups_dir() -> Path:
    backup_dir = PROJECT_ROOT / ".runtime" / "db_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def _local_django_manage_env(*, settings_module: str = "config.settings.prod") -> dict:
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = settings_module
    return env


def list_remote_database_backups(*, limit: int = 30) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    safe_limit = max(1, min(int(limit or 30), 200))
    lines: list[str] = []

    if bool(context.get("local_db_ops")):
        backup_dir = _local_db_backups_dir()
        entries: list[tuple[float, Path]] = []
        for file_path in backup_dir.glob("*.dump"):
            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                continue
            entries.append((mtime, file_path))
        entries.sort(key=lambda item: item[0], reverse=True)
        for mtime, path in entries[:safe_limit]:
            try:
                size_value = path.stat().st_size
            except OSError:
                size_value = 0
            lines.append(f"{mtime}|{path}|{size_value}")
    else:
        ssh_settings = _validate_dbops_ssh_settings(
            _extract_dbops_ssh_from_config(config)
        )
        repo_path = str(ssh_settings.get("repo_path", "$HOME/mrquentinha")).strip()
        remote_script = f"""
set -euo pipefail
REPO_PATH={shlex.quote(repo_path)}
BACKUP_DIR="$REPO_PATH/.runtime/db_backups"
mkdir -p "$BACKUP_DIR"
find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.dump' -printf '%T@|%p|%s\\n' \
  | sort -nr | head -n {safe_limit}
"""
        result, command_preview = _run_remote_dbops_script(
            ssh_settings=ssh_settings,
            remote_shell_script=remote_script,
            timeout_seconds=40,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise ValidationError(
                "Falha ao listar backups remotos. "
                f"Comando: {command_preview}. Detalhe: {detail or 'sem detalhe'}"
            )
        lines = (result.stdout or "").splitlines()

    backups: list[dict] = []
    for line in lines:
        parts = line.strip().split("|", 2)
        if len(parts) != 3:
            continue
        try:
            ts_float = float(parts[0])
        except ValueError:
            ts_float = 0.0
        path = parts[1].strip()
        try:
            size_bytes = int(parts[2].strip())
        except ValueError:
            size_bytes = 0
        backups.append(
            {
                "path": path,
                "size_bytes": size_bytes,
                "updated_at": (
                    datetime.fromtimestamp(ts_float).isoformat() if ts_float > 0 else ""
                ),
                "filename": Path(path).name,
            }
        )

    return {
        "ok": True,
        "count": len(backups),
        "results": backups,
        "runtime": context,
    }


def create_remote_database_backup(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    payload = payload if isinstance(payload, dict) else {}
    label = _normalize_dbops_label(payload.get("label", "manual"))
    if bool(context.get("local_db_ops")):
        local_env, local_db_name = _build_local_pg_env()
        pg_dump_bin = shutil.which("pg_dump")
        if not pg_dump_bin:
            raise ValidationError("PG_DUMP_AUSENTE no ambiente local.")
        backup_dir = _local_db_backups_dir()
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"mrq_prod_{timestamp}_{label}.dump"
        meta_file = backup_dir / f"mrq_prod_{timestamp}_{label}.json"
        result = subprocess.run(
            [
                pg_dump_bin,
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                "--dbname",
                local_db_name,
                "--file",
                str(backup_file),
            ],
            check=False,
            env=local_env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise ValidationError(
                f"Falha ao gerar backup local. Detalhe: {detail or 'sem detalhe'}"
            )
        commit_hash = (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(PROJECT_ROOT),
                check=False,
                capture_output=True,
                text=True,
            ).stdout.strip()
            or "unknown"
        )
        meta_payload = {
            "created_at": timezone.now().isoformat(),
            "label": label,
            "dump_file": str(backup_file),
            "commit": commit_hash,
        }
        try:
            meta_file.write_text(
                json.dumps(meta_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass
        size_bytes = backup_file.stat().st_size if backup_file.exists() else 0
        return {
            "ok": True,
            "label": label,
            "backup_file": str(backup_file),
            "metadata_file": str(meta_file),
            "size_bytes": size_bytes,
            "ssh_target": "",
            "runtime": context,
        }

    ssh_settings = _validate_dbops_ssh_settings(_extract_dbops_ssh_from_config(config))
    repo_path = str(ssh_settings.get("repo_path", "$HOME/mrquentinha")).strip()

    remote_script = f"""
set -euo pipefail
REPO_PATH={shlex.quote(repo_path)}
BACKUP_LABEL={shlex.quote(label)}
BACKUP_DIR="$REPO_PATH/.runtime/db_backups"
mkdir -p "$BACKUP_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
DUMP_FILE="$BACKUP_DIR/mrq_prod_${{TS}}_${{BACKUP_LABEL}}.dump"
META_FILE="$BACKUP_DIR/mrq_prod_${{TS}}_${{BACKUP_LABEL}}.json"
if [ -f "$REPO_PATH/workspaces/backend/.env.prod" ]; then
  set -a
  . "$REPO_PATH/workspaces/backend/.env.prod"
  set +a
fi
if [ -z "${{DATABASE_URL:-}}" ]; then
  echo "DATABASE_URL_NAO_DEFINIDA" >&2
  exit 41
fi
if ! command -v pg_dump >/dev/null 2>&1; then
  echo "PG_DUMP_AUSENTE" >&2
  exit 42
fi
pg_dump --format=custom --no-owner --no-privileges \
  --dbname="$DATABASE_URL" --file="$DUMP_FILE"
COMMIT_HASH="$(
  cd "$REPO_PATH" && git rev-parse --short HEAD 2>/dev/null || echo unknown
)"
cat > "$META_FILE" <<EOF
{"created_at":"$(date -Is)","label":"$BACKUP_LABEL",
"dump_file":"$DUMP_FILE","commit":"$COMMIT_HASH"}
EOF
SIZE_BYTES="$(wc -c < "$DUMP_FILE" | tr -d ' ')"
echo "MQ_BACKUP_FILE=$DUMP_FILE"
echo "MQ_BACKUP_META=$META_FILE"
echo "MQ_BACKUP_SIZE=$SIZE_BYTES"
"""
    result, command_preview = _run_remote_dbops_script(
        ssh_settings=ssh_settings,
        remote_shell_script=remote_script,
        timeout_seconds=180,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ValidationError(
            "Falha ao gerar backup remoto de producao. "
            f"Comando: {command_preview}. Detalhe: {detail or 'sem detalhe'}"
        )

    backup_file = ""
    meta_file = ""
    size_bytes = 0
    for line in (result.stdout or "").splitlines():
        if line.startswith("MQ_BACKUP_FILE="):
            backup_file = line.split("=", 1)[1].strip()
        elif line.startswith("MQ_BACKUP_META="):
            meta_file = line.split("=", 1)[1].strip()
        elif line.startswith("MQ_BACKUP_SIZE="):
            try:
                size_bytes = int(line.split("=", 1)[1].strip())
            except ValueError:
                size_bytes = 0

    if not backup_file:
        raise ValidationError(
            "Backup remoto finalizou sem retorno do caminho do arquivo .dump."
        )

    return {
        "ok": True,
        "label": label,
        "backup_file": backup_file,
        "metadata_file": meta_file,
        "size_bytes": size_bytes,
        "ssh_target": _build_ssh_destination(ssh_settings),
        "runtime": context,
    }


def restore_remote_database_backup(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    payload = payload if isinstance(payload, dict) else {}
    confirm = str(payload.get("confirm", "")).strip().upper()
    if confirm != "RESTAURAR":
        raise ValidationError(
            "Confirmacao obrigatoria. "
            "Informe confirm='RESTAURAR' para executar restore."
        )
    backup_file = str(payload.get("backup_file", "")).strip()
    if not backup_file:
        raise ValidationError("Informe backup_file para restaurar no ambiente remoto.")
    if not INSTALLER_SAFE_REMOTE_PATH_RE.fullmatch(backup_file):
        raise ValidationError("backup_file invalido para execucao remota.")

    if bool(context.get("local_db_ops")):
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise ValidationError("BACKUP_NAO_ENCONTRADO no ambiente local.")
        local_env, local_db_name = _build_local_pg_env()
        pg_restore_bin = shutil.which("pg_restore")
        if not pg_restore_bin:
            raise ValidationError("PG_RESTORE_AUSENTE no ambiente local.")
        restore_result = subprocess.run(
            [
                pg_restore_bin,
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                "--dbname",
                local_db_name,
                str(backup_path),
            ],
            check=False,
            env=local_env,
            capture_output=True,
            text=True,
        )
        if restore_result.returncode != 0:
            detail = (restore_result.stderr or restore_result.stdout or "").strip()
            raise ValidationError(
                "Falha ao restaurar backup local. "
                f"Detalhe: {detail or 'sem detalhe'}"
            )
        migrate_result = subprocess.run(
            [sys.executable, "manage.py", "migrate", "--noinput"],
            cwd=str(PROJECT_ROOT / "workspaces" / "backend"),
            check=False,
            env=_local_django_manage_env(settings_module="config.settings.prod"),
            capture_output=True,
            text=True,
        )
        if migrate_result.returncode != 0:
            detail = (migrate_result.stderr or migrate_result.stdout or "").strip()
            raise ValidationError(
                "Restore local aplicado, mas migrate falhou. "
                f"Detalhe: {detail or 'sem detalhe'}"
            )
        return {
            "ok": True,
            "backup_file": backup_file,
            "summary": "Restore local concluido e migracoes aplicadas.",
            "runtime": context,
        }

    ssh_settings = _validate_dbops_ssh_settings(_extract_dbops_ssh_from_config(config))
    repo_path = str(ssh_settings.get("repo_path", "$HOME/mrquentinha")).strip()

    remote_script = f"""
set -euo pipefail
REPO_PATH={shlex.quote(repo_path)}
BACKUP_FILE={shlex.quote(backup_file)}
if [ ! -f "$BACKUP_FILE" ]; then
  echo "BACKUP_NAO_ENCONTRADO" >&2
  exit 44
fi
if [ -f "$REPO_PATH/workspaces/backend/.env.prod" ]; then
  set -a
  . "$REPO_PATH/workspaces/backend/.env.prod"
  set +a
fi
if [ -z "${{DATABASE_URL:-}}" ]; then
  echo "DATABASE_URL_NAO_DEFINIDA" >&2
  exit 41
fi
if ! command -v pg_restore >/dev/null 2>&1; then
  echo "PG_RESTORE_AUSENTE" >&2
  exit 45
fi
pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname="$DATABASE_URL" "$BACKUP_FILE"
if [ -f "$REPO_PATH/workspaces/backend/.venv/bin/activate" ]; then
  . "$REPO_PATH/workspaces/backend/.venv/bin/activate"
fi
cd "$REPO_PATH/workspaces/backend"
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate --noinput
echo "MQ_RESTORE_OK"
"""
    result, command_preview = _run_remote_dbops_script(
        ssh_settings=ssh_settings,
        remote_shell_script=remote_script,
        timeout_seconds=300,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ValidationError(
            "Falha ao restaurar backup no ambiente remoto. "
            f"Comando: {command_preview}. Detalhe: {detail or 'sem detalhe'}"
        )

    return {
        "ok": True,
        "backup_file": backup_file,
        "summary": "Restore remoto concluido e migracoes aplicadas.",
        "runtime": context,
    }


def sync_remote_database_backup_to_dev(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    if bool(context.get("local_db_ops")):
        raise ValidationError(
            "Sync para DEV a partir de remoto nao se aplica nesta instancia local."
        )
    payload = payload if isinstance(payload, dict) else {}
    backup_file = str(payload.get("backup_file", "")).strip()
    if not backup_file:
        raise ValidationError("Informe backup_file para sincronizar no ambiente DEV.")
    if not INSTALLER_SAFE_REMOTE_PATH_RE.fullmatch(backup_file):
        raise ValidationError("backup_file invalido para sincronizacao.")

    ssh_settings = _validate_dbops_ssh_settings(_extract_dbops_ssh_from_config(config))
    _ensure_dbops_runtime_dirs()
    sync_stamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    local_dump_path = DBOPS_SYNC_DIR / f"prod_to_dev_{sync_stamp}.dump"

    cat_script = f"set -euo pipefail; cat {shlex.quote(backup_file)}"
    cat_command = _build_ssh_exec_command(
        ssh_settings=ssh_settings,
        remote_shell_script=cat_script,
        mask_sensitive=False,
    )
    preview_command = _render_command_preview(
        _build_ssh_exec_command(
            ssh_settings=ssh_settings,
            remote_shell_script=cat_script,
            mask_sensitive=True,
        )
    )

    try:
        with open(local_dump_path, "wb") as dump_handle:
            transfer_result = subprocess.run(
                cat_command,
                check=False,
                stdout=dump_handle,
                stderr=subprocess.PIPE,
                timeout=240,
            )
    except subprocess.TimeoutExpired as exc:
        raise ValidationError("Sync DEV: timeout ao transferir dump remoto.") from exc
    except OSError as exc:
        raise ValidationError("Sync DEV: falha ao salvar dump local.") from exc

    if transfer_result.returncode != 0:
        stderr_text = (
            transfer_result.stderr.decode("utf-8", errors="ignore")
            if transfer_result.stderr
            else ""
        )
        raise ValidationError(
            "Sync DEV: falha ao transferir backup remoto. "
            "Comando: "
            f"{preview_command}. Detalhe: {stderr_text.strip() or 'sem detalhe'}"
        )

    local_env, local_db_name = _build_local_pg_env()
    local_backup_before_restore = DBOPS_SYNC_DIR / f"dev_before_sync_{sync_stamp}.dump"
    pg_dump_bin = shutil.which("pg_dump")
    if pg_dump_bin:
        subprocess.run(
            [
                pg_dump_bin,
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                "--dbname",
                local_db_name,
                "--file",
                str(local_backup_before_restore),
            ],
            check=False,
            env=local_env,
            capture_output=True,
            text=True,
        )

    pg_restore_bin = shutil.which("pg_restore")
    if not pg_restore_bin:
        raise ValidationError("Sync DEV: utilitario pg_restore nao encontrado.")
    restore_result = subprocess.run(
        [
            pg_restore_bin,
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            "--dbname",
            local_db_name,
            str(local_dump_path),
        ],
        check=False,
        env=local_env,
        capture_output=True,
        text=True,
    )
    if restore_result.returncode != 0:
        detail = (restore_result.stderr or restore_result.stdout or "").strip()
        raise ValidationError(
            "Sync DEV: falha ao restaurar dump no banco local. "
            f"Detalhe: {detail or 'sem detalhe'}"
        )

    backend_cwd = PROJECT_ROOT / "workspaces" / "backend"
    migrate_env = os.environ.copy()
    migrate_env["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
    migrate_result = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        cwd=str(backend_cwd),
        check=False,
        env=migrate_env,
        capture_output=True,
        text=True,
    )
    if migrate_result.returncode != 0:
        detail = (migrate_result.stderr or migrate_result.stdout or "").strip()
        raise ValidationError(
            "Sync DEV: restore aplicado, mas migrate DEV falhou. "
            f"Detalhe: {detail or 'sem detalhe'}"
        )

    size_bytes = local_dump_path.stat().st_size if local_dump_path.exists() else 0
    return {
        "ok": True,
        "source_backup_file": backup_file,
        "local_dump_file": str(local_dump_path),
        "local_dump_size_bytes": size_bytes,
        "local_pre_restore_backup": (
            str(local_backup_before_restore)
            if local_backup_before_restore.exists()
            else ""
        ),
        "summary": "Banco DEV sincronizado com backup remoto de producao.",
    }


def _ensure_installer_runtime_dirs() -> None:
    INSTALLER_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    INSTALLER_JOBS_DIR.mkdir(parents=True, exist_ok=True)


def _installer_job_file(job_id: str) -> Path:
    return INSTALLER_JOBS_DIR / f"{job_id}.json"


def _tail_text_file(file_path: Path, *, lines: int = 40) -> list[str]:
    if not file_path.exists():
        return []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    all_lines = content.splitlines()
    if len(all_lines) <= lines:
        return all_lines
    return all_lines[-lines:]


def _is_pid_running(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _read_installer_job(job_id: str) -> dict:
    normalized_job_id = str(job_id).strip()
    if not normalized_job_id:
        raise ValidationError("Informe um job_id valido.")
    if "/" in normalized_job_id or "\\" in normalized_job_id:
        raise ValidationError("job_id invalido.")

    job_file = _installer_job_file(normalized_job_id)
    if not job_file.exists():
        raise ValidationError("Job de instalacao nao encontrado.")

    try:
        payload = json.loads(job_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError("Falha ao ler o estado do job de instalacao.") from exc

    if not isinstance(payload, dict):
        raise ValidationError("Estado do job de instalacao invalido.")

    return payload


def _write_installer_job(payload: dict) -> dict:
    job_id = str(payload.get("job_id", "")).strip()
    if not job_id:
        raise ValidationError("Estado do job sem identificador.")

    _ensure_installer_runtime_dirs()
    job_file = _installer_job_file(job_id)
    try:
        job_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ValidationError(
            "Falha ao persistir estado do job de instalacao."
        ) from exc
    return payload


def _normalize_installer_wizard_payload(
    raw_payload: object | None,
) -> tuple[dict, list[str]]:
    if not isinstance(raw_payload, dict):
        raw_payload = {}

    warnings: list[str] = []
    normalized: dict = {}

    mode = str(raw_payload.get("mode", "dev")).strip().lower()
    if mode not in INSTALLER_ALLOWED_ENVS:
        mode = "dev"
    normalized["mode"] = mode

    stack = str(raw_payload.get("stack", "vm")).strip().lower()
    if stack not in INSTALLER_ALLOWED_STACKS:
        stack = "vm"
    normalized["stack"] = stack
    if stack == "docker":
        warnings.append(
            "Stack Docker selecionada. "
            "A arquitetura oficial inicial permanece VM sem Docker."
        )

    target = str(raw_payload.get("target", "local")).strip().lower()
    if target not in INSTALLER_ALLOWED_TARGETS:
        target = "local"
    normalized["target"] = target

    start_after_install = bool(raw_payload.get("start_after_install", False))
    normalized["start_after_install"] = start_after_install

    ssh = raw_payload.get("ssh")
    normalized_ssh = {
        "host": "",
        "port": 22,
        "user": "",
        "auth_mode": "key",
        "key_path": "",
        "password": "",
        "repo_path": "$HOME/mrquentinha",
        "auto_clone_repo": False,
        "git_remote_url": "",
        "git_branch": "main",
    }
    if isinstance(ssh, dict):
        normalized_ssh["host"] = str(ssh.get("host", "")).strip()
        normalized_ssh["user"] = str(ssh.get("user", "")).strip()
        normalized_ssh["key_path"] = str(ssh.get("key_path", "")).strip()
        normalized_ssh["password"] = str(ssh.get("password", "")).strip()
        repo_path = str(ssh.get("repo_path", "$HOME/mrquentinha")).strip()
        if repo_path.startswith("~/"):
            repo_path = "$HOME/" + repo_path[2:]
        elif repo_path == "~":
            repo_path = "$HOME"
        normalized_ssh["repo_path"] = repo_path or "$HOME/mrquentinha"
        normalized_ssh["auto_clone_repo"] = bool(ssh.get("auto_clone_repo", False))
        normalized_ssh["git_remote_url"] = str(ssh.get("git_remote_url", "")).strip()
        git_branch = str(ssh.get("git_branch", "main")).strip()
        normalized_ssh["git_branch"] = git_branch or "main"
        try:
            port = int(ssh.get("port", 22))
        except (TypeError, ValueError):
            port = 22
        normalized_ssh["port"] = max(1, min(port, 65535))
        auth_mode = str(ssh.get("auth_mode", "key")).strip().lower()
        if auth_mode not in INSTALLER_ALLOWED_SSH_AUTH_MODES:
            auth_mode = "key"
        normalized_ssh["auth_mode"] = auth_mode
    normalized["ssh"] = normalized_ssh

    cloud = raw_payload.get("cloud")
    normalized_cloud = {
        "provider": "aws",
        "auth_mode": "profile",
        "profile_name": "",
        "access_key_id": "",
        "secret_access_key": "",
        "session_token": "",
        "region": "",
        "instance_type": "",
        "ami": "",
        "key_pair_name": "",
        "ebs_gb": 20,
        "route53_hosted_zone_id": "",
        "ec2_instance_id": "",
        "elastic_ip_allocation_id": "",
        "use_elastic_ip": True,
        "use_codedeploy": False,
        "codedeploy_application_name": "",
        "codedeploy_deployment_group": "",
    }
    if isinstance(cloud, dict):
        provider = str(cloud.get("provider", "aws")).strip().lower()
        if provider not in INSTALLER_ALLOWED_CLOUD_PROVIDERS:
            provider = "aws"
        auth_mode = str(cloud.get("auth_mode", "profile")).strip().lower()
        if auth_mode not in INSTALLER_ALLOWED_AWS_AUTH_MODES:
            auth_mode = "profile"
        normalized_cloud["provider"] = provider
        normalized_cloud["auth_mode"] = auth_mode
        normalized_cloud["profile_name"] = str(cloud.get("profile_name", "")).strip()
        normalized_cloud["access_key_id"] = str(cloud.get("access_key_id", "")).strip()
        normalized_cloud["secret_access_key"] = str(
            cloud.get("secret_access_key", "")
        ).strip()
        normalized_cloud["session_token"] = str(cloud.get("session_token", "")).strip()
        normalized_cloud["region"] = str(cloud.get("region", "")).strip()
        normalized_cloud["instance_type"] = str(cloud.get("instance_type", "")).strip()
        normalized_cloud["ami"] = str(cloud.get("ami", "")).strip()
        normalized_cloud["key_pair_name"] = str(cloud.get("key_pair_name", "")).strip()
        normalized_cloud["route53_hosted_zone_id"] = str(
            cloud.get("route53_hosted_zone_id", "")
        ).strip()
        normalized_cloud["ec2_instance_id"] = str(
            cloud.get("ec2_instance_id", "")
        ).strip()
        normalized_cloud["elastic_ip_allocation_id"] = str(
            cloud.get("elastic_ip_allocation_id", "")
        ).strip()
        normalized_cloud["use_elastic_ip"] = bool(cloud.get("use_elastic_ip", True))
        normalized_cloud["use_codedeploy"] = bool(cloud.get("use_codedeploy", False))
        normalized_cloud["codedeploy_application_name"] = str(
            cloud.get("codedeploy_application_name", "")
        ).strip()
        normalized_cloud["codedeploy_deployment_group"] = str(
            cloud.get("codedeploy_deployment_group", "")
        ).strip()
        try:
            ebs_gb = int(cloud.get("ebs_gb", 20))
        except (TypeError, ValueError):
            ebs_gb = 20
        normalized_cloud["ebs_gb"] = max(8, min(ebs_gb, 1024))
    if target in INSTALLER_ALLOWED_CLOUD_PROVIDERS:
        normalized_cloud["provider"] = target
    if normalized_cloud["provider"] != "aws":
        normalized_cloud["auth_mode"] = "profile"
        normalized_cloud["profile_name"] = ""
        normalized_cloud["access_key_id"] = ""
        normalized_cloud["secret_access_key"] = ""
        normalized_cloud["session_token"] = ""
        normalized_cloud["route53_hosted_zone_id"] = ""
        normalized_cloud["ec2_instance_id"] = ""
        normalized_cloud["elastic_ip_allocation_id"] = ""
        normalized_cloud["use_codedeploy"] = False
        normalized_cloud["codedeploy_application_name"] = ""
        normalized_cloud["codedeploy_deployment_group"] = ""
    normalized["cloud"] = normalized_cloud

    deployment = raw_payload.get("deployment")
    normalized_deployment = {
        "store_name": "Mr Quentinha",
        "root_domain": "mrquentinha.com.br",
        "portal_domain": "www.mrquentinha.com.br",
        "client_domain": "app.mrquentinha.com.br",
        "admin_domain": "admin.mrquentinha.com.br",
        "api_domain": "api.mrquentinha.com.br",
        "seed_mode": "empty",
    }
    if isinstance(deployment, dict):
        for key in (
            "store_name",
            "root_domain",
            "portal_domain",
            "client_domain",
            "admin_domain",
            "api_domain",
            "seed_mode",
        ):
            value = str(deployment.get(key, normalized_deployment[key])).strip()
            if value:
                normalized_deployment[key] = value
    if normalized_deployment["seed_mode"] not in {"empty", "examples"}:
        normalized_deployment["seed_mode"] = "empty"
    normalized["deployment"] = normalized_deployment

    lifecycle = raw_payload.get("lifecycle")
    normalized_lifecycle = {
        "enforce_sync_memory": True,
        "enforce_quality_gate": True,
        "enforce_installer_workflow_check": True,
    }
    if isinstance(lifecycle, dict):
        for key in normalized_lifecycle:
            normalized_lifecycle[key] = bool(
                lifecycle.get(key, normalized_lifecycle[key])
            )
    normalized["lifecycle"] = normalized_lifecycle

    if target == "ssh":
        if not normalized_ssh["host"]:
            raise ValidationError("SSH: informe o host remoto.")
        if not normalized_ssh["user"]:
            raise ValidationError("SSH: informe o usuario remoto.")
        if not normalized_ssh[
            "repo_path"
        ] or not INSTALLER_SAFE_REMOTE_PATH_RE.fullmatch(normalized_ssh["repo_path"]):
            raise ValidationError(
                "SSH: repo_path invalido. Use apenas letras, numeros, ., /, _, -, $."
            )
        if normalized_ssh["auth_mode"] == "key" and not normalized_ssh["key_path"]:
            warnings.append(
                "SSH por chave selecionado sem key_path. "
                "Valide o caminho da chave privada."
            )
        if normalized_ssh["auth_mode"] == "password" and not normalized_ssh["password"]:
            raise ValidationError("SSH: informe a senha quando auth_mode=password.")
        if normalized_ssh["auto_clone_repo"] and not normalized_ssh["git_remote_url"]:
            raise ValidationError(
                "SSH: informe git_remote_url para auto_clone_repo=true."
            )
        if not INSTALLER_SAFE_GIT_REF_RE.fullmatch(normalized_ssh["git_branch"]):
            raise ValidationError(
                "SSH: git_branch invalida. Use apenas letras, numeros, ., _, -, /."
            )

    if target in {"aws", "gcp"} and not normalized_cloud["region"]:
        warnings.append(
            "Cloud sem regiao definida. O assistente vai exigir antes da execucao."
        )
    if (
        target == "aws"
        and normalized_cloud["auth_mode"] == "access_key"
        and not normalized_cloud["access_key_id"]
    ):
        warnings.append(
            "AWS auth_mode=access_key sem access_key_id. Informe a chave para validar."
        )
    if (
        target == "aws"
        and normalized_cloud["auth_mode"] == "access_key"
        and not normalized_cloud["secret_access_key"]
    ):
        warnings.append(
            "AWS auth_mode=access_key sem secret_access_key. "
            "Informe a chave secreta para validar."
        )

    return normalized, warnings


def _build_local_installer_command(
    *, stack: str, env_name: str, start_after: bool
) -> list[str]:
    command = [
        "bash",
        str(PROJECT_ROOT / "scripts" / "install_mrquentinha.sh"),
        "--stack",
        stack,
        "--env",
        env_name,
        "--yes",
    ]
    if start_after:
        command.append("--start")
    return command


def _sanitize_installer_payload(payload: dict) -> dict:
    sanitized = deepcopy(payload)
    ssh_settings = sanitized.get("ssh")
    if isinstance(ssh_settings, dict):
        if "password" in ssh_settings:
            ssh_settings["password"] = ""
    cloud_settings = sanitized.get("cloud")
    if isinstance(cloud_settings, dict):
        if "secret_access_key" in cloud_settings:
            cloud_settings["secret_access_key"] = ""
        if "session_token" in cloud_settings:
            cloud_settings["session_token"] = ""
    return sanitized


def _build_ssh_destination(ssh_settings: dict) -> str:
    host = str(ssh_settings.get("host", "")).strip()
    user = str(ssh_settings.get("user", "")).strip()
    return f"{user}@{host}"


def _resolve_ssh_key_path(ssh_settings: dict) -> str:
    raw_path = str(ssh_settings.get("key_path", "")).strip()
    if not raw_path:
        return ""
    return os.path.expanduser(raw_path)


def _build_ssh_base_command(
    *, ssh_settings: dict, mask_sensitive: bool = False
) -> list[str]:
    auth_mode = str(ssh_settings.get("auth_mode", "key")).strip().lower()
    port = int(ssh_settings.get("port", 22) or 22)
    base_ssh = [
        "ssh",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-p",
        str(port),
    ]

    if auth_mode == "password":
        password = str(ssh_settings.get("password", "")).strip()
        if not password:
            raise ValidationError("SSH: senha nao informada para auth_mode=password.")
        sshpass_bin = shutil.which("sshpass")
        if not sshpass_bin:
            raise ValidationError(
                "SSH com senha requer 'sshpass' instalado no servidor do backend."
            )
        sanitized_password = "***" if mask_sensitive else password
        return [
            sshpass_bin,
            "-p",
            sanitized_password,
            *base_ssh,
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
        ]

    key_path = _resolve_ssh_key_path(ssh_settings)
    if key_path:
        base_ssh.extend(["-i", key_path])
    base_ssh.extend(["-o", "BatchMode=yes"])
    return base_ssh


def _build_ssh_exec_command(
    *, ssh_settings: dict, remote_shell_script: str, mask_sensitive: bool = False
) -> list[str]:
    command = _build_ssh_base_command(
        ssh_settings=ssh_settings,
        mask_sensitive=mask_sensitive,
    )
    command.append(_build_ssh_destination(ssh_settings))
    command.append(f"bash -lc {shlex.quote(remote_shell_script)}")
    return command


def _render_command_preview(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _run_ssh_connectivity_probe(*, ssh_settings: dict) -> dict:
    probe_script = "set -euo pipefail; echo MQ_SSH_CONNECTIVITY_OK"
    probe_command = _build_ssh_exec_command(
        ssh_settings=ssh_settings,
        remote_shell_script=probe_script,
        mask_sensitive=False,
    )
    preview_command = _build_ssh_exec_command(
        ssh_settings=ssh_settings,
        remote_shell_script=probe_script,
        mask_sensitive=True,
    )

    try:
        result = subprocess.run(
            probe_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValidationError(
            "SSH: timeout ao validar conectividade com o host remoto."
        ) from exc
    except OSError as exc:
        raise ValidationError(
            "SSH: falha ao executar cliente SSH no servidor do backend."
        ) from exc

    stdout = str(result.stdout or "").strip()
    stderr = str(result.stderr or "").strip()

    if result.returncode != 0:
        detail = stderr or stdout or "sem detalhe"
        raise ValidationError(
            "SSH: conexao rejeitada. "
            f"Comando: { _render_command_preview(preview_command) }. "
            f"Detalhe: {detail}"
        )

    return {
        "name": "ssh_connectivity",
        "status": "ok",
        "detail": "Conectividade SSH validada com sucesso.",
        "checked_at": timezone.now().isoformat(),
        "target": _build_ssh_destination(ssh_settings),
        "command_preview": _render_command_preview(preview_command),
    }


def _ensure_dbops_runtime_dirs() -> None:
    DBOPS_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    DBOPS_KEYS_DIR.mkdir(parents=True, exist_ok=True)
    DBOPS_SYNC_DIR.mkdir(parents=True, exist_ok=True)


def _normalize_dbops_label(raw_value: object | None) -> str:
    value = str(raw_value or "").strip().lower()
    if not value:
        return "manual"
    normalized = re.sub(r"[^a-z0-9_-]+", "-", value).strip("-_")
    if not normalized:
        normalized = "manual"
    if len(normalized) > 40:
        normalized = normalized[:40]
    if not DBOPS_ALLOWED_LABEL_RE.fullmatch(normalized):
        raise ValidationError(
            "Label de backup invalida. Use letras, numeros, '_' ou '-' (max 40)."
        )
    return normalized


def _resolve_operation_mode(*, config: PortalConfig) -> str:
    installer_settings = _normalize_installer_settings(config.installer_settings)
    explicit_mode = _normalize_operation_mode(installer_settings.get("operation_mode"))
    if explicit_mode in {"dev", "prod", "hybrid"}:
        return explicit_mode

    wizard = installer_settings.get("wizard", {})
    draft = wizard.get("draft", {}) if isinstance(wizard, dict) else {}
    mode = str(draft.get("mode", "")).strip().lower()
    cloudflare_mode = str(config.cloudflare_settings.get("mode", "")).strip().lower()
    if cloudflare_mode == "hybrid":
        return "hybrid"
    if mode in {"dev", "prod"}:
        return mode
    root_domain = str(config.root_domain or "").strip().lower()
    if root_domain.endswith(".local"):
        return "dev"
    return "dev"


def _detect_runtime_machine_kind() -> str:
    explicit = str(os.environ.get("MRQ_RUNTIME_MACHINE", "")).strip().lower()
    if explicit in {"vm", "ec2"}:
        return explicit

    if os.environ.get("AWS_EXECUTION_ENV") or os.environ.get("EC2_INSTANCE_ID"):
        return "ec2"

    for probe_path in (
        "/sys/hypervisor/uuid",
        "/sys/devices/virtual/dmi/id/board_vendor",
        "/sys/devices/virtual/dmi/id/sys_vendor",
    ):
        try:
            content = Path(probe_path).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        normalized = content.strip().lower()
        if "amazon ec2" in normalized or normalized.startswith("ec2"):
            return "ec2"

    return "vm"


def resolve_database_runtime_context(*, config: PortalConfig) -> dict:
    machine_kind = _detect_runtime_machine_kind()
    operation_mode = _resolve_operation_mode(config=config)
    local_db_ops = machine_kind == "ec2" and operation_mode in {"prod", "hybrid"}
    return {
        "machine_kind": machine_kind,
        "operation_mode": operation_mode,
        "local_db_ops": local_db_ops,
        "ssh_required": not local_db_ops,
        "tunnel_available": not local_db_ops,
        "psql_transport": "local" if local_db_ops else "ssh",
        "backup_transport": "local" if local_db_ops else "ssh",
        "copy_to_dev_via_scp_available": not local_db_ops,
        "sync_to_dev_available": not local_db_ops,
    }


def _normalize_dbops_ssh_settings(raw_value: object | None) -> dict:
    payload = {
        "mode": "dev",
        "stack": "vm",
        "target": "ssh",
        "start_after_install": False,
        "ssh": raw_value if isinstance(raw_value, dict) else {},
    }
    normalized_payload, _warnings = _normalize_installer_wizard_payload(payload)
    normalized_ssh = normalized_payload.get("ssh", {})
    if not isinstance(normalized_ssh, dict):
        normalized_ssh = {}
    return normalized_ssh


def _extract_dbops_ssh_from_config(config: PortalConfig) -> dict:
    installer_settings = _normalize_installer_settings(config.installer_settings)
    wizard = installer_settings.get("wizard", {})
    draft = wizard.get("draft", {}) if isinstance(wizard, dict) else {}
    ssh_settings = draft.get("ssh", {}) if isinstance(draft, dict) else {}
    return _normalize_dbops_ssh_settings(ssh_settings)


def _validate_dbops_ssh_settings(ssh_settings: dict) -> dict:
    normalized = _normalize_dbops_ssh_settings(ssh_settings)
    host = str(normalized.get("host", "")).strip()
    user = str(normalized.get("user", "")).strip()
    auth_mode = str(normalized.get("auth_mode", "key")).strip().lower()

    if not host:
        raise ValidationError("SSH: informe o host do ambiente de producao.")
    if not user:
        raise ValidationError("SSH: informe o usuario do ambiente de producao.")
    if auth_mode == "key":
        key_path = _resolve_ssh_key_path(normalized)
        if not key_path:
            raise ValidationError("SSH: key_path obrigatorio para auth_mode=key.")
        if not os.path.exists(key_path):
            raise ValidationError(f"SSH: chave nao encontrada em '{key_path}'.")
    if auth_mode == "password" and not str(normalized.get("password", "")).strip():
        raise ValidationError("SSH: informe a senha para auth_mode=password.")

    repo_path = str(normalized.get("repo_path", "$HOME/mrquentinha")).strip()
    if not repo_path:
        repo_path = "$HOME/mrquentinha"
    if repo_path.startswith("~/"):
        repo_path = "$HOME/" + repo_path[2:]
    elif repo_path == "~":
        repo_path = "$HOME"
    if not INSTALLER_SAFE_REMOTE_PATH_RE.fullmatch(repo_path):
        raise ValidationError(
            "SSH: repo_path invalido. Use apenas letras, numeros, ., /, _, -, $."
        )
    normalized["repo_path"] = repo_path
    return normalized


def _save_dbops_ssh_in_installer_settings(
    *,
    config: PortalConfig,
    ssh_settings: dict,
    completed_step: str = "database-ssh",
) -> PortalConfig:
    installer_settings = _normalize_installer_settings(config.installer_settings)
    wizard = installer_settings.get("wizard", {})
    if not isinstance(wizard, dict):
        wizard = {}
    draft = wizard.get("draft", {})
    if not isinstance(draft, dict):
        draft = {}
    draft["ssh"] = _sanitize_installer_payload({"ssh": ssh_settings}).get("ssh", {})
    if str(draft.get("target", "")).strip().lower() not in {"ssh", "aws", "gcp"}:
        draft["target"] = "ssh"
    wizard["draft"] = draft
    wizard["last_completed_step"] = str(completed_step or "database-ssh").strip()
    installer_settings["wizard"] = wizard
    installer_settings["last_synced_at"] = timezone.now().isoformat()
    installer_settings["last_sync_note"] = (
        "Configuracao SSH do modulo Banco de dados atualizada."
    )
    config.installer_settings = _normalize_installer_settings(installer_settings)
    config.save(update_fields=["installer_settings", "updated_at"])
    return config


def _run_remote_dbops_script(
    *,
    ssh_settings: dict,
    remote_shell_script: str,
    timeout_seconds: int = 120,
) -> tuple[subprocess.CompletedProcess[str], str]:
    command = _build_ssh_exec_command(
        ssh_settings=ssh_settings,
        remote_shell_script=remote_shell_script,
        mask_sensitive=False,
    )
    preview_command = _build_ssh_exec_command(
        ssh_settings=ssh_settings,
        remote_shell_script=remote_shell_script,
        mask_sensitive=True,
    )
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValidationError(
            "DB Ops: timeout ao executar comando remoto via SSH."
        ) from exc
    except OSError as exc:
        raise ValidationError("DB Ops: falha ao executar cliente SSH local.") from exc
    return result, _render_command_preview(preview_command)


def _build_scp_base_command(
    *,
    ssh_settings: dict,
    mask_sensitive: bool = False,
) -> list[str]:
    auth_mode = str(ssh_settings.get("auth_mode", "key")).strip().lower()
    port = int(ssh_settings.get("port", 22) or 22)
    base_scp = [
        "scp",
        "-P",
        str(port),
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]

    if auth_mode == "password":
        password = str(ssh_settings.get("password", "")).strip()
        if not password:
            raise ValidationError("SCP: senha nao informada para auth_mode=password.")
        sshpass_bin = shutil.which("sshpass")
        if not sshpass_bin:
            raise ValidationError(
                "SCP com senha requer 'sshpass' instalado no servidor do backend."
            )
        safe_password = "***" if mask_sensitive else password
        return [sshpass_bin, "-p", safe_password, *base_scp]

    key_path = _resolve_ssh_key_path(ssh_settings)
    if key_path:
        base_scp.extend(["-i", key_path])
    return base_scp


def _build_local_pg_env() -> tuple[dict, str]:
    from django.db import connections

    settings_dict = connections["default"].settings_dict
    db_name = str(settings_dict.get("NAME", "")).strip()
    if not db_name:
        raise ValidationError("DB local: nome do banco nao identificado nas settings.")

    env = os.environ.copy()
    env["PGHOST"] = str(settings_dict.get("HOST", "") or "127.0.0.1")
    env["PGPORT"] = str(settings_dict.get("PORT", "") or "5432")
    env["PGUSER"] = str(settings_dict.get("USER", "") or "")
    password = str(settings_dict.get("PASSWORD", "") or "")
    if password:
        env["PGPASSWORD"] = password
    return env, db_name


def _dbops_read_tunnel_pid() -> int | None:
    return _read_pid_from_file(DBOPS_TUNNEL_PID_FILE)


def _dbops_store_tunnel_state(
    *,
    config: PortalConfig,
    tunnel_state: dict,
) -> PortalConfig:
    installer_settings = _normalize_installer_settings(config.installer_settings)
    database_ops = _normalize_database_ops_settings(
        installer_settings.get("database_ops")
    )
    database_ops["tunnel"] = tunnel_state
    installer_settings["database_ops"] = database_ops
    installer_settings["last_synced_at"] = timezone.now().isoformat()
    installer_settings["last_sync_note"] = "Estado do tunnel SSH de banco atualizado."
    config.installer_settings = _normalize_installer_settings(installer_settings)
    config.save(update_fields=["installer_settings", "updated_at"])
    return config


def _dbops_read_tunnel_settings(*, config: PortalConfig) -> dict:
    installer_settings = _normalize_installer_settings(config.installer_settings)
    database_ops = _normalize_database_ops_settings(
        installer_settings.get("database_ops")
    )
    return database_ops.get(
        "tunnel",
        _default_database_ops_settings_payload()["tunnel"],
    )


def _dbops_build_tunnel_state_payload(*, config: PortalConfig) -> dict:
    tunnel_state = _dbops_read_tunnel_settings(config=config)
    runtime_pid = _dbops_read_tunnel_pid()
    running = _is_pid_running(runtime_pid)
    if not running:
        runtime_pid = None
    tunnel_state["pid"] = runtime_pid
    tunnel_state["status"] = "active" if running else "inactive"
    return tunnel_state


@transaction.atomic
def save_database_tunnel_settings(*, payload: dict | None) -> PortalConfig:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    if bool(context.get("local_db_ops")):
        raise ValidationError(
            "Tunnel SSH nao se aplica neste ambiente (EC2 com banco local)."
        )
    payload = payload if isinstance(payload, dict) else {}
    installer_settings = _normalize_installer_settings(config.installer_settings)
    database_ops = _normalize_database_ops_settings(
        installer_settings.get("database_ops")
    )
    tunnel_state = database_ops.get("tunnel", {})
    if not isinstance(tunnel_state, dict):
        tunnel_state = _default_database_ops_settings_payload()["tunnel"]

    local_bind_host = str(
        payload.get("local_bind_host", tunnel_state["local_bind_host"])
    ).strip()
    if not local_bind_host:
        local_bind_host = "127.0.0.1"
    remote_db_host = str(
        payload.get("remote_db_host", tunnel_state["remote_db_host"])
    ).strip()
    if not remote_db_host:
        remote_db_host = "127.0.0.1"
    try:
        local_port = int(payload.get("local_port", tunnel_state["local_port"]))
    except (TypeError, ValueError):
        local_port = int(tunnel_state["local_port"])
    try:
        remote_db_port = int(
            payload.get("remote_db_port", tunnel_state["remote_db_port"])
        )
    except (TypeError, ValueError):
        remote_db_port = int(tunnel_state["remote_db_port"])
    tunnel_state["local_bind_host"] = local_bind_host
    tunnel_state["local_port"] = max(1024, min(local_port, 65535))
    tunnel_state["remote_db_host"] = remote_db_host
    tunnel_state["remote_db_port"] = max(1, min(remote_db_port, 65535))
    database_ops["tunnel"] = tunnel_state
    installer_settings["database_ops"] = database_ops
    installer_settings["last_synced_at"] = timezone.now().isoformat()
    installer_settings["last_sync_note"] = "Configuracao de tunnel SSH atualizada."
    config.installer_settings = _normalize_installer_settings(installer_settings)
    config.save(update_fields=["installer_settings", "updated_at"])
    return config


@transaction.atomic
def manage_database_ssh_tunnel(*, action: str) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    action_name = str(action or "status").strip().lower()
    if action_name not in {"start", "stop", "status"}:
        raise ValidationError("Acao de tunnel invalida. Use start, stop ou status.")
    if bool(context.get("local_db_ops")):
        tunnel_state = _dbops_build_tunnel_state_payload(config=config)
        tunnel_state["status"] = "inactive"
        tunnel_state["pid"] = None
        tunnel_state["last_error"] = (
            "Tunnel SSH indisponivel neste ambiente (EC2 com banco local)."
        )
        if action_name == "stop":
            tunnel_state["last_stopped_at"] = timezone.now().isoformat()
        _dbops_store_tunnel_state(config=config, tunnel_state=tunnel_state)
        return {
            "ok": True,
            "action": action_name,
            "tunnel": tunnel_state,
            "runtime": context,
        }

    ssh_settings = _validate_dbops_ssh_settings(_extract_dbops_ssh_from_config(config))
    tunnel_state = _dbops_read_tunnel_settings(config=config)
    now_iso = timezone.now().isoformat()

    _ensure_dbops_runtime_dirs()
    current_pid = _dbops_read_tunnel_pid()
    running = _is_pid_running(current_pid)

    if action_name == "start":
        if running:
            tunnel_state["status"] = "active"
            tunnel_state["pid"] = current_pid
            _dbops_store_tunnel_state(config=config, tunnel_state=tunnel_state)
            return {
                "ok": True,
                "action": action_name,
                "tunnel": tunnel_state,
                "runtime": context,
            }

        local_bind_host = str(tunnel_state.get("local_bind_host", "127.0.0.1")).strip()
        local_port = int(tunnel_state.get("local_port", 55432) or 55432)
        remote_db_host = str(tunnel_state.get("remote_db_host", "127.0.0.1")).strip()
        remote_db_port = int(tunnel_state.get("remote_db_port", 5432) or 5432)
        ssh_command = _build_ssh_base_command(
            ssh_settings=ssh_settings,
            mask_sensitive=False,
        )
        ssh_command.extend(
            [
                "-N",
                "-L",
                f"{local_bind_host}:{local_port}:{remote_db_host}:{remote_db_port}",
                _build_ssh_destination(ssh_settings),
            ]
        )
        try:
            log_handle = open(DBOPS_TUNNEL_LOG_FILE, "a", encoding="utf-8")
        except OSError as exc:
            raise ValidationError("Falha ao abrir log do tunnel SSH.") from exc
        try:
            process = subprocess.Popen(
                ssh_command,
                cwd=PROJECT_ROOT,
                stdout=log_handle,
                stderr=log_handle,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            log_handle.close()
            raise ValidationError("Falha ao iniciar tunnel SSH de banco.") from exc
        finally:
            log_handle.close()

        DBOPS_TUNNEL_PID_FILE.write_text(str(process.pid), encoding="utf-8")
        tunnel_state["status"] = "active"
        tunnel_state["pid"] = process.pid
        tunnel_state["last_started_at"] = now_iso
        tunnel_state["last_error"] = ""
        _dbops_store_tunnel_state(config=config, tunnel_state=tunnel_state)
        return {
            "ok": True,
            "action": action_name,
            "tunnel": tunnel_state,
            "runtime": context,
        }

    if action_name == "stop":
        if running and current_pid:
            try:
                os.kill(current_pid, signal.SIGTERM)
            except OSError:
                pass
        if DBOPS_TUNNEL_PID_FILE.exists():
            try:
                DBOPS_TUNNEL_PID_FILE.unlink()
            except OSError:
                pass
        tunnel_state["status"] = "inactive"
        tunnel_state["pid"] = None
        tunnel_state["last_stopped_at"] = now_iso
        _dbops_store_tunnel_state(config=config, tunnel_state=tunnel_state)
        return {
            "ok": True,
            "action": action_name,
            "tunnel": tunnel_state,
            "runtime": context,
        }

    tunnel_state = _dbops_build_tunnel_state_payload(config=config)
    _dbops_store_tunnel_state(config=config, tunnel_state=tunnel_state)
    return {
        "ok": True,
        "action": action_name,
        "tunnel": tunnel_state,
        "runtime": context,
    }


@transaction.atomic
def run_remote_psql_command(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    payload = payload if isinstance(payload, dict) else {}
    command_sql = str(payload.get("command", "")).strip()
    if not command_sql:
        raise ValidationError("Informe o comando SQL para execucao remota.")
    read_only = bool(payload.get("read_only", True))
    confirm = str(payload.get("confirm", "")).strip().upper()
    if not read_only and confirm != "EXECUTAR":
        raise ValidationError("Para comando com escrita, informe confirm='EXECUTAR'.")

    if read_only:
        first_token = command_sql.split(None, 1)[0].lower() if command_sql else ""
        if first_token not in {"select", "show", "explain", "with"}:
            raise ValidationError(
                "Comando read_only permite apenas SELECT/SHOW/EXPLAIN/WITH."
            )

    if bool(context.get("local_db_ops")):
        local_env, local_db_name = _build_local_pg_env()
        psql_bin = shutil.which("psql")
        if not psql_bin:
            raise ValidationError("PSQL_AUSENTE no ambiente local.")
        result = subprocess.run(
            [
                psql_bin,
                local_db_name,
                "-v",
                "ON_ERROR_STOP=1",
                "-P",
                "pager=off",
                "-c",
                command_sql,
            ],
            check=False,
            env=local_env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        command_preview = (
            f"psql {shlex.quote(local_db_name)} -v ON_ERROR_STOP=1 "
            f"-P pager=off -c {shlex.quote(command_sql)}"
        )
    else:
        ssh_settings = _validate_dbops_ssh_settings(
            _extract_dbops_ssh_from_config(config)
        )
        repo_path = str(ssh_settings.get("repo_path", "$HOME/mrquentinha")).strip()
        remote_script = f"""
set -euo pipefail
REPO_PATH={shlex.quote(repo_path)}
if [ -f "$REPO_PATH/workspaces/backend/.env.prod" ]; then
  set -a
  . "$REPO_PATH/workspaces/backend/.env.prod"
  set +a
fi
if [ -z "${{DATABASE_URL:-}}" ]; then
  echo "DATABASE_URL_NAO_DEFINIDA" >&2
  exit 41
fi
if ! command -v psql >/dev/null 2>&1; then
  echo "PSQL_AUSENTE" >&2
  exit 46
fi
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -P pager=off -c {shlex.quote(command_sql)}
"""
        result, command_preview = _run_remote_dbops_script(
            ssh_settings=ssh_settings,
            remote_shell_script=remote_script,
            timeout_seconds=120,
        )

    installer_settings = _normalize_installer_settings(config.installer_settings)
    database_ops = _normalize_database_ops_settings(
        installer_settings.get("database_ops")
    )
    database_ops["psql"]["last_command"] = command_sql[:500]
    database_ops["psql"]["last_executed_at"] = timezone.now().isoformat()
    installer_settings["database_ops"] = database_ops
    config.installer_settings = _normalize_installer_settings(installer_settings)
    config.save(update_fields=["installer_settings", "updated_at"])

    return {
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
        "command_preview": command_preview,
        "runtime": context,
    }


@transaction.atomic
def sync_remote_database_via_django(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    payload = payload if isinstance(payload, dict) else {}
    mode = str(payload.get("mode", "dump")).strip().lower()
    if mode not in {"dump", "sync_dev"}:
        raise ValidationError("Modo invalido. Use 'dump' ou 'sync_dev'.")
    exclude_apps = payload.get("exclude_apps", [])
    excludes: list[str] = []
    if isinstance(exclude_apps, list):
        excludes = [str(item).strip() for item in exclude_apps if str(item).strip()]
    if not excludes:
        excludes = ["auth.permission", "contenttypes", "admin.logentry", "sessions"]

    _ensure_dbops_runtime_dirs()
    stamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    local_dump_file = DBOPS_SYNC_DIR / f"django_dump_{stamp}.json"
    if bool(context.get("local_db_ops")):
        if mode == "sync_dev":
            raise ValidationError(
                "sync_dev indisponivel nesta instancia (EC2 com banco local)."
            )
        backend_cwd = PROJECT_ROOT / "workspaces" / "backend"
        dump_cmd = [
            sys.executable,
            "manage.py",
            "dumpdata",
            "--natural-foreign",
            "--natural-primary",
            "--indent",
            "2",
        ]
        for excluded in excludes:
            dump_cmd.extend(["--exclude", excluded])
        dump_result = subprocess.run(
            dump_cmd,
            cwd=str(backend_cwd),
            check=False,
            env=_local_django_manage_env(settings_module="config.settings.prod"),
            capture_output=True,
            text=True,
            timeout=240,
        )
        if dump_result.returncode != 0:
            detail = (dump_result.stderr or dump_result.stdout or "").strip()
            raise ValidationError(
                "Falha ao executar dumpdata local. "
                f"Detalhe: {detail or 'sem detalhe'}"
            )
        dump_payload = dump_result.stdout or "[]"
    else:
        ssh_settings = _validate_dbops_ssh_settings(
            _extract_dbops_ssh_from_config(config)
        )
        repo_path = str(ssh_settings.get("repo_path", "$HOME/mrquentinha")).strip()
        excludes_cli = " ".join(f"--exclude {shlex.quote(item)}" for item in excludes)
        remote_script = f"""
set -euo pipefail
REPO_PATH={shlex.quote(repo_path)}
if [ -f "$REPO_PATH/workspaces/backend/.venv/bin/activate" ]; then
  . "$REPO_PATH/workspaces/backend/.venv/bin/activate"
fi
cd "$REPO_PATH/workspaces/backend"
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py dumpdata --natural-foreign --natural-primary \
  {excludes_cli} --indent 2
"""
        result, command_preview = _run_remote_dbops_script(
            ssh_settings=ssh_settings,
            remote_shell_script=remote_script,
            timeout_seconds=240,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise ValidationError(
                "Falha ao executar dumpdata remoto. "
                f"Comando: {command_preview}. Detalhe: {detail or 'sem detalhe'}"
            )
        dump_payload = result.stdout or "[]"
    try:
        local_dump_file.write_text(dump_payload, encoding="utf-8")
    except OSError as exc:
        raise ValidationError("Falha ao gravar dump Django local.") from exc

    synced = False
    if mode == "sync_dev":
        backend_cwd = PROJECT_ROOT / "workspaces" / "backend"
        env = os.environ.copy()
        env["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
        flush_result = subprocess.run(
            [sys.executable, "manage.py", "flush", "--noinput"],
            cwd=str(backend_cwd),
            check=False,
            env=env,
            capture_output=True,
            text=True,
        )
        if flush_result.returncode != 0:
            detail = (flush_result.stderr or flush_result.stdout or "").strip()
            raise ValidationError(
                "Falha ao limpar banco DEV antes do loaddata. "
                f"Detalhe: {detail or 'sem detalhe'}"
            )
        load_result = subprocess.run(
            [sys.executable, "manage.py", "loaddata", str(local_dump_file)],
            cwd=str(backend_cwd),
            check=False,
            env=env,
            capture_output=True,
            text=True,
        )
        if load_result.returncode != 0:
            detail = (load_result.stderr or load_result.stdout or "").strip()
            raise ValidationError(
                "Falha ao executar loaddata no DEV. "
                f"Detalhe: {detail or 'sem detalhe'}"
            )
        migrate_result = subprocess.run(
            [sys.executable, "manage.py", "migrate", "--noinput"],
            cwd=str(backend_cwd),
            check=False,
            env=env,
            capture_output=True,
            text=True,
        )
        if migrate_result.returncode != 0:
            detail = (migrate_result.stderr or migrate_result.stdout or "").strip()
            raise ValidationError(
                "Sincronizacao Django aplicada, mas migrate DEV falhou. "
                f"Detalhe: {detail or 'sem detalhe'}"
            )
        synced = True

    installer_settings = _normalize_installer_settings(config.installer_settings)
    database_ops = _normalize_database_ops_settings(
        installer_settings.get("database_ops")
    )
    database_ops["django_sync"]["last_dump_file"] = str(local_dump_file)
    database_ops["django_sync"]["last_synced_at"] = timezone.now().isoformat()
    database_ops["django_sync"]["last_synced_by"] = "web-admin"
    installer_settings["database_ops"] = database_ops
    config.installer_settings = _normalize_installer_settings(installer_settings)
    config.save(update_fields=["installer_settings", "updated_at"])

    return {
        "ok": True,
        "mode": mode,
        "local_dump_file": str(local_dump_file),
        "synced": synced,
        "exclude_apps": excludes,
        "runtime": context,
    }


def copy_remote_backup_to_dev_via_scp(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    if bool(context.get("local_db_ops")):
        raise ValidationError(
            "Copia SCP nao se aplica nesta instancia (EC2 com banco local)."
        )
    payload = payload if isinstance(payload, dict) else {}
    backup_file = str(payload.get("backup_file", "")).strip()
    if not backup_file:
        raise ValidationError("Informe backup_file para copia via scp.")
    if not INSTALLER_SAFE_REMOTE_PATH_RE.fullmatch(backup_file):
        raise ValidationError("backup_file invalido para copia via scp.")

    ssh_settings = _validate_dbops_ssh_settings(_extract_dbops_ssh_from_config(config))
    _ensure_dbops_runtime_dirs()
    local_filename = (
        str(payload.get("local_filename", "")).strip() or Path(backup_file).name
    )
    local_target_path = DBOPS_SYNC_DIR / local_filename

    src = f"{_build_ssh_destination(ssh_settings)}:{backup_file}"
    scp_command = _build_scp_base_command(
        ssh_settings=ssh_settings,
        mask_sensitive=False,
    )
    scp_command.extend([src, str(local_target_path)])
    preview_command = _build_scp_base_command(
        ssh_settings=ssh_settings,
        mask_sensitive=True,
    )
    preview_command.extend([src, str(local_target_path)])

    try:
        result = subprocess.run(
            scp_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValidationError("SCP: timeout ao copiar backup remoto para DEV.") from exc
    except OSError as exc:
        raise ValidationError("SCP: falha ao executar cliente scp local.") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ValidationError(
            "SCP: falha ao copiar backup remoto. "
            f"Comando: {_render_command_preview(preview_command)}. "
            f"Detalhe: {detail or 'sem detalhe'}"
        )

    size_bytes = local_target_path.stat().st_size if local_target_path.exists() else 0
    return {
        "ok": True,
        "source_backup_file": backup_file,
        "local_dump_file": str(local_target_path),
        "local_dump_size_bytes": size_bytes,
        "transfer_method": "scp",
        "runtime": context,
    }


def run_remote_django_dbbackup(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    payload = payload if isinstance(payload, dict) else {}
    mode = str(payload.get("mode", "backup")).strip().lower()
    if mode not in {"backup", "list", "restore"}:
        raise ValidationError("Modo invalido para django-dbbackup.")

    input_filename = str(payload.get("input_filename", "")).strip()
    confirm = str(payload.get("confirm", "")).strip().upper()
    if mode == "restore" and confirm != "RESTAURAR":
        raise ValidationError(
            "Confirmacao obrigatoria para dbrestore: use confirm='RESTAURAR'."
        )
    if mode == "restore" and not input_filename:
        raise ValidationError("Informe input_filename para dbrestore.")

    if bool(context.get("local_db_ops")):
        backend_cwd = PROJECT_ROOT / "workspaces" / "backend"
        local_env = _local_django_manage_env(settings_module="config.settings.prod")
        command_args: list[str] = [sys.executable, "manage.py"]
        if mode == "backup":
            command_args.extend(
                ["dbbackup", "--clean", "--compress", "--verbosity", "1"]
            )
        elif mode == "list":
            command_args.append("listbackups")
        else:
            if not Path(input_filename).exists():
                raise ValidationError(
                    "Arquivo de restore nao encontrado no ambiente local."
                )
            command_args.extend(
                ["dbrestore", "--noinput", "--input-filename", input_filename]
            )
        result = subprocess.run(
            command_args,
            cwd=str(backend_cwd),
            check=False,
            env=local_env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        command_preview = _render_command_preview(command_args)
    else:
        ssh_settings = _validate_dbops_ssh_settings(
            _extract_dbops_ssh_from_config(config)
        )
        repo_path = str(ssh_settings.get("repo_path", "$HOME/mrquentinha")).strip()
        command_line = ""
        if mode == "backup":
            command_line = "python manage.py dbbackup --clean --compress --verbosity 1"
        elif mode == "list":
            command_line = "python manage.py listbackups"
        else:
            command_line = (
                "python manage.py dbrestore --noinput "
                f"--input-filename {shlex.quote(input_filename)}"
            )

        remote_script = f"""
set -euo pipefail
REPO_PATH={shlex.quote(repo_path)}
if [ -f "$REPO_PATH/workspaces/backend/.venv/bin/activate" ]; then
  . "$REPO_PATH/workspaces/backend/.venv/bin/activate"
fi
cd "$REPO_PATH/workspaces/backend"
export DJANGO_SETTINGS_MODULE=config.settings.prod
{command_line}
"""
        result, command_preview = _run_remote_dbops_script(
            ssh_settings=ssh_settings,
            remote_shell_script=remote_script,
            timeout_seconds=300,
        )
    return {
        "ok": result.returncode == 0,
        "mode": mode,
        "exit_code": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
        "command_preview": command_preview,
        "runtime": context,
    }


def build_database_ops_command_catalog(*, sample_backup_file: str = "") -> dict:
    config = ensure_portal_config()
    context = resolve_database_runtime_context(config=config)
    example_backup = (
        sample_backup_file or "$HOME/mrquentinha/.runtime/db_backups/backup.dump"
    )
    local_file = "$HOME/mrquentinha/.runtime/db_ops/sync/backup.dump"
    if bool(context.get("local_db_ops")):
        local_env, local_db_name = _build_local_pg_env()
        local_host = str(local_env.get("PGHOST", "127.0.0.1"))
        local_port = str(local_env.get("PGPORT", "5432"))
        local_user = str(local_env.get("PGUSER", "postgres"))
        tunnel_cmd = "indisponivel-em-ec2-local-db"
        list_cmd = "find .runtime/db_backups -maxdepth 1 -type f -name '*.dump' | sort"
        pg_dump_cmd = (
            f"PGHOST={shlex.quote(local_host)} PGPORT={shlex.quote(local_port)} "
            f"PGUSER={shlex.quote(local_user)} pg_dump --format=custom --no-owner "
            f"--no-privileges --dbname={shlex.quote(local_db_name)} "
            "--file .runtime/db_backups/manual.dump"
        )
        pg_restore_cmd = (
            f"PGHOST={shlex.quote(local_host)} PGPORT={shlex.quote(local_port)} "
            f"PGUSER={shlex.quote(local_user)} pg_restore --clean --if-exists "
            f"--no-owner --no-privileges --dbname={shlex.quote(local_db_name)} "
            f"{shlex.quote(example_backup)}"
        )
        psql_cmd = (
            f"PGHOST={shlex.quote(local_host)} PGPORT={shlex.quote(local_port)} "
            f"PGUSER={shlex.quote(local_user)} psql {shlex.quote(local_db_name)} "
            '-v ON_ERROR_STOP=1 -c "SELECT now();"'
        )
        scp_cmd = "indisponivel-em-ec2-local-db"
        dbbackup_cmd = (
            "cd workspaces/backend && "
            "DJANGO_SETTINGS_MODULE=config.settings.prod "
            "python manage.py dbbackup --clean --compress --verbosity 1"
        )
        dbrestore_cmd = (
            "cd workspaces/backend && "
            "DJANGO_SETTINGS_MODULE=config.settings.prod "
            "python manage.py dbrestore --noinput "
            f"--input-filename {shlex.quote(example_backup)}"
        )
    else:
        ssh_settings = _validate_dbops_ssh_settings(
            _extract_dbops_ssh_from_config(config)
        )
        tunnel_state = _dbops_read_tunnel_settings(config=config)
        local_bind_host = str(tunnel_state.get("local_bind_host", "127.0.0.1")).strip()
        local_port = int(tunnel_state.get("local_port", 55432) or 55432)
        remote_db_host = str(tunnel_state.get("remote_db_host", "127.0.0.1")).strip()
        remote_db_port = int(tunnel_state.get("remote_db_port", 5432) or 5432)
        ssh_destination = _build_ssh_destination(ssh_settings)
        repo_path = str(ssh_settings.get("repo_path", "$HOME/mrquentinha")).strip()
        tunnel_cmd = _render_command_preview(
            _build_ssh_base_command(ssh_settings=ssh_settings, mask_sensitive=True)
            + [
                "-N",
                "-L",
                f"{local_bind_host}:{local_port}:{remote_db_host}:{remote_db_port}",
                ssh_destination,
            ]
        )
        list_cmd = _render_command_preview(
            _build_ssh_exec_command(
                ssh_settings=ssh_settings,
                remote_shell_script=(
                    f"cd {shlex.quote(repo_path)}; "
                    "find .runtime/db_backups -maxdepth 1 -type f -name '*.dump' | sort"
                ),
                mask_sensitive=True,
            )
        )
        pg_dump_cmd = _render_command_preview(
            _build_ssh_exec_command(
                ssh_settings=ssh_settings,
                remote_shell_script=(
                    f"cd {shlex.quote(repo_path)}/workspaces/backend; "
                    "set -a; [ -f .env.prod ] && . .env.prod; set +a; "
                    "pg_dump --format=custom --no-owner --no-privileges "
                    '--dbname="$DATABASE_URL" --file ".runtime/db_backups/manual.dump"'
                ),
                mask_sensitive=True,
            )
        )
        pg_restore_cmd = _render_command_preview(
            _build_ssh_exec_command(
                ssh_settings=ssh_settings,
                remote_shell_script=(
                    f"cd {shlex.quote(repo_path)}/workspaces/backend; "
                    "set -a; [ -f .env.prod ] && . .env.prod; set +a; "
                    "pg_restore --clean --if-exists --no-owner --no-privileges "
                    f'--dbname="$DATABASE_URL" {shlex.quote(example_backup)}'
                ),
                mask_sensitive=True,
            )
        )
        psql_cmd = _render_command_preview(
            _build_ssh_exec_command(
                ssh_settings=ssh_settings,
                remote_shell_script=(
                    f"cd {shlex.quote(repo_path)}/workspaces/backend; "
                    "set -a; [ -f .env.prod ] && . .env.prod; set +a; "
                    'psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "SELECT now();"'
                ),
                mask_sensitive=True,
            )
        )
        scp_cmd = _render_command_preview(
            _build_scp_base_command(ssh_settings=ssh_settings, mask_sensitive=True)
            + [f"{ssh_destination}:{example_backup}", local_file]
        )
        dbbackup_cmd = _render_command_preview(
            _build_ssh_exec_command(
                ssh_settings=ssh_settings,
                remote_shell_script=(
                    f"cd {shlex.quote(repo_path)}/workspaces/backend; "
                    "export DJANGO_SETTINGS_MODULE=config.settings.prod; "
                    "python manage.py dbbackup --clean --compress --verbosity 1"
                ),
                mask_sensitive=True,
            )
        )
        dbrestore_cmd = _render_command_preview(
            _build_ssh_exec_command(
                ssh_settings=ssh_settings,
                remote_shell_script=(
                    f"cd {shlex.quote(repo_path)}/workspaces/backend; "
                    "export DJANGO_SETTINGS_MODULE=config.settings.prod; "
                    "python manage.py dbrestore --noinput "
                    f"--input-filename {shlex.quote(example_backup)}"
                ),
                mask_sensitive=True,
            )
        )

    return {
        "ok": True,
        "commands": {
            "tunnel_start": tunnel_cmd,
            "backup_list": list_cmd,
            "backup_create_pg_dump": pg_dump_cmd,
            "backup_restore_pg_restore": pg_restore_cmd,
            "psql_execute": psql_cmd,
            "backup_copy_scp": scp_cmd,
            "django_dbbackup": dbbackup_cmd,
            "django_dbrestore": dbrestore_cmd,
        },
        "notes": [
            "Os comandos usam preview com mascaramento de senha quando aplicavel.",
            "Para restore com escrita em producao, mantenha confirmacao operacional.",
            "Depois de restore, execute migrate para alinhar schema.",
        ],
        "runtime": context,
    }


def _build_remote_installer_shell_script(*, payload: dict) -> str:
    ssh_settings = payload.get("ssh", {})
    repo_path = str(ssh_settings.get("repo_path", "$HOME/mrquentinha")).strip()
    if repo_path.startswith("~/"):
        repo_path = "$HOME/" + repo_path[2:]
    elif repo_path == "~":
        repo_path = "$HOME"
    if not repo_path:
        repo_path = "$HOME/mrquentinha"

    if not INSTALLER_SAFE_REMOTE_PATH_RE.fullmatch(repo_path):
        raise ValidationError(
            "SSH: repo_path invalido. Use apenas letras, numeros, ., /, _, -, $."
        )

    auto_clone_repo = bool(ssh_settings.get("auto_clone_repo", False))
    git_remote_url = str(ssh_settings.get("git_remote_url", "")).strip()
    git_branch = str(ssh_settings.get("git_branch", "main")).strip() or "main"
    if not INSTALLER_SAFE_GIT_REF_RE.fullmatch(git_branch):
        raise ValidationError(
            "SSH: git_branch invalida. Use apenas letras, numeros, ., _, -, /."
        )
    if auto_clone_repo and not git_remote_url:
        raise ValidationError("SSH: git_remote_url obrigatoria para auto_clone_repo.")

    stack = str(payload.get("stack", "vm")).strip().lower() or "vm"
    env_name = str(payload.get("mode", "dev")).strip().lower() or "dev"
    start_after = bool(payload.get("start_after_install", False))
    start_flag = " --start" if start_after else ""

    clone_or_check_lines: list[str] = []
    if auto_clone_repo:
        safe_git_url = shlex.quote(git_remote_url)
        safe_branch = shlex.quote(git_branch)
        clone_or_check_lines.extend(
            [
                f'mkdir -p "{repo_path}"',
                f'if [ ! -d "{repo_path}/.git" ]; then',
                (
                    f"  git clone --branch {safe_branch} --single-branch "
                    f'{safe_git_url} "{repo_path}"'
                ),
                "else",
                f'  cd "{repo_path}"',
                "  git fetch --all --prune",
                f"  git checkout {safe_branch}",
                f"  git pull --ff-only origin {safe_branch}",
                "fi",
            ]
        )
    else:
        clone_or_check_lines.extend(
            [
                f'if [ ! -d "{repo_path}" ]; then',
                f'  echo "Repositorio remoto nao encontrado em {repo_path}" >&2',
                "  exit 21",
                "fi",
            ]
        )

    install_command = (
        "bash scripts/install_mrquentinha.sh "
        f"--stack {shlex.quote(stack)} --env {shlex.quote(env_name)} --yes{start_flag}"
    )

    script_lines = [
        "set -euo pipefail",
        *clone_or_check_lines,
        f'cd "{repo_path}"',
        'if [ ! -f "scripts/install_mrquentinha.sh" ]; then',
        '  echo "Instalador nao encontrado em scripts/install_mrquentinha.sh" >&2',
        "  exit 22",
        "fi",
        install_command,
    ]
    return "; ".join(script_lines)


def _resolve_aws_auth_mode(cloud: dict) -> str:
    auth_mode = str(cloud.get("auth_mode", "profile")).strip().lower()
    if auth_mode not in INSTALLER_ALLOWED_AWS_AUTH_MODES:
        return "profile"
    return auth_mode


def _mask_sensitive_token(raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def _build_aws_cli_execution_env(
    *, cloud: dict, force_region: str | None = None
) -> dict:
    env = os.environ.copy()
    for env_key in (
        "AWS_PROFILE",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
    ):
        env.pop(env_key, None)

    region = force_region or str(cloud.get("region", "")).strip()
    if region:
        env["AWS_REGION"] = region
        env["AWS_DEFAULT_REGION"] = region

    auth_mode = _resolve_aws_auth_mode(cloud)
    if auth_mode == "profile":
        profile_name = str(cloud.get("profile_name", "")).strip()
        if profile_name:
            env["AWS_PROFILE"] = profile_name
        return env

    access_key_id = str(cloud.get("access_key_id", "")).strip()
    secret_access_key = str(cloud.get("secret_access_key", "")).strip()
    if not access_key_id or not secret_access_key:
        raise ValidationError(
            "AWS: auth_mode=access_key requer access_key_id e secret_access_key."
        )
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    session_token = str(cloud.get("session_token", "")).strip()
    if session_token:
        env["AWS_SESSION_TOKEN"] = session_token
    return env


def _run_aws_cli_json(
    *,
    aws_bin: str,
    args: list[str],
    cloud: dict,
    timeout: int = 20,
    allow_failure: bool = False,
    force_region: str | None = None,
    error_label: str = "AWS CLI",
) -> tuple[dict | None, str]:
    command = [aws_bin, *args]
    try:
        env = _build_aws_cli_execution_env(cloud=cloud, force_region=force_region)
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        message = f"{error_label}: timeout ao executar comando AWS."
        if allow_failure:
            return None, message
        raise ValidationError(message) from exc
    except OSError as exc:
        message = f"{error_label}: falha ao executar comando AWS local."
        if allow_failure:
            return None, message
        raise ValidationError(message) from exc

    if result.returncode != 0:
        detail = str(result.stderr or result.stdout or "").strip() or "sem detalhe"
        message = f"{error_label}: {detail}"
        if allow_failure:
            return None, message
        raise ValidationError(message) from None

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        message = f"{error_label}: resposta JSON invalida do AWS CLI."
        if allow_failure:
            return None, message
        raise ValidationError(message) from None

    if not isinstance(payload, dict):
        payload = {}
    return payload, ""


def _run_aws_cli_text(
    *,
    aws_bin: str,
    args: list[str],
    cloud: dict,
    timeout: int = 20,
    allow_failure: bool = False,
    force_region: str | None = None,
    error_label: str = "AWS CLI",
) -> tuple[str, str]:
    command = [aws_bin, *args]
    try:
        env = _build_aws_cli_execution_env(cloud=cloud, force_region=force_region)
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        message = f"{error_label}: timeout ao executar comando AWS."
        if allow_failure:
            return "", message
        raise ValidationError(message) from exc
    except OSError as exc:
        message = f"{error_label}: falha ao executar comando AWS local."
        if allow_failure:
            return "", message
        raise ValidationError(message) from exc

    if result.returncode != 0:
        detail = str(result.stderr or result.stdout or "").strip() or "sem detalhe"
        message = f"{error_label}: {detail}"
        if allow_failure:
            return "", message
        raise ValidationError(message)

    return str(result.stdout or "").strip(), ""


def _run_gcloud_cli_json(
    *,
    gcloud_bin: str,
    args: list[str],
    timeout: int = 20,
    allow_failure: bool = False,
    error_label: str = "GCP CLI",
) -> tuple[dict | list | None, str]:
    command = [gcloud_bin, *args]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        message = f"{error_label}: timeout ao executar comando gcloud."
        if allow_failure:
            return None, message
        raise ValidationError(message) from exc
    except OSError as exc:
        message = f"{error_label}: falha ao executar comando gcloud local."
        if allow_failure:
            return None, message
        raise ValidationError(message) from exc

    if result.returncode != 0:
        detail = str(result.stderr or result.stdout or "").strip() or "sem detalhe"
        message = f"{error_label}: {detail}"
        if allow_failure:
            return None, message
        raise ValidationError(message) from None

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        message = f"{error_label}: resposta JSON invalida do gcloud."
        if allow_failure:
            return None, message
        raise ValidationError(message) from None

    if not isinstance(payload, (dict, list)):
        payload = {}
    return payload, ""


def _run_gcloud_cli_text(
    *,
    gcloud_bin: str,
    args: list[str],
    timeout: int = 20,
    allow_failure: bool = False,
    error_label: str = "GCP CLI",
) -> tuple[str, str]:
    command = [gcloud_bin, *args]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        message = f"{error_label}: timeout ao executar comando gcloud."
        if allow_failure:
            return "", message
        raise ValidationError(message) from exc
    except OSError as exc:
        message = f"{error_label}: falha ao executar comando gcloud local."
        if allow_failure:
            return "", message
        raise ValidationError(message) from exc

    if result.returncode != 0:
        detail = str(result.stderr or result.stdout or "").strip() or "sem detalhe"
        message = f"{error_label}: {detail}"
        if allow_failure:
            return "", message
        raise ValidationError(message)

    return str(result.stdout or "").strip(), ""


def _normalize_gcp_project_value(raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    if value.lower() in {"(unset)", "unset", "none", "null"}:
        return ""
    return value


def _extract_gcp_resource_name(raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    if "/" not in value:
        return value
    return value.rstrip("/").rsplit("/", 1)[-1]


def _coerce_float(raw_value: object) -> float:
    try:
        return float(str(raw_value or "0").strip())
    except (TypeError, ValueError):
        return 0.0


def _collect_aws_monthly_cost_snapshot(*, aws_bin: str, cloud: dict) -> dict:
    now = timezone.now().date()
    month_start = now.replace(day=1)
    month_end = now + timedelta(days=1)
    payload, error_detail = _run_aws_cli_json(
        aws_bin=aws_bin,
        args=[
            "ce",
            "get-cost-and-usage",
            "--time-period",
            f"Start={month_start.isoformat()},End={month_end.isoformat()}",
            "--granularity",
            "MONTHLY",
            "--metrics",
            "UnblendedCost",
            "--group-by",
            "Type=DIMENSION,Key=SERVICE",
            "--output",
            "json",
        ],
        cloud=cloud,
        allow_failure=True,
        force_region="us-east-1",
        error_label="AWS Cost Explorer",
    )
    if payload is None:
        return {
            "available": False,
            "detail": error_detail,
            "month_start": month_start.isoformat(),
            "month_end_exclusive": month_end.isoformat(),
            "total_mtd_usd": 0.0,
            "top_services": [],
        }

    results = payload.get("ResultsByTime", [])
    result_bucket = results[0] if isinstance(results, list) and results else {}
    groups = result_bucket.get("Groups", [])
    service_costs: list[dict] = []
    total_mtd_usd = 0.0
    if isinstance(groups, list):
        for group in groups:
            if not isinstance(group, dict):
                continue
            keys = group.get("Keys", [])
            service_name = ""
            if isinstance(keys, list) and keys:
                service_name = str(keys[0]).strip()
            amount = _coerce_float(
                group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0")
            )
            if amount <= 0:
                continue
            total_mtd_usd += amount
            service_costs.append(
                {
                    "service": service_name or "UNKNOWN",
                    "mtd_usd": round(amount, 2),
                }
            )

    service_costs.sort(key=lambda item: item["mtd_usd"], reverse=True)
    return {
        "available": True,
        "detail": "Cost Explorer consultado com sucesso.",
        "month_start": month_start.isoformat(),
        "month_end_exclusive": month_end.isoformat(),
        "total_mtd_usd": round(total_mtd_usd, 2),
        "top_services": service_costs[:6],
    }


def _build_aws_cost_estimate_payload(*, payload: dict, aws_cost_snapshot: dict) -> dict:
    cloud = payload.get("cloud", {})
    deployment = payload.get("deployment", {})
    instance_type = str(cloud.get("instance_type", "")).strip().lower()
    ec2_hourly = AWS_COST_EC2_HOURLY_BY_INSTANCE.get(
        instance_type, AWS_COST_DEFAULT_EC2_HOURLY_USD
    )
    hours_per_month = 730
    try:
        ebs_gb_value = int(cloud.get("ebs_gb", 20) or 20)
    except (TypeError, ValueError):
        ebs_gb_value = 20
    ebs_gb = max(8, min(ebs_gb_value, 1024))
    use_elastic_ip = bool(cloud.get("use_elastic_ip", True))
    has_dns = bool(
        str(cloud.get("route53_hosted_zone_id", "")).strip()
        or str(deployment.get("root_domain", "")).strip()
    )

    ec2_month = round(ec2_hourly * hours_per_month, 2)
    ebs_month = round(ebs_gb * AWS_COST_EBS_GB_MONTH_USD, 2)
    eip_month = AWS_COST_EIP_MONTH_USD if use_elastic_ip else 0.0
    route53_month = (
        AWS_COST_ROUTE53_HOSTED_ZONE_MONTH_USD + AWS_COST_ROUTE53_QUERIES_MONTH_USD
        if has_dns
        else 0.0
    )
    data_transfer_month = AWS_COST_DATA_TRANSFER_MONTH_USD
    codedeploy_month = 0.0
    total = round(
        ec2_month
        + ebs_month
        + eip_month
        + route53_month
        + data_transfer_month
        + codedeploy_month,
        2,
    )

    range_min = round(total * 0.8, 2)
    range_max = round(total * 1.2, 2)

    notes = [
        "Estimativa inicial para cenario ate 20 clientes e crescimento gradual.",
        "Valores reais variam por regiao, classe de instancia, "
        "trafego e descontos da conta.",
    ]
    if not aws_cost_snapshot.get("available"):
        notes.append(
            "Consumo real via Cost Explorer indisponivel. "
            "Verifique permissao ce:GetCostAndUsage."
        )

    return {
        "currency": "USD",
        "estimated_monthly_total_usd": total,
        "estimated_monthly_range_usd": {
            "min": range_min,
            "max": range_max,
        },
        "breakdown": [
            {
                "service": "EC2",
                "estimate_monthly_usd": ec2_month,
                "detail": (
                    f"instance_type={instance_type or 'nao-informado'} | "
                    f"{hours_per_month}h/mes"
                ),
            },
            {
                "service": "EBS",
                "estimate_monthly_usd": ebs_month,
                "detail": f"ebs_gb={ebs_gb}",
            },
            {
                "service": "Elastic IP",
                "estimate_monthly_usd": round(eip_month, 2),
                "detail": "IP estatico habilitado" if use_elastic_ip else "IP dinamico",
            },
            {
                "service": "Route53",
                "estimate_monthly_usd": round(route53_month, 2),
                "detail": "zona + consultas basicas" if has_dns else "nao estimado",
            },
            {
                "service": "Transferencia de dados",
                "estimate_monthly_usd": round(data_transfer_month, 2),
                "detail": "estimativa inicial de egress",
            },
            {
                "service": "CodeDeploy",
                "estimate_monthly_usd": round(codedeploy_month, 2),
                "detail": "deploy em EC2 (custo estimado zero do servico)",
            },
        ],
        "current_month_cost": aws_cost_snapshot,
        "notes": notes,
    }


def _run_aws_prerequisite_checks(*, aws_bin: str, payload: dict) -> dict:
    cloud = payload.get("cloud", {})
    deployment = payload.get("deployment", {})
    checks: list[dict] = []
    warnings: list[str] = []

    route53_zone_id = str(cloud.get("route53_hosted_zone_id", "")).strip()
    root_domain = str(deployment.get("root_domain", "")).strip().lower().rstrip(".")
    route53_check = {
        "name": "aws_route53",
        "status": "pending",
        "detail": "Informe hosted zone ou dominio raiz para validar DNS no Route53.",
    }
    if route53_zone_id:
        payload_zone, error_detail = _run_aws_cli_json(
            aws_bin=aws_bin,
            args=[
                "route53",
                "get-hosted-zone",
                "--id",
                route53_zone_id,
                "--output",
                "json",
            ],
            cloud=cloud,
            allow_failure=True,
            error_label="AWS Route53",
        )
        if payload_zone is None:
            route53_check["status"] = "error"
            route53_check["detail"] = error_detail
        else:
            zone_name = (
                str(payload_zone.get("HostedZone", {}).get("Name", ""))
                .strip()
                .rstrip(".")
            )
            route53_check["status"] = "ok"
            route53_check["detail"] = (
                f"Hosted zone encontrada ({zone_name or route53_zone_id})."
            )
            route53_check["zone_name"] = zone_name
    elif root_domain:
        payload_zone, error_detail = _run_aws_cli_json(
            aws_bin=aws_bin,
            args=[
                "route53",
                "list-hosted-zones-by-name",
                "--dns-name",
                root_domain,
                "--max-items",
                "1",
                "--output",
                "json",
            ],
            cloud=cloud,
            allow_failure=True,
            error_label="AWS Route53",
        )
        if payload_zone is None:
            route53_check["status"] = "error"
            route53_check["detail"] = error_detail
        else:
            hosted_zones = payload_zone.get("HostedZones", [])
            first_zone = (
                hosted_zones[0]
                if isinstance(hosted_zones, list) and hosted_zones
                else {}
            )
            zone_name = str(first_zone.get("Name", "")).strip().rstrip(".")
            if zone_name and zone_name == root_domain:
                route53_check["status"] = "ok"
                route53_check["detail"] = (
                    f"Dominio {root_domain} encontrado no Route53."
                )
                route53_check["zone_name"] = zone_name
                route53_check["zone_id"] = str(first_zone.get("Id", "")).strip()
            else:
                route53_check["status"] = "warning"
                route53_check["detail"] = (
                    f"Dominio {root_domain} nao localizado na conta AWS atual."
                )
    checks.append(route53_check)

    ec2_instance_id = str(cloud.get("ec2_instance_id", "")).strip()
    ec2_check = {
        "name": "aws_ec2_instance",
        "status": "pending",
        "detail": "Informe ec2_instance_id para validar instancia alvo.",
    }
    if ec2_instance_id:
        payload_instance, error_detail = _run_aws_cli_json(
            aws_bin=aws_bin,
            args=[
                "ec2",
                "describe-instances",
                "--instance-ids",
                ec2_instance_id,
                "--output",
                "json",
            ],
            cloud=cloud,
            allow_failure=True,
            error_label="AWS EC2",
        )
        if payload_instance is None:
            ec2_check["status"] = "error"
            ec2_check["detail"] = error_detail
        else:
            reservations = payload_instance.get("Reservations", [])
            instances = (
                reservations[0].get("Instances", [])
                if isinstance(reservations, list) and reservations
                else []
            )
            instance = instances[0] if isinstance(instances, list) and instances else {}
            state = str(instance.get("State", {}).get("Name", "")).strip()
            public_ip = str(instance.get("PublicIpAddress", "")).strip()
            private_ip = str(instance.get("PrivateIpAddress", "")).strip()
            ec2_check["status"] = "ok" if instance else "warning"
            ec2_check["detail"] = (
                f"Instancia {ec2_instance_id} validada "
                f"(state={state or 'desconhecido'})."
                if instance
                else f"Instancia {ec2_instance_id} nao encontrada."
            )
            ec2_check["state"] = state
            ec2_check["public_ip"] = public_ip
            ec2_check["private_ip"] = private_ip
    checks.append(ec2_check)

    use_elastic_ip = bool(cloud.get("use_elastic_ip", True))
    allocation_id = str(cloud.get("elastic_ip_allocation_id", "")).strip()
    eip_check = {
        "name": "aws_elastic_ip",
        "status": "skipped" if not use_elastic_ip else "pending",
        "detail": (
            "Elastic IP desabilitado. Operacao seguira com IP dinamico."
            if not use_elastic_ip
            else "Informe allocation id para validar Elastic IP."
        ),
    }
    if use_elastic_ip and allocation_id:
        payload_eip, error_detail = _run_aws_cli_json(
            aws_bin=aws_bin,
            args=[
                "ec2",
                "describe-addresses",
                "--allocation-ids",
                allocation_id,
                "--output",
                "json",
            ],
            cloud=cloud,
            allow_failure=True,
            error_label="AWS Elastic IP",
        )
        if payload_eip is None:
            eip_check["status"] = "error"
            eip_check["detail"] = error_detail
        else:
            addresses = payload_eip.get("Addresses", [])
            address = addresses[0] if isinstance(addresses, list) and addresses else {}
            public_ip = str(address.get("PublicIp", "")).strip()
            associated_instance_id = str(address.get("InstanceId", "")).strip()
            eip_check["status"] = "ok" if address else "warning"
            eip_check["detail"] = (
                f"Elastic IP {allocation_id} validado ({public_ip or '-'})."
                if address
                else f"Elastic IP {allocation_id} nao encontrado."
            )
            eip_check["public_ip"] = public_ip
            eip_check["associated_instance_id"] = associated_instance_id
    checks.append(eip_check)

    use_codedeploy = bool(cloud.get("use_codedeploy", False))
    app_name = str(cloud.get("codedeploy_application_name", "")).strip()
    deployment_group_name = str(cloud.get("codedeploy_deployment_group", "")).strip()
    codedeploy_check = {
        "name": "aws_codedeploy",
        "status": "skipped" if not use_codedeploy else "pending",
        "detail": (
            "CodeDeploy desabilitado. Assistente usara fluxo de provisionamento base."
            if not use_codedeploy
            else "Informe nome da aplicacao CodeDeploy para validar."
        ),
    }
    if use_codedeploy and app_name:
        payload_app, error_detail = _run_aws_cli_json(
            aws_bin=aws_bin,
            args=[
                "deploy",
                "get-application",
                "--application-name",
                app_name,
                "--output",
                "json",
            ],
            cloud=cloud,
            allow_failure=True,
            error_label="AWS CodeDeploy",
        )
        if payload_app is None:
            codedeploy_check["status"] = "error"
            codedeploy_check["detail"] = error_detail
        else:
            codedeploy_check["status"] = "ok"
            codedeploy_check["detail"] = (
                f"CodeDeploy application '{app_name}' localizada."
            )
            codedeploy_check["application_name"] = app_name
            if deployment_group_name:
                payload_group, group_error = _run_aws_cli_json(
                    aws_bin=aws_bin,
                    args=[
                        "deploy",
                        "get-deployment-group",
                        "--application-name",
                        app_name,
                        "--deployment-group-name",
                        deployment_group_name,
                        "--output",
                        "json",
                    ],
                    cloud=cloud,
                    allow_failure=True,
                    error_label="AWS CodeDeploy",
                )
                if payload_group is None:
                    codedeploy_check["status"] = "warning"
                    codedeploy_check["detail"] = (
                        "Aplicacao encontrada, mas deployment group invalido "
                        f"({group_error})."
                    )
                else:
                    codedeploy_check["deployment_group_name"] = deployment_group_name
    elif use_codedeploy and not app_name:
        warnings.append(
            "CodeDeploy habilitado sem codedeploy_application_name definido."
        )
    checks.append(codedeploy_check)

    return {
        "checks": checks,
        "warnings": warnings,
    }


def _build_aws_cloud_report(*, payload: dict, include_costs: bool = True) -> dict:
    cloud = payload.get("cloud", {})
    aws_bin = shutil.which("aws")
    if not aws_bin:
        raise ValidationError(
            "AWS: CLI nao encontrada. Instale awscli no servidor do backend "
            "(ex.: curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip)."
        )

    auth_mode = _resolve_aws_auth_mode(cloud)
    profile_name = str(cloud.get("profile_name", "")).strip()
    access_key_id = str(cloud.get("access_key_id", "")).strip()
    cli_version, _ = _run_aws_cli_text(
        aws_bin=aws_bin,
        args=["--version"],
        cloud=cloud,
        allow_failure=True,
        error_label="AWS CLI version",
    )

    identity_payload, _identity_error = _run_aws_cli_json(
        aws_bin=aws_bin,
        args=["sts", "get-caller-identity", "--output", "json"],
        cloud=cloud,
        error_label="AWS STS",
    )
    if identity_payload is None:
        identity_payload = {}

    account_id = str(identity_payload.get("Account", "")).strip()
    arn = str(identity_payload.get("Arn", "")).strip()
    user_id = str(identity_payload.get("UserId", "")).strip()

    aliases_payload, alias_error = _run_aws_cli_json(
        aws_bin=aws_bin,
        args=["iam", "list-account-aliases", "--output", "json"],
        cloud=cloud,
        allow_failure=True,
        error_label="AWS IAM",
    )
    account_alias = ""
    if aliases_payload:
        aliases = aliases_payload.get("AccountAliases", [])
        if isinstance(aliases, list) and aliases:
            account_alias = str(aliases[0]).strip()

    connectivity_check = {
        "name": "aws_connectivity",
        "status": "ok",
        "detail": "AWS STS validado com sucesso.",
        "checked_at": timezone.now().isoformat(),
        "cli_installed": True,
        "cli_version": cli_version,
        "account_id": account_id,
        "arn": arn,
        "user_id": user_id,
        "account_alias": account_alias,
        "region": str(cloud.get("region", "")).strip(),
        "auth_mode": auth_mode,
        "profile_name": profile_name,
        "access_key_hint": _mask_sensitive_token(access_key_id),
    }
    if alias_error:
        connectivity_check["alias_warning"] = alias_error

    prerequisites = _run_aws_prerequisite_checks(aws_bin=aws_bin, payload=payload)
    cost_snapshot = (
        _collect_aws_monthly_cost_snapshot(aws_bin=aws_bin, cloud=cloud)
        if include_costs
        else {
            "available": False,
            "detail": "Snapshot de custo nao solicitado.",
            "month_start": "",
            "month_end_exclusive": "",
            "total_mtd_usd": 0.0,
            "top_services": [],
        }
    )
    costs = _build_aws_cost_estimate_payload(
        payload=payload,
        aws_cost_snapshot=cost_snapshot,
    )

    warnings: list[str] = []
    warnings.extend(prerequisites.get("warnings", []))
    if alias_error:
        warnings.append(alias_error)

    return {
        "provider": "aws",
        "checked_at": timezone.now().isoformat(),
        "connectivity": connectivity_check,
        "prerequisites": prerequisites,
        "costs": costs,
        "warnings": warnings,
    }


def _run_gcp_prerequisite_checks(
    *, gcloud_bin: str, payload: dict, project_id: str
) -> dict:
    cloud = payload.get("cloud", {})
    checks: list[dict] = []
    warnings: list[str] = []

    dns_zone = str(cloud.get("route53_hosted_zone_id", "")).strip()
    dns_check = {
        "name": "gcp_dns",
        "status": "pending",
        "detail": "Informe a zona Cloud DNS para validar no projeto ativo.",
    }
    if dns_zone:
        payload_zone, error_detail = _run_gcloud_cli_json(
            gcloud_bin=gcloud_bin,
            args=[
                "dns",
                "managed-zones",
                "describe",
                dns_zone,
                "--project",
                project_id,
                "--format=json",
            ],
            allow_failure=True,
            error_label="GCP Cloud DNS",
        )
        if payload_zone is None:
            dns_check["status"] = "error"
            dns_check["detail"] = error_detail
        elif isinstance(payload_zone, dict):
            dns_name = str(payload_zone.get("dnsName", "")).strip()
            dns_check["status"] = "ok"
            dns_name_display = dns_name or "dnsName nao informado"
            dns_check["detail"] = (
                f"Zona Cloud DNS '{dns_zone}' localizada ({dns_name_display})."
            )
            dns_check["dns_name"] = dns_name
    checks.append(dns_check)

    instance_name = str(cloud.get("ec2_instance_id", "")).strip()
    compute_check = {
        "name": "gcp_compute_instance",
        "status": "pending",
        "detail": (
            "Informe a VM do Compute Engine para validar "
            "conectividade de deploy."
        ),
    }
    if instance_name:
        instances_payload, error_detail = _run_gcloud_cli_json(
            gcloud_bin=gcloud_bin,
            args=[
                "compute",
                "instances",
                "list",
                "--filter",
                f"name={instance_name}",
                "--project",
                project_id,
                "--format=json",
            ],
            allow_failure=True,
            error_label="GCP Compute Engine",
        )
        if instances_payload is None:
            compute_check["status"] = "error"
            compute_check["detail"] = error_detail
        elif isinstance(instances_payload, list):
            matching = [
                item
                for item in instances_payload
                if isinstance(item, dict)
                and str(item.get("name", "")).strip() == instance_name
            ]
            if matching:
                instance_item = matching[0]
                zone_name = _extract_gcp_resource_name(instance_item.get("zone", ""))
                status_name = str(instance_item.get("status", "")).strip() or "UNKNOWN"
                compute_check["status"] = "ok"
                compute_check["detail"] = (
                    f"VM '{instance_name}' localizada "
                    f"(zone={zone_name or 'nao-informada'}, status={status_name})."
                )
                compute_check["zone"] = zone_name
                compute_check["instance_status"] = status_name
            else:
                compute_check["status"] = "error"
                compute_check["detail"] = (
                    f"VM '{instance_name}' nao encontrada no projeto '{project_id}'."
                )
    checks.append(compute_check)

    use_static_ip = bool(cloud.get("use_elastic_ip", True))
    static_ip_name = str(cloud.get("elastic_ip_allocation_id", "")).strip()
    region = str(cloud.get("region", "")).strip()
    static_ip_check = {
        "name": "gcp_static_ip",
        "status": "pending",
        "detail": "IP estatico opcional para DNS previsivel em producao.",
    }
    if use_static_ip:
        if not static_ip_name:
            static_ip_check["status"] = "warning"
            static_ip_check["detail"] = (
                "IP estatico habilitado sem nome de endereco configurado."
            )
            warnings.append(
                "GCP: defina o nome do endereco estatico para validar custo/roteamento."
            )
        elif not region:
            static_ip_check["status"] = "warning"
            static_ip_check["detail"] = (
                "Informe a regiao para validar o endereco estatico no Compute Engine."
            )
            warnings.append(
                "GCP: regiao obrigatoria para validar endereco estatico regional."
            )
        else:
            address_payload, error_detail = _run_gcloud_cli_json(
                gcloud_bin=gcloud_bin,
                args=[
                    "compute",
                    "addresses",
                    "describe",
                    static_ip_name,
                    "--region",
                    region,
                    "--project",
                    project_id,
                    "--format=json",
                ],
                allow_failure=True,
                error_label="GCP Static IP",
            )
            if address_payload is None:
                static_ip_check["status"] = "error"
                static_ip_check["detail"] = error_detail
            elif isinstance(address_payload, dict):
                address = str(address_payload.get("address", "")).strip()
                static_ip_check["status"] = "ok"
                address_display = address or "sem IP"
                static_ip_check["detail"] = (
                    f"Endereco estatico '{static_ip_name}' localizado "
                    f"({address_display})."
                )
                static_ip_check["address"] = address
    else:
        static_ip_check["status"] = "warning"
        static_ip_check["detail"] = (
            "Operacao configurada sem IP estatico; "
            "DNS pode variar apos reprovisionamento."
        )
    checks.append(static_ip_check)

    use_cloud_deploy = bool(cloud.get("use_codedeploy", False))
    pipeline_name = str(cloud.get("codedeploy_application_name", "")).strip()
    target_name = str(cloud.get("codedeploy_deployment_group", "")).strip()
    deploy_check = {
        "name": "gcp_cloud_deploy",
        "status": "pending",
        "detail": (
            "Cloud Deploy opcional; "
            "use SSH quando pipeline nao estiver configurada."
        ),
    }
    if use_cloud_deploy:
        if not pipeline_name:
            deploy_check["status"] = "warning"
            deploy_check["detail"] = (
                "Cloud Deploy habilitado sem delivery pipeline informada."
            )
            warnings.append(
                "GCP: preencha delivery pipeline para habilitar "
                "deploy assistido no Cloud Deploy."
            )
        elif not region:
            deploy_check["status"] = "warning"
            deploy_check["detail"] = (
                "Informe a regiao para validar delivery pipeline no Cloud Deploy."
            )
            warnings.append(
                "GCP: regiao obrigatoria para validacao de pipeline do Cloud Deploy."
            )
        else:
            pipeline_payload, error_detail = _run_gcloud_cli_json(
                gcloud_bin=gcloud_bin,
                args=[
                    "deploy",
                    "delivery-pipelines",
                    "describe",
                    pipeline_name,
                    "--region",
                    region,
                    "--project",
                    project_id,
                    "--format=json",
                ],
                allow_failure=True,
                error_label="GCP Cloud Deploy",
            )
            if pipeline_payload is None:
                deploy_check["status"] = "error"
                deploy_check["detail"] = error_detail
            elif isinstance(pipeline_payload, dict):
                deploy_check["status"] = "ok"
                deploy_check["detail"] = (
                    f"Delivery pipeline '{pipeline_name}' localizada."
                )
                deploy_check["pipeline"] = pipeline_name
                if target_name:
                    target_payload, target_error = _run_gcloud_cli_json(
                        gcloud_bin=gcloud_bin,
                        args=[
                            "deploy",
                            "targets",
                            "describe",
                            target_name,
                            "--region",
                            region,
                            "--project",
                            project_id,
                            "--format=json",
                        ],
                        allow_failure=True,
                        error_label="GCP Cloud Deploy",
                    )
                    if target_payload is None:
                        deploy_check["status"] = "warning"
                        deploy_check["detail"] = (
                            "Pipeline encontrada, mas target invalido "
                            f"({target_error})."
                        )
                    else:
                        deploy_check["target"] = target_name
    checks.append(deploy_check)

    return {
        "checks": checks,
        "warnings": warnings,
    }


def _build_gcp_cloud_report(*, payload: dict) -> dict:
    cloud = payload.get("cloud", {})
    gcloud_bin = shutil.which("gcloud")
    if not gcloud_bin:
        raise ValidationError(
            "GCP: CLI gcloud nao encontrada. "
            "Instale o Google Cloud SDK no servidor do backend."
        )

    cli_version, _ = _run_gcloud_cli_text(
        gcloud_bin=gcloud_bin,
        args=["version", "--format=value(Google Cloud SDK)"],
        allow_failure=True,
        error_label="GCP CLI version",
    )
    active_account, account_error = _run_gcloud_cli_text(
        gcloud_bin=gcloud_bin,
        args=[
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=value(account)",
        ],
        allow_failure=True,
        error_label="GCP Auth",
    )
    if not active_account:
        detail = account_error or "sem detalhe"
        raise ValidationError(
            "GCP: falha ao validar autenticacao ativa no gcloud " f"({detail})."
        )

    project_value, project_error = _run_gcloud_cli_text(
        gcloud_bin=gcloud_bin,
        args=["config", "get-value", "project", "--quiet"],
        allow_failure=True,
        error_label="GCP Config",
    )
    project_id = _normalize_gcp_project_value(project_value)
    if not project_id:
        detail = project_error or "configure via 'gcloud config set project <id>'"
        raise ValidationError(
            "GCP: projeto ativo nao definido no gcloud " f"({detail})."
        )

    connectivity_check = {
        "name": "gcp_connectivity",
        "status": "ok",
        "detail": "Google Cloud SDK validado com sucesso.",
        "checked_at": timezone.now().isoformat(),
        "cli_installed": True,
        "cli_version": cli_version,
        "account": active_account,
        "project": project_id,
        "region": str(cloud.get("region", "")).strip(),
    }

    prerequisites = _run_gcp_prerequisite_checks(
        gcloud_bin=gcloud_bin,
        payload=payload,
        project_id=project_id,
    )
    warnings: list[str] = []
    warnings.extend(prerequisites.get("warnings", []))

    return {
        "provider": "gcp",
        "checked_at": timezone.now().isoformat(),
        "connectivity": connectivity_check,
        "prerequisites": prerequisites,
        "warnings": warnings,
    }


def _run_cloud_connectivity_probe(*, payload: dict) -> dict:
    cloud = payload.get("cloud", {})
    provider = str(cloud.get("provider", "aws")).strip().lower()

    if provider == "aws":
        aws_report = _build_aws_cloud_report(payload=payload, include_costs=False)
        connectivity = aws_report.get("connectivity", {})
        if isinstance(connectivity, dict):
            return connectivity

    if provider == "gcp":
        gcp_report = _build_gcp_cloud_report(payload=payload)
        connectivity = gcp_report.get("connectivity", {})
        if isinstance(connectivity, dict):
            return connectivity

    raise ValidationError("Cloud: provider invalido para validacao de conectividade.")


def _sync_installer_job_in_config(config: PortalConfig, job_payload: dict) -> None:
    installer_settings = _normalize_installer_settings(config.installer_settings)
    jobs_state = installer_settings.get("jobs", {})
    jobs_state["last_job_id"] = str(job_payload.get("job_id", "")).strip()
    jobs_state["last_job_status"] = str(job_payload.get("status", "")).strip() or "idle"
    jobs_state["last_job_started_at"] = str(job_payload.get("started_at", "")).strip()
    jobs_state["last_job_finished_at"] = str(job_payload.get("finished_at", "")).strip()
    jobs_state["last_job_summary"] = str(job_payload.get("summary", "")).strip()
    installer_settings["jobs"] = jobs_state
    installer_settings["last_synced_at"] = timezone.now().isoformat()
    installer_settings["last_sync_note"] = (
        "Fluxo do instalador sincronizado apos operacao do assistente."
    )
    installer_settings["requires_review"] = False
    config.installer_settings = _normalize_installer_settings(installer_settings)
    config.save(update_fields=["installer_settings", "updated_at"])


def _sync_installer_deployment_with_server_config(
    *, config: PortalConfig, normalized_payload: dict
) -> dict:
    deployment = normalized_payload.get("deployment")
    if not isinstance(deployment, dict):
        deployment = {}

    server_mapping = {
        "store_name": str(config.site_name or "").strip(),
        "root_domain": str(config.root_domain or "").strip(),
        "portal_domain": str(config.portal_domain or "").strip(),
        "client_domain": str(config.client_domain or "").strip(),
        "admin_domain": str(config.admin_domain or "").strip(),
        "api_domain": str(config.api_domain or "").strip(),
    }
    for field_name, value in server_mapping.items():
        if value:
            deployment[field_name] = value

    normalized_payload["deployment"] = deployment
    return normalized_payload


def _is_payment_provider_configured(
    *, provider_name: str, payment_settings: dict
) -> bool:
    normalized_provider = str(provider_name or "").strip().lower()
    if normalized_provider == "mercadopago":
        provider_settings = payment_settings.get("mercadopago", {})
        return bool(str(provider_settings.get("access_token", "")).strip())
    if normalized_provider == "efi":
        provider_settings = payment_settings.get("efi", {})
        return bool(
            str(provider_settings.get("client_id", "")).strip()
            and str(provider_settings.get("client_secret", "")).strip()
        )
    if normalized_provider == "asaas":
        provider_settings = payment_settings.get("asaas", {})
        return bool(str(provider_settings.get("api_key", "")).strip())
    return False


def _build_installer_prerequisites(
    *, config: PortalConfig, normalized_payload: dict
) -> dict:
    mode = str(normalized_payload.get("mode", "dev")).strip().lower()
    categories: list[dict] = []

    if mode != "prod":
        return {
            "mode": mode,
            "ready": True,
            "missing_count": 0,
            "categories": categories,
            "blocking_errors": [],
        }

    dns_missing_fields: list[dict] = []
    dns_required_fields = [
        ("root_domain", "Dominio raiz"),
        ("portal_domain", "Dominio do portal web"),
        ("client_domain", "Dominio do web client"),
        ("admin_domain", "Dominio do web admin"),
        ("api_domain", "Dominio da API"),
    ]
    for field_name, label in dns_required_fields:
        current_value = str(getattr(config, field_name, "") or "").strip()
        if current_value:
            continue
        dns_missing_fields.append(
            {
                "path": field_name,
                "label": label,
                "message": f"Preencha '{label}' nas configuracoes de servidor.",
            }
        )

    categories.append(
        {
            "key": "server_dns",
            "label": "Configuracao de servidor e DNS",
            "description": (
                "Obrigatorio para deploy em producao com portal, client, admin e API."
            ),
            "ready": len(dns_missing_fields) == 0,
            "missing_fields": dns_missing_fields,
        }
    )

    payment_missing_fields: list[dict] = []
    payment_settings = _normalize_payment_providers(config.payment_providers)
    receiver = payment_settings.get("receiver", {})
    receiver_person_type = str(receiver.get("person_type", "")).strip().upper()
    receiver_document = str(receiver.get("document", "")).strip()
    receiver_name = str(receiver.get("name", "")).strip()
    receiver_email = str(receiver.get("email", "")).strip()

    if receiver_person_type not in {"CPF", "CNPJ"}:
        payment_missing_fields.append(
            {
                "path": "payment_providers.receiver.person_type",
                "label": "Tipo de recebedor (CPF/CNPJ)",
                "message": "Configure CPF ou CNPJ para recebimento em producao.",
            }
        )
    if not receiver_document:
        payment_missing_fields.append(
            {
                "path": "payment_providers.receiver.document",
                "label": "Documento do recebedor",
                "message": "Informe CPF/CNPJ do recebedor para pagamentos.",
            }
        )
    if not receiver_name:
        payment_missing_fields.append(
            {
                "path": "payment_providers.receiver.name",
                "label": "Nome do recebedor",
                "message": "Informe nome/razao social do recebedor.",
            }
        )
    if not receiver_email:
        payment_missing_fields.append(
            {
                "path": "payment_providers.receiver.email",
                "label": "E-mail do recebedor",
                "message": "Informe e-mail de recebimento para conciliacao.",
            }
        )

    enabled_providers_raw = payment_settings.get("enabled_providers", [])
    enabled_providers = {
        str(item).strip().lower() for item in enabled_providers_raw if str(item).strip()
    }
    frontend_provider = payment_settings.get("frontend_provider", {})

    for channel in ("web", "mobile"):
        channel_label = "web client" if channel == "web" else "app mobile"
        provider_name = str(frontend_provider.get(channel, "")).strip().lower()
        if provider_name not in {"mercadopago", "efi", "asaas"}:
            payment_missing_fields.append(
                {
                    "path": f"payment_providers.frontend_provider.{channel}",
                    "label": f"Provider do {channel_label}",
                    "message": (
                        "Selecione Mercado Pago, Efi ou Asaas para "
                        f"{channel_label} em producao."
                    ),
                }
            )
            continue
        if provider_name not in enabled_providers:
            payment_missing_fields.append(
                {
                    "path": f"payment_providers.enabled_providers.{provider_name}",
                    "label": f"Provider habilitado ({provider_name})",
                    "message": f"Habilite {provider_name} para uso no {channel_label}.",
                }
            )
            continue
        if not _is_payment_provider_configured(
            provider_name=provider_name,
            payment_settings=payment_settings,
        ):
            payment_missing_fields.append(
                {
                    "path": f"payment_providers.{provider_name}",
                    "label": f"Credenciais do provider ({provider_name})",
                    "message": (
                        "Configure credenciais validas de "
                        f"{provider_name} para {channel_label}."
                    ),
                }
            )

    categories.append(
        {
            "key": "payment_gateway",
            "label": "Gateway de pagamento",
            "description": (
                "Obrigatorio em producao para checkout web/mobile e "
                "conciliacao de recebimentos."
            ),
            "ready": len(payment_missing_fields) == 0,
            "missing_fields": payment_missing_fields,
        }
    )

    missing_count = sum(
        len(category.get("missing_fields", [])) for category in categories
    )
    blocking_errors = [
        item.get("message", "")
        for category in categories
        for item in category.get("missing_fields", [])
        if str(item.get("message", "")).strip()
    ]

    return {
        "mode": mode,
        "ready": missing_count == 0,
        "missing_count": missing_count,
        "categories": categories,
        "blocking_errors": blocking_errors,
    }


def validate_installer_wizard_payload(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    normalized_payload, warnings = _normalize_installer_wizard_payload(payload)
    normalized_payload = _sync_installer_deployment_with_server_config(
        config=config,
        normalized_payload=normalized_payload,
    )
    prerequisites = _build_installer_prerequisites(
        config=config,
        normalized_payload=normalized_payload,
    )
    if normalized_payload.get("mode") == "prod" and not prerequisites.get("ready"):
        warnings.append(
            "Pre-requisitos de producao pendentes. Resolva DNS/servidor e "
            "gateway de pagamento."
        )
    return {
        "ok": True,
        "normalized_payload": normalized_payload,
        "warnings": warnings,
        "prerequisites": prerequisites,
        "workflow_version": INSTALLER_WORKFLOW_VERSION,
        "validated_at": timezone.now().isoformat(),
    }


def validate_installer_aws_setup(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    normalized_payload, warnings = _normalize_installer_wizard_payload(payload)
    normalized_payload = _sync_installer_deployment_with_server_config(
        config=config,
        normalized_payload=normalized_payload,
    )
    normalized_payload["target"] = "aws"
    cloud = normalized_payload.get("cloud", {})
    if not isinstance(cloud, dict):
        cloud = {}
    cloud["provider"] = "aws"
    normalized_payload["cloud"] = cloud

    aws_report = _build_aws_cloud_report(payload=normalized_payload, include_costs=True)
    warnings.extend(
        [
            str(item).strip()
            for item in aws_report.get("warnings", [])
            if str(item).strip()
        ]
    )

    return {
        "ok": True,
        "workflow_version": INSTALLER_WORKFLOW_VERSION,
        "validated_at": timezone.now().isoformat(),
        "normalized_payload": _sanitize_installer_payload(normalized_payload),
        "warnings": warnings,
        "cloud_validation": aws_report,
    }


def validate_installer_gcp_setup(*, payload: dict | None) -> dict:
    config = ensure_portal_config()
    normalized_payload, warnings = _normalize_installer_wizard_payload(payload)
    normalized_payload = _sync_installer_deployment_with_server_config(
        config=config,
        normalized_payload=normalized_payload,
    )
    normalized_payload["target"] = "gcp"
    cloud = normalized_payload.get("cloud", {})
    if not isinstance(cloud, dict):
        cloud = {}
    cloud["provider"] = "gcp"
    normalized_payload["cloud"] = cloud

    gcp_report = _build_gcp_cloud_report(payload=normalized_payload)
    warnings.extend(
        [
            str(item).strip()
            for item in gcp_report.get("warnings", [])
            if str(item).strip()
        ]
    )

    return {
        "ok": True,
        "workflow_version": INSTALLER_WORKFLOW_VERSION,
        "validated_at": timezone.now().isoformat(),
        "normalized_payload": _sanitize_installer_payload(normalized_payload),
        "warnings": warnings,
        "cloud_validation": gcp_report,
    }


@transaction.atomic
def save_installer_wizard_settings(
    *,
    payload: dict | None,
    completed_step: str = "mode",
) -> PortalConfig:
    config = ensure_portal_config()
    normalized_payload, _warnings = _normalize_installer_wizard_payload(payload)
    normalized_payload = _sync_installer_deployment_with_server_config(
        config=config,
        normalized_payload=normalized_payload,
    )
    installer_settings = _normalize_installer_settings(config.installer_settings)
    wizard = installer_settings.get("wizard", {})
    wizard["draft"] = _sanitize_installer_payload(normalized_payload)
    wizard["last_completed_step"] = str(completed_step or "mode").strip() or "mode"
    installer_settings["wizard"] = wizard
    installer_settings["workflow_version"] = INSTALLER_WORKFLOW_VERSION
    installer_settings["last_synced_at"] = timezone.now().isoformat()
    installer_settings["last_sync_note"] = "Draft do assistente salvo com sucesso."
    installer_settings["requires_review"] = False
    config.installer_settings = _normalize_installer_settings(installer_settings)
    config.save(update_fields=["installer_settings", "updated_at"])
    return config


def list_installer_jobs(*, limit: int = 20) -> list[dict]:
    _ensure_installer_runtime_dirs()
    files = sorted(
        INSTALLER_JOBS_DIR.glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    jobs: list[dict] = []
    for file_path in files[: max(1, min(limit, 100))]:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            jobs.append(payload)
    return jobs


@transaction.atomic
def start_installer_job(
    *, payload: dict | None, initiated_by: str = ""
) -> tuple[PortalConfig, dict]:
    config = ensure_portal_config()
    normalized_payload, warnings = _normalize_installer_wizard_payload(payload)
    normalized_payload = _sync_installer_deployment_with_server_config(
        config=config,
        normalized_payload=normalized_payload,
    )
    prerequisites = _build_installer_prerequisites(
        config=config,
        normalized_payload=normalized_payload,
    )
    if normalized_payload.get("mode") == "prod" and not prerequisites.get("ready"):
        blocking_errors = prerequisites.get("blocking_errors", [])
        summary = "; ".join(
            str(item).strip() for item in blocking_errors if str(item).strip()
        )
        if not summary:
            summary = (
                "Pre-requisitos de producao pendentes. Revise DNS/servidor e gateway."
            )
        raise ValidationError(summary)
    _ensure_installer_runtime_dirs()

    target = normalized_payload["target"]
    stack = normalized_payload["stack"]
    env_name = normalized_payload["mode"]
    start_after = bool(normalized_payload.get("start_after_install", False))
    now_iso = timezone.now().isoformat()
    job_id = timezone.now().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:8]

    log_file = INSTALLER_JOBS_DIR / f"{job_id}.log"
    exit_code_file = INSTALLER_JOBS_DIR / f"{job_id}.exit"

    job_payload: dict = {
        "job_id": job_id,
        "type": "installer-deploy",
        "status": "planned",
        "target": target,
        "stack": stack,
        "mode": env_name,
        "started_at": now_iso,
        "finished_at": "",
        "initiated_by": str(initiated_by or "").strip() or "sistema",
        "warnings": warnings,
        "payload": normalized_payload,
        "pid": None,
        "log_file": str(log_file),
        "exit_code_file": str(exit_code_file),
        "summary": "",
        "command_preview": "",
        "connectivity_checks": [],
    }

    if target == "local":
        local_command = _build_local_installer_command(
            stack=stack,
            env_name=env_name,
            start_after=start_after,
        )
        job_payload["command_preview"] = " ".join(
            shlex.quote(part) for part in local_command
        )

        wrapper_command = (
            f"cd {shlex.quote(str(PROJECT_ROOT))} && "
            f"{job_payload['command_preview']}; "
            f"rc=$?; echo $rc > {shlex.quote(str(exit_code_file))}; exit $rc"
        )
        try:
            log_handle = open(log_file, "w", encoding="utf-8")
        except OSError as exc:
            raise ValidationError("Falha ao criar log do job de instalacao.") from exc

        try:
            process = subprocess.Popen(
                ["bash", "-lc", wrapper_command],
                cwd=PROJECT_ROOT,
                stdout=log_handle,
                stderr=log_handle,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            log_handle.close()
            raise ValidationError("Falha ao iniciar job de instalacao local.") from exc
        finally:
            log_handle.close()

        job_payload["pid"] = process.pid
        job_payload["status"] = "running"
        job_payload["summary"] = "Instalador local iniciado em background."
    elif target == "ssh":
        ssh_settings = normalized_payload.get("ssh", {})
        auth_mode = str(ssh_settings.get("auth_mode", "key")).strip().lower()
        if auth_mode == "key":
            key_path = _resolve_ssh_key_path(ssh_settings)
            if not key_path:
                raise ValidationError("SSH: key_path obrigatorio para auth_mode=key.")
            if not os.path.exists(key_path):
                raise ValidationError(
                    f"SSH: chave privada nao encontrada em '{key_path}'."
                )

        connectivity_check = _run_ssh_connectivity_probe(ssh_settings=ssh_settings)
        job_payload["connectivity_checks"] = [connectivity_check]

        remote_script = _build_remote_installer_shell_script(payload=normalized_payload)
        ssh_command = _build_ssh_exec_command(
            ssh_settings=ssh_settings,
            remote_shell_script=remote_script,
            mask_sensitive=False,
        )
        ssh_command_preview = _build_ssh_exec_command(
            ssh_settings=ssh_settings,
            remote_shell_script=remote_script,
            mask_sensitive=True,
        )

        command_for_execution = _render_command_preview(ssh_command)
        job_payload["command_preview"] = _render_command_preview(ssh_command_preview)
        wrapper_command = (
            f"{command_for_execution}; "
            f"rc=$?; echo $rc > {shlex.quote(str(exit_code_file))}; exit $rc"
        )

        try:
            log_handle = open(log_file, "w", encoding="utf-8")
        except OSError as exc:
            raise ValidationError("Falha ao criar log do job SSH.") from exc

        try:
            process = subprocess.Popen(
                ["bash", "-lc", wrapper_command],
                cwd=PROJECT_ROOT,
                stdout=log_handle,
                stderr=log_handle,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            log_handle.close()
            raise ValidationError("Falha ao iniciar job remoto via SSH.") from exc
        finally:
            log_handle.close()

        job_payload["pid"] = process.pid
        job_payload["status"] = "running"
        job_payload["summary"] = (
            "Instalador remoto via SSH iniciado em background apos probe OK."
        )
    elif target in {"aws", "gcp"}:
        provider = (
            str(normalized_payload.get("cloud", {}).get("provider", "aws"))
            .strip()
            .lower()
        )
        if provider == "aws":
            aws_report = _build_aws_cloud_report(
                payload=normalized_payload,
                include_costs=True,
            )
            connectivity = aws_report.get("connectivity", {})
            prerequisite_checks = (
                aws_report.get("prerequisites", {}).get("checks", [])
                if isinstance(aws_report.get("prerequisites", {}), dict)
                else []
            )
            checks: list[dict] = []
            if isinstance(connectivity, dict):
                checks.append(connectivity)
            if isinstance(prerequisite_checks, list):
                checks.extend(
                    item for item in prerequisite_checks if isinstance(item, dict)
                )
            job_payload["connectivity_checks"] = checks
            job_payload["cloud_validation"] = aws_report
            estimated_monthly = _coerce_float(
                aws_report.get("costs", {}).get("estimated_monthly_total_usd", 0)
            )
            region = str(normalized_payload.get("cloud", {}).get("region", "")).strip()
            region_label = f"regiao={region}" if region else "regiao=nao-informada"
            job_payload["summary"] = (
                "Plano AWS validado com sucesso "
                f"({region_label}). Custo estimado mensal: USD {estimated_monthly:.2f}."
            )
            warnings.extend(
                [
                    str(item).strip()
                    for item in aws_report.get("warnings", [])
                    if str(item).strip()
                ]
            )
            job_payload["warnings"] = warnings
        elif provider == "gcp":
            gcp_report = _build_gcp_cloud_report(payload=normalized_payload)
            connectivity = gcp_report.get("connectivity", {})
            prerequisite_checks = (
                gcp_report.get("prerequisites", {}).get("checks", [])
                if isinstance(gcp_report.get("prerequisites", {}), dict)
                else []
            )
            checks: list[dict] = []
            if isinstance(connectivity, dict):
                checks.append(connectivity)
            if isinstance(prerequisite_checks, list):
                checks.extend(
                    item for item in prerequisite_checks if isinstance(item, dict)
                )
            job_payload["connectivity_checks"] = checks
            job_payload["cloud_validation"] = gcp_report
            region = str(normalized_payload.get("cloud", {}).get("region", "")).strip()
            region_label = f"regiao={region}" if region else "regiao=nao-informada"
            job_payload["summary"] = (
                "Plano GCP validado com sucesso " f"({region_label})."
            )
            warnings.extend(
                [
                    str(item).strip()
                    for item in gcp_report.get("warnings", [])
                    if str(item).strip()
                ]
            )
            job_payload["warnings"] = warnings
        else:
            raise ValidationError("Cloud provider invalido para target cloud.")
    else:
        raise ValidationError("Target de instalacao invalido.")

    job_payload["payload"] = _sanitize_installer_payload(normalized_payload)

    saved_job = _write_installer_job(job_payload)
    _sync_installer_job_in_config(config, saved_job)
    return config, saved_job


@transaction.atomic
def get_installer_job_status(*, job_id: str) -> tuple[PortalConfig, dict]:
    config = ensure_portal_config()
    job_payload = _read_installer_job(job_id)

    status_value = str(job_payload.get("status", "")).strip().lower()
    pid = job_payload.get("pid")
    running = _is_pid_running(int(pid)) if isinstance(pid, int) else False
    exit_code_file = Path(str(job_payload.get("exit_code_file", "")).strip())

    if status_value == "running" and not running:
        exit_code = None
        if exit_code_file.exists():
            try:
                exit_code = int(exit_code_file.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                exit_code = None

        if exit_code == 0:
            job_payload["status"] = "succeeded"
            job_payload["summary"] = "Instalador finalizado com sucesso."
        elif exit_code is None:
            job_payload["status"] = "finished"
            job_payload["summary"] = (
                "Instalador finalizado (sem codigo de saida registrado)."
            )
        else:
            job_payload["status"] = "failed"
            job_payload["summary"] = (
                f"Instalador finalizado com falha (exit_code={exit_code})."
            )
        job_payload["finished_at"] = timezone.now().isoformat()
        _write_installer_job(job_payload)

    log_file = Path(str(job_payload.get("log_file", "")).strip())
    job_payload["last_log_lines"] = _tail_text_file(log_file, lines=60)
    job_payload["running"] = _is_pid_running(
        int(job_payload.get("pid")) if isinstance(job_payload.get("pid"), int) else None
    )

    _sync_installer_job_in_config(config, job_payload)
    return config, job_payload


@transaction.atomic
def cancel_installer_job(*, job_id: str) -> tuple[PortalConfig, dict]:
    config = ensure_portal_config()
    job_payload = _read_installer_job(job_id)
    pid = job_payload.get("pid")
    if isinstance(pid, int) and _is_pid_running(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

    job_payload["status"] = "canceled"
    job_payload["finished_at"] = timezone.now().isoformat()
    job_payload["summary"] = "Job cancelado manualmente pelo operador."
    _write_installer_job(job_payload)
    _sync_installer_job_in_config(config, job_payload)
    return config, job_payload


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
