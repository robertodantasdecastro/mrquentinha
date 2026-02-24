# Plano do MVP e cronograma

Data de referencia: 24/02/2026.

## Status atual do roadmap
- Etapa 0: concluida
- Etapa 1: concluida
- Etapa 2: concluida
- Etapa 3 e 3.1: concluida
- Etapa 4: concluida
- Etapa 5.0 a 5.6.3: concluida
- Etapa 6.0 e 6.0.1: concluida
- Etapa 7.0: concluida

## Fechamento do MVP operacional
O MVP operacional foi fechado com o backend cobrindo:
- catalogo
- estoque e compras
- producao
- pedidos
- financeiro completo no escopo MVP (AP/AR/caixa/ledger/conciliacao/fechamento/relatorios)

## Cronograma consolidado (realizado)
- Fase base: Etapas 0 a 2
- Fase operacao: Etapas 3, 3.1 e 4
- Fase financeira: Etapa 5 (5.0 a 5.6.3)
- Fase canais web iniciais: Etapa 6.0/6.0.1 e 7.0

## Proximas fases (planejado)
### 7.1 Auth + RBAC
Dependencias:
- modelo de papeis por modulo consolidado
- estrategia de sessao/token definida para web cliente e gestao
- hardening de permissao nos endpoints hoje com TODO de `AllowAny`

### 7.2 Pagamentos online
Dependencias:
- auth e identificacao de cliente final (7.1)
- escolha de gateway (PIX/cartao/VR)
- politica de reconciliacao financeira com provider (`provider_ref`)

### 6.1 Nginx local e consolidacao de dominios dev
Dependencias:
- stack dev estavel (backend + portal + client)
- definicao de hosts locais e proxy reverso por subdominio
- checklist de CORS/CSRF por ambiente

### 8 Financas pessoais (expansao de produto)
Dependencias:
- operacao B2C estabilizada
- governanca de dados pessoais e segregacao de escopos
- definicao de produto e limites entre financeiro operacional e pessoal

## Regra de execucao continua
Cada nova fase deve manter:
- cobertura de testes automatizados
- idempotencia em integracoes criticas
- documentacao viva (`CHANGELOG`, `DECISIONS`, runbooks)
