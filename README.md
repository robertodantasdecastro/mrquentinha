# Mr Quentinha

Repositorio principal do ecossistema **Mr Quentinha**, com backend Django e frontends web separados.

## Estrutura atual
- `workspaces/backend`: API Django + DRF (catalogo, estoque, compras, producao, pedidos, financeiro, OCR)
- `workspaces/web/portal`: portal institucional
- `workspaces/web/client`: web cliente (PWA-like)
- `workspaces/web/ui`: pacote compartilhado de componentes/tokens
- `scripts/`: scripts de start/seed/smoke para DX
- `docs/`: arquitetura, roadmap e memoria viva do projeto

## Subir stack de desenvolvimento
No root (`~/mrquentinha`), use terminais separados:

```bash
./scripts/start_backend_dev.sh
./scripts/start_portal_dev.sh
./scripts/start_client_dev.sh
```

Portas padrao:
- backend: `8000`
- portal: `3000`
- client: `3001`

## Seed de dados demo
```bash
./scripts/seed_demo.sh
```

## Smoke tests
Stack completo:

```bash
./scripts/smoke_stack_dev.sh
```

Somente client:

```bash
./scripts/smoke_client_dev.sh
```

## Painel operacional (estilo btop)

Gerenciar e monitorar backend/portal/client em um unico terminal:

```bash
./scripts/ops_dashboard.sh
```

Opcional direto em Python:

```bash
python3 scripts/ops_center.py
```

Controles no painel:
- `1/2/3`: start/stop/restart backend
- `4/5/6`: start/stop/restart portal
- `7/8/9`: start/stop/restart client
- `a`: start all
- `s`: stop all
- `r`: restart all
- `q`: sair

Modo snapshot (coleta unica, util para troubleshooting):

```bash
python3 scripts/ops_center.py --once
```

Export continuo para historico diario (JSONL e CSV automaticos):

```bash
./scripts/ops_dashboard.sh --export-json --export-csv --export-interval 5
```

Arquivos gerados em: `.runtime/ops/exports/`


## Qualidade
### Backend (a partir do root)
```bash
make check
make lint
make test
pytest
```

### Backend (direto no workspace)
```bash
cd workspaces/backend
make lint
make test
```

### Frontends
```bash
cd workspaces/web/portal
npm run lint
npm run build
```

```bash
cd workspaces/web/client
npm run lint
npm run build
```

## Documentos de referencia
- `AGENTS.md`
- `docs/00-visao-geral.md`
- `docs/10-plano-mvp-cronograma.md`
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/RUNBOOK_DEV.md`
