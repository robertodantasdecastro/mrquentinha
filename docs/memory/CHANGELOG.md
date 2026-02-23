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

> Atualize a cada sprint com o que foi entregue.

- Etapa 3.1 auto-requisicao por cardapio:
  - novo service `generate_purchase_request_from_menu(menu_day_id, requested_by=None)` em procurement.
  - calculo de necessidade por ingrediente com base em `MenuDay -> MenuItem -> DishIngredient`.
  - regra MVP de multiplicador: `available_qty` quando informado; caso contrario, `1` lote por prato.
  - validacao explicita de unidade sem conversao automatica (TODO documentado para conversao futura).
  - endpoint DRF adicionado: `POST /api/v1/procurement/requests/from-menu/`.
  - sem falta de ingredientes: retorna `created=false` e nao cria `PurchaseRequest`.
  - testes pytest cobrindo cenarios sem estoque, estoque suficiente, estoque parcial e endpoint HTTP.
