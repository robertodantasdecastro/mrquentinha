---
description: Wrapper para entrega frontend. Fonte de verdade: W10/W12/W17/W21 + padrao UI compartilhada.
---

# Workflow 03 - Feature Frontend (Wrapper)

## Precondicao
- Ler `AGENTS.md` e `GEMINI.md`.
- Validar branch do agente:
  - Codex: `bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - Antigravity: `bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`

## Execucao
1. Implementar com `workspaces/web/ui` e layout clean.
2. Carregar Node LTS antes de npm:
  - `source ~/.nvm/nvm.sh && nvm use --lts`
3. Validar builds/lint dos frontends.
4. Atualizar memoria/docs via `W17_atualizar_documentacao_memoria`.
5. Sincronizar e commitar via `W21_sync_codex_antigravity` e `W12_salvar_checkpoint`.
