from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServiceUnit:
    key: str
    label: str
    unit: str


@dataclass(frozen=True)
class EndpointSpec:
    key: str
    label: str
    url: str
    expected_codes: tuple[int, ...]


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / ".runtime" / "gestor-servidor"
EVENTS_LOG = RUNTIME_DIR / "events.log"
METRICS_LOG = RUNTIME_DIR / "metrics.jsonl"

ROOT_DOMAIN = "mrquentinha.com.br"
DOMAINS = {
    "root": ROOT_DOMAIN,
    "www": "www.mrquentinha.com.br",
    "app": "app.mrquentinha.com.br",
    "admin": "admin.mrquentinha.com.br",
    "api": "api.mrquentinha.com.br",
    "web_legacy": "web.mrquentinha.com.br",
}

SERVICE_UNITS: tuple[ServiceUnit, ...] = (
    ServiceUnit("nginx", "Nginx", "nginx"),
    ServiceUnit("postgres", "PostgreSQL", "postgresql"),
    ServiceUnit("ssh", "SSH", "ssh"),
    ServiceUnit("backend", "Backend Prod", "mrq-backend-prod"),
    ServiceUnit("portal", "Portal Prod", "mrq-portal-prod"),
    ServiceUnit("client", "WebClient Prod", "mrq-client-prod"),
    ServiceUnit("admin", "WebAdmin Prod", "mrq-admin-prod"),
)

SERVICE_GROUP_UNITS = tuple(unit.unit for unit in SERVICE_UNITS if unit.unit.startswith("mrq-"))

ENDPOINT_TIMEOUT_SECONDS = 2.5
ENDPOINT_SPECS_BASE: tuple[EndpointSpec, ...] = (
    EndpointSpec("www", "Portal (www)", "https://www.mrquentinha.com.br", (200, 301, 302)),
    EndpointSpec("app", "WebClient (app)", "https://app.mrquentinha.com.br", (200, 301, 302)),
    EndpointSpec("admin", "WebAdmin", "https://admin.mrquentinha.com.br", (200, 301, 302)),
    EndpointSpec("api_public", "API Publica", "https://api.mrquentinha.com.br/api/v1/health", (200,)),
    EndpointSpec("web_legacy", "Web legado", "https://web.mrquentinha.com.br", (404,)),
    EndpointSpec("api_localhost", "API Localhost", "http://127.0.0.1:8000/api/v1/health", (200, 301, 302)),
)

REFRESH_INTERVAL_SECONDS = 2.0
ALERT_COOLDOWN_SECONDS = 30
CPU_ALERT_THRESHOLD = 85.0
MEMORY_ALERT_THRESHOLD = 90.0
DISK_ALERT_THRESHOLD = 90.0
LATENCY_ALERT_THRESHOLD_MS = 1200.0
CONNECTION_ALERT_THRESHOLD = 2000
