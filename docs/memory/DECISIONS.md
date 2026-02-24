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

## Etapa 5.4 - Producao e consumo de estoque
- Integracao de referencia em estoque para producao:
  - `StockMovement.reference_type = "PRODUCTION"`
  - `StockMovement.reference_id = <production_batch.id>`
- Idempotencia no fechamento do lote:
  - `complete_batch` nao deve gerar novos movimentos se o lote ja estiver `DONE`.
  - se ja houver movimentos `OUT` de referencia `PRODUCTION` para o lote, apenas conclui status e retorna.
- Unidade sem conversao (MVP):
  - consumo de ingrediente em producao exige unidade compativel entre receita (`DishIngredient.unit`) e estoque/ingrediente.
  - ao detectar unidade incompativel, o service retorna `ValidationError` explicita.
  - TODO: implementar conversao de unidades (g<->kg, ml<->l, etc.) em subfase futura.

## Etapa 5.5 - Custos, margem e DRE simplificada
- Base de receita no MVP:
  - a receita dos relatorios (`DRE` e `KPIs`) considera pedidos com status `DELIVERED` no periodo.
- CMV do MVP:
  - calculado como custo estimado dos itens vendidos (`OrderItem.qty * custo_menu_item`).
  - nao usa consumo real de estoque nesta fase.
  - TODO futuro: comparar custo estimado vs custo real (com base em movimentos de producao/estoque).
- Custo de ingrediente:
  - media ponderada por compras (`PurchaseItem`): `sum(qty * unit_price + tax) / sum(qty)`.
- Sem conversao de unidades no MVP:
  - divergencia entre unidade de compra/receita e unidade base do ingrediente gera `ValidationError` explicita.
  - TODO: implementar conversao de unidades (g<->kg, ml<->l, etc.) para custos reais e comparaveis.

## Etapa 5.6.1 - Ledger de auditoria financeira
- Escopo do ledger no MVP:
  - registrar trilha de auditoria financeira orientada a eventos do AP/AR/Caixa.
  - nao substitui contabilidade completa (livro diario/razao) nesta fase.
- Decisao de lancamento por evento:
  - para recebimento de AR, registrar duas entradas: `AR_RECEIVED` e `CASH_IN`.
  - para pagamento de AP, registrar duas entradas: `AP_PAID` e `CASH_OUT`.
  - motivo: manter visao de evento de negocio e evento de caixa separadas para auditoria operacional.
- Idempotencia do ledger:
  - chave unica em (`reference_type`, `reference_id`, `entry_type`).
  - services usam `get_or_create` para reprocessamento seguro sem duplicidade.
- TODO futuro:
  - evoluir para modelo contabil completo com partidas dobradas obrigatorias e fechamento por periodo.

## Etapa 5.6.2 - Conciliacao de caixa (extrato)
- Modelo de conciliacao MVP:
  - conciliacao manual via vinculo `CashMovement.statement_line`.
  - flag `CashMovement.is_reconciled` indica pendencia/conciliado para filtros operacionais.
- Regra de idempotencia:
  - reconciliar o mesmo movimento com a mesma `StatementLine` e operacao idempotente.
  - se o movimento ja estiver conciliado com outra linha, o service retorna erro claro (nao sobrescreve).
- Reconciliacao inversa:
  - `unreconcile_cash_movement` remove vinculo e volta `is_reconciled=false`.
- Relatorio de pendencias:
  - endpoint `reports/unreconciled` retorna apenas movimentos nao conciliados por periodo (`from`/`to`).

## Etapa 5.6.3 - Fechamento por periodo (MVP)
- Escopo de bloqueio no MVP:
  - bloqueio aplicado no service layer (sem trigger no banco nesta etapa).
  - alteracoes em `CashMovement`, `APBill`, `ARReceivable` e `LedgerEntry` sao barradas quando a data relevante estiver em periodo fechado.
- Snapshot no fechamento:
  - `FinancialClose.totals_json` registra totais congelados do periodo no momento do fechamento.
  - totais incluem DRE (`receita_total`, `despesas_total`, `cmv_estimado`, `lucro_bruto`, `resultado`) e caixa (`saldo_caixa_periodo`, `saldo_caixa_final`).
- Regra de duplicidade:
  - nao permitir fechar o mesmo intervalo (`period_start`, `period_end`) duas vezes.
  - comportamento definido: retornar erro de validacao claro no service `close_period`.

## 24/02/2026 - Midia, OCR e dados DEMO ponta a ponta
- Midia (MVP dev):
  - imagens armazenadas em `MEDIA_ROOT` local com `MEDIA_URL=/media/`.
  - uploads expostos por endpoints dedicados (ingrediente, prato, comprovante de compra e OCR job).
  - decisao de nao usar S3/CDN nesta fase; migracao para storage externo fica para fase de deploy/producao.

- OCR (MVP funcional):
  - pipeline com fallback:
    - prioridade para `pytesseract` quando disponivel;
    - fallback para modo simulado com `raw_text` enviado na requisicao.
  - parser MVP extrai campos principais de rotulo e comprovante para `parsed_json`.
  - aplicacao de OCR (`/ocr/jobs/<id>/apply/`) suporta `merge` e `overwrite`.

- Nutricao (MVP):
  - dados em `NutritionFact` por 100g/ml e por porcao opcional.
  - sem conversao de unidades nesta fase; divergencia gera erro claro + TODO.
  - referencia normativa documentada: RDC 429/2020 e IN 75/2020.
  - escopo restrito a dados capturados/estimados + fonte, sem alegacoes nutricionais de marketing.

- Seed DEMO:
  - comando `seed_demo` cobre cadeia completa: catalogo, compras, estoque, producao, pedidos, financeiro e OCR simulado.
  - comportamento idempotente para repeticao em ambiente de desenvolvimento.

- UI compartilhada (portal/client):
  - pacote comum em `workspaces/web/ui` com componentes base e `TemplateProvider`.
  - frontends configurados para usar visual "clean" com tokens da marca.
  - build dos apps web padronizado com `next build --webpack` para compatibilidade com pacote compartilhado local.

## 24/02/2026 - Catalogo publico read-only para smoke/frontends
- Contexto:
  - apos hardening de Auth/RBAC, o smoke do stack e os frontends passaram a receber `401` em `GET /api/v1/catalog/menus/`.
- Decisao MVP:
  - manter RBAC/`IsAuthenticated` como padrao em catalogo.
  - liberar apenas leitura publica minima de cardapio:
    - `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
    - `GET /api/v1/catalog/menus/today/`
- Justificativa:
  - portal/client precisam de consulta publica de cardapio no MVP.
  - nao ha liberacao de CRUD (`ingredients`, `dishes`, `menus` list/create/update/delete) para anonimos.
- Risco controlado:
  - superficie publica limitada somente a leitura de cardapio.
- Opcao futura (nao implementada nesta etapa):
  - smoke autenticado via JWT para cobrir fluxos privados com perfil de teste.

## 24/02/2026 - Politica de branches Codex x Antigravity x Join
- `BRANCH_CODEX_PRIMARY=feature/etapa-4-orders`.
- Codex opera somente em `BRANCH_CODEX_PRIMARY`.
- Antigravity opera somente em `ag/<tipo>/<slug>`.
- Integracao entre agentes ocorre em `join/codex-ag`.
- Guard rail operacional:
  - `scripts/branch_guard.sh` em modo `--strict` antes de checkpoint/sync/merge.
