---
description: Wrapper de release/checkpoint. Fonte de verdade: W19_release_tag + W21_sync_codex_antigravity.
---

# Workflow 06 - Release Checkpoint (Wrapper)

## Precondicao
- Ler `/home/roberto/.gemini/GEMINI.md`.
- Validar branch:
  - Codex (`main`/`main-etapa-*` ou union quando integracao):
    - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - Antigravity: nao publica release em branch do Codex/union.

## Encaminhamento oficial
1. Executar `W19_release_tag`.
2. Executar `W21_sync_codex_antigravity`.
