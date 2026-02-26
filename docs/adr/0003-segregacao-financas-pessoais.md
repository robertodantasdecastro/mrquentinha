# ADR-0003: Segregacao entre Financeiro Operacional e Financas Pessoais

## Status
Aceito

## Contexto
O produto precisa evoluir para uma trilha de financas pessoais sem contaminar o dominio
financeiro operacional ja consolidado no MVP. O risco principal e misturar dados sensiveis
pessoais com dados de operacao interna, aumentando superficie de acesso e risco LGPD.

## Decisao
- Manter `finance` como dominio exclusivo da operacao do Mr Quentinha.
- Criar novo dominio `personal_finance` para a trilha pessoal.
- Adotar segregacao logica por ownership em todas as tabelas pessoais (`owner_user` obrigatorio).
- Publicar API dedicada (`/api/v1/personal-finance/...`) com autenticacao obrigatoria e filtro por
  dono em toda consulta/mutacao.
- Nao compartilhar payload pessoal com modulos operacionais; apenas agregados anonimizados quando
  houver necessidade futura de analytics.

## Consequencias
- Positivas:
  - fronteira de dominio clara entre B2B operacional e B2C pessoal.
  - menor risco de vazamento cruzado de dados.
  - evolucao independente da trilha pessoal sem quebrar modulo `finance`.
- Trade-offs:
  - novos modelos/endpoints e custo inicial de implementacao.
  - duplicacao parcial de conceitos financeiros (conta, categoria, lancamento) em dominos distintos.

## Alternativas consideradas
- Reusar tabelas do `finance` com um campo de escopo (`OPERATIONAL`/`PERSONAL`).
- Separar fisicamente em outro banco desde o primeiro MVP.
