# Guia de Uso dos Workflows (Codex + Antigravity)

## Principios
- Fonte de verdade: workflows `W09..W25`.
- Wrappers `00..06` existem para atalhos e onboarding.
- Fonte global unica: `/home/roberto/.gemini/GEMINI.md`.
- Nunca iniciar tarefa sem ler `AGENTS.md`, `GEMINI` global e rodar `bash scripts/gemini_check.sh`.

## Politica de branches
- Codex: `main` (ou `main/etapa-*` em desenvolvimento por etapa).
- Antigravity: `AntigravityIDE` (ou `AntigravityIDE/etapa-*`).
- Integracao: `Antigravity_Codex`.
- Regra global Codex: antes de qualquer comando git, confirme branch correta com git branch --show-current e rode o guard rail correspondente.
- Guard rail obrigatorio:
  - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - `bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - `bash scripts/branch_guard.sh --agent union --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`

## Fluxo recomendado (dia a dia)
1. `W09_preflight_antigravity`
2. `W10_iniciar_sessao` (ou `W11_continuar_sessao`)
3. `W02_feature_backend` ou `W03_feature_frontend`
4. `W16_auditoria_qualidade`
5. `W17_atualizar_documentacao_memoria`
6. `W21_sync_codex_antigravity`
7. `W12_salvar_checkpoint`

## Trabalho paralelo (Codex + Antigravity)
1. Antes de editar, ler `.agent/memory/IN_PROGRESS.md`.
2. Registrar lock humano no `IN_PROGRESS.md` (agente, branch, arquivos/areas).
3. Evitar editar os mesmos arquivos ao mesmo tempo.
4. Se houver intersecao, combinar ordem de entrega e usar `Antigravity_Codex` para integracao.
5. Fechar com `W21_sync_codex_antigravity` antes de checkpoint/PR.

## Workflows adicionais
- `W22_layout_references_audit`: registrar referencias e CTA em `docs/memory/LAYOUT_REFERENCES.md`.
- `W23_design_system_sync`: auditar uso de `ui/` e tokens em `docs/memory/DESIGN_SYSTEM_STATUS.md`.
- `W24_git_comparison_review`: comparar `main`, `AntigravityIDE`, `Antigravity_Codex` em `docs/memory/GIT_COMPARE_REPORT.md`.
- `W25_recovery_readonly`: executar recovery sem alteracoes e registrar `docs/memory/RECOVERY_TEMPLATE.md`.

## PR e release
- PR/merge: `W18_preparar_pr_merge`.
- Release/tag: `W19_release_tag` (sempre apos QA completo).

## Venv/NVM (obrigatorio)
- Testes Python:
```bash
cd workspaces/backend && source .venv/bin/activate
```
- Comandos npm:
```bash
source ~/.nvm/nvm.sh && nvm use --lts
```
