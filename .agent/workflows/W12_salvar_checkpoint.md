---
id: W12
title: Salvar checkpoint
description: Salvar progresso com branch policy, quality gate minimo e memoria sincronizada.
inputs:
  - agente (codex|antigravity|join)
  - mensagem_checkpoint
  - criar_tag (opcional)
outputs:
  - commit_checkpoint
  - tag_checkpoint (opcional)
commands:
  - sed -n '1,220p' GEMINI.md
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary feature/etapa-4-orders --allow-codex-join
  - git diff --stat
  - cd workspaces/backend && source .venv/bin/activate && make lint && make test
  - source ~/.nvm/nvm.sh && nvm use --lts
  - cd workspaces/web/portal && npm run build
  - cd workspaces/web/client && npm run build
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

## Regras por agente
- Codex:
  - pode commitar em `feature/etapa-4-orders`.
  - para integracao, pode commitar em `join/codex-ag` (usar `--allow-codex-join`).
- Antigravity:
  - commita apenas em `ag/<tipo>/<slug>`.
  - nunca commitar em branch do Codex.

## Passos
1. Ler `GEMINI.md`.
2. Validar branch com `branch_guard`.
3. Rodar quality gate minimo (venv + nvm LTS).
4. Atualizar `docs/memory/CHANGELOG.md`.
5. Commitar com mensagem rastreavel.
