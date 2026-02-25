# Regra Global - Codex <-> Antigravity

Esta regra deve aparecer no painel `Rules > Global` do Antigravity e permanecer compativel com o fluxo do Codex.

## Fonte unica da regra global
- Fonte unica: `/home/roberto/.gemini/GEMINI.md`.
- No Antigravity, `Rules > Global` deve usar esse arquivo global.
- Nunca depender de `GEMINI.md` do repositorio para decisao operacional.
- Validacao obrigatoria antes de fluxo com escrita:
  - `bash scripts/gemini_check.sh`

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
  - `scripts/gemini_check.sh`
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
- `BRANCH_CODEX_PRIMARY=main`
- `BRANCH_ANTIGRAVITY=AntigravityIDE`
- `BRANCH_UNION=Antigravity_Codex`
- Codex: somente `main` e `main/etapa-*`.
- Antigravity: somente `AntigravityIDE` e `AntigravityIDE/etapa-*`.
- Union: somente `Antigravity_Codex` para merge/cherry-pick/PR.
- Nenhum agente deve comitar em branch principal do outro.
- Guard rail obrigatorio antes de commit/push:
  - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - `bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - `bash scripts/branch_guard.sh --agent union --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`

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
- Regra global Codex: antes de qualquer comando git (commit, push, pull, merge, rebase, cherry-pick), confirme a branch correta com git branch --show-current e execute scripts/branch_guard.sh no modo do agente atual.
- Commits pequenos e revisaveis.
- Em mudancas grandes, preferir separar em commits de infra/docs e feature.
- Rodar quality gate antes de push.
