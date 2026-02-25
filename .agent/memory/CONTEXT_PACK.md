# Context Pack (Resumo Operacional)

## Mapa rapido do repo
- `AGENTS.md` (regras centrais)
- `/home/roberto/.gemini/GEMINI.md` (fonte unica de policy de branches)
- `docs/memory/*` (estado, decisoes, changelog, runbook, paralelo)
- `scripts/*` (start/smoke/seed/session/sync/quality/commit/branch_guard/union)
- `workspaces/backend` (API Django/DRF)
- `workspaces/web/portal` (frontend portal)
- `workspaces/web/client` (frontend client)
- `workspaces/web/ui` (Design System compartilhado)
- `.agent/*` (workflows/prompts/rules/memory)
- `.antigravity/*` (ponte para regra global)

## Estado atual
- Etapas concluidas: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`, `7.1.1`, `7.1.2`.
- Etapa atual: `7.1.3` (fechamento de Auth/RBAC end-to-end).

## Portas e scripts
- Backend: `8000` -> `scripts/start_backend_dev.sh`
- Portal: `3000` -> `scripts/start_portal_dev.sh`
- Client: `3001` -> `scripts/start_client_dev.sh`
- Seed: `scripts/seed_demo.sh`
- Smokes: `scripts/smoke_stack_dev.sh` e `scripts/smoke_client_dev.sh`
- Guard rail: `scripts/branch_guard.sh`
- GEMINI check: `scripts/gemini_check.sh`
- Union: `scripts/union_branch_build_and_test.sh`
- Session helper: `scripts/session.sh`
- Sync helper: `scripts/sync_memory.sh`
- Quality gate: `scripts/quality_gate_all.sh`

## Endpoints chave
- `GET /` (API index)
- `GET /api/v1/health`
- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/token/`
- `POST /api/v1/accounts/token/refresh/`
- `GET /api/v1/accounts/me/`
- `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/` (publico read-only)
- `GET /api/v1/catalog/menus/today/` (publico read-only)
- `POST /api/v1/orders/orders/`
- `GET /api/v1/orders/orders/`
- `GET /api/v1/finance/reports/cashflow/`
- `GET /api/v1/finance/reports/dre/`
- `GET /api/v1/finance/reports/kpis/`
- `POST /api/v1/production/batches/<id>/complete/`
- `POST /api/v1/ocr/jobs/`
- `POST /api/v1/ocr/jobs/<id>/apply/`

## Branches e paralelo
- Codex principal: `main`
- Antigravity principal: `AntigravityIDE`
- Union neutro: `Antigravity_Codex`
- Branches por etapa:
  - `main/etapa-*`
  - `AntigravityIDE/etapa-*`
- Lock humano: `.agent/memory/IN_PROGRESS.md`

## Regra critica
- Sem segredos no repositorio. Valores reais somente em `.env` local (gitignored).
