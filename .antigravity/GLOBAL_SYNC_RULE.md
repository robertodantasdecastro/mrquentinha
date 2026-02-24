# GLOBAL SYNC RULE - Codex <-> Antigravity

Regra global unificada para manter evolucao tecnica, memoria e documentacao sincronizadas entre Codex e Antigravity.

## Regra de ouro
Qualquer alteracao em codigo, scripts ou configuracao exige atualizacao de memoria + docs operacionais.

## Fonte de verdade (ler sempre antes de agir)
- `AGENTS.md`
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/CHANGELOG.md`
- `docs/memory/DECISIONS.md`
- `docs/memory/RUNBOOK_DEV.md`
- `.agent/memory/CONTEXT_PACK.md`

## Diretrizes obrigatorias
- Sem segredos:
  - nunca commitar `.env` real, tokens, senhas ou chaves.
  - usar apenas `.env.example` com placeholders.
- Commits pequenos e revisaveis.
- Mudanca grande: dividir, sempre que aplicavel, em:
  - (A) infra/docs/sync
  - (B) feature
- Validador obrigatorio antes de commit:
  - backend tests
  - build portal/client
  - smoke scripts

## Trigger de sincronizacao
Se houver alteracao em:
- `workspaces/backend/**`
- `workspaces/web/**`
- `scripts/**`
- endpoints, portas, env vars ou scripts

Entao e obrigatorio atualizar o Sync Pack.

## Sync Pack obrigatorio
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/CHANGELOG.md`
- `docs/memory/DECISIONS.md`
- `docs/memory/RUNBOOK_DEV.md`
- `.agent/memory/CONTEXT_PACK.md`
- `.agent/memory/TODO_NEXT.md`
- `docs/07-workflow-codex.md`
- `.agent/workflows/USAGE_GUIDE.md`
