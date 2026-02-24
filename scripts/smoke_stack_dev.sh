#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VM_IP="${VM_IP:-10.211.55.21}"
BACKEND_BASE_URL="http://${VM_IP}:8000"
PORTAL_BASE_URL="http://${VM_IP}:3000"
CLIENT_BASE_URL="http://${VM_IP}:3001"

BACKEND_LOG="/tmp/mrq_smoke_backend.log"
PORTAL_LOG="/tmp/mrq_smoke_portal.log"
CLIENT_LOG="/tmp/mrq_smoke_client.log"

BACKEND_PID=""
PORTAL_PID=""
CLIENT_PID=""

declare -a PRE_BACKEND_PORT_PIDS=()
declare -a PRE_PORTAL_PORT_PIDS=()
declare -a PRE_CLIENT_PORT_PIDS=()

list_port_pids() {
  local port="$1"

  if command -v ss >/dev/null 2>&1; then
    ss -ltnp "sport = :$port" 2>/dev/null \
      | awk -F'pid=' 'NR > 1 && NF > 1 {split($2, data, ","); print data[1]}' \
      | awk 'NF' \
      | sort -u
    return
  fi

  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | awk 'NF' | sort -u
    return
  fi

  if command -v fuser >/dev/null 2>&1; then
    fuser -n tcp "$port" 2>/dev/null | tr ' ' '\n' | awk 'NF' | sort -u
    return
  fi
}

capture_preexisting_ports() {
  mapfile -t PRE_BACKEND_PORT_PIDS < <(list_port_pids 8000 || true)
  mapfile -t PRE_PORTAL_PORT_PIDS < <(list_port_pids 3000 || true)
  mapfile -t PRE_CLIENT_PORT_PIDS < <(list_port_pids 3001 || true)
}

pid_in_list() {
  local needle="$1"
  shift

  local pid
  for pid in "$@"; do
    if [[ "$pid" == "$needle" ]]; then
      return 0
    fi
  done

  return 1
}

stop_pid_gracefully() {
  local pid="$1"

  if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
    return
  fi

  kill -INT "$pid" 2>/dev/null || true
  for _ in {1..3}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid" 2>/dev/null || true
      return
    fi
    sleep 1
  done

  kill -TERM "$pid" 2>/dev/null || true
  for _ in {1..3}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid" 2>/dev/null || true
      return
    fi
    sleep 1
  done

  kill -KILL "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

cleanup_port_new_listeners() {
  local port="$1"
  shift

  local existing_pids=("$@")
  local current_pids=()
  local new_pids=()
  local pid

  mapfile -t current_pids < <(list_port_pids "$port" || true)

  for pid in "${current_pids[@]}"; do
    if ! pid_in_list "$pid" "${existing_pids[@]}"; then
      new_pids+=("$pid")
    fi
  done

  if (( ${#new_pids[@]} > 0 )); then
    echo "[smoke] Encerrando listeners remanescentes na porta ${port}: ${new_pids[*]}" >&2
    for pid in "${new_pids[@]}"; do
      stop_pid_gracefully "$pid"
    done
  fi
}

cleanup() {
  local status=$?

  stop_pid_gracefully "$CLIENT_PID"
  stop_pid_gracefully "$PORTAL_PID"
  stop_pid_gracefully "$BACKEND_PID"

  cleanup_port_new_listeners 3001 "${PRE_CLIENT_PORT_PIDS[@]}"
  cleanup_port_new_listeners 3000 "${PRE_PORTAL_PORT_PIDS[@]}"
  cleanup_port_new_listeners 8000 "${PRE_BACKEND_PORT_PIDS[@]}"

  if [[ $status -ne 0 ]]; then
    echo "[smoke] Falhou. Ultimas linhas dos logs:" >&2
    echo "--- backend log ---" >&2
    tail -n 80 "$BACKEND_LOG" >&2 || true
    echo "--- portal log ---" >&2
    tail -n 80 "$PORTAL_LOG" >&2 || true
    echo "--- client log ---" >&2
    tail -n 80 "$CLIENT_LOG" >&2 || true
  fi

  exit "$status"
}

trap cleanup EXIT INT TERM

wait_for_200() {
  local url="$1"
  local attempts="${2:-60}"
  local watched_pid="${3:-}"

  for ((i = 1; i <= attempts; i++)); do
    local status_code
    status_code="$(curl -sS -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || true)"

    if [[ -n "$watched_pid" ]] && ! kill -0 "$watched_pid" 2>/dev/null; then
      echo "[smoke] Processo encerrou antes de responder 200: $url" >&2
      return 1
    fi

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

capture_preexisting_ports

echo "[smoke] Subindo backend..."
"$ROOT_DIR/scripts/start_backend_dev.sh" >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo "[smoke] Aguardando backend..."
wait_for_200 "$BACKEND_BASE_URL/api/v1/health" 60 "$BACKEND_PID"

echo "[smoke] Aplicando seed DEMO..."
"$ROOT_DIR/scripts/seed_demo.sh"

echo "[smoke] Subindo portal..."
NEXT_PUBLIC_API_BASE_URL="$BACKEND_BASE_URL" \
  "$ROOT_DIR/scripts/start_portal_dev.sh" >"$PORTAL_LOG" 2>&1 &
PORTAL_PID=$!

echo "[smoke] Subindo client..."
NEXT_PUBLIC_API_BASE_URL="$BACKEND_BASE_URL" \
NEXT_PUBLIC_DEMO_CUSTOMER_ID="1" \
  "$ROOT_DIR/scripts/start_client_dev.sh" >"$CLIENT_LOG" 2>&1 &
CLIENT_PID=$!

echo "[smoke] Aguardando portal e client..."
wait_for_200 "$PORTAL_BASE_URL/" 60 "$PORTAL_PID"
wait_for_200 "$CLIENT_BASE_URL/" 60 "$CLIENT_PID"

root_body="$(curl -sS "$BACKEND_BASE_URL/")"
assert_contains "$root_body" '"app"[[:space:]]*:[[:space:]]*"mrquentinha"' "backend /"
assert_contains "$root_body" '"endpoints"' "backend /"

health_body="$(curl -sS "$BACKEND_BASE_URL/api/v1/health")"
assert_contains "$health_body" '"status"[[:space:]]*:[[:space:]]*"ok"' "backend /api/v1/health"

today_menu_status="$(curl -sS -o /dev/null -w "%{http_code}" "$BACKEND_BASE_URL/api/v1/catalog/menus/today/")"
if [[ "$today_menu_status" != "200" ]]; then
  echo "[smoke] Backend /api/v1/catalog/menus/today/ retornou status $today_menu_status" >&2
  echo "[smoke] Resposta: $(curl -sS "$BACKEND_BASE_URL/api/v1/catalog/menus/today/" || true)" >&2
  exit 1
fi

today_menu_body="$(curl -sS "$BACKEND_BASE_URL/api/v1/catalog/menus/today/")"
assert_contains "$today_menu_body" '"menu_date"|"detail"' "backend /api/v1/catalog/menus/today/"

portal_cardapio_status="$(curl -sS -o /dev/null -w "%{http_code}" "$PORTAL_BASE_URL/cardapio")"
if [[ "$portal_cardapio_status" != "200" ]]; then
  echo "[smoke] Portal /cardapio retornou status $portal_cardapio_status" >&2
  exit 1
fi

client_cardapio_status="$(curl -sS -o /dev/null -w "%{http_code}" "$CLIENT_BASE_URL/cardapio")"
if [[ "$client_cardapio_status" != "200" ]]; then
  echo "[smoke] Client /cardapio retornou status $client_cardapio_status" >&2
  exit 1
fi

client_pedidos_status="$(curl -sS -o /dev/null -w "%{http_code}" "$CLIENT_BASE_URL/pedidos")"
if [[ "$client_pedidos_status" != "200" ]]; then
  echo "[smoke] Client /pedidos retornou status $client_pedidos_status" >&2
  exit 1
fi

admin_status="$(curl -sS -o /dev/null -w "%{http_code}" "$BACKEND_BASE_URL/admin/")"
if [[ "$admin_status" != "200" && "$admin_status" != "302" ]]; then
  echo "[smoke] Backend /admin retornou status $admin_status" >&2
  exit 1
fi

cors_headers="$(curl -sS -D - -o /dev/null -H "Origin: http://${VM_IP}:3000" "$BACKEND_BASE_URL/api/v1/health")"
assert_contains "$cors_headers" "access-control-allow-origin: http://${VM_IP}:3000" "CORS"

echo "[smoke] OK: stack dev validado (backend + portal + client + seed)."
