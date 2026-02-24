---
description: Wrapper para entrega backend. Fonte de verdade: W10/W12/W17/W21 + padrao services/selectors.
---

# Workflow 02 - Feature Backend (Wrapper)

## Precondicao
- Ler `AGENTS.md` e `/home/roberto/.gemini/GEMINI.md`.
- Validar branch do agente:
  - Codex: `bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - Antigravity: `bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`

## Execucao
1. Implementar no padrao: `services`, `selectors`, `serializers`, `views`, `urls`, `tests`.
2. Validar backend com venv ativa:
  - `cd workspaces/backend && source .venv/bin/activate`
  - `python manage.py check && make lint && make test`
3. Atualizar memoria/docs via `W17_atualizar_documentacao_memoria`.
4. Sincronizar e commitar via `W21_sync_codex_antigravity` e `W12_salvar_checkpoint`.
