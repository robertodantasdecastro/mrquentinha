#!/usr/bin/env bash
set -euo pipefail

PROXY_URL="${PROXY_URL:-http://127.0.0.1:8088}"

check_route() {
  local host="$1"
  local path="$2"
  local expected="$3"

  local status
  status="$(curl -sS -o /dev/null -w "%{http_code}" -H "Host: ${host}" "${PROXY_URL}${path}" || true)"

  if [[ "$status" != "$expected" ]]; then
    echo "[smoke-proxy] FALHA ${host}${path} -> HTTP ${status} (esperado ${expected})" >&2
    return 1
  fi

  echo "[smoke-proxy] OK ${host}${path} -> HTTP ${status}"
}

check_route "api.mrquentinha.local" "/api/v1/health" "200"
check_route "www.mrquentinha.local" "/" "200"
check_route "app.mrquentinha.local" "/" "200"
check_route "admin.mrquentinha.local" "/" "200"

echo "[smoke-proxy] OK: proxy local validado."
