# Project State (dev)

Referencia de atualizacao: 24/02/2026.

## Etapas concluidas
- Concluidas: 0 -> 5.6.3, 6.0, 6.0.1, 7.0.

## Antigravity
- Antigravity Rules Path: `.agent/rules/global.md`
- Espelho para topo do painel: `.agent/rules/00_GLOBAL_RULE.md`

## Modulos backend ativos
- `catalog`
- `inventory`
- `procurement`
- `orders`
- `finance`
- `production`
- `ocr_ai`

## Frontends ativos
- Portal institucional (`workspaces/web/portal`) na porta `3000`
- Client web (`workspaces/web/client`) na porta `3001`
- UI compartilhada (`workspaces/web/ui`) usada por portal e client

## API backend
- Porta: `8000`
- Endpoint raiz: `GET /` (API index)
- Health: `GET /api/v1/health`

## Endpoints principais por dominio
- Catalog:
  - `/api/v1/catalog/ingredients/`
  - `/api/v1/catalog/dishes/`
  - `/api/v1/catalog/menus/`
  - `/api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
- Inventory:
  - `/api/v1/inventory/stock-items/`
  - `/api/v1/inventory/movements/`
- Procurement:
  - `/api/v1/procurement/requests/`
  - `/api/v1/procurement/requests/from-menu/`
  - `/api/v1/procurement/purchases/`
- Orders:
  - `/api/v1/orders/orders/`
  - `/api/v1/orders/orders/<id>/status/`
  - `/api/v1/orders/payments/`
- Production:
  - `/api/v1/production/batches/`
  - `/api/v1/production/batches/<id>/complete/`
- Finance:
  - `/api/v1/finance/accounts/`
  - `/api/v1/finance/ap-bills/`
  - `/api/v1/finance/ar-receivables/`
  - `/api/v1/finance/cash-movements/`
  - `/api/v1/finance/ledger/`
  - `/api/v1/finance/reports/cashflow/`
  - `/api/v1/finance/reports/dre/`
  - `/api/v1/finance/reports/kpis/`
  - `/api/v1/finance/reports/unreconciled/`
  - `/api/v1/finance/closes/`
  - `/api/v1/finance/closes/is-closed/`
- OCR:
  - `/api/v1/ocr/jobs/`
  - `/api/v1/ocr/jobs/<id>/apply/`

## Scripts e smokes
- Start/execucao:
  - `scripts/start_backend_dev.sh`
  - `scripts/start_portal_dev.sh`
  - `scripts/start_client_dev.sh`
- Dados e smoke:
  - `scripts/seed_demo.sh`
  - `scripts/smoke_stack_dev.sh`
  - `scripts/smoke_client_dev.sh`
- Operacao de workflow/sync:
  - `scripts/session.sh`
  - `scripts/sync_memory.sh`
  - `scripts/quality_gate_all.sh`
  - `scripts/commit_sync.sh`

## Quickstart
No root (`~/mrquentinha`), em terminais separados:

```bash
./scripts/start_backend_dev.sh
./scripts/start_portal_dev.sh
./scripts/start_client_dev.sh
```

Validacao rapida:

```bash
./scripts/smoke_stack_dev.sh
./scripts/smoke_client_dev.sh
```

Sync/check final antes de commit:

```bash
bash scripts/sync_memory.sh --check
bash scripts/quality_gate_all.sh
```

## Variaveis de ambiente (sem segredos)
### Backend (`workspaces/backend/.env`)

```env
DATABASE_URL=postgresql://mrq_user:CHANGE_ME@localhost:5432/mrquentinha
ALLOWED_HOSTS=localhost,127.0.0.1,10.211.55.21
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,http://10.211.55.21:3000,http://10.211.55.21:3001
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,http://10.211.55.21:3000,http://10.211.55.21:3001
```

### Portal (`workspaces/web/portal/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://10.211.55.21:8000
```

### Client (`workspaces/web/client/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://10.211.55.21:8000
NEXT_PUBLIC_DEMO_CUSTOMER_ID=1
```

## Regra de segredos
- Valores reais apenas em `.env` local (gitignored).
- Repositorio deve conter somente placeholders em `.env.example`.
