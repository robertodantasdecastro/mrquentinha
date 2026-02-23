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
