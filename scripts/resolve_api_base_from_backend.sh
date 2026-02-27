#!/usr/bin/env bash
set -euo pipefail

BACKEND_BASE_URL="${INTERNAL_API_BASE_URL:-http://127.0.0.1:8000}"
CHANNEL="${1:-portal}"
PAGE="${2:-home}"

ENDPOINT="${BACKEND_BASE_URL%/}/api/v1/portal/config/?channel=${CHANNEL}&page=${PAGE}"

python3 - "$ENDPOINT" <<'PY'
import json
import sys
import urllib.error
import urllib.request


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

    print(api_base_url)
    return 0


raise SystemExit(main())
PY
