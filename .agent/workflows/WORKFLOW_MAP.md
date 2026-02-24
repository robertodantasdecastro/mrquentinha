# Workflow Map

| Workflow | Objetivo | Entrada | Saida | Validacao | Memoria atualizada |
|---|---|---|---|---|---|
| W10 | Iniciar sessao do dia | objetivo_dia | sessao_pronta | make test + build fronts | opcional: PROJECT_STATE |
| W11 | Continuar sessao | objetivo_atual | contexto_recarregado | smoke_stack + smoke_client | TODO_NEXT (se prioridade mudou) |
| W12 | Salvar checkpoint | mensagem_checkpoint | commit_checkpoint | lint/test/build | CHANGELOG |
| W13 | Corrigir bug | descricao_bug | bug_corrigido | teste novo + regressao | CHANGELOG/DECISIONS |
| W14 | Analisar e corrigir | incidente | causa_raiz | validacao final | RUNBOOK_DEV |
| W15 | Refatorar com limpeza | alvo_refatoracao | codigo_refatorado | golden tests + lint/test | DECISIONS (se aplicavel) |
| W16 | Auditoria de qualidade | escopo_validacao | relatorio_qa | check/lint/test/build/smoke | CHANGELOG (marco) |
| W17 | Atualizar docs/memoria | mudancas_realizadas | docs_sincronizadas | revisao de estado real | PROJECT_STATE/TODO_NEXT/DECISIONS/CHANGELOG |
| W18 | Preparar PR/merge | branch_origem | branch_pronta_para_pr | auditoria completa + DoD | CHANGELOG (se ajuste final) |
| W19 | Release/tag | nome_tag | release_publicada | quality gate completo | CHANGELOG |
| W20 | Limpar ambiente | modo_limpeza | ambiente_pronto | portas livres + lock limpo | sem atualizacao obrigatoria |
| W21 | Sync Codex <-> Antigravity | escopo_da_mudanca | sync_concluido | quality_gate_all + sync_memory + check de segredos | Sync Pack completo |
