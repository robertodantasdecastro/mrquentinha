# Mr Quentinha

<p align="center">
  <img src="assets/brand/png/logo_wordmark_2000x.png" alt="Logo Mr Quentinha" width="420" />
</p>

Ecossistema completo para operacao de marmitas com foco em escala, rastreabilidade e qualidade operacional.

Resumo executivo:
- `README_EXECUTIVO.md`

O projeto integra:
- backend unico (Django + DRF + PostgreSQL)
- portal institucional web
- frontend web do cliente
- web admin de gestao operacional
- contrato para app mobile

## Visao geral

O Mr Quentinha centraliza em uma unica API os fluxos de:
- catalogo e cardapio por data
- estoque, compras e producao
- pedidos e pagamentos online
- financeiro operacional (AP/AR, caixa, ledger, conciliacao e relatorios)
- CMS de portal/cliente
- releases mobile
- monitoramento realtime do ecossistema

## Principais capacidades

### Cliente (web/mobile)
- consulta de cardapio por data
- checkout com `PIX`, `CARD` e `VR`
- historico de pedidos e confirmacao de recebimento
- login JWT
- base para login social Google/Apple via configuracao centralizada no CMS

### Operacao interna (admin)
- modulos de Cardapio, Compras, Estoque, Producao, Pedidos e Financeiro
- Usuarios/RBAC
- Relatorios e exportacoes CSV
- Portal CMS (template, conteudo dinamico, conectividade, auth social, pagamentos e release mobile)
- Monitoramento em tempo real de servicos, gateways e lifecycle de pedidos

### Pagamentos multigateway
- provedores suportados: `mercadopago`, `efi`, `asaas` e `mock`
- configuracao central no Portal CMS
- selecao de provider por canal (`web` e `mobile`)
- webhooks dedicados por provider
- sincronizacao de status para o ecossistema via backend

## Arquitetura

Padrao principal:
- backend orientado a dominio (apps Django)
- service layer para regras de negocio
- selectors para leitura
- frontend desacoplado consumindo API `/api/v1/...`

Dominios backend:
- `accounts`
- `catalog`
- `inventory`
- `procurement`
- `orders`
- `finance`
- `production`
- `portal`
- `personal_finance`
- `ocr_ai`

## Estrutura de repositorio

- `workspaces/backend`: API Django + DRF
- `workspaces/web/admin`: web admin
- `workspaces/web/portal`: portal institucional
- `workspaces/web/client`: frontend web do cliente
- `workspaces/web/ui`: pacote compartilhado de UI/tokens
- `workspaces/mobile`: contratos de brand/content para app mobile
- `scripts/`: start, smoke, seed, quality gate e operacao
- `docs/`: arquitetura, plano, ADRs e memoria viva

## Requisitos de ambiente

- Linux/VM de desenvolvimento
- Python 3.11+
- Node.js LTS
- PostgreSQL
- Sem Docker no fluxo oficial

## Setup rapido

### 1) Backend

```bash
cd workspaces/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
```

### 2) Frontends web

```bash
cd workspaces/web/admin && npm install
cd ../portal && npm install
cd ../client && npm install
```

## Subir stack local

A partir da raiz do repositorio:

```bash
./scripts/start_backend_dev.sh
./scripts/start_admin_dev.sh
./scripts/start_portal_dev.sh
./scripts/start_client_dev.sh
```

Portas oficiais:
- backend: `8000`
- admin: `3002`
- portal: `3000`
- client: `3001`
- proxy local nginx: `8088`

## Proxy local

```bash
./scripts/start_proxy_dev.sh
./scripts/smoke_proxy_dev.sh
```

Hosts:
- `api.mrquentinha.local` -> backend
- `admin.mrquentinha.local` -> admin
- `www.mrquentinha.local` -> portal
- `app.mrquentinha.local` -> client

Parar proxy:

```bash
./scripts/stop_proxy_dev.sh
```

## Observabilidade e operacao

Painel operacional em terminal:

```bash
./scripts/ops_dashboard.sh
```

Tambem disponivel:

```bash
python3 scripts/ops_center.py
```

Monitoramento realtime no backend:
- `GET /api/v1/orders/ops/realtime/`

Monitoramento no Admin:
- modulo `Monitoramento` em `/modulos/monitoramento`

## Qualidade

### Backend (raiz)

```bash
make check
make lint
make test
```

### Frontends

```bash
cd workspaces/web/admin && npm run lint && npm run build
cd workspaces/web/portal && npm run lint && npm run build
cd workspaces/web/client && npm run lint && npm run build
```

### Gate integrado

```bash
./scripts/quality_gate_all.sh
```

## Seed e smoke

Seed de dados demo:

```bash
./scripts/seed_demo.sh
```

Smokes:

```bash
./scripts/smoke_stack_dev.sh
./scripts/smoke_client_dev.sh
./scripts/smoke_proxy_dev.sh
```

## Seguranca e governanca

- autenticacao JWT
- RBAC por perfis
- parametros sensiveis fora de repo (`.env`)
- OAuth Google/Apple configurado no Portal CMS (payload publico sem segredos)
- integracoes de pagamento com idempotencia de eventos/webhooks

## Documentacao essencial

- `AGENTS.md`
- `docs/02-arquitetura.md`
- `docs/03-modelo-de-dados.md`
- `docs/05-auth-rbac.md`
- `docs/10-plano-mvp-cronograma.md`
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/CHANGELOG.md`
- `docs/memory/RUNBOOK_DEV.md`

## Roadmap imediato

Prioridades ativas:
- `T7.2.4-A4`: homologacao externa real dos gateways
- `T9.2.1-A2`: rodada manual E2E completa com evidencias
- `T8.2.3`: hardening da trilha de financas pessoais
