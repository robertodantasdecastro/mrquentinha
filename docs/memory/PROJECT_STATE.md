# Project State (dev)

Referencia de atualizacao: 25/02/2026.

## Etapas
- Concluidas: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`, `7.1.1`, `7.1.2`, `7.1.3`, `7.2.1`, `7.2.2`, `7.2.3`, `6.3.1`, `9.0.1`, `9.0.2`, `9.0.3`, `9.1.1`.
- Em progresso: `6.2` (Portal template no fluxo Antigravity).
- Proxima execucao recomendada (unica): `T6.1.1`.

## Planejamento oficial (docs-first)
- Requisitos consolidados: `docs/memory/REQUIREMENTS_BACKLOG.md`
- Roadmap mestre: `docs/memory/ROADMAP_MASTER.md`
- Backlog priorizado: `docs/memory/BACKLOG.md`
- Fila operacional curta: `.agent/memory/TODO_NEXT.md`

## Politica de branches (anti-conflito)
- `BRANCH_CODEX_PRIMARY=main`
- `BRANCH_ANTIGRAVITY=AntigravityIDE`
- `BRANCH_UNION=Antigravity_Codex`
- Codex: `main` e `main-etapa-*`.
- Antigravity: `AntigravityIDE` e `AntigravityIDE/etapa-*`.
- Uniao: `Antigravity_Codex` (somente merge/cherry-pick/PR).
- Guard rail: `scripts/branch_guard.sh`.

## Antigravity / GEMINI
- Fonte unica GEMINI (runtime + policy): `/home/roberto/.gemini/GEMINI.md`
- Validacao obrigatoria: `bash scripts/gemini_check.sh`
- Rules path: `.agent/rules/global.md`
- Espelho topo: `.agent/rules/00_GLOBAL_RULE.md`
- Guia de uso: `.agent/workflows/USAGE_GUIDE.md`
- Mapa oficial: `.agent/workflows/WORKFLOW_MAP.md`

## Modo paralelo
- Regras: `docs/memory/PARALLEL_DEV_RULES.md`
- Lock humano: `.agent/memory/IN_PROGRESS.md`
- Sync obrigatorio: `W21_sync_codex_antigravity`
- Observacao: se `6.2 portal template` estiver ativo no Antigravity, Codex evita alteracao concorrente de layout no portal.

## Estado por componente

### Backend (Django)
- Status: operacional (Auth JWT, Finance MVP completo, OCR mock, nutricao, producao, relatorios).
- Banco: PostgreSQL (`mrquentinhabd`).
- Modulos ativos: `core`, `accounts`, `catalog`, `inventory`, `procurement`, `orders`, `finance`, `production`, `ocr_ai`, `portal`.
- Pagamentos online (`7.2.1` + `7.2.2` + `7.2.3`):
  - `PaymentIntent` persistido com idempotencia por pagamento/chave.
  - provider abstraction inicial (`mock`) com payload de intent para PIX/CARD/VR.
  - webhook idempotente com reconciliacao para `AR/Cash/Ledger`.
  - criacao de pedido com `payment_method` (PIX/CARD/VR) para acionar checkout online por intent.
  - eventos de webhook persistidos em `PaymentWebhookEvent` para replay seguro por `provider + event_id`.

### Web Portal (Next.js - 3000)
- Status: institucional em evolucao de template (`classic` + `letsfit-clean`).
- Integracao: cardapio por API (`/today/` e `/by-date/`).
- Risco de conflito: alto em paralelo com trilha Antigravity de template.

### Web Client (Next.js - 3001)
- Status: auth real concluida (`register/token/refresh/me`).
- Pedido/historico: escopo autenticado sem demo.
- Checkout online concluido com intents por metodo (PIX/CARD/VR), painel de instrucoes e polling via `intent/latest`.

### Admin Web (Next.js - 3002)
- Status: `T9.1.1` concluida (Pedidos/Financeiro/Estoque/Cardapio/Compras/Producao + Usuarios/RBAC operacionais).
- Entrega atual: modulos de Pedidos/Financeiro/Estoque/Cardapio/Compras/Producao estaveis com fluxo operacional e modulo Usuarios/RBAC com atribuicao de papeis.
- Workspace ativo: `workspaces/web/admin`.
- Proximo alvo: hardening final de UX e relatorios exportaveis no bloco Admin Web apos alinhamento de prioridades.

## Portas e scripts oficiais
- Backend: `8000` -> `scripts/start_backend_dev.sh`
- Portal: `3000` -> `scripts/start_portal_dev.sh`
- Client: `3001` -> `scripts/start_client_dev.sh`
- Admin Web: `3002` -> `cd workspaces/web/admin && npm run dev -- --hostname 0.0.0.0 --port 3002`
- Smoke: `scripts/smoke_stack_dev.sh`, `scripts/smoke_client_dev.sh`
- Seed: `scripts/seed_demo.sh`
- Quality gate: `scripts/quality_gate_all.sh`
- Sync docs: `scripts/sync_memory.sh --check`

## Endpoints chave
- `GET /`
- `GET /api/v1/health`
- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/token/`
- `POST /api/v1/accounts/token/refresh/`
- `GET /api/v1/accounts/me/`
- `GET /api/v1/accounts/roles/`
- `GET /api/v1/accounts/users/`
- `GET /api/v1/accounts/users/<id>/`
- `POST /api/v1/accounts/users/<id>/roles/`
- Publicos read-only de menu:
  - `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
  - `GET /api/v1/catalog/menus/today/`
- Pagamentos intent:
  - `POST /api/v1/orders/payments/<id>/intent/`
  - `GET /api/v1/orders/payments/<id>/intent/latest/`
- Webhook pagamentos:
  - `POST /api/v1/orders/payments/webhook/` (`X-Webhook-Token`)
- Portal CMS publico:
  - `GET /api/v1/portal/config/`
  - `GET /api/v1/portal/config/version`

## Plano da etapa ativa
- Trilha principal: `9.1 Admin Web completo`.
- T9.0.1 concluida (Admin Web foundation: shell + auth + dashboard inicial).
- T9.0.2 concluida (Admin Web operacional: Pedidos, Financeiro e Estoque conectados ao backend).
- T9.0.3 concluida (Admin Web expansion: baseline de Cardapio, Compras e Producao).
- T9.1.1 concluida (modulo Usuarios/RBAC entregue com endpoints admin + painel no Admin Web).
- Proxima subetapa unica: executar `T6.1.1` (Nginx/proxy local em janela dedicada).
- Trilhas correlatas apos 9.1.1: `T6.3.2`, `T6.2.1`.
