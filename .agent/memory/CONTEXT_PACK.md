# Context Pack (Resumo Operacional)

## Portas e apps
- Backend API: `8000`
- Portal institucional: `3000`
- Web Client: `3001`

## Scripts principais
- `scripts/start_backend_dev.sh`
- `scripts/start_portal_dev.sh`
- `scripts/start_client_dev.sh`
- `scripts/seed_demo.sh`
- `scripts/smoke_stack_dev.sh`
- `scripts/smoke_client_dev.sh`

## Endpoints chave
- `GET /`
- `GET /api/v1/health`
- `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
- `POST /api/v1/orders/orders/`
- `GET /api/v1/finance/reports/cashflow/`
- `GET /api/v1/finance/reports/dre/`
- `GET /api/v1/finance/reports/kpis/`
- `POST /api/v1/production/batches/<id>/complete/`
- `POST /api/v1/ocr/jobs/`
- `POST /api/v1/ocr/jobs/<id>/apply/`

## Branch e convencao
- Branch atual: `feature/etapa-4-orders`
- Convencao para novas branches de agentes: `codex/<escopo-curto>`.

## Regras de execucao
- Nunca comitar segredos.
- Sempre validar antes de commit.
- Sempre atualizar docs de memoria com estado real.
