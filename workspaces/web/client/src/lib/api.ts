import type { CreatedOrderResponse, MenuDayData, OrderData } from "@/types/api";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";
}

function parseErrorMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  if ("detail" in payload && typeof payload.detail === "string") {
    return payload.detail;
  }

  if ("non_field_errors" in payload && Array.isArray(payload.non_field_errors)) {
    return payload.non_field_errors.map((item) => String(item)).join(" ");
  }

  const messageParts: string[] = [];

  for (const [key, value] of Object.entries(payload)) {
    if (Array.isArray(value)) {
      messageParts.push(`${key}: ${value.map((item) => String(item)).join(" ")}`);
    } else if (typeof value === "string") {
      messageParts.push(`${key}: ${value}`);
    }
  }

  return messageParts.length > 0 ? messageParts.join(" | ") : null;
}

async function requestJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let fallbackMessage = `Erro HTTP ${response.status} ao consultar a API.`;

    try {
      const payload = (await response.json()) as unknown;
      const parsed = parseErrorMessage(payload);
      if (parsed) {
        fallbackMessage = parsed;
      }
    } catch {
      // Mantem mensagem de fallback sem JSON.
    }

    throw new ApiError(fallbackMessage, response.status);
  }

  return (await response.json()) as T;
}

export async function fetchMenuByDate(menuDate: string): Promise<MenuDayData> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new ApiError(
      "Defina NEXT_PUBLIC_API_BASE_URL para consultar o cardapio em tempo real.",
      0,
    );
  }

  const url = `${baseUrl}/api/v1/catalog/menus/by-date/${menuDate}/`;
  return requestJson<MenuDayData>(url, {
    method: "GET",
    cache: "no-store",
  });
}

export async function createOrder(
  deliveryDate: string,
  items: Array<{ menu_item_id: number; qty: number }>,
): Promise<CreatedOrderResponse> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new ApiError(
      "Defina NEXT_PUBLIC_API_BASE_URL para criar pedidos.",
      0,
    );
  }

  return requestJson<CreatedOrderResponse>(`${baseUrl}/api/v1/orders/orders/`, {
    method: "POST",
    body: JSON.stringify({
      delivery_date: deliveryDate,
      items: items.map((item) => ({
        menu_item: item.menu_item_id,
        qty: item.qty,
      })),
    }),
  });
}

export async function listOrders(): Promise<OrderData[]> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new ApiError(
      "Defina NEXT_PUBLIC_API_BASE_URL para consultar pedidos.",
      0,
    );
  }

  return requestJson<OrderData[]>(`${baseUrl}/api/v1/orders/orders/`, {
    method: "GET",
    cache: "no-store",
  });
}

export function getDemoCustomerId(): number | null {
  const raw = process.env.NEXT_PUBLIC_DEMO_CUSTOMER_ID;
  if (!raw) {
    return null;
  }

  const parsed = Number(raw);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null;
  }

  return parsed;
}
