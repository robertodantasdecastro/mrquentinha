#!/usr/bin/env bash
set -euo pipefail

ROOT_DOMAIN="${MRQ_ROOT_DOMAIN:-mrquentinha.com.br}"
PORTAL_DOMAIN="${MRQ_PORTAL_DOMAIN:-www.${ROOT_DOMAIN}}"
CLIENT_DOMAIN="${MRQ_CLIENT_DOMAIN:-app.${ROOT_DOMAIN}}"
ADMIN_DOMAIN="${MRQ_ADMIN_DOMAIN:-admin.${ROOT_DOMAIN}}"
API_DOMAIN="${MRQ_API_DOMAIN:-api.${ROOT_DOMAIN}}"

SSL_EMAIL="${MRQ_SSL_EMAIL:-}"
SSL_DOMAINS="${MRQ_SSL_DOMAINS:-}"
SSL_DRY_RUN="${MRQ_SSL_DRY_RUN:-0}"

ensure_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    return 0
  fi
  if sudo -n true >/dev/null 2>&1; then
    return 0
  fi
  echo "[ssl] Precisa de sudo para configurar certificados." >&2
  sudo -v
}

normalize_domains() {
  if [[ -n "$SSL_DOMAINS" ]]; then
    echo "$SSL_DOMAINS"
    return 0
  fi

  echo "${PORTAL_DOMAIN},${CLIENT_DOMAIN},${ADMIN_DOMAIN},${API_DOMAIN}"
}

apply_certs() {
  local domains
  local extra_flags=()

  if [[ -z "$SSL_EMAIL" ]]; then
    echo "[ssl] MRQ_SSL_EMAIL nao definido." >&2
    exit 1
  fi

  domains="$(normalize_domains)"

  if [[ "$SSL_DRY_RUN" == "1" ]]; then
    extra_flags+=(--dry-run)
  fi

  ensure_root
  sudo bash scripts/setup_nginx_prod.sh

  sudo certbot --nginx \
    -m "$SSL_EMAIL" \
    --agree-tos \
    --non-interactive \
    --redirect \
    --cert-name mrquentinha \
    -d "${domains//,/ -d }" \
    "${extra_flags[@]}"
}

main() {
  apply_certs
  echo "[ssl] Certificados aplicados com sucesso."
}

main "$@"
