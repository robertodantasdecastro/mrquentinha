# Decisoes vivas do projeto

Use este arquivo para registrar decisoes "em andamento" (menos formais).
Quando uma decisao for definitiva e afetar arquitetura, crie um ADR em `docs/adr/`.

## Padroes definidos
- Backend: Django + DRF
- DB: PostgreSQL
- Sem Docker no MVP
- Mobile: React Native
- Web Gestao: React/Next

## Itens para decidir (aberto)
- Gateway de pagamento (Pix/Cartao/VR)
- OCR (servico externo vs interno)
- Distribuicao iOS (TestFlight/Enterprise)

## Marca
- Nome: Mr Quentinha
- Dominio: www.mrquentinha.com.br
- Cor primaria: #FF6A00
- Assets: assets/brand/

## Pendencias tecnicas (catalogo)
- RBAC do `catalog` ainda esta em modo MVP com `AllowAny` nas views.
- Proxima etapa deve substituir por permissoes por perfil (Admin/Cozinha CRUD, Financeiro leitura e Cliente leitura de cardapio).

## Pendencias tecnicas (inventory/procurement)
- RBAC de `inventory` e `procurement` ainda esta temporario com `AllowAny` no MVP.
- Proxima etapa deve substituir por permissoes por perfil (Admin/Compras/Estoque CRUD, Cozinha criacao de solicitacao e leitura, Financeiro leitura).

## Etapa 3.1 - Geracao de requisicao por cardapio
- Multiplicador de consumo no MVP:
  - se `MenuItem.available_qty` estiver preenchido, usar esse valor para multiplicar os ingredientes da receita.
  - se `available_qty` estiver vazio, considerar `1` lote por prato.
- Conversao de unidade:
  - nao implementar nesta etapa.
  - service valida compatibilidade entre `DishIngredient.unit` e unidade base do ingrediente/estoque.
  - TODO: implementar conversao de unidades (g<->kg, ml<->l, etc.) em etapa futura.

## Decisoes abertas para Etapas 6-8
- Stack do portal institucional (Etapa 6):
  - decidir entre Next.js (SSR/SSG) ou estrutura estatica mais simples.
  - definir nivel de integracao com autenticacao e acesso ao admin.
- Estrategia de web clientes/PWA (Etapa 7):
  - definir escopo minimo do PWA (instalacao, cache, offline parcial, push).
  - definir paridade funcional entre mobile nativo e canal web.
- Segregacao de dados pessoais (Etapa 8):
  - definir separacao logica/fisica entre dados operacionais da empresa e dados pessoais sensiveis.
  - definir politicas de retencao, mascaramento e trilha de auditoria aderentes a LGPD.

## Decisoes abertas para Finance (Etapa 5)
- Padrao de integracao AP/AR/Caixa por referencia:
  - adotar `reference_type` + `reference_id` como contrato unico entre dominios operacionais e financeiro.
  - mapear origens minimas: `PURCHASE` -> AP, `ORDER` -> AR, liquidacao -> Caixa.
- Idempotencia por referencia:
  - definir unique composta por tipo e id de referencia no financeiro para evitar duplicidade de lancamentos.
  - decidir comportamento em reprocessamento (ignorar duplicado vs atualizar registro existente).
- Producao na subfase 5.4:
  - criar app dedicado `production` para consolidar rotina operacional e fechamento diario.
  - decidir fronteira entre `orders`, `inventory` e `production` para evitar sobreposicao de responsabilidades.

## TODO Etapa 5 - AR a partir de Order
- Gerar `finance_ar_receivable` automaticamente a partir de `Order` confirmado.
- Usar referencia padrao:
  - `reference_type = ORDER`
  - `reference_id = <order.id>`
- Definir gatilho exato de criacao no fluxo (ex.: `CONFIRMED` ou `DELIVERED`).

## Etapa 5.0 - padrao financeiro implementado
- Contrato de integracao entre dominios:
  - `reference_type` + `reference_id` como referencia cruzada entre operacional e financeiro.
- Idempotencia em AP/AR:
  - `APBill` e `ARReceivable` com unique por referencia quando preenchida.
  - services retornam registro existente ao receber a mesma referencia.
- Caixa na fundacao:
  - `CashMovement` mantem referencia opcional da origem.
  - services de caixa aplicam idempotencia por referencia (`AR` e `AP`) para evitar duplicidade em reprocessamento.
- Integracoes planejadas para proximas subfases:
  - 5.1: consolidar geracao de AP a partir de `Purchase`.
  - 5.2: consolidar geracao de AR a partir de `Order`/`Payment`.

## Etapa 5.1 - Regra idempotente de AP por compra
- Gatilho de integracao:
  - o service `create_purchase_and_apply_stock` passa a chamar `finance.services.create_ap_from_purchase` ao final da criacao da compra.
- Contrato de referencia para AP de compras:
  - `reference_type = "PURCHASE"`
  - `reference_id = <purchase.id>`
- Idempotencia aplicada em camada de service (antes de depender apenas da constraint):
  - se ja existir `APBill` com a referencia da compra, o service retorna o registro existente.
  - comportamento definido para reprocessamento: nao duplica titulo financeiro.
- Regra de valor do AP (MVP):
  - usar `Purchase.total_amount` quando maior que zero.
  - fallback para soma de itens (`qty * unit_price + tax_amount`) quando total vier zerado.

## Etapa 5.2 - Idempotencia de cash-in por AR
- Integracao `Order -> AR`:
  - todo pedido criado deve gerar (ou reaproveitar) um `ARReceivable` por referencia `ORDER` + `order.id`.
  - conta padrao do AR no MVP: `Vendas` (REVENUE).
- Integracao `Payment PAID -> AR -> Caixa`:
  - ao marcar pagamento como `PAID`, localizar AR pela referencia do pedido.
  - AR deve ser marcado como `RECEIVED`.
  - registrar `CashMovement` de entrada com referencia `AR` + `ar.id`.
  - conta padrao de caixa para entrada: `Caixa/Banco` (ASSET).
- Regra idempotente obrigatoria:
  - se o AR ja estiver recebido e/ou ja existir movimento `IN` referenciado ao AR, nao gerar novo movimento.
  - reprocessamento de pagamento `PAID` deve ser seguro e sem duplicidade financeira.

## Etapa 5.3 - Cashflow (MVP)
- Relatorio de caixa por periodo usa agregacao diaria de `CashMovement`.
- Decisao MVP sobre dias sem movimento:
  - dias sem movimentacao nao sao retornados no endpoint de cashflow.
  - motivo: resposta mais enxuta no MVP, mantendo foco nos dias com evento financeiro.
  - TODO futuro: opcao para preencher dias vazios com zero quando necessario para dashboards.
