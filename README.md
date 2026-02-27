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

Instalador unico (Ubuntu) com escolha de modelo (`vm` ou `docker`) e ambiente (`dev` ou `prod`):

```bash
bash scripts/install_mrquentinha.sh
```

Modo nao interativo (exemplo):

```bash
bash scripts/install_mrquentinha.sh --stack docker --env dev --yes
```

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

### Ciclo Docker (novo)

```bash
bash scripts/docker_lifecycle.sh dev up
bash scripts/docker_lifecycle.sh dev ps
bash scripts/docker_lifecycle.sh dev logs
bash scripts/docker_lifecycle.sh dev down
```

Para producao em Docker, troque `dev` por `prod`.

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

## Exposicao online com Cloudflare

No Web Admin, acesse:
- `Portal CMS` -> `Conectividade` -> `Cloudflare online (1 clique)`

### Modo DEV (URLs aleatorias `trycloudflare`)
Fluxo recomendado:
1. Ative `Modo DEV com dominios aleatorios (trycloudflare)`.
2. Mantenha `auto_apply_routes` ligado.
3. Clique em `Ativar Cloudflare`.
4. Clique em `Iniciar tunnel`.
5. Use as URLs geradas para `Portal`, `Client`, `Admin` e `API`.
6. Use `Gerar novos dominios DEV` quando precisar renovar os dominios aleatorios.

Importante:
- quando o runtime DEV reinicia, as URLs mudam;
- apos mudar URLs, sincronize os frontends (Web Admin/Client/Portal) para usar a nova `API` via script de terminal (abaixo).
- o card de runtime no Web Admin exibe monitoramento por servico (URL, PID, HTTP, latencia e status de conectividade).
- `GET /api/v1/` pode retornar `404` (esperado); use `GET /api/v1/health` para validar a API.
- validacao funcional concluida em `27/02/2026`: comunicacao `Portal/Client/Admin -> API` funcionando via dominios aleatorios `trycloudflare`.

### Modo OPERACAO (dominio oficial)
Fluxo recomendado:
1. Desative `Modo DEV`.
2. Configure dominio raiz, subdominios e credenciais do tunnel.
3. Escolha modo `cloudflare_only` (tipico de deploy) ou `hybrid`.
4. Clique em `Ativar Cloudflare`.
5. Inicie runtime por `Iniciar tunnel`.

Script operacional do tunnel:

```bash
./scripts/cloudflare_tunnel.sh status
./scripts/cloudflare_tunnel.sh start
./scripts/cloudflare_tunnel.sh logs 80
./scripts/cloudflare_tunnel.sh stop
```

Variaveis aceitas no script:
- `CF_TUNNEL_TOKEN`
- `CF_TUNNEL_NAME` (fallback: `mrquentinha`)

### Automacao por terminal (mesma API do Web Admin)
Script principal:

```bash
./scripts/cloudflare_admin.sh status
```

Instalacao local do binario `cloudflared` (sem apt/sudo):

```bash
./scripts/install_cloudflared_local.sh
```

DEV (trycloudflare):

```bash
./scripts/cloudflare_admin.sh dev-up
./scripts/cloudflare_admin.sh dev-refresh
./scripts/cloudflare_admin.sh dev-down
```

PRODUCAO (dominio oficial):

```bash
./scripts/cloudflare_admin.sh preview-prod --root-domain mrquentinha.com.br
./scripts/cloudflare_admin.sh prod-up --root-domain mrquentinha.com.br --mode cloudflare_only
./scripts/cloudflare_admin.sh prod-refresh
./scripts/cloudflare_admin.sh prod-down
```

Sincronizacao manual dos frontends com a URL da API vigente:

```bash
./scripts/cloudflare_sync_frontends.sh --api-base-url http://127.0.0.1:8000
```

Credenciais para comandos admin (quando nao usar token direto):

```bash
export MQ_ADMIN_USER="seu_usuario_admin"
export MQ_ADMIN_PASSWORD="sua_senha_admin"
```

Ou token JWT:

```bash
export MQ_ADMIN_ACCESS_TOKEN="<jwt_access>"
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

### Como usar o `ops_dashboard` no dev

Com auto-inicializacao do stack:

```bash
./scripts/ops_dashboard.sh --auto-start
```

Atalhos principais:
- `a`: start all
- `s`: stop all
- `r`: restart all
- `1/2/3`: backend (start/stop/restart)
- `g/h/j`: admin (start/stop/restart)
- `4/5/6`: portal (start/stop/restart)
- `7/8/9`: client (start/stop/restart)
- `l`: modo de logs
- `c`: modo compacto
- `?`: ajuda
- `q`: sair

Modo snapshot unico (diagnostico rapido):

```bash
python3 scripts/ops_center.py --once
```

Export de metricas para historico:

```bash
./scripts/ops_dashboard.sh --export-json --export-csv --export-interval 5
```

Arquivos de exportacao: `.runtime/ops/exports/`.

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
