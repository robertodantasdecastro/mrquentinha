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

export type HealthPayload = {
  status?: string;
  service?: string;
  detail?: string;
};

export type OrderStatus =
  | "CREATED"
  | "CONFIRMED"
  | "IN_PROGRESS"
  | "DELIVERED"
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
  unit: "g" | "kg" | "ml" | "l" | "unidade";
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
  unit: "g" | "kg" | "ml" | "l" | "unidade";
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
  unit: "g" | "kg" | "ml" | "l" | "unidade";
  reference_type: "PURCHASE" | "CONSUMPTION" | "ADJUSTMENT" | "PRODUCTION";
  reference_id?: number;
  note?: string;
};
