export type DishSummary = {
  id: number;
  name: string;
  yield_portions: number;
  image_url?: string | null;
  composition?: DishCompositionItem[];
};

export type DishCompositionItem = {
  id: number;
  quantity: string;
  unit: string;
  ingredient: {
    id: number;
    name: string;
    unit: string;
    image_url?: string | null;
  };
};

export type MenuItemData = {
  id: number;
  dish: DishSummary;
  sale_price: string;
  available_qty: number | null;
  is_active: boolean;
};

export type MenuDayData = {
  id: number;
  menu_date: string;
  title: string;
  menu_items: MenuItemData[];
};

export type OrderItemData = {
  id: number;
  menu_item: number;
  menu_item_name: string;
  qty: number;
  unit_price: string;
};

export type PaymentMethod = "PIX" | "CARD" | "VR" | "CASH";
export type OnlinePaymentMethod = "PIX" | "CARD" | "VR";
export type OrderStatus =
  | "CREATED"
  | "CONFIRMED"
  | "IN_PROGRESS"
  | "OUT_FOR_DELIVERY"
  | "DELIVERED"
  | "RECEIVED"
  | "CANCELED";

export type PaymentSummary = {
  id: number;
  method: PaymentMethod;
  status: string;
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
  payments: PaymentSummary[];
};

export type CreatedOrderResponse = {
  id: number;
  total_amount: string;
  delivery_date: string;
  order_items: OrderItemData[];
  payments: PaymentSummary[];
};

export type PaymentIntentPayload = {
  method: PaymentMethod;
  amount: string;
  currency: string;
  provider: string;
  idempotency_key: string;
  pix?: {
    copy_paste_code?: string;
    qr_code?: string;
    qr_code_base64?: string;
    expiration_date?: string;
  };
  card?: {
    checkout_token?: string;
    requires_redirect?: boolean;
  };
  vr?: {
    authorization_token?: string;
    network?: string;
  };
  checkout_url?: string;
};

export type PaymentIntentStatus =
  | "REQUIRES_ACTION"
  | "PROCESSING"
  | "SUCCEEDED"
  | "FAILED"
  | "CANCELED"
  | "EXPIRED";

export type PaymentIntentData = {
  id: number;
  payment_id: number;
  provider: string;
  status: PaymentIntentStatus;
  idempotency_key: string;
  provider_intent_ref: string | null;
  client_payload: PaymentIntentPayload;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
  idempotent_replay?: boolean;
};

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
  email_verified: boolean;
  email_verified_at?: string | null;
  essential_profile_complete?: boolean;
  missing_essential_profile_fields?: string[];
};

export type RegisterPayload = {
  username: string;
  password: string;
  email: string;
  first_name?: string;
  last_name?: string;
};

export type RegisterAccountResult = {
  id: number;
  username: string;
  email: string;
  roles: string[];
  email_verification_sent: boolean;
  email_verification_detail: string;
};

export type EmailVerificationConfirmResult = {
  detail: string;
  email_verified: boolean;
  username?: string;
};

export type EmailVerificationResendResult = {
  detail: string;
  sent: boolean;
  email: string;
  client_base_url: string;
};

export type PublicGoogleAuthProvider = {
  enabled: boolean;
  configured: boolean;
  web_client_id: string;
  ios_client_id: string;
  android_client_id: string;
  auth_uri: string;
  token_uri: string;
  redirect_uri_web: string;
  redirect_uri_mobile: string;
  scope: string;
};

export type PublicAppleAuthProvider = {
  enabled: boolean;
  configured: boolean;
  service_id: string;
  team_id: string;
  key_id: string;
  auth_uri: string;
  token_uri: string;
  redirect_uri_web: string;
  redirect_uri_mobile: string;
  scope: string;
};

export type PublicAuthProvidersConfig = {
  google: PublicGoogleAuthProvider;
  apple: PublicAppleAuthProvider;
};

export type PublicPaymentProviderStatus = {
  enabled: boolean;
  configured: boolean;
  api_base_url: string;
  sandbox: boolean;
};

export type PublicPaymentProvidersConfig = {
  default_provider: string;
  enabled_providers: string[];
  frontend_provider: {
    web: string;
    mobile: string;
  };
  method_provider_order: {
    PIX: string[];
    CARD: string[];
    VR: string[];
  };
  receiver: {
    person_type: "CPF" | "CNPJ";
    document: string;
    name: string;
    email: string;
  };
  mercadopago: PublicPaymentProviderStatus;
  efi: PublicPaymentProviderStatus;
  asaas: PublicPaymentProviderStatus;
};

export type ClientPortalPublicConfig = {
  active_template: string;
  auth_providers: PublicAuthProvidersConfig;
  payment_providers: PublicPaymentProvidersConfig;
};
