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

trim_space() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  echo "$value"
}

build_domain_args() {
  local -n out_ref="$1"
  local domains_csv raw_domain domain
  local -a split_domains=()
  local -A seen_domains=()

  domains_csv="$(normalize_domains)"
  IFS=',' read -r -a split_domains <<< "$domains_csv"

  for raw_domain in "${split_domains[@]}"; do
    domain="$(trim_space "$raw_domain")"
    if [[ -z "$domain" ]]; then
      continue
    fi
    if [[ -n "${seen_domains[$domain]:-}" ]]; then
      continue
    fi
    seen_domains["$domain"]=1
    out_ref+=(-d "$domain")
  done

  if [[ "${#out_ref[@]}" -eq 0 ]]; then
    echo "[ssl] Nenhum dominio valido para certbot." >&2
    exit 1
  fi
}

apply_certs() {
  local certbot_cmd=()
  local domain_args=()

  if [[ -z "$SSL_EMAIL" ]]; then
    echo "[ssl] MRQ_SSL_EMAIL nao definido." >&2
    exit 1
  fi

  build_domain_args domain_args

  ensure_root
  sudo bash scripts/setup_nginx_prod.sh

  if [[ "$SSL_DRY_RUN" == "1" ]]; then
    certbot_cmd=(sudo certbot certonly --nginx --dry-run)
  else
    certbot_cmd=(sudo certbot --nginx --redirect)
  fi

  "${certbot_cmd[@]}" \
    -m "$SSL_EMAIL" \
    --agree-tos \
    --non-interactive \
    --cert-name mrquentinha \
    "${domain_args[@]}"
}

main() {
  apply_certs
  echo "[ssl] Certificados aplicados com sucesso."
}

main "$@"
