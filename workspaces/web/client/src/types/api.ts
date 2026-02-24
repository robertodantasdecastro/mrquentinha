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

export type PaymentSummary = {
  id: number;
  method: string;
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
};
