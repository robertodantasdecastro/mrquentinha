# Workflow Map Oficial

## Regra de arquitetura
- Fonte de verdade: `W09..W25`.
- Wrappers: `00..06` apenas encaminham para os W-workflows.
- Precondicao universal: ler `AGENTS.md`, ` /home/roberto/.gemini/GEMINI.md` e rodar `bash scripts/gemini_check.sh`.

| Workflow | Tipo | Objetivo | Precondicoes | Comandos-chave | Atualiza memoria |
|---|---|---|---|---|---|
| 00_bootstrap | Wrapper | Encaminhar bootstrap | GEMINI global valido | Chama W09/W10/W11 | Nao direto |
| 01_dev_loop | Wrapper | Encadear rotina diaria | GEMINI global valido | Chama W10/W11/W16/W17/W21/W12 | Nao direto |
| 02_feature_backend | Wrapper | Entrega backend | gemini_check + branch_guard | padrao services/selectors/tests + venv | via W17/W21 |
| 03_feature_frontend | Wrapper | Entrega frontend | gemini_check + branch_guard + nvm LTS | build/lint frontend | via W17/W21 |
| 04_quality_gate | Wrapper | Gate unico | GEMINI global valido | Chama W16 + quality_gate_all.sh | Nao direto |
| 05_docs_update | Wrapper | Sync docs | GEMINI global valido | Chama W17 + sync_memory --check | Nao direto |
| 06_release_checkpoint | Wrapper | Release/checkpoint | gemini_check + branch_guard | Chama W19 + W21 | Nao direto |
| W09_preflight_antigravity | Fonte | Preflight de runtime | gemini_check + branch_guard | validar regra global e branch | Nao obrigatorio |
| W10_iniciar_sessao | Fonte | Iniciar dia | gemini_check + branch_guard + IN_PROGRESS | make test + builds com nvm | IN_PROGRESS |
| W11_continuar_sessao | Fonte | Retomar sessao | gemini_check + branch_guard + IN_PROGRESS | smokes + contexto | IN_PROGRESS |
| W12_salvar_checkpoint | Fonte | Commit checkpoint | gemini_check + branch_guard obrigatorio | lint/test/build + commit | CHANGELOG |
| W13_corrigir_bug | Fonte | Bugfix por teste | GEMINI global valido | teste falhando -> fix -> regressao | CHANGELOG/DECISIONS |
| W14_analisar_e_corrigir | Fonte | RCA e correcao | GEMINI global valido | logs/hipoteses/solucao | RUNBOOK_DEV |
| W15_refatoracao_com_limpeza | Fonte | Refatorar sem regressao | GEMINI global valido | golden tests + lint/test | DECISIONS (se aplicavel) |
| W16_auditoria_qualidade | Fonte | QA completo | venv + nvm LTS | check/lint/test/build/smoke | CHANGELOG (marco) |
| W17_atualizar_documentacao_memoria | Fonte | Sync Pack | GEMINI global valido | sync_memory --check | Sync Pack |
| W18_preparar_pr_merge | Fonte | PR/merge sem conflito | gemini_check + branch_guard codex | union_branch_build_and_test.sh | CHANGELOG (se ajuste) |
| W19_release_tag | Fonte | Tag/release | gemini_check + branch_guard codex/union | W16 + tag + push | CHANGELOG |
| W20_limpar_ambiente | Fonte | Limpeza segura | GEMINI global valido | encerrar portas + locks | Nao obrigatorio |
| W21_sync_codex_antigravity | Fonte | Sync obrigatorio | gemini_check + branch_guard + QA | quality_gate_all + sync_memory | Sync Pack |
| W22_layout_references_audit | Fonte | Auditoria de layout/copy | GEMINI global valido | mapear referencias e CTA | LAYOUT_REFERENCES |
| W23_design_system_sync | Fonte | Auditoria DS portal/client | GEMINI global valido | mapear uso de ui/tokens | DESIGN_SYSTEM_STATUS |
| W24_git_comparison_review | Fonte | Comparar branches | gemini_check + branch_guard | git diff/log entre branches | GIT_COMPARE_REPORT |
| W25_recovery_readonly | Fonte | Recovery sem alteracoes | GEMINI global valido | diagnostico read-only | RECOVERY_TEMPLATE + RUNBOOK |

## Padrao de ambiente (obrigatorio)
- Python:
```bash
cd workspaces/backend && source .venv/bin/activate
```
- Node:
```bash
source ~/.nvm/nvm.sh && nvm use --lts
```
