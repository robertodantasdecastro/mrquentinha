# T8.0.1 - Discovery de Financas Pessoais e Segregacao (LGPD)

Data de referencia: 26/02/2026.
Status: concluida (discovery/documentacao).

## 1) Objetivo do discovery
- Definir fronteira funcional entre financeiro operacional do negocio (B2B interno) e financeiro pessoal (B2C colaborador/usuario).
- Definir estrategia de segregacao de dados pessoais com risco controlado de LGPD.
- Preparar backlog tecnico executavel para `T8.1.1`.

## 2) Escopo aprovado para T8.1.1 (MVP tecnico)
- Criar dominio dedicado `personal_finance` no backend (sem reutilizar tabelas de `finance` operacional).
- Segregacao logica por proprietario (`owner_user`) em todas as entidades pessoais.
- RBAC e ownership estritos:
  - usuario acessa apenas os proprios dados pessoais;
  - perfis internos (ADMIN/FINANCEIRO) nao acessam dados pessoais por padrao.
- API dedicada sob `/api/v1/personal-finance/...` com autenticacao obrigatoria.
- Auditoria minima de acesso/alteracao em dados pessoais sensiveis.

## 3) Fora de escopo (T8.1.1 nao cobre)
- Open finance, integracao bancaria ou importacao OFX/CSV automatica.
- Compartilhamento familiar multiusuario.
- Regras tributarias complexas (IRPF completo).
- App mobile dedicado para pessoal (apenas API e base web/client para MVP tecnico).

## 4) Modelo de segregacao decidido
- Banco unico PostgreSQL (sem novo cluster nesta fase).
- Segregacao por dominio + ownership:
  - `finance` permanece exclusivo da operacao do Mr Quentinha;
  - `personal_finance` atende trilha pessoal.
- Regra obrigatoria:
  - nenhuma tabela operacional (`finance`, `orders`, `procurement`) deve armazenar payload pessoal detalhado.
- Compartilhamento permitido apenas via agregados anonimizados, quando necessario.

## 5) Modelo de dados proposto (T8.1.1)
- `personal_finance_account`
  - `id`, `owner_user_id`, `name`, `type` (`CHECKING`, `CASH`, `CARD`, `SAVINGS`), `is_active`, timestamps.
- `personal_finance_category`
  - `id`, `owner_user_id`, `name`, `direction` (`IN`, `OUT`), `is_active`.
- `personal_finance_entry`
  - `id`, `owner_user_id`, `account_id`, `category_id`, `direction`, `amount`, `entry_date`, `description`, `metadata`, timestamps.
- `personal_finance_budget`
  - `id`, `owner_user_id`, `category_id`, `month_ref`, `limit_amount`, timestamps.
- Indices e constraints:
  - indice por `owner_user_id` em todas as tabelas.
  - unicidade por dono para nomes de conta/categoria.

## 6) Requisitos de seguranca e LGPD
- Base legal e finalidade:
  - coletar apenas dados necessarios para controle financeiro pessoal.
- Minimizacao:
  - nao armazenar documentos sensiveis (CPF, RG, dados bancarios completos) no MVP tecnico.
- Controle de acesso:
  - endpoints pessoais autenticados + filtro obrigatorio por `owner_user=request.user`.
- Retencao:
  - politica inicial de retencao por 24 meses para logs tecnicos; dados financeiros pessoais sem expiracao automatica no MVP.
- Direitos do titular:
  - preparar endpoint de exportacao de dados pessoais para fase seguinte.
- Observabilidade:
  - registrar auditoria de leitura/escrita sem vazar payload sensivel em logs.

## 7) Impacto arquitetural
- Baixo acoplamento com modulos atuais.
- Sem alteracao de schema do modulo `finance` operacional nesta fase.
- Possivel reuso de componentes de relatorio (selectors/services) sem mistura de banco de regras.

## 8) Plano de execucao recomendado (T8.1.1)
1. Criar app `personal_finance` com modelos, migrations e admin basico.
2. Implementar services/selectors com ownership estrito.
3. Publicar endpoints DRF (`accounts`, `categories`, `entries`, `budgets`).
4. Adicionar testes unitarios e API (ownership + validacoes).
5. Expor leitura minima no client web autenticado (modulo inicial).
6. Rodar `bash scripts/quality_gate_all.sh` e atualizar memoria/changelog.

## 9) Criterios de aceite para fechar T8.1.1
- CRUD de contas/categorias/lancamentos pessoais isolado por usuario.
- Nenhum usuario consegue listar/ler/editar dados pessoais de outro usuario.
- Suite de testes cobrindo isolamento de dados.
- Documentacao atualizada (`CHANGELOG`, `PROJECT_STATE`, `ROADMAP_MASTER` e ADR aplicavel).

## 10) Riscos e mitigacoes
- Risco: regressao de seguranca por filtro de ownership ausente.
  - Mitigacao: testes de autorizacao por endpoint + revisao de permissions.
- Risco: confusao de produto entre financeiro operacional e pessoal.
  - Mitigacao: separar menus, rotas e naming desde o backend.
- Risco: aumento de escopo antes da validacao do MVP tecnico.
  - Mitigacao: manter backlog de integracoes externas explicitamente fora de escopo.
