# Paths e Portas Oficiais

## Referencia
- Fonte de politica: `/home/roberto/.gemini/GEMINI.md`
- Estado real: `docs/memory/PROJECT_STATE.md`

## Paths principais
- Backend: `workspaces/backend`
- Portal: `workspaces/web/portal`
- Client: `workspaces/web/client`
- Admin Web: `workspaces/web/admin`
- Proxy local: `infra/nginx`
- UI compartilhada: `workspaces/web/ui`
- Scripts: `scripts/`
- Workflows: `.agent/workflows/`
- Memoria viva: `docs/memory/` e `.agent/memory/`

## Portas locais
- Backend API: `8000`
- Admin Web: `3002`
- Portal: `3000`
- Client: `3001`
- Proxy local Nginx: `8088`

## URLs locais comuns
- `http://127.0.0.1:8000`
- `http://127.0.0.1:3002`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`
- `http://127.0.0.1:8088` (usar header `Host`)

## Hosts do proxy dev
- `api.mrquentinha.local` -> backend (`8000`)
- `www.mrquentinha.local` -> portal (`3000`)
- `app.mrquentinha.local` -> client (`3001`)
- `admin.mrquentinha.local` -> admin (`3002`)

## Scripts oficiais
- Start:
  - `scripts/start_backend_dev.sh`
  - `scripts/start_admin_dev.sh`
  - `scripts/start_portal_dev.sh`
  - `scripts/start_client_dev.sh`
  - `scripts/start_proxy_dev.sh`
  - `scripts/install_cloudflared_local.sh`
  - `scripts/cloudflare_admin.sh` (Cloudflare DEV/PROD via API admin)
  - `scripts/cloudflare_sync_frontends.sh` (sync de `.env.local` dos frontends)
- Stop:
  - `scripts/stop_proxy_dev.sh`
- Smoke:
  - `scripts/smoke_stack_dev.sh`
  - `scripts/smoke_client_dev.sh`
  - `scripts/smoke_proxy_dev.sh`
- Sync/QA:
  - `scripts/sync_memory.sh --check`
  - `scripts/quality_gate_all.sh`
- Branch policy:
  - `scripts/branch_guard.sh`
