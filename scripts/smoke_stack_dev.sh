#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VM_IP="${VM_IP:-10.211.55.21}"
BACKEND_BASE_URL="http://${VM_IP}:8000"
PORTAL_BASE_URL="http://${VM_IP}:3000"

BACKEND_LOG="/tmp/mrq_smoke_backend.log"
PORTAL_LOG="/tmp/mrq_smoke_portal.log"

BACKEND_PID=""
PORTAL_PID=""

cleanup() {
  local status=$?

  if [[ -n "$PORTAL_PID" ]] && kill -0 "$PORTAL_PID" 2>/dev/null; then
    kill -INT "$PORTAL_PID" 2>/dev/null || true
    wait "$PORTAL_PID" 2>/dev/null || true
  fi

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill -INT "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ $status -ne 0 ]]; then
    echo "[smoke] Falhou. Ultimas linhas dos logs:" >&2
    echo "--- backend log ---" >&2
    tail -n 40 "$BACKEND_LOG" >&2 || true
    echo "--- portal log ---" >&2
    tail -n 40 "$PORTAL_LOG" >&2 || true
  fi

  exit "$status"
}

trap cleanup EXIT INT TERM

wait_for_200() {
  local url="$1"
  local attempts="${2:-60}"

  for ((i = 1; i <= attempts; i++)); do
    local status_code
    status_code="$(curl -sS -o /dev/null -w "%{http_code}" "$url" || true)"
    if [[ "$status_code" == "200" ]]; then
      return 0
    fi
    sleep 1
  done

  echo "[smoke] Timeout aguardando 200 em: $url" >&2
  return 1
}

assert_contains() {
  local content="$1"
  local expected="$2"
  local label="$3"

  if ! grep -Eiq "$expected" <<<"$content"; then
    echo "[smoke] Conteudo invalido em ${label}. Esperado: ${expected}" >&2
    return 1
  fi
}

echo "[smoke] Subindo backend..."
"$ROOT_DIR/scripts/start_backend_dev.sh" >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo "[smoke] Subindo portal..."
NEXT_PUBLIC_API_BASE_URL="$BACKEND_BASE_URL" \
  "$ROOT_DIR/scripts/start_portal_dev.sh" >"$PORTAL_LOG" 2>&1 &
PORTAL_PID=$!

echo "[smoke] Aguardando backend e portal..."
wait_for_200 "$BACKEND_BASE_URL/api/v1/health"
wait_for_200 "$PORTAL_BASE_URL/"

root_body="$(curl -sS "$BACKEND_BASE_URL/")"
assert_contains "$root_body" '"app"[[:space:]]*:[[:space:]]*"mrquentinha"' "backend /"
assert_contains "$root_body" '"endpoints"' "backend /"

health_body="$(curl -sS "$BACKEND_BASE_URL/api/v1/health")"
assert_contains "$health_body" '"status"[[:space:]]*:[[:space:]]*"ok"' "backend /api/v1/health"

portal_root_status="$(curl -sS -o /dev/null -w "%{http_code}" "$PORTAL_BASE_URL/")"
if [[ "$portal_root_status" != "200" ]]; then
  echo "[smoke] Portal / retornou status $portal_root_status" >&2
  exit 1
fi

portal_cardapio_status="$(curl -sS -o /dev/null -w "%{http_code}" "$PORTAL_BASE_URL/cardapio")"
if [[ "$portal_cardapio_status" != "200" ]]; then
  echo "[smoke] Portal /cardapio retornou status $portal_cardapio_status" >&2
  exit 1
fi

admin_status="$(curl -sS -o /dev/null -w "%{http_code}" "$BACKEND_BASE_URL/admin/")"
if [[ "$admin_status" != "200" && "$admin_status" != "302" ]]; then
  echo "[smoke] Backend /admin retornou status $admin_status" >&2
  exit 1
fi

cors_headers="$(curl -sS -I -H "Origin: http://10.211.55.21:3000" "$BACKEND_BASE_URL/api/v1/health")"
assert_contains "$cors_headers" 'access-control-allow-origin: http://10.211.55.21:3000' "CORS"

echo "[smoke] OK: stack dev validado (backend + portal)."
