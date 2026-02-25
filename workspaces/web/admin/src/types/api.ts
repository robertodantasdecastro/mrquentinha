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

export type IngredientUnit = "g" | "kg" | "ml" | "l" | "unidade";

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
  created_at: string;
  updated_at: string;
};

export type MenuItemData = {
  id: number;
  dish: DishSummaryData;
  sale_price: string;
  available_qty: number | null;
  is_active: boolean;
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

export type PurchaseItemData = {
  id: number;
  ingredient: ProcurementIngredientSummaryData;
  qty: string;
  unit: IngredientUnit;
  unit_price: string;
  tax_amount: string | null;
  expiry_date: string | null;
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

export type ProductionBatchStatus =
  | "PLANNED"
  | "IN_PROGRESS"
  | "DONE"
  | "CANCELED";

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
