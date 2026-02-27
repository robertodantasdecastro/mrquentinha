export type AuthTokens = {
  access: string;
  refresh: string;
};

export type AuthUserProfile = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
  email_verified?: boolean;
  email_verified_at?: string | null;
  essential_profile_complete?: boolean;
  missing_essential_profile_fields?: string[];
};

export type UserDocumentType =
  | ""
  | "CPF"
  | "CNPJ"
  | "RG"
  | "CNH"
  | "PASSAPORTE"
  | "OUTRO";

export type UserBiometricStatus =
  | "NOT_CONFIGURED"
  | "PENDING_REVIEW"
  | "VERIFIED"
  | "REJECTED";

export type UserProfileData = {
  id: number;
  user: number;
  full_name: string;
  preferred_name: string;
  phone: string;
  secondary_phone: string;
  birth_date: string | null;
  cpf: string;
  cnpj: string;
  rg: string;
  occupation: string;
  postal_code: string;
  street: string;
  street_number: string;
  address_complement: string;
  neighborhood: string;
  city: string;
  state: string;
  country: string;
  document_type: UserDocumentType;
  document_number: string;
  document_issuer: string;
  profile_photo_url: string | null;
  document_front_image_url: string | null;
  document_back_image_url: string | null;
  document_selfie_image_url: string | null;
  biometric_photo_url: string | null;
  biometric_status: UserBiometricStatus;
  biometric_captured_at: string | null;
  biometric_verified_at: string | null;
  notes: string;
  extra_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type UpdateUserProfilePayload = Partial<
  Pick<
    UserProfileData,
    | "full_name"
    | "preferred_name"
    | "phone"
    | "secondary_phone"
    | "birth_date"
    | "cpf"
    | "cnpj"
    | "rg"
    | "occupation"
    | "postal_code"
    | "street"
    | "street_number"
    | "address_complement"
    | "neighborhood"
    | "city"
    | "state"
    | "country"
    | "document_type"
    | "document_number"
    | "document_issuer"
    | "notes"
    | "extra_data"
  >
>;

export type RoleData = {
  id: number;
  code: string;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AdminUserData = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
  roles: string[];
  email_verified: boolean;
  email_verified_at: string | null;
  email_verification_last_sent_at: string | null;
  essential_profile_complete: boolean;
  missing_essential_profile_fields: string[];
};

export type AssignUserRolesPayload = {
  role_codes: string[];
  replace?: boolean;
};

export type AssignUserRolesResultData = {
  user_id: number;
  username: string;
  role_codes: string[];
};

export type HealthPayload = {
  status?: string;
  service?: string;
  detail?: string;
};

export type IngredientUnit = "g" | "kg" | "ml" | "l" | "unidade";

export type OrderStatus =
  | "CREATED"
  | "CONFIRMED"
  | "IN_PROGRESS"
  | "OUT_FOR_DELIVERY"
  | "DELIVERED"
  | "RECEIVED"
  | "CANCELED";

export type OrderItemData = {
  id: number;
  menu_item: number;
  menu_item_name: string;
  qty: number;
  unit_price: string;
};

export type PaymentSummaryData = {
  id: number;
  method: "PIX" | "CARD" | "VR" | "CASH";
  status: "PENDING" | "PAID" | "FAILED" | "REFUNDED";
  amount: string;
  provider_ref: string | null;
  paid_at: string | null;
};

export type OrderData = {
  id: number;
  customer: number | null;
  order_date: string;
  delivery_date: string;
  status: OrderStatus;
  total_amount: string;
  created_at: string;
  updated_at: string;
  order_items: OrderItemData[];
  payments: PaymentSummaryData[];
};

export type FinanceKpisPayload = {
  from: string;
  to: string;
  kpis: {
    pedidos: number;
    receita_total: string;
    despesas_total: string;
    cmv_estimado: string;
    lucro_bruto: string;
    ticket_medio: string;
    margem_media: string;
  };
};

export type FinanceCashflowItem = {
  date: string;
  total_in: string;
  total_out: string;
  net: string;
  running_balance: string;
};

export type FinanceCashflowPayload = {
  from: string;
  to: string;
  items: FinanceCashflowItem[];
};

export type FinanceDrePayload = {
  from: string;
  to: string;
  dre: {
    receita_total: string;
    despesas_total: string;
    cmv_estimado: string;
    lucro_bruto: string;
    resultado: string;
  };
};

export type CashMovementData = {
  id: number;
  movement_date: string;
  direction: "IN" | "OUT";
  amount: string;
  account: number;
  note: string | null;
  reference_type: string | null;
  reference_id: number | null;
  statement_line: number | null;
  is_reconciled: boolean;
  created_at: string;
};

export type FinanceUnreconciledPayload = {
  from: string;
  to: string;
  items: CashMovementData[];
};

export type StockItemData = {
  id: number;
  ingredient: number;
  ingredient_name: string;
  balance_qty: string;
  unit: IngredientUnit;
  min_qty: string | null;
  created_at: string;
  updated_at: string;
};

export type StockMovementData = {
  id: number;
  ingredient: number;
  ingredient_name: string;
  movement_type: "IN" | "OUT" | "ADJUST";
  qty: string;
  unit: IngredientUnit;
  reference_type: "PURCHASE" | "CONSUMPTION" | "ADJUSTMENT" | "PRODUCTION";
  reference_id: number | null;
  note: string | null;
  created_by: number | null;
  created_at: string;
};

export type CreateStockMovementPayload = {
  ingredient: number;
  movement_type: "IN" | "OUT" | "ADJUST";
  qty: string;
  unit: IngredientUnit;
  reference_type: "PURCHASE" | "CONSUMPTION" | "ADJUSTMENT" | "PRODUCTION";
  reference_id?: number;
  note?: string;
};

export type DishSummaryData = {
  id: number;
  name: string;
  yield_portions: number;
  image_url: string | null;
};

export type DishData = {
  id: number;
  name: string;
  description: string | null;
  yield_portions: number;
  image_url: string | null;
  composition?: DishCompositionItemData[];
  created_at: string;
  updated_at: string;
};

export type DishCompositionItemData = {
  id: number;
  ingredient: ProcurementIngredientSummaryData;
  quantity: string;
  unit: string;
};

export type DishCompositionItemWritePayload = {
  ingredient: number;
  quantity: string;
  unit?: string;
};

export type CreateDishPayload = {
  name: string;
  description?: string;
  yield_portions: number;
  ingredients: DishCompositionItemWritePayload[];
};

export type UpdateDishPayload = Partial<CreateDishPayload>;

export type IngredientData = {
  id: number;
  name: string;
  unit: IngredientUnit;
  is_active: boolean;
  image_url: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateIngredientPayload = {
  name: string;
  unit: IngredientUnit;
  is_active?: boolean;
};

export type UpdateIngredientPayload = Partial<CreateIngredientPayload>;

export type MenuItemData = {
  id: number;
  dish: DishSummaryData;
  sale_price: string;
  available_qty: number | null;
  is_active: boolean;
};

export type MenuItemWritePayload = {
  dish: number;
  sale_price: string;
  available_qty?: number | null;
  is_active?: boolean;
};

export type UpsertMenuDayPayload = {
  menu_date: string;
  title: string;
  items: MenuItemWritePayload[];
};

export type MenuDayData = {
  id: number;
  menu_date: string;
  title: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  menu_items: MenuItemData[];
};

export type ProcurementRequestStatus =
  | "OPEN"
  | "APPROVED"
  | "BOUGHT"
  | "CANCELED";

export type ProcurementIngredientSummaryData = {
  id: number;
  name: string;
  unit: IngredientUnit;
  image_url: string | null;
};

export type PurchaseRequestItemData = {
  id: number;
  ingredient: ProcurementIngredientSummaryData;
  required_qty: string;
  unit: IngredientUnit;
};

export type PurchaseRequestData = {
  id: number;
  requested_by: number | null;
  status: ProcurementRequestStatus;
  requested_at: string;
  note: string | null;
  request_items: PurchaseRequestItemData[];
};

export type PurchaseRequestFromMenuItemData = {
  ingredient_id: number;
  ingredient_name: string;
  required_qty: string;
  unit: IngredientUnit;
};

export type PurchaseRequestFromMenuResultData = {
  created: boolean;
  purchase_request_id: number | null;
  message: string;
  items: PurchaseRequestFromMenuItemData[];
  alerts?: {
    email?: {
      configured?: boolean;
      sent_count?: number;
      recipients?: string[];
    };
    whatsapp?: {
      configured?: boolean;
      sent?: boolean;
      error?: string | null;
    };
  };
};

export type OpsPipelineStageData = {
  stage: string;
  count: number;
  status: "ok" | "warning" | "info" | "neutral";
  detail: string;
  path: string;
};

export type OpsAlertData = {
  level: "warning" | "info" | "danger";
  title: string;
  detail: string;
  path: string;
};

export type OrdersOpsDashboardData = {
  generated_at: string;
  kpis: {
    menus_hoje: number;
    requisicoes_abertas: number;
    requisicoes_aprovadas: number;
    compras_hoje: number;
    lotes_planejados: number;
    lotes_em_progresso: number;
    lotes_concluidos: number;
    pedidos_hoje: number;
    pedidos_fila: number;
    pedidos_entregues: number;
    pedidos_recebidos: number;
    receita_hoje: string;
  };
  pipeline: OpsPipelineStageData[];
  alerts: OpsAlertData[];
  series_last_7_days: Array<{
    date: string;
    orders: number;
    revenue: string;
    deliveries: number;
  }>;
};

export type EcosystemServiceMonitorData = {
  key: string;
  name: string;
  port: number | null;
  status: "online" | "running" | "offline";
  pid: number | null;
  uptime_seconds: number | null;
  rss_mb: number | null;
  listener_ok: boolean;
};

export type PaymentProviderRealtimeData = {
  provider: string;
  enabled: boolean;
  configured: boolean;
  sync_status: "ok" | "warning" | "danger" | "neutral";
  intents_24h: number;
  webhooks_24h: number;
  webhooks_failed_24h: number;
  success_rate_24h: number;
  last_event_at: string | null;
};

export type EcosystemOpsRealtimeData = {
  generated_at: string;
  server_health: {
    uptime_seconds: number;
    cpu_count: number;
    load_avg_1m: number;
    load_avg_5m: number;
    load_avg_15m: number;
    memory: {
      total_mb: number;
      available_mb: number;
      used_mb: number;
      used_percent: number;
    };
    disk: {
      total_gb: number;
      used_gb: number;
      free_gb: number;
      used_percent: number;
    };
  };
  services: EcosystemServiceMonitorData[];
  payment_monitor: {
    communication_channel: {
      transport: string;
      auth: string;
      encryption: string;
    };
    frontend_provider: {
      web: string;
      mobile: string;
    };
    summary: {
      payments_pending: number;
      payments_paid: number;
      payments_failed: number;
      intents_active: number;
      intents_processing: number;
      webhooks_last_15m: number;
    };
    providers: PaymentProviderRealtimeData[];
    order_lifecycle: {
      created: number;
      confirmed: number;
      in_progress: number;
      out_for_delivery: number;
      delivered: number;
      received: number;
      canceled: number;
    };
    series_last_15_minutes: Array<{
      minute: string;
      orders_created: number;
      payments_paid: number;
      webhooks_received: number;
    }>;
  };
};

export type PurchaseItemData = {
  id: number;
  ingredient: ProcurementIngredientSummaryData;
  qty: string;
  unit: IngredientUnit;
  unit_price: string;
  tax_amount: string | null;
  expiry_date: string | null;
  label_front_image_url?: string | null;
  label_back_image_url?: string | null;
};

export type PurchaseData = {
  id: number;
  buyer: number | null;
  supplier_name: string;
  invoice_number: string | null;
  purchase_date: string;
  total_amount: string;
  receipt_image_url: string | null;
  created_at: string;
  updated_at: string;
  purchase_items: PurchaseItemData[];
};

export type CreatePurchaseItemPayload = {
  ingredient: number;
  qty: string;
  unit: IngredientUnit;
  unit_price: string;
  tax_amount?: string;
};

export type CreatePurchasePayload = {
  supplier_name: string;
  invoice_number?: string;
  purchase_date: string;
  items: CreatePurchaseItemPayload[];
};

export type OcrKind = "LABEL_FRONT" | "LABEL_BACK" | "RECEIPT";

export type OcrJobStatus = "PENDING" | "PROCESSED" | "APPLIED" | "FAILED";

export type OcrJobData = {
  id: number;
  kind: OcrKind;
  status: OcrJobStatus;
  image_url: string | null;
  raw_text: string | null;
  parsed_json: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type ApplyOcrPayload = {
  target_type: "INGREDIENT" | "PURCHASE_ITEM" | "PURCHASE";
  target_id: number;
  mode: "overwrite" | "merge";
};

export type ApplyOcrResultData = {
  job_id: number;
  status: OcrJobStatus;
  target_type: "INGREDIENT" | "PURCHASE_ITEM" | "PURCHASE";
  target_id: number;
  nutrition_fact_id?: number;
  saved_image_field?: string | null;
};

export type ProductionBatchStatus =
  | "PLANNED"
  | "IN_PROGRESS"
  | "DONE"
  | "CANCELED";

export type ProductionItemWritePayload = {
  menu_item: number;
  qty_planned: number;
  qty_produced?: number;
  qty_waste?: number;
  note?: string;
};

export type CreateProductionBatchPayload = {
  production_date: string;
  note?: string;
  items: ProductionItemWritePayload[];
};

export type ProductionItemData = {
  id: number;
  menu_item: number;
  menu_item_name: string;
  qty_planned: number;
  qty_produced: number;
  qty_waste: number;
  note: string | null;
};

export type ProductionBatchData = {
  id: number;
  production_date: string;
  status: ProductionBatchStatus;
  note: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  production_items: ProductionItemData[];
};

export type PortalTemplateData = {
  id: string;
  label?: string;
};

export type PortalGoogleAuthConfig = {
  enabled: boolean;
  web_client_id: string;
  ios_client_id: string;
  android_client_id: string;
  client_secret: string;
  auth_uri: string;
  token_uri: string;
  redirect_uri_web: string;
  redirect_uri_mobile: string;
  scope: string;
};

export type PortalAppleAuthConfig = {
  enabled: boolean;
  service_id: string;
  team_id: string;
  key_id: string;
  private_key: string;
  auth_uri: string;
  token_uri: string;
  redirect_uri_web: string;
  redirect_uri_mobile: string;
  scope: string;
};

export type PortalAuthProvidersConfig = {
  google: PortalGoogleAuthConfig;
  apple: PortalAppleAuthConfig;
};

export type PortalPaymentReceiverConfig = {
  person_type: "CPF" | "CNPJ";
  document: string;
  name: string;
  email: string;
};

export type PortalPaymentProviderRouting = {
  PIX: string[];
  CARD: string[];
  VR: string[];
};

export type PortalMercadoPagoConfig = {
  enabled: boolean;
  api_base_url: string;
  access_token: string;
  webhook_secret: string;
  sandbox: boolean;
};

export type PortalEfiConfig = {
  enabled: boolean;
  api_base_url: string;
  client_id: string;
  client_secret: string;
  webhook_secret: string;
  sandbox: boolean;
};

export type PortalAsaasConfig = {
  enabled: boolean;
  api_base_url: string;
  api_key: string;
  webhook_secret: string;
  sandbox: boolean;
};

export type PortalPaymentProvidersConfig = {
  default_provider: string;
  enabled_providers: string[];
  frontend_provider: {
    web: string;
    mobile: string;
  };
  method_provider_order: PortalPaymentProviderRouting;
  receiver: PortalPaymentReceiverConfig;
  mercadopago: PortalMercadoPagoConfig;
  efi: PortalEfiConfig;
  asaas: PortalAsaasConfig;
};

export type PortalPaymentProviderTestResult = {
  provider: string;
  ok: boolean;
  detail: string;
};

export type PortalCloudflareMode = "local_only" | "cloudflare_only" | "hybrid";

export type PortalCloudflareSubdomains = {
  portal: string;
  client: string;
  admin: string;
  api: string;
};

export type PortalCloudflareRuntime = {
  state: string;
  last_started_at: string;
  last_stopped_at: string;
  last_error: string;
  run_command: string;
};

export type PortalCloudflareDevUrls = {
  portal: string;
  client: string;
  admin: string;
  api: string;
};

export type PortalCloudflareConfig = {
  enabled: boolean;
  mode: PortalCloudflareMode;
  dev_mode: boolean;
  scheme: "http" | "https";
  root_domain: string;
  subdomains: PortalCloudflareSubdomains;
  tunnel_name: string;
  tunnel_id: string;
  tunnel_token: string;
  account_id: string;
  zone_id: string;
  api_token: string;
  auto_apply_routes: boolean;
  last_action_at: string;
  last_status_message: string;
  runtime: PortalCloudflareRuntime;
  dev_urls: PortalCloudflareDevUrls;
  local_snapshot: Record<string, unknown>;
};

export type PortalCloudflarePreviewData = {
  mode: PortalCloudflareMode;
  dev_mode?: boolean;
  scheme: string;
  root_domain: string;
  domains: {
    portal: string;
    client: string;
    admin: string;
    api: string;
  };
  urls: {
    portal_base_url: string;
    client_base_url: string;
    admin_base_url: string;
    api_base_url: string;
    backend_base_url: string;
  };
  cors_allowed_origins: string[];
  tunnel: {
    name: string;
    id: string;
    configured: boolean;
    run_command: string;
  };
  ingress_rules: string[];
  coexistence_note: string;
  generated_at: string;
};

export type PortalCloudflareToggleResult = {
  config: PortalConfigData;
  preview: PortalCloudflarePreviewData;
  enabled: boolean;
};

export type PortalCloudflareRuntimeData = {
  state: string;
  pid: number | null;
  log_file: string;
  last_started_at: string;
  last_stopped_at: string;
  last_error: string;
  run_command: string;
  last_log_lines: string[];
  dev_mode?: boolean;
  dev_urls?: PortalCloudflareDevUrls;
  dev_services?: Array<{
    key: string;
    name: string;
    port: number;
    pid: number | null;
    url: string;
    log_file: string;
    running: boolean;
    connectivity?: "online" | "offline" | "unknown";
    http_status?: number | null;
    latency_ms?: number | null;
    checked_url?: string;
    checked_at?: string;
    error?: string;
  }>;
};

export type PortalCloudflareRuntimeResult = {
  config: PortalConfigData;
  runtime: PortalCloudflareRuntimeData;
  action: "start" | "stop" | "status" | "refresh";
};

export type PortalConfigData = {
  id: number;
  active_template: string;
  available_templates: Array<PortalTemplateData | string>;
  client_active_template: string;
  client_available_templates: Array<PortalTemplateData | string>;
  admin_active_template: string;
  admin_available_templates: Array<PortalTemplateData | string>;
  site_name: string;
  site_title: string;
  meta_description: string;
  primary_color: string;
  secondary_color: string;
  dark_bg_color: string;
  android_download_url: string;
  ios_download_url: string;
  qr_target_url: string;
  api_base_url: string;
  local_hostname: string;
  local_network_ip: string;
  root_domain: string;
  portal_domain: string;
  client_domain: string;
  admin_domain: string;
  api_domain: string;
  portal_base_url: string;
  client_base_url: string;
  admin_base_url: string;
  backend_base_url: string;
  proxy_base_url: string;
  cors_allowed_origins: string[];
  cloudflare_settings: PortalCloudflareConfig;
  auth_providers: PortalAuthProvidersConfig;
  payment_providers: PortalPaymentProvidersConfig;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type PortalConfigWritePayload = Partial<
  Pick<
    PortalConfigData,
    | "active_template"
    | "available_templates"
    | "client_active_template"
    | "client_available_templates"
    | "admin_active_template"
    | "admin_available_templates"
    | "local_hostname"
    | "local_network_ip"
    | "root_domain"
    | "portal_domain"
    | "client_domain"
    | "admin_domain"
    | "api_domain"
    | "portal_base_url"
    | "client_base_url"
    | "admin_base_url"
    | "backend_base_url"
    | "proxy_base_url"
    | "cors_allowed_origins"
    | "cloudflare_settings"
    | "api_base_url"
    | "auth_providers"
    | "payment_providers"
  >
>;

export type MobileReleaseStatus =
  | "QUEUED"
  | "BUILDING"
  | "TESTING"
  | "SIGNED"
  | "PUBLISHED"
  | "FAILED";

export type MobileReleaseUpdatePolicy = "OPTIONAL" | "FORCE";

export type MobileReleaseData = {
  id: number;
  config: number;
  release_version: string;
  build_number: number;
  status: MobileReleaseStatus;
  update_policy: MobileReleaseUpdatePolicy;
  is_critical_update: boolean;
  min_supported_version: string;
  recommended_version: string;
  api_base_url_snapshot: string;
  host_publico_snapshot: string;
  android_relative_path: string;
  ios_relative_path: string;
  android_download_url: string;
  ios_download_url: string;
  android_checksum_sha256: string;
  ios_checksum_sha256: string;
  release_notes: string;
  build_log: string;
  metadata: Record<string, unknown>;
  published_at: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export type CreateMobileReleasePayload = {
  config: number;
  release_version: string;
  build_number: number;
  update_policy?: MobileReleaseUpdatePolicy;
  is_critical_update?: boolean;
  min_supported_version?: string;
  recommended_version?: string;
  release_notes?: string;
};

export type PortalSectionData = {
  id: number;
  config: number;
  template_id: string;
  page: string;
  key: string;
  title: string;
  body_json: unknown;
  is_enabled: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type PortalSectionWritePayload = Partial<
  Pick<PortalSectionData, "title" | "is_enabled" | "sort_order"> & {
    body_json: unknown;
  }
>;
