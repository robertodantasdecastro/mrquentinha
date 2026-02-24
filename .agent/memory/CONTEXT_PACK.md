# Context Pack (Resumo Operacional)

## Estado atual
- Etapas concluidas: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`.
- Branch atual de trabalho deve ser validada no inicio da sessao.

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

## Proximos passos (fonte: TODO_NEXT)
1. 7.0.1: consolidar smoke_client (robustez continua).
2. 7.1: Auth/RBAC para cliente real.
3. 7.2: Pagamentos (Pix/Cartao/VR).
4. 6.1: Nginx local sem DNS.
5. 8: Financas pessoais.

## Regras de execucao
- Nunca comitar segredos.
- Sempre validar antes de commit (test/build/smoke conforme escopo).
- Sempre atualizar docs de memoria quando houver impacto operacional.
