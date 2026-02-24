# Project State (dev)

Referencia de atualizacao: 24/02/2026.

## Etapas concluidas
- Concluidas: 0 -> 5.6.3, 6.0, 6.0.1, 7.0.
- Proximas macro-etapas planejadas:
  - 7.1 Auth/RBAC
  - 7.2 Pagamentos
  - 6.1 Nginx local
  - 8 Financas pessoais

## Portas e URLs atuais
- Backend API (Django): `http://127.0.0.1:8000` e `http://10.211.55.21:8000`
- Portal institucional (Next): `http://127.0.0.1:3000` e `http://10.211.55.21:3000`
- Web Cliente (Next): `http://127.0.0.1:3001` e `http://10.211.55.21:3001`

## Quickstart (scripts oficiais)
No root do projeto (`~/mrquentinha`), em terminais separados:

```bash
./scripts/start_backend_dev.sh
```

```bash
./scripts/start_portal_dev.sh
```

```bash
./scripts/start_client_dev.sh
```

Para validacao automatica:

```bash
./scripts/smoke_stack_dev.sh
./scripts/smoke_client_dev.sh
```

## Scripts de desenvolvimento
- `./scripts/start_backend_dev.sh`
  - ativa `workspaces/backend/.venv`
  - roda `python manage.py migrate`
  - sobe API em `0.0.0.0:8000`
- `./scripts/start_portal_dev.sh`
  - entra em `workspaces/web/portal`
  - instala dependencias se necessario
  - sobe Next em `0.0.0.0:3000`
- `./scripts/start_client_dev.sh`
  - entra em `workspaces/web/client`
  - encerra processo/lock antigo do Next na porta `3001`
  - sobe Next em `0.0.0.0:3001`
- `./scripts/seed_demo.sh`
  - aplica migracoes
  - executa `python manage.py seed_demo`
- `./scripts/smoke_stack_dev.sh`
  - sobe backend + portal + client
  - executa seed demo
  - valida rotas e encerra processos
- `./scripts/smoke_client_dev.sh`
  - sobe client em background
  - aguarda disponibilidade com timeout
  - valida `/`, `/pedidos`, `/cardapio`

## Modulos e endpoints principais
- Base:
  - `GET /`
  - `GET /api/v1/health`
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

## Variaveis de ambiente (somente nomes/exemplos)
### Backend (`workspaces/backend/.env`)

```env
DATABASE_URL=postgresql://mrq_user:CHANGE_ME@localhost:5432/mrquentinha
DJANGO_SETTINGS_MODULE=config.settings.dev
DEBUG=True
SECRET_KEY=django-insecure-dev-only-change-me
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

## Observacoes de estado
- Upload de imagens e OCR MVP ativos no backend.
- Seed DEMO idempotente para navegação ponta a ponta.
- Portal e client consumindo API dinamica por `NEXT_PUBLIC_API_BASE_URL`.
- Nao versionar segredos: manter apenas placeholders em arquivos de exemplo.
