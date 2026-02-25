# Project State (dev)

Referencia de atualizacao: 25/02/2026.

## Etapas
- Concluidas: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`, `7.1.1`, `7.1.2`, `7.1.3`.
- Em progresso: `7.2` (pagamentos online) com planejamento acoplado de `6.3` (Portal CMS backend-only) e `9.0` (Admin Web MVP).
- Proxima execucao recomendada (unica): `T7.2.1`.

## Planejamento oficial (docs-first)
- Requisitos consolidados: `docs/memory/REQUIREMENTS_BACKLOG.md`
- Roadmap mestre: `docs/memory/ROADMAP_MASTER.md`
- Backlog priorizado: `docs/memory/BACKLOG.md`
- Fila operacional curta: `.agent/memory/TODO_NEXT.md`

## Politica de branches (anti-conflito)
- `BRANCH_CODEX_PRIMARY=main`
- `BRANCH_ANTIGRAVITY=AntigravityIDE`
- `BRANCH_UNION=Antigravity_Codex`
- Codex: `main` e `main/etapa-*`.
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
- Modulos ativos: `core`, `accounts`, `catalog`, `inventory`, `procurement`, `orders`, `finance`, `production`, `ocr_ai`.

### Web Portal (Next.js - 3000)
- Status: institucional em evolucao de template (`classic` + `letsfit-clean`).
- Integracao: cardapio por API (`/today/` e `/by-date/`).
- Risco de conflito: alto em paralelo com trilha Antigravity de template.

### Web Client (Next.js - 3001)
- Status: auth real concluida (`register/token/refresh/me`).
- Pedido/historico: escopo autenticado sem demo.
- Gap aberto: checkout com pagamento online (`7.2`).

### Admin Web (planejado)
- Status: nao iniciado no `main`.
- Epico alvo: `9.0` (MVP operacional) e `9.1` (completo).

## Portas e scripts oficiais
- Backend: `8000` -> `scripts/start_backend_dev.sh`
- Portal: `3000` -> `scripts/start_portal_dev.sh`
- Client: `3001` -> `scripts/start_client_dev.sh`
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
- Publicos read-only de menu:
  - `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
  - `GET /api/v1/catalog/menus/today/`

## Plano da etapa ativa
- Trilha principal: `7.2 Pagamentos online`.
- Trilha bloqueadora correlata: `6.3 Portal CMS backend-only`.
- Trilha estrutural obrigatoria: `9.0 Admin Web MVP`.
- Proximo passo unico recomendado: iniciar `T7.2.1` (provider abstraction + intents + idempotencia).
