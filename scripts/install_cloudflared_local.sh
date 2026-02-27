#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT_DIR/.runtime/bin"
TARGET_BIN="$BIN_DIR/cloudflared"
TMP_FILE="$(mktemp)"

cleanup() {
  rm -f "$TMP_FILE"
}
trap cleanup EXIT

resolve_asset_name() {
  local os_name arch_name
  os_name="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch_name="$(uname -m)"

  if [[ "$os_name" != "linux" ]]; then
    echo "[cloudflared-install] SO nao suportado neste script: $os_name" >&2
    exit 1
  fi

  case "$arch_name" in
    x86_64|amd64)
      echo "cloudflared-linux-amd64"
      ;;
    aarch64|arm64)
      echo "cloudflared-linux-arm64"
      ;;
    *)
      echo "[cloudflared-install] Arquitetura nao suportada: $arch_name" >&2
      exit 1
      ;;
  esac
}

ASSET_NAME="$(resolve_asset_name)"
DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/${ASSET_NAME}"

mkdir -p "$BIN_DIR"

echo "[cloudflared-install] Baixando: $DOWNLOAD_URL"
curl -fL "$DOWNLOAD_URL" -o "$TMP_FILE"

install -m 0755 "$TMP_FILE" "$TARGET_BIN"

echo "[cloudflared-install] Instalado em: $TARGET_BIN"
"$TARGET_BIN" --version

echo "[cloudflared-install] Para usar no backend, mantenha o binario em $TARGET_BIN"
