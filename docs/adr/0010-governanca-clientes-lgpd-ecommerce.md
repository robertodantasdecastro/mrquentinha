# ADR 0010 - Governanca de clientes no Web Admin com compliance LGPD

- Status: Aceita
- Data: 27/02/2026

## Contexto
O ecossistema precisava de uma area administrativa unica para operar clientes de ecommerce com foco em:
- manutencao cadastral e documental;
- bloqueio/liberacao de checkout por risco operacional;
- controle de consentimentos e solicitacoes LGPD com rastreabilidade.

Antes desta decisao, os dados de cliente estavam distribuídos e sem trilha operacional especifica para compliance.

## Decisao
1. Criar governanca explicita de cliente no dominio `accounts`:
   - `CustomerGovernanceProfile` (status de conta, bloqueio de checkout, KYC e consentimentos).
   - `CustomerLgpdRequest` (protocolo, tipo, canal, prazo e resolucao).
2. Disponibilizar API administrativa dedicada para ciclo de vida do cliente:
   - listagem/detalhe, edicao de perfil, status, consentimentos, LGPD e reenvio de validacao de e-mail.
3. Integrar regra de elegibilidade de checkout diretamente no fluxo de criacao de pedido (`orders`), bloqueando conta suspensa/bloqueada.
4. Expor modulo completo no Web Admin (`/modulos/clientes`) com visao operacional + compliance.

## Consequencias
- Beneficios:
  - padroniza governanca de cliente no backend e no painel administrativo;
  - melhora aderencia operacional a LGPD no modelo de ecommerce;
  - reduz risco de venda para contas com restricao ativa.
- Trade-offs:
  - aumenta volume de estados de conta que precisam de procedimento operacional claro;
  - exige disciplina de suporte para manter motivos de bloqueio e resolucao LGPD consistentes.

## Implementacao
- Backend:
  - models: `CustomerGovernanceProfile`, `CustomerLgpdRequest`.
  - migration: `accounts.0004_customergovernanceprofile_customerlgpdrequest`.
  - services/selectors/serializers/views dedicados em `apps/accounts`.
  - rotas em `apps/accounts/urls.py`.
  - validacao de checkout no `apps/orders/services.py`.
- Web Admin:
  - painel `CustomersManagementPanel`.
  - hotpage de modulo em `/modulos/clientes` com secoes de gestao, compliance e operacao.
  - navegacao atualizada nos templates AdminKit/AdminDek e catalogo de modulos.

## Testes
- Backend:
  - novos testes de API em `tests/test_customers_admin_api.py`.
  - `python manage.py check` e `python manage.py makemigrations --check`.
- Web Admin:
  - `npm run lint` e `npm run build`.
