# Paths e Portas Oficiais

## Referencia
- Fonte de politica: `/home/roberto/.gemini/GEMINI.md`
- Estado real: `docs/memory/PROJECT_STATE.md`

## Paths principais
- Backend: `workspaces/backend`
- Portal: `workspaces/web/portal`
- Client: `workspaces/web/client`
- UI compartilhada: `workspaces/web/ui`
- Scripts: `scripts/`
- Workflows: `.agent/workflows/`
- Memoria viva: `docs/memory/` e `.agent/memory/`

## Portas locais
- Backend API: `8000`
- Portal: `3000`
- Client: `3001`

## URLs locais comuns
- `http://127.0.0.1:8000`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

## Scripts oficiais
- Start:
  - `scripts/start_backend_dev.sh`
  - `scripts/start_portal_dev.sh`
  - `scripts/start_client_dev.sh`
- Smoke:
  - `scripts/smoke_stack_dev.sh`
  - `scripts/smoke_client_dev.sh`
- Sync/QA:
  - `scripts/sync_memory.sh --check`
  - `scripts/quality_gate_all.sh`
- Branch policy:
  - `scripts/branch_guard.sh`
