# Context Pack (Resumo Operacional)

## Mapa rapido do repo
- `AGENTS.md` (regras centrais)
- `docs/memory/*` (estado, decisoes, changelog, runbook)
- `scripts/*` (start/smoke/seed/session/sync/quality/commit)
- `workspaces/backend` (API Django/DRF)
- `workspaces/web/portal` (frontend portal)
- `workspaces/web/client` (frontend client)
- `workspaces/web/ui` (Design System compartilhado)
- `.agent/*` (workflows/prompts/rules/memory)
- `.antigravity/*` (regras globais)

## Estado atual
- Etapas concluidas: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`.

## Portas e scripts
- Backend: `8000` -> `scripts/start_backend_dev.sh`
- Portal: `3000` -> `scripts/start_portal_dev.sh`
- Client: `3001` -> `scripts/start_client_dev.sh`
- Seed: `scripts/seed_demo.sh`
- Smokes: `scripts/smoke_stack_dev.sh` e `scripts/smoke_client_dev.sh`
- Session helper: `scripts/session.sh`
- Sync helper: `scripts/sync_memory.sh`
- Quality gate total: `scripts/quality_gate_all.sh`
- Commit assistido: `scripts/commit_sync.sh`

## Endpoints chave
- `GET /` (API index)
- `GET /api/v1/health`
- `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
- `POST /api/v1/orders/orders/`
- `GET /api/v1/finance/reports/cashflow/`
- `GET /api/v1/finance/reports/dre/`
- `GET /api/v1/finance/reports/kpis/`
- `POST /api/v1/production/batches/<id>/complete/`
- `POST /api/v1/ocr/jobs/`
- `POST /api/v1/ocr/jobs/<id>/apply/`

## Proximos passos (TODO_NEXT)
1. 7.0.1: consolidar smoke_client (robustez continua)
2. 7.1: Auth/RBAC para cliente real
3. 7.2: Pagamentos (Pix/Cartao/VR)
4. 6.1: Nginx local sem DNS
5. 8: Financas pessoais

## Regra critica
- Sem segredos no repositorio. Valores reais somente em `.env` local (gitignored).
