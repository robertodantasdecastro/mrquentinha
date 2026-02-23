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

> Atualize a cada sprint com o que foi entregue.
