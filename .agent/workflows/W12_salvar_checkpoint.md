---
id: W12
title: Salvar checkpoint
description: Salvar progresso com commit limpo, quality gate e memoria atualizada.
inputs:
  - mensagem_checkpoint
  - criar_tag (opcional)
outputs:
  - commit_checkpoint
  - tag_checkpoint (opcional)
commands:
  - git diff --stat
  - (cd workspaces/backend && source .venv/bin/activate && make lint && make test)
  - (cd workspaces/web/portal && npm run build)
  - (cd workspaces/web/client && npm run build)
  - git add ...
  - git commit -m "<mensagem>"
  - git tag -a checkpoint-YYYYMMDD-HHMM -m "checkpoint" (opcional)
quality_gate:
  - backend lint/test + builds dos frontends
memory_updates:
  - atualizar CHANGELOG com entrada curta do checkpoint
---

# W12 - Salvar checkpoint

## Passos
1. Revisar escopo com `git diff --stat`.
2. Rodar quality gate minimo:
   - backend: lint/test
   - portal/client: build
3. Atualizar `docs/memory/CHANGELOG.md` com resumo curto.
4. Commitar com mensagem padronizada e rastreavel.
5. Opcional: criar tag `checkpoint-YYYYMMDD-HHMM`.

## Criterio de saida
- Commit validado e memoria sincronizada.
