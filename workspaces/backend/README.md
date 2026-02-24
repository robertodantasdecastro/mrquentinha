# Backend Mr Quentinha (Django + DRF)

## Estrutura adotada
Foi utilizado o padrao `src/` para manter separacao clara entre codigo da aplicacao e arquivos de infraestrutura:

- `manage.py`: entrada do Django
- `src/config/`: configuracao principal (urls, wsgi/asgi, settings)
- `src/config/settings/`: separacao por ambiente (`dev` e `prod`)
- `src/apps/`: apps de dominio
- `tests/`: testes automatizados de integracao/API

## Apps de dominio criados
- `accounts`
- `catalog`
- `inventory`
- `procurement`
- `orders`
- `production`
- `finance`
- `ocr_ai`

## Requisitos
- Python 3.11+
- PostgreSQL 15+

## Setup local
1. Entrar na pasta do backend:
   ```bash
   cd workspaces/backend
   ```
2. Criar/ativar virtualenv:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Configurar ambiente:
   ```bash
   cp .env.example .env
   ```
5. Ajustar `DATABASE_URL` no `.env` para seu PostgreSQL.

## PostgreSQL para testes (pytest)
O `pytest` com Django cria um banco temporario no padrao `test_<nome_do_banco>`.
Para isso funcionar, o usuario configurado no `DATABASE_URL` precisa da permissao `CREATEDB`.

Comando de ajuste (exemplo com a role `mrq_user`):
```bash
sudo -u postgres psql -c "ALTER ROLE mrq_user CREATEDB;"
```

## Comandos principais
- Verificacao de configuracao Django:
  ```bash
  python manage.py check
  ```
- Criar migracoes:
  ```bash
  python manage.py makemigrations
  ```
- Aplicar migracoes:
  ```bash
  python manage.py migrate
  ```
- Subir servidor local:
  ```bash
  python manage.py runserver
  ```
- Rodar testes:
  ```bash
  pytest
  ```

## Qualidade (ruff + black + pytest)
Com Makefile:

- Lint:
  ```bash
  make lint
  ```
- Testes:
  ```bash
  make test
  ```
- Formatar codigo:
  ```bash
  make format
  ```

## Endpoint de health
- `GET /api/v1/health`
- Resposta esperada:
  ```json
  { "status": "ok", "app": "mrquentinha", "version": "v1" }
  ```

## Catalogo (Etapa 2 - MVP)
### Decisao de API
- Os itens de cardapio foram modelados como recurso embutido no `MenuDay`:
  - escrita via campo `items`
  - leitura via campo `menu_items`
- Nao foi criado endpoint separado para `menu-items` neste MVP.

### Endpoints
- `GET/POST /api/v1/catalog/ingredients/`
- `GET/POST /api/v1/catalog/dishes/`
- `GET/POST /api/v1/catalog/menus/`
- `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`

### Exemplos curl
Criar ingrediente:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/catalog/ingredients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cebola Roxa",
    "unit": "kg",
    "is_active": true
  }'
```

Criar prato com ingredientes:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/catalog/dishes/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Frango Grelhado",
    "description": "Proteina",
    "yield_portions": 10,
    "ingredients": [
      {"ingredient": 1, "quantity": "1.500", "unit": "kg"}
    ]
  }'
```

Criar/atualizar cardapio do dia com itens:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/catalog/menus/ \
  -H "Content-Type: application/json" \
  -d '{
    "menu_date": "2026-02-24",
    "title": "Cardapio de Terca",
    "items": [
      {"dish": 1, "sale_price": "24.90", "available_qty": 30, "is_active": true}
    ]
  }'
```

Consultar cardapio por data:
```bash
curl http://127.0.0.1:8000/api/v1/catalog/menus/by-date/2026-02-24/
```

## Estoque + Compras (Etapa 3 - MVP)
### Endpoints
- `GET/POST /api/v1/inventory/stock-items/`
- `GET/POST /api/v1/inventory/movements/`
- `GET/POST /api/v1/procurement/requests/`
- `GET/POST /api/v1/procurement/purchases/`

### Regras de negocio implementadas
- Movimentacao `OUT` nao permite saldo negativo.
- Movimentacao `IN` incrementa saldo do estoque.
- Ao criar compra (`Purchase` + `PurchaseItem`), o sistema gera `StockMovement` de entrada e atualiza `StockItem`.
- `total_amount` da compra e calculado no service como soma de `(qty * unit_price) + tax_amount`.

### Exemplos curl
Criar movimento de estoque (`IN`):
```bash
curl -X POST http://127.0.0.1:8000/api/v1/inventory/movements/ \
  -H "Content-Type: application/json" \
  -d '{
    "ingredient": 1,
    "movement_type": "IN",
    "qty": "2.500",
    "unit": "kg",
    "reference_type": "ADJUSTMENT",
    "note": "Entrada inicial"
  }'
```

Criar solicitacao de compra:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/procurement/requests/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "OPEN",
    "note": "Reposicao semanal",
    "items": [
      {"ingredient": 1, "required_qty": "5.000", "unit": "kg"}
    ]
  }'
```

Criar compra e aplicar entrada em estoque:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/procurement/purchases/ \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_name": "Atacado Sul",
    "invoice_number": "NF-900",
    "purchase_date": "2026-02-25",
    "items": [
      {
        "ingredient": 1,
        "qty": "4.000",
        "unit": "kg",
        "unit_price": "8.00",
        "tax_amount": "1.20"
      }
    ]
  }'
```

### Auto-requisicao por cardapio (Etapa 3.1)
- `POST /api/v1/procurement/requests/from-menu/`
- Objetivo: gerar `PurchaseRequest` automaticamente a partir de um `MenuDay` e saldo atual de estoque.
- Regra de multiplicador MVP: quando `MenuItem.available_qty` estiver preenchido, ele e usado como multiplicador da receita; quando estiver vazio, o sistema considera `1` lote do prato.
- Permissoes no MVP: `AllowAny` temporario (TODO de RBAC para permitir ao menos COZINHA/COMPRAS/Admin).

Gerar solicitacao de compra automatica por cardapio:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/procurement/requests/from-menu/ \
  -H "Content-Type: application/json" \
  -d '{
    "menu_day_id": 1
  }'
```

## Pedidos (Etapa 4 - MVP)
### Endpoints
- `GET/POST /api/v1/orders/orders/`
- `PATCH /api/v1/orders/orders/<id>/status/`
- `GET /api/v1/orders/payments/`
- `GET/PATCH /api/v1/orders/payments/<id>/`

### Regras de negocio implementadas
- Pedido so pode ser criado para data que possua `MenuDay`.
- Cada `menu_item` do pedido deve pertencer ao cardapio da `delivery_date`.
- `total_amount` do pedido e calculado no service (`sum qty * sale_price`).
- `unit_price` e salvo como snapshot em `OrderItem`.
- Criacao de pedido gera automaticamente `Payment` com status `PENDING` no MVP.
- Transicoes de status centralizadas no service:
  - `CREATED -> CONFIRMED -> IN_PROGRESS -> DELIVERED`
  - `CANCELED` permitido antes de `DELIVERED`.

### Exemplos curl
Criar pedido:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "delivery_date": "2026-03-09",
    "items": [
      {"menu_item": 1, "qty": 2}
    ]
  }'
```

Atualizar status do pedido:
```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/orders/orders/1/status/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "CONFIRMED"
  }'
```

Atualizar status do pagamento:
```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/orders/payments/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "PAID",
    "provider_ref": "pix-abc-123"
  }'
```

Listar pagamentos:
```bash
curl http://127.0.0.1:8000/api/v1/orders/payments/
```

## Financeiro (Etapa 5.0 - Foundation)
### Endpoints
- `GET/POST /api/v1/finance/accounts/`
- `GET/POST /api/v1/finance/ap-bills/`
- `GET/POST /api/v1/finance/ar-receivables/`
- `GET/POST /api/v1/finance/cash-movements/`
- `GET/POST /api/v1/finance/bank-statements/`
- `GET/POST /api/v1/finance/statement-lines/`
- `GET/POST /api/v1/finance/bank-statements/<id>/lines/`
- `POST /api/v1/finance/cash-movements/<id>/reconcile/`
- `POST /api/v1/finance/cash-movements/<id>/unreconcile/`
- `GET /api/v1/finance/ledger/` (read-only no MVP)
- `GET /api/v1/finance/reports/unreconciled/?from=YYYY-MM-DD&to=YYYY-MM-DD`

### Regras base implementadas
- Integracao por referencia com `reference_type` + `reference_id`.
- Unicidade de referencia em AP e AR quando preenchida.
- Services com idempotencia para:
  - `create_ap_from_purchase(...)`
  - `create_ar_from_order(...)`
  - `record_cash_in_from_ar(...)`
  - `record_cash_out_from_ap(...)`
- Compra gera AP automaticamente ao criar `Purchase` via service de procurement, com `reference_type="PURCHASE"` e `reference_id=<purchase.id>`.
- A geracao de AP e idempotente: se a referencia da compra ja existir, o service retorna o titulo existente sem duplicar.
- Pedido gera AR automaticamente na conta de receita `Vendas` com referencia `ORDER`/`order.id`.
- Pagamento com status `PAID` liquida o AR e gera `CashMovement` de entrada na conta `Caixa/Banco` (ASSET), sem duplicar em reprocessamento.
- Ledger de auditoria (Etapa 5.6.1):
  - ao receber AR, registra `AR_RECEIVED` e `CASH_IN`
  - ao pagar AP, registra `AP_PAID` e `CASH_OUT`
- Idempotencia do ledger por (`reference_type`, `reference_id`, `entry_type`), sem duplicar entradas em reprocessamentos.
- Conciliacao de caixa (Etapa 5.6.2):
  - `reconcile_cash_movement` vincula `CashMovement` a `StatementLine` e marca `is_reconciled=true`.
  - reconciliar novamente com a mesma linha e idempotente (sem erro).
  - tentativa de reconciliar com outra linha gera erro claro e exige desconciliacao previa.
  - `unreconcile_cash_movement` remove vinculo e retorna o movimento para pendencia de conciliacao.
- Permissoes temporarias no MVP: `AllowAny` com TODO explicito para RBAC.

### Exemplos curl
Criar conta contabil:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/accounts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vendas",
    "type": "REVENUE",
    "is_active": true
  }'
```

Criar AP com referencia de compra:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/ap-bills/ \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_name": "Fornecedor Centro",
    "account": 1,
    "amount": "150.00",
    "due_date": "2026-03-25",
    "status": "OPEN",
    "reference_type": "PURCHASE",
    "reference_id": 10
  }'
```

Criar AR com referencia de pedido:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/ar-receivables/ \
  -H "Content-Type: application/json" \
  -d '{
    "account": 1,
    "amount": "89.90",
    "due_date": "2026-03-25",
    "status": "OPEN",
    "reference_type": "ORDER",
    "reference_id": 22
  }'
```

Criar movimento de caixa:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/cash-movements/ \
  -H "Content-Type: application/json" \
  -d '{
    "direction": "IN",
    "amount": "89.90",
    "account": 1,
    "reference_type": "PAYMENT",
    "reference_id": 35,
    "note": "Recebimento PIX"
  }'
```

Listar lancamentos de auditoria (ledger):
```bash
curl http://127.0.0.1:8000/api/v1/finance/ledger/
```

Relatorio de cashflow por periodo:
```bash
curl "http://127.0.0.1:8000/api/v1/finance/reports/cashflow/?from=2026-03-01&to=2026-03-07"
```


Relatorio DRE simplificada por periodo:
```bash
curl "http://127.0.0.1:8000/api/v1/finance/reports/dre/?from=2026-04-01&to=2026-04-30"
```

Relatorio de KPIs por periodo:
```bash
curl "http://127.0.0.1:8000/api/v1/finance/reports/kpis/?from=2026-04-01&to=2026-04-30"
```

### Custos, margem e DRE (Etapa 5.5 - MVP)
- Custo do ingrediente: media ponderada por compras (`PurchaseItem`) ate a data de referencia.
- Custo do prato: soma dos ingredientes da receita (`DishIngredient`).
- Custo do `MenuItem`: custo do prato dividido por `yield_portions`.
- Margem: calculada com base em receita - CMV estimado.
- Receita da DRE no MVP: pedidos com status `DELIVERED` no periodo.
- CMV no MVP: custo estimado dos itens vendidos (`OrderItem.qty * custo_menu_item`).
- Limitacao atual: sem conversao de unidades; divergencia de unidade gera erro com TODO explicito.

## Producao (Etapa 5.4 - MVP)
### Decisao de API
- Os itens de producao ficam embutidos no `ProductionBatch` via campo `items` na escrita e `production_items` na leitura.
- Nao foi criado endpoint separado para `production/items` no MVP.

### Endpoints
- `GET/POST /api/v1/production/batches/`
- `POST /api/v1/production/batches/<id>/complete/`

### Regras de negocio implementadas
- Criacao de lote valida existencia de `MenuDay` para a data e se cada `menu_item` pertence ao cardapio do dia.
- Conclusao do lote (`complete`) consome estoque automaticamente com base em `DishIngredient.quantity * qty_produced`.
- Consumo de estoque gera `StockMovement OUT` com referencia `PRODUCTION` + `batch.id`.
- Nao permite saldo negativo (reaproveita validacao do modulo `inventory`).
- Idempotencia na conclusao: se o lote ja estiver `DONE`, nao gera movimentos duplicados.
- Conversao de unidade ainda nao implementada: unidade da receita deve ser compativel com a unidade do ingrediente/estoque (TODO futuro).

### Exemplos curl
Criar lote de producao:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/production/batches/ \
  -H "Content-Type: application/json" \
  -d '{
    "production_date": "2026-03-20",
    "note": "Lote de producao da cozinha",
    "items": [
      {
        "menu_item": 1,
        "qty_planned": 30,
        "qty_produced": 28,
        "qty_waste": 2
      }
    ]
  }'
```

Concluir lote e aplicar consumo de estoque:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/production/batches/1/complete/
```

## Financeiro - Conciliacao de Caixa (Etapa 5.6.2)
### Endpoints
- `GET/POST /api/v1/finance/bank-statements/`
- `GET/POST /api/v1/finance/statement-lines/`
- `GET/POST /api/v1/finance/bank-statements/<id>/lines/`
- `POST /api/v1/finance/cash-movements/<id>/reconcile/`
- `POST /api/v1/finance/cash-movements/<id>/unreconcile/`
- `GET /api/v1/finance/reports/unreconciled/?from=YYYY-MM-DD&to=YYYY-MM-DD`

### Regras de conciliacao (MVP)
- Reconciliar com a mesma `statement_line` e idempotente (nao duplica e nao falha).
- Se o movimento ja estiver conciliado com outra linha, retorna erro claro.
- `unreconcile` remove o vinculo e marca o movimento como pendente (`is_reconciled=false`).

### Exemplos curl
Criar extrato bancario:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/bank-statements/ \
  -H "Content-Type: application/json" \
  -d '{
    "period_start": "2026-08-01",
    "period_end": "2026-08-31",
    "opening_balance": "1000.00",
    "closing_balance": "1200.00",
    "source": "Banco MVP"
  }'
```

Criar linha no extrato:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/bank-statements/1/lines/ \
  -H "Content-Type: application/json" \
  -d '{
    "line_date": "2026-08-05",
    "description": "Credito PIX",
    "amount": "150.00"
  }'
```

Conciliar movimento de caixa:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/cash-movements/1/reconcile/ \
  -H "Content-Type: application/json" \
  -d '{
    "statement_line_id": 10
  }'
```

Desconciliar movimento de caixa:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/cash-movements/1/unreconcile/
```

Relatorio de pendencias de conciliacao:
```bash
curl "http://127.0.0.1:8000/api/v1/finance/reports/unreconciled/?from=2026-08-01&to=2026-08-31"
```

## Financeiro - Fechamento Mensal (Etapa 5.6.3)
### Endpoints
- `GET/POST /api/v1/finance/closes/`
- `GET /api/v1/finance/closes/is-closed/?date=YYYY-MM-DD`

### Regras de fechamento (MVP)
- `close_period(period_start, period_end)` gera snapshot em `totals_json` com:
  - `receita_total`, `despesas_total`, `cmv_estimado`, `lucro_bruto`, `resultado`
  - `saldo_caixa_periodo` e `saldo_caixa_final`
- O mesmo periodo nao pode ser fechado duas vezes.
- Bloqueio por periodo fechado aplicado no service layer para alteracoes em:
  - `CashMovement`
  - `APBill`
  - `ARReceivable`
  - `LedgerEntry`

### Exemplos curl
Fechar periodo:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/finance/closes/ \
  -H "Content-Type: application/json" \
  -d '{
    "period_start": "2026-12-01",
    "period_end": "2026-12-31"
  }'
```

Consultar se uma data esta fechada:
```bash
curl "http://127.0.0.1:8000/api/v1/finance/closes/is-closed/?date=2026-12-15"
```


## Acesso via IP da VM (DEV)
Checklist minimo para acesso via navegador/portal no IP da VM:

1. Ajustar variaveis no `.env`:
```env
ALLOWED_HOSTS=localhost,127.0.0.1,10.211.55.21
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://10.211.55.21:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://10.211.55.21:3000
```
2. Rodar migracoes:
```bash
python manage.py migrate
```
3. Subir servidor em todas as interfaces:
```bash
python manage.py runserver 0.0.0.0:8000
```
4. Validar endpoints base:
```bash
curl http://10.211.55.21:8000/
curl http://10.211.55.21:8000/api/v1/health
```

Notas:
- `ALLOWED_HOSTS` libera os hosts/IPs aceitos pelo Django.
- `CSRF_TRUSTED_ORIGINS` deve conter as origens web confiaveis (portal).
- `CORS_ALLOWED_ORIGINS` libera chamadas cross-origin no ambiente de desenvolvimento.
