# Session Commands (macros de rotina)

## Regra base
- Ler `AGENTS.md` e `GEMINI.md` antes de qualquer macro.
- Em fluxos com commit/push/merge, executar `scripts/branch_guard.sh`.

## Mapeamento de macros (fonte de verdade W09..W25)
- `PREFLIGHT` -> `W09_preflight_antigravity.md`
- `INICIAR_SESSAO` -> `W10_iniciar_sessao.md`
- `CONTINUAR_SESSAO` -> `W11_continuar_sessao.md`
- `SALVAR_CHECKPOINT` -> `W12_salvar_checkpoint.md`
- `CORRIGIR_BUG` -> `W13_corrigir_bug.md`
- `ANALISAR_E_CORRIGIR` -> `W14_analisar_e_corrigir.md`
- `REFATORAR_COM_LIMPEZA` -> `W15_refatoracao_com_limpeza.md`
- `AUDITAR_QUALIDADE` -> `W16_auditoria_qualidade.md`
- `ATUALIZAR_DOCS_MEMORIA` -> `W17_atualizar_documentacao_memoria.md`
- `PREPARAR_PR_MERGE` -> `W18_preparar_pr_merge.md`
- `RELEASE_TAG` -> `W19_release_tag.md`
- `LIMPAR_AMBIENTE` -> `W20_limpar_ambiente.md`
- `SYNC_CODEX_ANTIGRAVITY` -> `W21_sync_codex_antigravity.md`
- `AUDITAR_LAYOUT` -> `W22_layout_references_audit.md`
- `SYNC_DESIGN_SYSTEM` -> `W23_design_system_sync.md`
- `COMPARAR_BRANCHES` -> `W24_git_comparison_review.md`
- `RECOVERY_READONLY` -> `W25_recovery_readonly.md`

## Wrappers (00..06)
- `BOOTSTRAP` -> `00_bootstrap.md`
- `DEV_LOOP` -> `01_dev_loop.md`
- `FEATURE_BACKEND` -> `02_feature_backend.md`
- `FEATURE_FRONTEND` -> `03_feature_frontend.md`
- `QUALITY_GATE` -> `04_quality_gate.md`
- `DOCS_UPDATE` -> `05_docs_update.md`
- `RELEASE_CHECKPOINT` -> `06_release_checkpoint.md`

## Sequencia recomendada
1. `PREFLIGHT`
2. `INICIAR_SESSAO` (ou `CONTINUAR_SESSAO`)
3. `FEATURE_BACKEND` ou `FEATURE_FRONTEND`
4. `AUDITAR_QUALIDADE`
5. `ATUALIZAR_DOCS_MEMORIA`
6. `SYNC_CODEX_ANTIGRAVITY`
7. `SALVAR_CHECKPOINT`
