# T8.2.1 - Discovery de Evolucao da Trilha de Financas Pessoais

Data de referencia: 26/02/2026.
Status: concluida (discovery/documentacao).

## 1) Objetivo
- Definir a proxima fase funcional da trilha `personal_finance` apos fundacao tecnica e LGPD operacional.
- Priorizar entregas de maior valor para o usuario final sem aumentar risco de vazamento de dados.
- Gerar backlog tecnico objetivo para `T8.2.2`.

## 2) Contexto de partida
- `T8.1.1` concluida: CRUD pessoal isolado por ownership (`accounts`, `categories`, `entries`, `budgets`).
- `T8.1.2` concluida: exportacao de dados, trilha de auditoria e retencao operacional.
- Estado atual: base solida de dados pessoais, faltando recursos de uso continuo e analise pessoal.

## 3) Problemas de produto identificados
- Usuario ainda registra lancamentos de forma muito manual (friccao recorrente).
- Falta visao consolidada mensal para tomada de decisao rapida.
- Nao existe importacao assistida de movimentacoes externas (CSV).
- Nao ha mecanismo de metas financeiras pessoais no ciclo mensal.

## 4) Hipoteses de valor (priorizadas)
1. Regras de recorrencia reduzem esforco operacional e aumentam uso continuo.
2. Resumo mensal (entradas, saidas, saldo, top categorias) melhora clareza de decisao.
3. Importacao CSV assistida acelera onboarding de usuarios com historico externo.

## 5) Escopo proposto para T8.2.2 (proxima execucao)
- Recorrencia de lancamentos:
  - criar regra recorrente (`mensal`, `semanal`) e materializar ocorrencias no periodo.
- Resumo mensal pessoal:
  - endpoint de dashboard por mes com totais e agregacao por categoria.
- Importacao CSV MVP:
  - upload de arquivo + preview + confirmacao de importacao com deduplicacao basica.
- Metas pessoais por categoria:
  - manter budget como base e expor status de consumo no resumo mensal.

## 6) Fora de escopo (T8.2.2 nao cobre)
- Open finance via API bancaria.
- Categorizacao automatica por IA.
- Conciliacao multi-conta com regra complexa.
- Compartilhamento familiar/multiusuario.

## 7) Estrategia tecnica recomendada
- Evolucao incremental em cima de `personal_finance`, sem misturar com `finance`.
- Processos potencialmente pesados (importacao/materializacao) via jobs internos simples no backend.
- Contratos de API versionados no mesmo namespace `/api/v1/personal-finance/...`.
- Reuso de padroes atuais:
  - `services.py` para regra de negocio;
  - `selectors.py` para leitura/agregacao;
  - testes de ownership como criterio obrigatorio.

## 8) Novas entidades candidatas (T8.2.2)
- `personal_finance_recurring_rule`
  - owner, tipo, intervalo, proxima_execucao, payload de lancamento.
- `personal_finance_import_job`
  - owner, status, arquivo, resumo de validacao, total importado, erros.
- `personal_finance_import_row`
  - owner, import_job, hash_linha, payload bruto, status de processamento.

## 9) Criterios de aceite para fechar T8.2.2
- Usuario cria regra recorrente e gera lancamentos sem duplicidade indevida.
- Endpoint de resumo mensal retorna totais e agregacoes corretas no periodo.
- Importacao CSV permite preview e confirmacao com tratamento de linhas invalidas.
- Cobertura de testes para ownership, idempotencia basica e validacoes de formato.
- `quality_gate_all.sh` em `OK`.

## 10) Riscos e mitigacoes
- Risco: duplicidade de lancamentos por recorrencia/processamento repetido.
  - Mitigacao: chave idempotente por regra+competencia e testes de reprocessamento.
- Risco: importacao de CSV com baixa padronizacao.
  - Mitigacao: parser em duas etapas (preview e confirmacao) + relatorio de erros por linha.
- Risco: crescimento rapido de complexidade no modulo pessoal.
  - Mitigacao: manter backlog faseado (T8.2.2 MVP, T8.2.3 otimizacoes).

## 11) Proxima execucao sugerida
- `T8.2.2` - implementacao tecnica da evolucao pessoal (recorrencia, resumo mensal e importacao CSV MVP).
