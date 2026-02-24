# Guia de Uso dos Workflows Customizados

## Objetivo
Padronizar como iniciar, continuar, corrigir, refatorar, validar e entregar durante todo o ciclo de desenvolvimento.

## Workflows disponiveis (W10..W20)
- `W10_iniciar_sessao`: inicio do dia com baseline tecnico.
- `W11_continuar_sessao`: retomar contexto apos pausa.
- `W12_salvar_checkpoint`: salvar progresso com quality gate.
- `W13_corrigir_bug`: bugfix orientado por teste.
- `W14_analisar_e_corrigir`: investigacao profunda + correcao definitiva.
- `W15_refatoracao_com_limpeza`: refatorar sem alterar comportamento.
- `W16_auditoria_qualidade`: quality gate completo com relatorio.
- `W17_atualizar_documentacao_memoria`: sincronizar docs/memoria.
- `W18_preparar_pr_merge`: preparar branch para PR/merge.
- `W19_release_tag`: checkpoint de release com tag.
- `W20_limpar_ambiente`: limpar ambiente de dev com seguranca.

## Sequencia recomendada do dia
1. `W10_iniciar_sessao`
2. `W11_continuar_sessao` (se retomada apos pausa)
3. `W02_feature_backend` ou `W03_feature_frontend`
4. `W16_auditoria_qualidade`
5. `W12_salvar_checkpoint`

## Quando usar W13 e W14
- Use `W13` quando o bug e bem localizado e ja existe reproducao clara.
- Use `W14` quando houver incerteza, necessidade de logs/hipoteses e analise de causa raiz.

## Quando usar W15
- Use `W15` para limpar arquitetura/codigo sem alterar comportamento funcional.
- Sempre com golden tests antes e depois.

## Quando usar W18 e W19
- `W18`: antes de abrir PR e antes de merge.
- `W19`: quando for gerar checkpoint de release interna com tag.

## Como atualizar TODO_NEXT e PROJECT_STATE
- `TODO_NEXT`: manter fila cronologica e objetiva dos proximos passos.
- `PROJECT_STATE`: refletir estado real (portas, endpoints, scripts, quickstart, modulos ativos).
- Sempre registrar no `CHANGELOG` quando houver alteracao estrutural.
