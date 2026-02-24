---
id: W18
title: Preparar PR e merge (Union)
description: Criar/atualizar Antigravity_Codex com uniao main + AntigravityIDE sem alterar branches originais.
inputs:
  - agente_executor (codex)
outputs:
  - union_branch_validada
  - pr_pronto_para_main
commands:
  - sed -n '1,220p' GEMINI.md
  - bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  - bash scripts/union_branch_build_and_test.sh
quality_gate:
  - backend check/makemigrations/lint/test
  - root make test
  - portal/client build
  - smokes stack/client
memory_updates:
  - atualizar docs/memory/CHANGELOG.md e PROJECT_STATE.md se houver ajuste de fluxo
---

# W18 - Preparar PR/Merge (Fluxo Union)

## Objetivo
Preparar `Antigravity_Codex` com integracao de `main` + `AntigravityIDE`, sem modificar historico das branches de origem.

## Passos obrigatorios (manual)
1. `git checkout main && git pull`
2. `git fetch origin`
3. `git checkout -B Antigravity_Codex origin/main`
4. `git merge --no-ff origin/AntigravityIDE -m "merge: AntigravityIDE -> Antigravity_Codex"`
  - Se houver conflito: parar e reportar. Nao resolver automaticamente sem instrucao.
5. Rodar validacao de integracao completa:
  - backend: `python manage.py check`, `python manage.py makemigrations --check`, `make lint`, `make test`
  - root: `make test`
  - front: `npm run build` em portal/client com `nvm use --lts`
  - smoke: `./scripts/smoke_stack_dev.sh` e `./scripts/smoke_client_dev.sh`
6. Se tudo OK:
  - `git push -u origin Antigravity_Codex`
  - Abrir PR `Antigravity_Codex -> main` (merge final apenas Codex)

## Automacao recomendada
```bash
./scripts/union_branch_build_and_test.sh
```
Use `--dry-run` para validar os comandos sem executar.
