---
description: Wrapper de release/checkpoint. Fonte de verdade: W19_release_tag + W21_sync_codex_antigravity.
---

# Workflow 06 - Release Checkpoint (Wrapper)

## Precondicao
- Ler `GEMINI.md`.
- Validar branch:
  - Codex (feature/join):
    - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders --allow-codex-join`
  - Antigravity: nao publica release em branch Codex/join.

## Encaminhamento oficial
1. Executar `W19_release_tag`.
2. Executar `W21_sync_codex_antigravity`.
