# Regra Global - Codex <-> Antigravity

Esta regra deve aparecer no painel `Rules > Global` do Antigravity e permanecer compativel com o fluxo do Codex.

## Contexto rapido do projeto
- Produto: ecossistema Mr Quentinha (API + portal + client).
- Estrutura principal:
  - `workspaces/backend/` (Django/DRF)
  - `workspaces/web/portal/` (Next.js institucional)
  - `workspaces/web/client/` (Next.js cliente)
  - `workspaces/web/ui/` (Design System compartilhado)
  - `scripts/` (start/smoke/seed/quality/sync)
  - `docs/memory/` e `.agent/memory/` (memoria viva)

## Portas padrao
- Backend: `8000`
- Portal: `3000`
- Client: `3001`

## Scripts obrigatorios de operacao
- Start:
  - `scripts/start_backend_dev.sh`
  - `scripts/start_portal_dev.sh`
  - `scripts/start_client_dev.sh`
- Smoke:
  - `scripts/smoke_stack_dev.sh`
  - `scripts/smoke_client_dev.sh`
- Seed:
  - `scripts/seed_demo.sh`
- Qualidade/sync:
  - `scripts/sync_memory.sh --check`
  - `scripts/quality_gate_all.sh`

## Endpoints-chave
- `GET /`
- `GET /api/v1/health`
- `/api/v1/catalog/...`
- `/api/v1/orders/...`
- `/api/v1/finance/...`
- `/api/v1/production/...`
- `/api/v1/ocr/...`

## Padrao tecnico obrigatorio
- Backend: `services/selectors/serializers/views/urls/tests`.
- Frontend: uso de `workspaces/web/ui`, `TemplateProvider` e layout clean/modular.

## Politica de Branches (Anti-Conflito)
- `BRANCH_CODEX_PRIMARY=feature/etapa-4-orders`
- Codex trabalha somente em `BRANCH_CODEX_PRIMARY`.
- Antigravity sempre cria/usa branch `ag/<tipo>/<slug>`.
- Integracao entre agentes ocorre apenas em `join/codex-ag`.
- Nenhum agente deve comitar em branch do outro.
- Guard rail obrigatorio antes de commit/push:
  - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders`
  - `bash scripts/branch_guard.sh --agent antigravity --strict`
  - `bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders`

## Sync Pack obrigatorio
Atualizar quando houver mudanca de codigo, script, configuracao, endpoint, porta ou env var:
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/CHANGELOG.md`
- `docs/memory/DECISIONS.md`
- `docs/memory/RUNBOOK_DEV.md`
- `.agent/memory/CONTEXT_PACK.md`
- `.agent/memory/TODO_NEXT.md`

## Regra de ouro
Qualquer mudanca em `workspaces/backend`, `workspaces/web/*` ou `scripts/` exige atualizar memoria/docs e rodar quality gate antes de push.

## Seguranca
- Nunca comitar segredos (`.env` real, tokens, senhas, chaves).
- O repositorio deve conter apenas `.env.example` com placeholders.

## Git hygiene
- Commits pequenos e revisaveis.
- Em mudancas grandes, preferir separar em commits de infra/docs e feature.
- Rodar quality gate antes de push.

## Compatibilidade de fonte completa
- Fonte detalhada complementar: `.antigravity/GLOBAL_RULE.md` e `.antigravity/GLOBAL_SYNC_RULE.md`.
