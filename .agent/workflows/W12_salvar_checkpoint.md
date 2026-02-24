---
id: W12
title: Salvar checkpoint
description: Salvar progresso com commit limpo, quality gate e memoria atualizada.
inputs:
  - agente (codex|antigravity|join)
  - mensagem_checkpoint
  - criar_tag (opcional)
outputs:
  - commit_checkpoint
  - tag_checkpoint (opcional)
commands:
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary feature/etapa-4-orders
  - git diff --stat
  - (cd workspaces/backend && source .venv/bin/activate && make lint && make test)
  - (cd workspaces/web/portal && npm run build)
  - (cd workspaces/web/client && npm run build)
  - git add ...
  - git commit -m "<mensagem>"
  - git tag -a checkpoint-YYYYMMDD-HHMM -m "checkpoint" (opcional)
quality_gate:
  - branch_guard em modo strict
  - backend lint/test + builds dos frontends
memory_updates:
  - atualizar CHANGELOG com entrada curta do checkpoint
---

# W12 - Salvar checkpoint

## Passos
1. Validar branch do agente antes de qualquer commit:
   - Codex: `bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders`
   - Antigravity: `bash scripts/branch_guard.sh --agent antigravity --strict`
   - Join: `bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders`
2. Revisar escopo com `git diff --stat`.
3. Rodar quality gate minimo:
   - backend: lint/test
   - portal/client: build
4. Atualizar `docs/memory/CHANGELOG.md` com resumo curto.
5. Commitar com mensagem padronizada e rastreavel.
6. Opcional: criar tag `checkpoint-YYYYMMDD-HHMM`.

## Criterio de saida
- Commit validado e memoria sincronizada.
