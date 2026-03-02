#!/usr/bin/env bash
set -euo pipefail

MEDIA_ROOT="${MRQ_BACKEND_MEDIA_ROOT:-/home/ubuntu/mrquentinha/workspaces/backend/media}"
OWNER_USER="${MRQ_MEDIA_OWNER_USER:-ubuntu}"
OWNER_GROUP="${MRQ_MEDIA_OWNER_GROUP:-www-data}"

if [[ ! -d "$MEDIA_ROOT" ]]; then
  mkdir -p "$MEDIA_ROOT"
fi

sudo chown -R "${OWNER_USER}:${OWNER_GROUP}" "$MEDIA_ROOT"
sudo find "$MEDIA_ROOT" -type d -exec chmod 750 {} \;
sudo find "$MEDIA_ROOT" -type f -exec chmod 640 {} \;

echo "[media] Permissoes aplicadas com sucesso."
echo "[media] root=$MEDIA_ROOT owner=${OWNER_USER}:${OWNER_GROUP}"
