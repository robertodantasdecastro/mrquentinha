#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/workspaces/backend"
PORTAL_DIR="$ROOT_DIR/workspaces/web/portal"
CLIENT_DIR="$ROOT_DIR/workspaces/web/client"
ADMIN_DIR="$ROOT_DIR/workspaces/web/admin"
RUN_USER="${MRQ_RUN_USER:-ubuntu}"
INTERNAL_API_BASE_URL="${MRQ_INTERNAL_API_BASE_URL:-http://127.0.0.1:8000}"
NODE_MAX_OLD_SPACE_MB="${MRQ_NODE_MAX_OLD_SPACE_MB:-256}"
GUNICORN_WORKERS="${MRQ_GUNICORN_WORKERS:-1}"
GUNICORN_TIMEOUT="${MRQ_GUNICORN_TIMEOUT:-120}"

ensure_sudo() {
  if [[ "$(id -u)" -eq 0 ]]; then
    return 0
  fi
  sudo -v
}

require_paths() {
  [[ -f "$BACKEND_DIR/.venv/bin/activate" ]] || {
    echo "[systemd-prod] venv nao encontrado em $BACKEND_DIR/.venv" >&2
    exit 1
  }
  [[ -f "$BACKEND_DIR/.env.prod" ]] || {
    echo "[systemd-prod] .env.prod nao encontrado em $BACKEND_DIR" >&2
    exit 1
  }
  [[ -d "$PORTAL_DIR/.next" && -d "$CLIENT_DIR/.next" && -d "$ADMIN_DIR/.next" ]] || {
    echo "[systemd-prod] Build dos frontends ausente (.next). Rode npm run build nos 3 frontends." >&2
    exit 1
  }
}

write_units() {
  sudo tee /etc/systemd/system/mrq-backend-prod.service >/dev/null <<UNIT
[Unit]
Description=Mr Quentinha Backend (Django/Gunicorn) - Producao
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${BACKEND_DIR}
Environment=DJANGO_SETTINGS_MODULE=config.settings.prod
Environment=DEBUG=False
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/env bash -lc 'set -euo pipefail; cd "${BACKEND_DIR}"; ln -sfn .env.prod .env; source .venv/bin/activate; python manage.py migrate --noinput; exec gunicorn config.wsgi:application --chdir "${BACKEND_DIR}/src" --bind 127.0.0.1:8000 --workers ${GUNICORN_WORKERS} --timeout ${GUNICORN_TIMEOUT}'
Restart=always
RestartSec=3
TimeoutStopSec=30
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
UNIT

  sudo tee /etc/systemd/system/mrq-portal-prod.service >/dev/null <<UNIT
[Unit]
Description=Mr Quentinha Portal Web - Producao
After=network.target mrq-backend-prod.service
Requires=mrq-backend-prod.service

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${PORTAL_DIR}
Environment=NODE_ENV=production
Environment=NODE_OPTIONS=--max-old-space-size=${NODE_MAX_OLD_SPACE_MB}
Environment=INTERNAL_API_BASE_URL=${INTERNAL_API_BASE_URL}
Environment=NEXT_PUBLIC_API_BASE_URL=${INTERNAL_API_BASE_URL}
ExecStart=/usr/bin/env bash -lc 'set -euo pipefail; cd "${PORTAL_DIR}"; exec npm run start -- --hostname 127.0.0.1 --port 3000'
Restart=always
RestartSec=3
TimeoutStopSec=30
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
UNIT

  sudo tee /etc/systemd/system/mrq-client-prod.service >/dev/null <<UNIT
[Unit]
Description=Mr Quentinha Web Client - Producao
After=network.target mrq-backend-prod.service
Requires=mrq-backend-prod.service

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${CLIENT_DIR}
Environment=NODE_ENV=production
Environment=NODE_OPTIONS=--max-old-space-size=${NODE_MAX_OLD_SPACE_MB}
Environment=INTERNAL_API_BASE_URL=${INTERNAL_API_BASE_URL}
Environment=NEXT_PUBLIC_API_BASE_URL=${INTERNAL_API_BASE_URL}
ExecStart=/usr/bin/env bash -lc 'set -euo pipefail; cd "${CLIENT_DIR}"; exec npm run start -- --hostname 127.0.0.1 --port 3001'
Restart=always
RestartSec=3
TimeoutStopSec=30
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
UNIT

  sudo tee /etc/systemd/system/mrq-admin-prod.service >/dev/null <<UNIT
[Unit]
Description=Mr Quentinha Web Admin - Producao
After=network.target mrq-backend-prod.service
Requires=mrq-backend-prod.service

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${ADMIN_DIR}
Environment=NODE_ENV=production
Environment=NODE_OPTIONS=--max-old-space-size=${NODE_MAX_OLD_SPACE_MB}
Environment=INTERNAL_API_BASE_URL=${INTERNAL_API_BASE_URL}
Environment=NEXT_PUBLIC_API_BASE_URL=${INTERNAL_API_BASE_URL}
ExecStart=/usr/bin/env bash -lc 'set -euo pipefail; cd "${ADMIN_DIR}"; exec npm run start -- --hostname 127.0.0.1 --port 3002'
Restart=always
RestartSec=3
TimeoutStopSec=30
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
UNIT

  sudo tee /etc/systemd/system/mrq-stack-prod.target >/dev/null <<UNIT
[Unit]
Description=Mr Quentinha Stack - Producao
Requires=mrq-backend-prod.service mrq-portal-prod.service mrq-client-prod.service mrq-admin-prod.service
After=network.target

[Install]
WantedBy=multi-user.target
UNIT
}

restart_stack() {
  sudo systemctl daemon-reload
  sudo systemctl enable mrq-stack-prod.target >/dev/null
  sudo systemctl restart mrq-backend-prod.service mrq-portal-prod.service mrq-client-prod.service mrq-admin-prod.service
  sudo systemctl start mrq-stack-prod.target
}

show_status() {
  echo "[systemd-prod] Unidades ativas:" 
  systemctl --no-pager --full status mrq-backend-prod.service mrq-portal-prod.service mrq-client-prod.service mrq-admin-prod.service | sed -n '1,120p'
}

main() {
  ensure_sudo
  id "$RUN_USER" >/dev/null 2>&1 || {
    echo "[systemd-prod] Usuario nao encontrado: $RUN_USER" >&2
    exit 1
  }
  require_paths
  write_units
  restart_stack
  show_status
  echo "[systemd-prod] Stack de producao configurada com systemd e habilitada no boot."
}

main "$@"
