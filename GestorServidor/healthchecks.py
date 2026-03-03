from __future__ import annotations

import socket
import subprocess
import time
from dataclasses import dataclass

from .config import ENDPOINT_SPECS_BASE, ENDPOINT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class EndpointResult:
    key: str
    label: str
    url: str
    expected_codes: tuple[int, ...]
    status_code: int
    latency_ms: float
    ok: bool
    detail: str


@dataclass(frozen=True)
class DnsResult:
    host: str
    resolved_ip: str
    matches_public_ip: bool


@dataclass(frozen=True)
class HealthSnapshot:
    endpoints: list[EndpointResult]
    dns_rows: list[DnsResult]


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    return proc.returncode, out or err


def endpoint_checks(local_ip: str, public_ip: str) -> list[EndpointResult]:
    specs = list(ENDPOINT_SPECS_BASE)
    if local_ip and local_ip not in {"127.0.0.1", "-"}:
        specs.append(
            type(ENDPOINT_SPECS_BASE[0])(
                key="api_local_ip",
                label="API IP local",
                url=f"http://{local_ip}:8000/api/v1/health",
                expected_codes=(200, 301, 302, 403),
            )
        )
    if public_ip and public_ip not in {"-", "127.0.0.1"}:
        specs.append(
            type(ENDPOINT_SPECS_BASE[0])(
                key="api_public_ip",
                label="API IP publico",
                url=f"http://{public_ip}:8000/api/v1/health",
                expected_codes=(200, 301, 302, 403),
            )
        )

    rows: list[EndpointResult] = []
    for spec in specs:
        started = time.monotonic()
        code, out = _run(
            [
                "curl",
                "-sS",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "--max-time",
                str(ENDPOINT_TIMEOUT_SECONDS),
                spec.url,
            ]
        )
        latency = (time.monotonic() - started) * 1000.0
        if code == 0 and out.isdigit():
            status_code = int(out)
            ok = status_code in spec.expected_codes
            detail = "ok" if ok else "http inesperado"
        else:
            status_code = 0
            detail = out or "falha de rede"
            # Em producao, checks por IP:8000 podem ser bloqueados por firewall.
            if spec.key in {"api_local_ip", "api_public_ip"}:
                ok = True
                detail = "porta 8000 indisponivel/bloqueada (informativo)"
            else:
                ok = False
        rows.append(
            EndpointResult(
                key=spec.key,
                label=spec.label,
                url=spec.url,
                expected_codes=spec.expected_codes,
                status_code=status_code,
                latency_ms=latency,
                ok=ok,
                detail=detail,
            )
        )
    return rows


def dns_checks(public_ip: str, hosts: dict[str, str]) -> list[DnsResult]:
    rows: list[DnsResult] = []
    for _, host in hosts.items():
        try:
            resolved = socket.gethostbyname(host)
        except OSError:
            resolved = "-"
        matches = resolved == public_ip and public_ip != "-"
        rows.append(DnsResult(host, resolved, matches))
    return rows


def collect_health_snapshot(local_ip: str, public_ip: str, hosts: dict[str, str]) -> HealthSnapshot:
    return HealthSnapshot(
        endpoints=endpoint_checks(local_ip, public_ip),
        dns_rows=dns_checks(public_ip, hosts),
    )
