# ADR-0005: Estrategia de evolucao da trilha de financas pessoais (fase 8.2)

## Status
Aceito

## Contexto
Com `T8.1.1` e `T8.1.2` concluidas, o dominio `personal_finance` esta estavel em termos de
segregacao e LGPD operacional minima. A proxima fase precisa adicionar valor real ao usuario final
sem misturar dominio pessoal com financeiro operacional do negocio.

## Decisao
- Evoluir a trilha pessoal em fases incrementais no proprio app `personal_finance`.
- Priorizar em `T8.2.2`:
  - recorrencia de lancamentos;
  - resumo mensal por categoria/totais;
  - importacao CSV com preview e confirmacao.
- Manter API no namespace `/api/v1/personal-finance/...`, sem acoplamento com `finance`.
- Adotar idempotencia explicita para recorrencia/importacao.

## Consequencias
- Positivas:
  - incremento de valor de produto com risco tecnico controlado.
  - preserva isolamento de dados pessoais e fronteira arquitetural definida no ADR-0003.
  - permite iteracao rapida com backlog faseado.
- Trade-offs:
  - aumento de escopo do modulo `personal_finance`.
  - necessidade de regras adicionais para deduplicacao e processamento de lotes.

## Alternativas consideradas
- Implementar integracao bancaria/open finance antes de recorrencia/importacao CSV.
- Reaproveitar estruturas do modulo `finance` operacional com flag de escopo.
- Mover evolucao pessoal para um microservico separado nesta fase.
