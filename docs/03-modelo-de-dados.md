# Modelo de dados (PostgreSQL + Django)

## Convencoes gerais
- Toda tabela tem chave primaria `id` auto-incremental:
  - Django: `BigAutoField` (recomendado)
- Campos padrao recomendados:
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `deleted_at` (timestamp, opcional para soft delete)
- Integridade:
  - FKs com `ON DELETE` coerente (geralmente `PROTECT` para historico financeiro)
- Indices:
  - indices em campos de busca frequente (ex.: `date`, `status`, `user_id`)
  - unique constraints onde faz sentido (ex.: `email`)

> Observacao: para integracoes externas e mobile, e util adicionar tambem um `public_id` (UUID), mas **sem substituir** o `id`.

---

## Nucleo: Usuarios e perfis
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

### `accounts_user_profile`
- `id` (PK)
- `user_id` (FK unique -> accounts_user)
- dados pessoais:
  - `full_name`, `preferred_name`
  - `phone`, `secondary_phone`
  - `birth_date`
  - `cpf`, `cnpj`, `rg`
  - `occupation`
- endereco:
  - `postal_code`, `street`, `street_number`
  - `address_complement`, `neighborhood`
  - `city`, `state`, `country`
- documentos:
  - `document_type` (`CPF`, `CNPJ`, `RG`, `CNH`, `PASSAPORTE`, `OUTRO`)
  - `document_number`, `document_issuer`
  - `document_front_image`, `document_back_image`, `document_selfie_image`
- identidade visual e biometria:
  - `profile_photo`
  - `biometric_photo`
  - `biometric_status` (`NOT_CONFIGURED`, `PENDING_REVIEW`, `VERIFIED`, `REJECTED`)
  - `biometric_captured_at`, `biometric_verified_at`
- complementares:
  - `notes`
  - `extra_data` (JSON)
- auditoria:
  - `created_at`, `updated_at`

### `accounts_customer_governance_profile`
- `id` (PK)
- `user_id` (FK unique -> accounts_user)
- status de conta:
  - `account_status` (`ACTIVE`, `UNDER_REVIEW`, `SUSPENDED`, `BLOCKED`)
  - `account_status_reason`
  - `checkout_blocked`, `checkout_block_reason`
- consentimentos:
  - `terms_accepted_at`
  - `privacy_policy_accepted_at`
  - `marketing_opt_in_at`, `marketing_opt_out_at`
- governanca e compliance:
  - `kyc_review_status` (`PENDING`, `APPROVED`, `REJECTED`)
  - `kyc_review_notes`
  - `lgpd_data_export_last_at`, `lgpd_data_anonymized_at`
  - `reviewed_by_id` (FK user), `reviewed_at`
  - `extra_data` (JSON)
- auditoria:
  - `created_at`, `updated_at`

### `accounts_customer_lgpd_request`
- `id` (PK)
- `customer_id` (FK -> accounts_user)
- `protocol_code` (unique)
- `request_type` (`ACCESS`, `CORRECTION`, `DELETION`, `ANONYMIZATION`, `PORTABILITY`, `REVOCATION`)
- `status` (`OPEN`, `IN_PROGRESS`, `COMPLETED`, `REJECTED`)
- `channel` (`APP`, `WEB`, `EMAIL`, `WHATSAPP`, `PHONE`, `IN_PERSON`)
- `requested_by_name`, `requested_by_email`
- `requested_at`, `due_at`
- `notes`, `request_payload` (JSON)
- `resolution_notes`
- `resolved_at`, `resolved_by_id` (FK user)
- auditoria:
  - `created_at`, `updated_at`

---

## Catalogo / Cardapio
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
- `yield_portions` (quantas porcoes a receita produz)
- `created_at`, `updated_at`

### `catalog_dish_ingredient`
(relacao N:N com quantidade)
- `id` (PK)
- `dish_id` (FK)
- `ingredient_id` (FK)
- `quantity` (decimal)
- `unit` (se precisar converter)

### `catalog_menu_day`
(cardapio por dia)
- `id` (PK)
- `menu_date` (date, index)
- `title`
- `created_by` (FK user)
- `created_at`, `updated_at`

### `catalog_menu_item`
- `id` (PK)
- `menu_day_id` (FK)
- `dish_id` (FK)
- `sale_price` (decimal)
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
- `created_at`, `updated_at`

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

---

## Pedidos (implementado na Etapa 4)
### `orders_order`
- `id` (PK)
- `customer_id` (FK user, null no MVP)
- `order_date` (auto_now_add)
- `delivery_date` (date)
- `status` (CREATED, CONFIRMED, IN_PROGRESS, DELIVERED, CANCELED)
- `total_amount` (decimal)
- `created_at`, `updated_at`

### `orders_order_item`
- `id` (PK)
- `order_id` (FK)
- `menu_item_id` (FK catalog_menu_item)
- `qty` (int)
- `unit_price` (decimal; snapshot)
- `unique(order_id, menu_item_id)`

### `orders_payment`
- `id` (PK)
- `order_id` (FK)
- `method` (PIX, CARD, VR, CASH)
- `status` (PENDING, PAID, FAILED, REFUNDED)
- `amount` (decimal)
- `provider_ref` (texto, opcional)
- `paid_at` (timestamp, opcional)
- `created_at`

Observacao operacional do MVP:
- ao criar `Order`, o sistema cria `Payment` inicial com status `PENDING`;
- o pedido valida `MenuDay` por `delivery_date` e pertencimento de cada `menu_item` ao cardapio do dia.

---

## Financeiro (Etapa 5)
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
- `reference_type` / `reference_id` (origem esperada: `PURCHASE`)

### `finance_ar_receivable` (contas a receber)
- `id` (PK)
- `customer_id` (FK user)
- `account_id` (FK finance_account)
- `amount`
- `due_date`
- `status` (OPEN, RECEIVED, CANCELED)
- `received_at`
- `reference_type` / `reference_id` (origem esperada: `ORDER`)

### `finance_cash_movement`
(fluxo de caixa)
- `id` (PK)
- `movement_date` (timestamp)
- `direction` (IN/OUT)
- `amount`
- `account_id` (FK)
- `note`
- `reference_type` / `reference_id` (ex.: `ORDER`, `PURCHASE`, `AR`, `AP`)

Requisito de integracao entre modulos:
- Finance deve referenciar eventos de **Order** e **Purchase** por `reference_type` + `reference_id`.
- A Etapa 5 deve definir idempotencia por referencia (ex.: unique composta) para impedir duplicidade de lancamentos.

---

## Financas pessoais (Etapas 8.1.1, 8.1.2 e 8.2.2)

### `personal_finance_personalaccount`
- `id` (PK)
- `owner_id` (FK user)
- `name`
- `type` (`CHECKING`, `CASH`, `CARD`, `SAVINGS`)
- `is_active`
- `created_at`, `updated_at`
- unique (`owner_id`, `name`)

### `personal_finance_personalcategory`
- `id` (PK)
- `owner_id` (FK user)
- `name`
- `direction` (`IN`, `OUT`)
- `is_active`
- `created_at`, `updated_at`
- unique (`owner_id`, `name`, `direction`)

### `personal_finance_personalentry`
- `id` (PK)
- `owner_id` (FK user)
- `account_id` (FK personal account)
- `category_id` (FK personal category)
- `recurring_rule_id` (FK opcional para regra recorrente)
- `import_job_id` (FK opcional para job de importacao CSV)
- `direction` (`IN`, `OUT`)
- `amount` (decimal)
- `entry_date` (date)
- `description` (opcional)
- `metadata` (JSON)
- `recurring_event_key` (chave idempotente opcional para materializacao de recorrencia)
- `import_hash` (chave idempotente opcional para importacao CSV)
- `created_at`, `updated_at`
- indice (`owner_id`, `entry_date`)
- indice (`owner_id`, `import_hash`)
- unique (`owner_id`, `recurring_event_key`)
- unique (`owner_id`, `import_hash`)

### `personal_finance_personalbudget`
- `id` (PK)
- `owner_id` (FK user)
- `category_id` (FK personal category)
- `month_ref` (date, normalizado para primeiro dia do mes)
- `limit_amount` (decimal)
- `created_at`, `updated_at`
- unique (`owner_id`, `category_id`, `month_ref`)

### `personal_finance_personalauditlog`
- `id` (PK)
- `owner_id` (FK user)
- `event_type` (`LIST`, `RETRIEVE`, `CREATE`, `UPDATE`, `DELETE`, `EXPORT`)
- `resource_type` (ex.: `ACCOUNT`, `CATEGORY`, `ENTRY`, `BUDGET`, `PERSONAL_DATA_EXPORT`)
- `resource_id` (opcional)
- `metadata` (JSON)
- `created_at`
- indice (`owner_id`, `created_at`)

### `personal_finance_personalrecurringrule`
- `id` (PK)
- `owner_id` (FK user)
- `account_id` (FK personal account)
- `category_id` (FK personal category)
- `direction` (`IN`, `OUT`)
- `amount` (decimal)
- `description` (opcional)
- `metadata` (JSON)
- `frequency` (`WEEKLY`, `MONTHLY`)
- `interval` (inteiro positivo)
- `start_date`, `end_date` (fim opcional)
- `next_run_date`
- `is_active`
- `created_at`, `updated_at`
- indice (`owner_id`, `next_run_date`)

### `personal_finance_personalimportjob`
- `id` (PK)
- `owner_id` (FK user)
- `status` (`PREVIEWED`, `CONFIRMED`, `FAILED`)
- `source_filename`, `delimiter`
- `preview_rows` (JSON), `error_rows` (JSON), `summary` (JSON)
- `rows_total`, `rows_valid`, `rows_invalid`
- `imported_count`, `skipped_count`
- `confirmed_at` (opcional)
- `created_at`, `updated_at`
- indice (`owner_id`, `status`)

Observacao de seguranca:
- todas as consultas/mutacoes do dominio pessoal devem ser filtradas por `owner_id=request.user.id`.
- modulo `finance` operacional e `personal_finance` permanecem segregados por dominio.
- politica de retencao dos logs de auditoria definida em `730` dias com comando operacional de limpeza.
- recorrencia e importacao CSV usam chaves de idempotencia para evitar duplicidade em reprocessamento.

---

## Auditoria administrativa (Web Admin)

### `admin_audit_adminactivitylog`
- `id` (PK)
- `request_id` (UUID, index)
- `actor_id` (FK opcional -> `accounts_user`)
- `actor_username` (snapshot textual do usuario no momento da acao)
- `actor_is_staff`, `actor_is_superuser`
- `channel` (ex.: `web-admin`, `admin-authenticated`)
- `method`, `path`, `query_string`
- `action_group`, `resource`
- `http_status`, `is_success`, `duration_ms`
- `ip_address`, `origin`, `referer`, `user_agent`
- `metadata` (JSON com payload/query sanitizados)
- `created_at`

Indices recomendados/implementados:
- (`-created_at`, `id`)
- (`actor_id`, `-created_at`)
- (`channel`, `-created_at`)
- (`action_group`, `-created_at`)
- (`http_status`, `-created_at`)

Observacao de seguranca:
- dados sensiveis de payload/query (`password`, `token`, `secret`, `authorization`, etc.) sao mascarados antes da persistencia.
- o endpoint de consulta da propria auditoria e excluido da trilha para evitar ruído de auto-registro.

---

## Custos (ligacao entre compras -> ingredientes -> pratos)
No MVP, o calculo pode ser **derivado**:
- custo medio do ingrediente = soma compras / quantidade
- custo do prato = soma (ingrediente_qty * custo_ingrediente)
- custo da marmita = custo_prato / yield_portions

Na fase 2, considerar tabelas de snapshot de custos para auditoria historica.

---

## Portal CMS e release mobile

### `portal_portalconfig` (campos de conectividade)
- `api_base_url` (URL publica principal da API para canais web/mobile)
- `local_hostname`, `local_network_ip`
- `portal_base_url`, `client_base_url`, `admin_base_url`, `backend_base_url`, `proxy_base_url`
- `cors_allowed_origins` (JSON com allowlist por origem)
- `auth_providers` (JSON):
  - `google`: `web_client_id`, `ios_client_id`, `android_client_id`, `client_secret`, `redirect_uri_*`, `scope`
  - `apple`: `service_id`, `team_id`, `key_id`, `private_key`, `redirect_uri_*`, `scope`
- `payment_providers` (JSON):
  - `default_provider`, `enabled_providers`
  - `method_provider_order` (`PIX`, `CARD`, `VR`)
  - `receiver` (`person_type` CPF/CNPJ, `document`, `name`, `email`)
  - credenciais por provider (`mercadopago`, `efi`, `asaas`)

Observacao de seguranca:
- segredos (`client_secret`, `private_key`, `access_token`, `api_key`, `client_secret` da Efi) sao admin-only.
- payload publico do CMS exposto ao client/mobile remove segredos e inclui apenas flags `configured`.

### `portal_mobilerelease`
- `id` (PK)
- `config_id` (FK `portal_portalconfig`)
- `release_version` (ex.: `1.0.0`)
- `build_number` (inteiro positivo)
- `status` (`QUEUED`, `BUILDING`, `TESTING`, `SIGNED`, `PUBLISHED`, `FAILED`)
- `update_policy` (`OPTIONAL`, `FORCE`)
- `is_critical_update` (bool)
- `min_supported_version`, `recommended_version`
- snapshots de ambiente:
  - `api_base_url_snapshot`
  - `host_publico_snapshot`
- links/checksums:
  - `android_download_url`, `ios_download_url`
  - `android_checksum_sha256`, `ios_checksum_sha256`
- metadados:
  - `release_notes`, `build_log`, `metadata` (JSON)
  - `published_at`, `created_by`, `created_at`, `updated_at`
- restricao de unicidade:
  - unique (`config_id`, `release_version`, `build_number`)

Observacao de operacao:
- o canal publico consome a release `PUBLISHED` mais recente para exibir links de download.
- o ciclo MVP de publicacao e controlado pelo Portal CMS (criar -> compilar -> publicar).

---

## Extensoes atuais (midia, OCR e nutricao)

### Mapeamento de imagens (MVP)
- `catalog_ingredient.image` (opcional)
- `catalog_dish.image` (opcional)
- `procurement_purchase.receipt_image` (opcional)
- `procurement_purchase_item.label_front_image` (opcional)
- `procurement_purchase_item.label_back_image` (opcional)

### `ocr_ai_ocr_job`
- `id` (PK)
- `kind` (LABEL_FRONT, LABEL_BACK, RECEIPT)
- `status` (PENDING, PROCESSED, APPLIED, FAILED)
- `image` (arquivo)
- `raw_text` (texto bruto OCR/simulado)
- `parsed_json` (JSON estruturado)
- `error_message` (opcional)
- `created_at`, `updated_at`

### `catalog_nutrition_fact`
(relacao 1:1 com ingrediente)
- `ingredient_id` (FK unique)
- Base por 100g/ml:
  - `energy_kcal_100g`
  - `carbs_g_100g`
  - `protein_g_100g`
  - `fat_g_100g`
  - `sat_fat_g_100g`
  - `fiber_g_100g`
  - `sodium_mg_100g`
- Base por porcao (opcional no MVP):
  - `serving_size_g`
  - `energy_kcal_per_serving`
  - `carbs_g_per_serving`
  - `protein_g_per_serving`
  - `fat_g_per_serving`
  - `sat_fat_g_per_serving`
  - `fiber_g_per_serving`
  - `sodium_mg_per_serving`
- `source` (MANUAL, OCR, ESTIMATED)

### Observacao normativa (Brasil)
A modelagem nutricional do MVP foi preparada para compatibilidade com rotulagem brasileira, com base em:
- **RDC 429/2020**
- **IN 75/2020**

Escopo atual:
- armazenar dados capturados/estimados + fonte (`MANUAL`/`OCR`/`ESTIMATED`);
- nao armazenar promessas nutricionais/alegacoes de marketing no modelo.
