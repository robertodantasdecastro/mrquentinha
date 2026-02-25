export type DishSummary = {
  id: number;
  name: string;
  yield_portions: number;
  image_url?: string | null;
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
  status: string;
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
  };
  card?: {
    checkout_token?: string;
    requires_redirect?: boolean;
  };
  vr?: {
    authorization_token?: string;
    network?: string;
  };
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
};

export type RegisterPayload = {
  username: string;
  password: string;
  email?: string;
  first_name?: string;
  last_name?: string;
};
