#!/usr/bin/env bash
set -euo pipefail

ROOT_DOMAIN="${MRQ_ROOT_DOMAIN:-mrquentinha.com.br}"
PORTAL_DOMAIN="${MRQ_PORTAL_DOMAIN:-www.${ROOT_DOMAIN}}"
CLIENT_DOMAIN="${MRQ_CLIENT_DOMAIN:-app.${ROOT_DOMAIN}}"
ADMIN_DOMAIN="${MRQ_ADMIN_DOMAIN:-admin.${ROOT_DOMAIN}}"
API_DOMAIN="${MRQ_API_DOMAIN:-api.${ROOT_DOMAIN}}"

PORTAL_PORT="${MRQ_PORTAL_PORT:-3000}"
CLIENT_PORT="${MRQ_CLIENT_PORT:-3001}"
ADMIN_PORT="${MRQ_ADMIN_PORT:-3002}"
API_PORT="${MRQ_API_PORT:-8000}"

NGINX_SITE_PATH="/etc/nginx/sites-available/mrquentinha.conf"
NGINX_SITE_LINK="/etc/nginx/sites-enabled/mrquentinha.conf"
LETSENCRYPT_CERT_DIR="${MRQ_SSL_CERT_DIR:-/etc/letsencrypt/live/mrquentinha}"
LETSENCRYPT_FULLCHAIN="${LETSENCRYPT_CERT_DIR}/fullchain.pem"
LETSENCRYPT_PRIVKEY="${LETSENCRYPT_CERT_DIR}/privkey.pem"

ensure_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    return 0
  fi
  if sudo -n true >/dev/null 2>&1; then
    return 0
  fi
  echo "[nginx-prod] Precisa de sudo para configurar o Nginx." >&2
  sudo -v
}

write_nginx_config() {
  ensure_root
  local tmp_file
  tmp_file="$(mktemp)"
  cat >"$tmp_file" <<EOF
server {
    listen 80;
    server_name ${PORTAL_DOMAIN};

    location / {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:${PORTAL_PORT};
    }
}

server {
    listen 80;
    server_name ${CLIENT_DOMAIN};

    location / {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:${CLIENT_PORT};
    }
}

server {
    listen 80;
    server_name ${ADMIN_DOMAIN};

    location / {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:${ADMIN_PORT};
    }
}

server {
    listen 80;
    server_name ${API_DOMAIN};

    location / {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:${API_PORT};
    }
}
EOF

  if sudo test -f "$LETSENCRYPT_FULLCHAIN" && sudo test -f "$LETSENCRYPT_PRIVKEY"; then
    cat >>"$tmp_file" <<EOF

server {
    listen 443 ssl http2;
    server_name ${PORTAL_DOMAIN};
    ssl_certificate ${LETSENCRYPT_FULLCHAIN};
    ssl_certificate_key ${LETSENCRYPT_PRIVKEY};

    location / {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:${PORTAL_PORT};
    }
}

server {
    listen 443 ssl http2;
    server_name ${CLIENT_DOMAIN};
    ssl_certificate ${LETSENCRYPT_FULLCHAIN};
    ssl_certificate_key ${LETSENCRYPT_PRIVKEY};

    location / {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:${CLIENT_PORT};
    }
}

server {
    listen 443 ssl http2;
    server_name ${ADMIN_DOMAIN};
    ssl_certificate ${LETSENCRYPT_FULLCHAIN};
    ssl_certificate_key ${LETSENCRYPT_PRIVKEY};

    location / {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:${ADMIN_PORT};
    }
}

server {
    listen 443 ssl http2;
    server_name ${API_DOMAIN};
    ssl_certificate ${LETSENCRYPT_FULLCHAIN};
    ssl_certificate_key ${LETSENCRYPT_PRIVKEY};

    location / {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:${API_PORT};
    }
}
EOF
  fi

  sudo install -m 0644 "$tmp_file" "$NGINX_SITE_PATH"
  rm -f "$tmp_file"
  sudo ln -sf "$NGINX_SITE_PATH" "$NGINX_SITE_LINK"
  sudo rm -f /etc/nginx/sites-enabled/default || true
  sudo nginx -t
  sudo systemctl reload nginx
}

main() {
  write_nginx_config
  echo "[nginx-prod] Configuracao aplicada: $NGINX_SITE_PATH"
}

main "$@"
