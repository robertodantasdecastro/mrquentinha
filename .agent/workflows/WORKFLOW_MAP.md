# Workflow Map Oficial

## Regra de arquitetura
- Fonte de verdade: `W10..W21`.
- Wrappers: `00..06` apenas encaminham para os W-workflows.
- Precondicao universal: ler `AGENTS.md` e `GEMINI.md`.

| Workflow | Tipo | Objetivo | Precondicoes | Comandos-chave | Atualiza memoria |
|---|---|---|---|---|---|
| 00_bootstrap | Wrapper | Encaminhar bootstrap | Ler GEMINI | Chama W10/W11 | Nao direto |
| 01_dev_loop | Wrapper | Encadear rotina diaria | Ler GEMINI | Chama W10/W11/W16/W17/W21/W12 | Nao direto |
| 02_feature_backend | Wrapper | Entrega backend | branch_guard por agente | padrao services/selectors/tests | via W17/W21 |
| 03_feature_frontend | Wrapper | Entrega frontend | branch_guard + nvm LTS | build/lint frontend | via W17/W21 |
| 04_quality_gate | Wrapper | Gate unico | Ler GEMINI | Chama W16 + quality_gate_all.sh | Nao direto |
| 05_docs_update | Wrapper | Sync docs | Ler GEMINI | Chama W17 + sync_memory --check | Nao direto |
| 06_release_checkpoint | Wrapper | Release/checkpoint | branch_guard | Chama W19 + W21 | Nao direto |
| W10_iniciar_sessao | Fonte | Iniciar dia | branch_guard + IN_PROGRESS | make test/pytest + build fronts | IN_PROGRESS |
| W11_continuar_sessao | Fonte | Retomar sessao | branch_guard + IN_PROGRESS | smokes + contexto | IN_PROGRESS |
| W12_salvar_checkpoint | Fonte | Commit checkpoint | branch_guard obrigatorio | lint/test/build + commit | CHANGELOG |
| W13_corrigir_bug | Fonte | Bugfix por teste | Ler GEMINI | teste falhando -> fix -> regressao | CHANGELOG/DECISIONS |
| W14_analisar_e_corrigir | Fonte | RCA e correcao | Ler GEMINI | logs/hipoteses/solucao | RUNBOOK_DEV |
| W15_refatoracao_com_limpeza | Fonte | Refatorar sem regressao | Ler GEMINI | golden tests + lint/test | DECISIONS (se aplicavel) |
| W16_auditoria_qualidade | Fonte | QA completo | venv + nvm LTS | check/lint/test/build/smoke | CHANGELOG (marco) |
| W17_atualizar_documentacao_memoria | Fonte | Sync Pack | Ler GEMINI | sync_memory --check | Sync Pack |
| W18_preparar_pr_merge | Fonte | PR/merge sem conflito | branch_guard por agente | fluxo codex/join ou ag-only | CHANGELOG (se ajuste) |
| W19_release_tag | Fonte | Tag/release | branch_guard codex/join | W16 + tag + push | CHANGELOG |
| W20_limpar_ambiente | Fonte | Limpeza segura | Ler GEMINI | encerrar portas + locks | Nao obrigatorio |
| W21_sync_codex_antigravity | Fonte | Sync obrigatorio | branch_guard + QA | quality_gate_all + sync_memory | Sync Pack |
