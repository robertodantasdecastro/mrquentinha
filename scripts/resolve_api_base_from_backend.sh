#!/usr/bin/env bash
set -euo pipefail

BACKEND_BASE_URL="${INTERNAL_API_BASE_URL:-http://127.0.0.1:8000}"
CHANNEL="${1:-portal}"
PAGE="${2:-home}"

ENDPOINT="${BACKEND_BASE_URL%/}/api/v1/portal/config/?channel=${CHANNEL}&page=${PAGE}"

python3 - "$ENDPOINT" <<'PY'
import json
import ipaddress
import sys
import urllib.error
import urllib.parse
import urllib.request


def _is_private_or_local_host(hostname: str) -> bool:
    host = (hostname or "").strip().lower()
    if not host:
        return False
    if host in {"localhost"}:
        return True
    try:
        ip_obj = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip_obj.is_private or ip_obj.is_loopback


def _normalize_local_http_url(api_base_url: str) -> str:
    parsed = urllib.parse.urlsplit(api_base_url)
    if parsed.scheme != "https":
        return api_base_url

    if parsed.port not in {8000, None}:
        return api_base_url

    if not _is_private_or_local_host(parsed.hostname or ""):
        return api_base_url

    return urllib.parse.urlunsplit(
        ("http", parsed.netloc, parsed.path, parsed.query, parsed.fragment)
    )


def main() -> int:
    endpoint = sys.argv[1]
    try:
        with urllib.request.urlopen(endpoint, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return 1

    if not isinstance(payload, dict):
        return 1

    api_base_url = str(payload.get("api_base_url", "")).strip().rstrip("/")
    if not api_base_url:
        return 1

    api_base_url = _normalize_local_http_url(api_base_url)

    print(api_base_url)
    return 0


raise SystemExit(main())
PY
