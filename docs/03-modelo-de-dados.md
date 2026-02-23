# Modelo de dados (PostgreSQL + Django)

## Convenções gerais
- Toda tabela tem chave primária `id` auto-incremental:
  - Django: `BigAutoField` (recomendado)
- Campos padrão recomendados:
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `deleted_at` (timestamp, opcional para soft delete)
- Integridade:
  - FKs com `ON DELETE` coerente (geralmente `PROTECT` para histórico financeiro)
- Índices:
  - índices em campos de busca frequente (ex.: `date`, `status`, `user_id`)
  - unique constraints onde faz sentido (ex.: `email`)

> Observação: para integrações externas e mobile, é útil adicionar também um `public_id` (UUID), mas **sem substituir** o `id`. Isso aumenta segurança (evita enumeração).

---

## Núcleo: Usuários e perfis
### `accounts_user`
- `id` (PK)
- `email` (unique)
- `name`
- `phone` (opcional)
- `google_sub` (opcional, unique)
- `is_active`
- `created_at`, `updated_at`

### `accounts_role`
- `id` (PK)
- `name` (unique) — ex.: ADMIN, FINANCEIRO, COZINHA, COMPRAS, CLIENTE

### `accounts_user_role`
- `id` (PK)
- `user_id` (FK)
- `role_id` (FK)

---

## Catálogo / Cardápio
### `catalog_ingredient`
- `id` (PK)
- `name`
- `unit` (ex.: g, kg, ml, l, unidade)
- `is_active`
- `created_at`, `updated_at`

### `catalog_dish`
- `id` (PK)
- `name`
- `description` (opcional)
- `yield_portions` (quantas porções a receita produz)
- `created_at`, `updated_at`

### `catalog_dish_ingredient`
(relação N:N com quantidade)
- `id` (PK)
- `dish_id` (FK)
- `ingredient_id` (FK)
- `quantity` (decimal)
- `unit` (se precisar converter)

### `catalog_menu_day`
(cardápio por dia)
- `id` (PK)
- `menu_date` (date, index)
- `title` (ex.: “Cardápio Segunda”)
- `created_by` (FK user)
- `created_at`, `updated_at`

### `catalog_menu_item`
- `id` (PK)
- `menu_day_id` (FK)
- `dish_id` (FK)
- `sale_price` (decimal) — preço do dia (pode variar)
- `available_qty` (int, opcional)
- `is_active`

---

## Estoque
### `inventory_stock_item`
- `id` (PK)
- `ingredient_id` (FK, unique)
- `balance_qty` (decimal)
- `unit`
- `min_qty` (decimal, opcional)

### `inventory_stock_movement`
- `id` (PK)
- `ingredient_id` (FK)
- `movement_type` (IN/OUT/ADJUST)
- `qty` (decimal)
- `unit`
- `reference_type` (ex.: PURCHASE, CONSUMPTION, ADJUSTMENT)
- `reference_id` (id externo da origem)
- `note` (opcional)
- `created_at`
- `created_by` (FK user)

---

## Compras
### `procurement_purchase_request`
- `id` (PK)
- `requested_by` (FK user)
- `status` (OPEN, APPROVED, BOUGHT, CANCELED)
- `requested_at`
- `note`

### `procurement_purchase_request_item`
- `id` (PK)
- `purchase_request_id` (FK)
- `ingredient_id` (FK)
- `required_qty` (decimal)
- `unit`

### `procurement_purchase`
- `id` (PK)
- `buyer_id` (FK user)
- `supplier_name` (texto no MVP)
- `invoice_number` (opcional)
- `purchase_date` (date)
- `total_amount` (decimal)
- `created_at`, `updated_at`

### `procurement_purchase_item`
- `id` (PK)
- `purchase_id` (FK)
- `ingredient_id` (FK)
- `qty` (decimal)
- `unit`
- `unit_price` (decimal)
- `tax_amount` (decimal, opcional)
- `expiry_date` (opcional)
- `label_images` (links, fase 2)

---

## Pedidos
### `orders_order`
- `id` (PK)
- `customer_id` (FK user)
- `order_date` (timestamp)
- `delivery_date` (date)
- `status` (CREATED, CONFIRMED, IN_PROGRESS, DELIVERED, CANCELED)
- `total_amount` (decimal)

### `orders_order_item`
- `id` (PK)
- `order_id` (FK)
- `menu_item_id` (FK)
- `qty` (int)
- `unit_price` (decimal)

### `orders_payment`
- `id` (PK)
- `order_id` (FK)
- `method` (PIX, CARD, VR, CASH)
- `status` (PENDING, PAID, FAILED, REFUNDED)
- `amount` (decimal)
- `provider_ref` (texto, gateway)
- `paid_at` (opcional)

---

## Financeiro (gestão completa)
### `finance_account`
(plano de contas simplificado)
- `id` (PK)
- `name`
- `type` (REVENUE, EXPENSE, ASSET, LIABILITY)
- `is_active`

### `finance_ap_bill` (contas a pagar)
- `id` (PK)
- `supplier_name`
- `account_id` (FK finance_account)
- `amount` (decimal)
- `due_date` (date)
- `status` (OPEN, PAID, CANCELED)
- `paid_at` (opcional)
- `reference_type` / `reference_id` (ex.: PURCHASE)

### `finance_ar_receivable` (contas a receber)
- `id` (PK)
- `customer_id` (FK user)
- `account_id` (FK finance_account)
- `amount`
- `due_date`
- `status` (OPEN, RECEIVED, CANCELED)
- `received_at`
- `reference_type` / `reference_id` (ex.: ORDER)

### `finance_cash_movement`
(fluxo de caixa)
- `id` (PK)
- `movement_date` (timestamp)
- `direction` (IN/OUT)
- `amount`
- `account_id` (FK)
- `note`
- `reference_type` / `reference_id`

---

## Custos (ligação entre compras → ingredientes → pratos)
No MVP, o cálculo pode ser **derivado**:
- custo médio do ingrediente = soma compras / quantidade
- custo do prato = soma (ingrediente_qty * custo_ingrediente)
- custo da marmita = custo_prato / yield_portions

Na fase 2, considere tabelas de snapshot de custos para auditoria histórica.
