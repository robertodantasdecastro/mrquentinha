# Changelog (por sprint)

## Sprint 0
- Marca oficial definida: Mr Quentinha (assets/brand/)
- Documentacao inicial criada
- Regras do Codex definidas em `AGENTS.md`
- Etapa 0 bootstrap
- Bootstrap valida versoes estaveis de git/python/node/postgres
- Bootstrap usa Node.js LTS como base minima
- Corrigido `scripts/bootstrap_dev_vm.sh`:
  - extracao de versao por comando funcionando
  - versoes minimas ajustadas para baseline realista (Git 2.30, Python 3.11, Node 20, PostgreSQL 15)
  - checklist final sem erro de `printf`
- Etapa 1 scaffold backend:
  - estrutura Django em `workspaces/backend` com padrao `src/`
  - settings por ambiente (`dev` e `prod`) via `.env` com `django-environ`
  - endpoint `GET /api/v1/health` com payload padronizado
  - apps criados: accounts, catalog, inventory, procurement, orders, finance, ocr_ai
  - qualidade configurada com `ruff`, `black` e `pytest` (Makefile com comandos de lint/test)
  - teste automatizado para health endpoint

- Etapa 2 catalogo:
  - dominio `catalog` com modelos: Ingredient, Dish, DishIngredient, MenuDay e MenuItem
  - migrations iniciais do catalog aplicadas
  - service layer em `services.py` para criacao/atualizacao de pratos e cardapio do dia
  - selectors em `selectors.py` para consulta de ingredientes ativos e cardapio por data
  - API DRF em `/api/v1/catalog/...` com endpoint `menus/by-date/<YYYY-MM-DD>/`
  - regra MVP: itens de cardapio embutidos em `MenuDay` (`items` escrita e `menu_items` leitura)
  - testes pytest cobrindo modelos, services, selectors e endpoints de catalog

- Docs/Bootstrap: aviso sobre CREATEDB para testes

- Etapa 2 encerrada:
  - resumo do entregue:
    - CRUD de catalogo (ingredientes, pratos/receitas com composicao e cardapio por dia)
    - endpoint de consulta por data (`/api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`)
    - service layer (`services.py`) e selectors (`selectors.py`) aplicados no dominio
    - testes automatizados cobrindo modelos, services/selectors e endpoints
  - comandos de validacao usados:
    - `python manage.py check`
    - `python manage.py makemigrations --check`
    - `python manage.py migrate`
    - `make lint`
    - `make test`

- Etapa 3 estoque/compras:
  - INVENTORY MVP com `StockItem` e `StockMovement` integrado a `Ingredient`.
  - regras de estoque em service layer (`apply_stock_movement`) com bloqueio de saldo negativo em `OUT`.
  - PROCUREMENT MVP com `PurchaseRequest`, `PurchaseRequestItem`, `Purchase` e `PurchaseItem`.
  - criacao de compra aplica entrada de estoque automaticamente (`StockMovement` tipo `IN`).
  - API DRF adicionada:
    - `/api/v1/inventory/stock-items/`
    - `/api/v1/inventory/movements/`
    - `/api/v1/procurement/requests/`
    - `/api/v1/procurement/purchases/`
  - testes pytest cobrindo regras de estoque, compras com impacto em saldo e endpoints API.

- Etapa 3.1 auto-requisicao por cardapio:
  - novo service `generate_purchase_request_from_menu(menu_day_id, requested_by=None)` em procurement.
  - calculo de necessidade por ingrediente com base em `MenuDay -> MenuItem -> DishIngredient`.
  - regra MVP de multiplicador: `available_qty` quando informado; caso contrario, `1` lote por prato.
  - validacao explicita de unidade sem conversao automatica (TODO documentado para conversao futura).
  - endpoint DRF adicionado: `POST /api/v1/procurement/requests/from-menu/`.
  - sem falta de ingredientes: retorna `created=false` e nao cria `PurchaseRequest`.
  - testes pytest cobrindo cenarios sem estoque, estoque suficiente, estoque parcial e endpoint HTTP.

- Docs: roadmap estendido (Etapas 6-8)
  - visao geral atualizada com ecossistema completo: mobile cliente, web gestao, portal institucional e web clientes.
  - escopo MVP reforcado com fechamento operacional nas etapas 4 e 5.
  - cronograma mantido ate M5 e ampliado com bloco pos-MVP (Etapas 6, 7 e 8) com dependencias.
  - deploy EC2 documentado com estrutura de dominios planejada (`www`, `admin`, `api`, `app`).
  - decisions atualizadas com pendencias de stack do portal, PWA e segregacao de dados pessoais.

> Atualize a cada sprint com o que foi entregue.

- Etapa 4 pedidos:
  - dominio `orders` implementado com modelos `Order`, `OrderItem` e `Payment`.
  - services com regras de negocio para criacao de pedido e transicao de status.
  - validacoes: cardapio por data, `menu_item` da data correta e snapshot de preco no item.
  - criacao automatica de `Payment` com status `PENDING` no MVP.
  - API DRF adicionada:
    - `/api/v1/orders/orders/`
    - `/api/v1/orders/orders/<id>/status/`
    - `/api/v1/orders/payments/`
  - testes pytest cobrindo service e endpoint de criacao de pedido.

- Etapa 4 encerrada:
  - resumo do que foi entregue:
    - modulo `orders` consolidado com `Order`, `OrderItem` e `Payment` no MVP.
    - validacoes de pedido por `MenuDay`/`delivery_date` e bloqueio de itens fora da data.
    - total do pedido calculado no service com snapshot de preco (`unit_price`) em `OrderItem`.
    - transicoes de status centralizadas no service e pagamento inicial `PENDING` criado automaticamente.
    - endpoints publicados para pedidos, alteracao de status e pagamentos.
  - comandos de validacao:
    - `python manage.py check`
    - `python manage.py makemigrations --check`
    - `python manage.py migrate`
    - `make lint`
    - `make test`

- Etapa 5.0 finance foundation:
  - modulo `finance` estruturado com modelos:
    - `Account`
    - `APBill`
    - `ARReceivable`
    - `CashMovement`
  - padrao de integracao por referencia implementado em AP/AR:
    - `reference_type` + `reference_id`
    - unique por referencia quando preenchida
  - service layer em `finance/services.py` com idempotencia:
    - `create_default_chart_of_accounts()`
    - `create_ap_from_purchase()` (stub para integracao completa na 5.1)
    - `create_ar_from_order()` (stub para integracao completa na 5.2)
    - `record_cash_in_from_ar()` e `record_cash_out_from_ap()`
  - API DRF adicionada:
    - `/api/v1/finance/accounts/`
    - `/api/v1/finance/ap-bills/`
    - `/api/v1/finance/ar-receivables/`
    - `/api/v1/finance/cash-movements/`
  - admin basico registrado para os modelos financeiros.
  - testes pytest cobrindo:
    - unicidade de `Account`
    - idempotencia de AP/AR por referencia
    - criacao de movimentos de caixa IN/OUT
    - endpoints basicos de finance

- Etapa 5.1 AP integrado a compras:
  - fluxo de `procurement` atualizado para gerar `APBill` automaticamente ao criar `Purchase`.
  - regra de referencia aplicada no AP: `reference_type="PURCHASE"` e `reference_id=<purchase.id>`.
  - idempotencia reforcada no service financeiro: reprocessamento da mesma compra retorna o AP existente sem duplicar.
  - fallback de valor no AP: quando `Purchase.total_amount` estiver zerado, o valor e calculado pelos itens (`qty * unit_price + tax_amount`).
  - testes de service e API adicionados para validar integracao compra -> AP.

- Etapa 5.2 AR + caixa por pagamento:
  - `orders.create_order` passou a gerar `ARReceivable` automaticamente (referencia `ORDER` + `order.id`).
  - AR criado com conta de receita padrao `Vendas` e vencimento no `delivery_date` do pedido.
  - ao atualizar `Payment` para `PAID`, o fluxo liquida o AR (`RECEIVED`) e gera `CashMovement` `IN`.
  - `CashMovement IN` usa conta patrimonial padrao `Caixa/Banco` (ASSET).
  - idempotencia aplicada em service: reprocessamento de `PAID` nao duplica AR nem movimento de caixa.
  - testes de service e API cobrindo pedido -> AR e pagamento -> caixa.

- Etapa 5.3 relatorio cashflow:
  - criado modulo de relatorios financeiros com `get_cashflow(from_date, to_date)`.
  - novo endpoint `GET /api/v1/finance/reports/cashflow/?from=YYYY-MM-DD&to=YYYY-MM-DD`.
  - retorno por dia com `total_in`, `total_out`, `net` e `running_balance`.
  - validacoes de entrada adicionadas (`from`/`to` obrigatorios e `from <= to`).
  - testes de relatorio e API cobrindo agregacao e saldo acumulado.

- Etapa 5.4 producao + consumo de estoque:
  - novo modulo `production` com modelos `ProductionBatch` e `ProductionItem`.
  - endpoint de lotes de producao publicado em `/api/v1/production/batches/` com acao `POST /<id>/complete/`.
  - conclusao de lote consome ingredientes por receita (`DishIngredient`) e gera `StockMovement` `OUT` com referencia `PRODUCTION`.
  - integracao com `inventory.services.apply_stock_movement` para reaproveitar regra de bloqueio de saldo negativo.
  - idempotencia no fechamento de lote: reprocessamento de `complete_batch` nao duplica movimentos.
  - testes pytest cobrindo criacao de lote, consumo de estoque, bloqueio por saldo insuficiente, idempotencia e endpoint `complete`.

- Etapa 5.5 custos + DRE + KPIs:
  - relatorios financeiros estendidos com custo medio ponderado de ingrediente, custo de prato e custo de item do cardapio.
  - DRE simplificada por periodo adicionada em `/api/v1/finance/reports/dre/`.
  - KPIs financeiros adicionados em `/api/v1/finance/reports/kpis/` (pedidos, ticket medio, margem media, receita, despesas, CMV estimado e lucro bruto).
  - premissa MVP documentada: receita por pedidos `DELIVERED` e CMV estimado por itens vendidos.
  - validacao de parametros `from`/`to` reaproveitada para `cashflow`, `dre` e `kpis`.
  - testes automatizados cobrindo custos, DRE/KPIs e endpoints de relatorio.

- DX: testes no root (Makefile + pytest config)
  - Makefile no root com delegacao para `workspaces/backend` (`test`, `lint`, `format`, `check`).
  - `pytest.ini` no root para executar testes do backend.
  - `conftest.py` no root para garantir `workspaces/backend/src` no `sys.path`.

- Etapa 5.6.1 ledger de auditoria financeira:
  - novo modelo `LedgerEntry` no modulo `finance` para trilha de auditoria financeira.
  - tipos de entrada MVP: `AP_PAID`, `AR_RECEIVED`, `CASH_IN`, `CASH_OUT`, `ADJUSTMENT`.
  - idempotencia por constraint unica em (`reference_type`, `reference_id`, `entry_type`).
  - integracao em services:
    - `record_cash_in_from_ar` registra ledger `AR_RECEIVED` e `CASH_IN`.
    - `record_cash_out_from_ap` registra ledger `AP_PAID` e `CASH_OUT`.
  - endpoint read-only publicado em `/api/v1/finance/ledger/`.
  - testes adicionados para idempotencia de ledger em AR/AP e listagem do endpoint.

- Etapa 5.6.2 conciliacao:
  - modelos adicionados no `finance`: `BankStatement` e `StatementLine`.
  - `CashMovement` estendido com `statement_line` e `is_reconciled`.
  - services de conciliacao criados:
    - `reconcile_cash_movement(cash_movement_id, statement_line_id)`
    - `unreconcile_cash_movement(cash_movement_id)`
  - idempotencia da conciliacao implementada (mesma linha nao duplica nem falha).
  - endpoint de pendencias publicado: `GET /api/v1/finance/reports/unreconciled/?from=...&to=...`.
  - endpoints de conciliacao publicados:
    - `POST /api/v1/finance/cash-movements/<id>/reconcile/`
    - `POST /api/v1/finance/cash-movements/<id>/unreconcile/`

- Etapa 5.6.3 fechamento mensal:
  - novo modelo `FinancialClose` para registrar fechamento por periodo com snapshot em `totals_json`.
  - service `close_period(period_start, period_end, closed_by=None)` para consolidar DRE + cashflow no momento do fechamento.
  - endpoint `POST/GET /api/v1/finance/closes/` publicado para criar e listar fechamentos.
  - endpoint auxiliar `GET /api/v1/finance/closes/is-closed/?date=YYYY-MM-DD` publicado.
  - bloqueio por periodo fechado aplicado no service layer para operacoes de `CashMovement`, `APBill`, `ARReceivable` e `LedgerEntry`.
  - testes de service e API adicionados para fechamento, duplicidade, bloqueios e consulta `is-closed`.

- Etapa 6.0 portal scaffold:
  - criado app `workspaces/web/portal` com Next.js (App Router) + TypeScript + Tailwind.
  - paginas implementadas: `/`, `/cardapio`, `/app`, `/contato`.
  - componentes base implementados: `Header`, `Footer`, `Hero`, `CardapioList`, `QRDownloadCard`.
  - tema light/dark aplicado com tokens da marca (paleta laranja/grafite).
  - integracao de cardapio por data via `NEXT_PUBLIC_API_BASE_URL` em `/api/v1/catalog/menus/by-date/YYYY-MM-DD/`.
  - pagina `/app` com QR Code para `https://www.mrquentinha.com.br/app` e botoes Android/iOS (placeholders documentados).
  - README do portal atualizado com setup local, env vars e build.
  - docs de deploy EC2 atualizadas com nota de deploy do portal via reverse proxy ou build estatico.

- Etapa 6.0.1 hardening portal (dev origins + audit + scripts):
  - `next.config.ts` atualizado com `allowedDevOrigins` para desenvolvimento local/VM.
  - `npm audit fix` executado sem `--force`; vulnerabilidades high restantes documentadas no README do portal.
  - scripts de DX criados no root:
    - `scripts/start_backend_dev.sh`
    - `scripts/start_portal_dev.sh`
  - README do root atualizado com fluxo rapido para subir backend + portal.

- Fix: ALLOWED_HOSTS dev para VM
  - settings carregam `ALLOWED_HOSTS` via env com default local (`localhost`, `127.0.0.1`).
  - adicionado `CSRF_TRUSTED_ORIGINS` via env (default vazio) para ambiente de desenvolvimento.
  - `.env.example` e `README` do backend atualizados com exemplos para acesso via IP da VM.

- DX: stack dev perfeito (API index, CORS, smoke script)
  - backend com endpoint raiz `/` (API index) e rota de `/favicon.ico` para evitar 404 em dev.
  - CORS em dev com `django-cors-headers` e `CORS_ALLOWED_ORIGINS` via `.env` (sem abrir prod).
  - ajustes de docs/env para acesso por IP da VM (`ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`).
  - script `scripts/smoke_stack_dev.sh` criado para validar backend + portal automaticamente.

- Etapa 7.0 web cliente MVP:
  - novo app `workspaces/web/client` com Next.js App Router + TypeScript + Tailwind.
  - layout mobile-first com navbar simples (`Cardapio`, `Meus pedidos`, `Conta`) e tema light/dark.
  - pagina de cardapio com consulta por data em `GET /api/v1/catalog/menus/by-date/YYYY-MM-DD/`.
  - carrinho local com controle de quantidade, total e finalizacao de pedido.
  - criacao de pedidos integrada em `POST /api/v1/orders/orders/`.
  - historico de pedidos em `/pedidos` com filtro demo best-effort no frontend.
  - README do client atualizado com setup, envs e observacoes de integracao.

- DX: start/smoke client + fix lock next dev
  - diagnostico e limpeza de lock/processo do Next no client (`.next/dev/lock`).
  - novo script `scripts/start_client_dev.sh` com:
    - encerramento gracioso de processo antigo na porta `3001` (SIGINT -> SIGTERM);
    - limpeza de lock stale quando nao houver `next dev` ativo;
    - defaults de env para `NEXT_PUBLIC_API_BASE_URL` e `NEXT_PUBLIC_DEMO_CUSTOMER_ID`.
  - novo script `scripts/smoke_client_dev.sh` para subir client em background, validar `/, /pedidos, /cardapio` e encerrar processos ao final.
  - `npm audit fix` executado sem `--force`; pendencias `high` de cadeia `eslint/minimatch` documentadas no README do client.

- DX: smoke_client_dev mais robusto (wait + exit codes)
  - espera ativa com timeout para disponibilidade do client (`/` -> 200) sem ruido de conexao no terminal.
  - falha explicita quando o processo do client encerra antes de subir ou quando estoura timeout.
  - em falha, imprime log do client e retorna exit code diferente de zero.
  - cleanup via trap `EXIT` mantendo encerramento dos processos do Next e limpeza de porta.

- Dynamic e2e (backend + portal + client):
  - backend com suporte de midia (`MEDIA_URL`/`MEDIA_ROOT`) e uploads de imagens para catalogo/procurement.
  - OCR MVP funcional com `OCRJob`, parser de rotulo/comprovante, fallback simulado por `raw_text` e endpoint de aplicacao (`/apply`).
  - modelo nutricional no catalogo com `NutritionFact` por 100g/ml e porcao opcional.
  - comando `seed_demo` cobrindo cadeia completa (catalogo, compras, estoque, producao, pedidos, financeiro e OCR).
  - pacote compartilhado `workspaces/web/ui` e padrao visual clean aplicado em portal/client.
  - portal e client com consumo dinamico da API via `NEXT_PUBLIC_API_BASE_URL`, incluindo imagens de pratos.
  - scripts atualizados para fluxo ponta a ponta (`seed_demo.sh`, `smoke_stack_dev.sh`) e runbook dev publicado.

- Docs/Workflow atualizados:
  - novo `docs/memory/PROJECT_STATE.md` com estado real de portas, scripts, endpoints e envs (sem segredos).
  - novo `docs/memory/RUNBOOK_DEV.md` com operacao completa de dev/seed/smoke/OCR.
  - atualizados `docs/00-visao-geral.md`, `docs/10-plano-mvp-cronograma.md`, `docs/07-workflow-codex.md`, `docs/templates/prompt_codex_base.md`, `docs/03-modelo-de-dados.md` e `docs/memory/DECISIONS.md`.

- Antigravity: regras, workflows e memoria do projeto adicionados
  - criadas regras globais em `.antigravity/rules.md` e espelhos operacionais em `.agent/rules/`.
  - criada memoria ativa versionada em `.agent/memory/` (`MEMORY_INDEX`, `CONTEXT_PACK`, `TODO_NEXT`).
  - criados workflows operacionais em `.agent/workflows/` cobrindo bootstrap, loop diario, backend, frontend, quality gate, docs e release checkpoint.
  - criados prompts base para agentes em `.agent/prompts/` (system, backend, frontend, data seed e bugfix).
  - `docs/memory/PROJECT_STATE.md` e `docs/memory/RUNBOOK_DEV.md` atualizados com estado real, quickstart, smoke e troubleshooting.

- Antigravity: workflows adicionais de sessao, bugfix, refactor, QA, PR e release
  - adicionados workflows W10-W20 para lifecycle completo de trabalho.
  - criado `SESSION_COMMANDS.md` com macros operacionais para iniciar/continuar/salvar/corrigir/auditar/release.
  - adicionados templates de prompts para sessao, bugfix, refactor, quality e docs.
  - memoria `.agent/memory` atualizada com index de workflows e contexto operacional vigente.

- Docs: GLOBAL_RULE Antigravity + guia de uso de workflows
  - adicionada regra-mae em `.antigravity/GLOBAL_RULE.md` com mapa do repo, padroes e politica de segredos.
  - adicionados guias `.agent/workflows/USAGE_GUIDE.md` e `.agent/workflows/WORKFLOW_MAP.md`.
  - atualizados `SESSION_COMMANDS`, `CONTEXT_PACK` e `PROJECT_STATE` para refletir o estado atual.
  - criado helper `scripts/session.sh` para atalhos `start`, `continue`, `save` e `qa`.
