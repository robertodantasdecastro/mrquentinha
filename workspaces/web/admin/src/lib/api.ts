import {
  clearAuthTokens,
  getStoredAccessToken,
  getStoredAuthTokens,
  persistAuthTokens,
} from "@/lib/storage";
import type {
  AuthTokens,
  AuthUserProfile,
  CreateStockMovementPayload,
  FinanceKpisPayload,
  FinanceUnreconciledPayload,
  HealthPayload,
  OrderData,
  OrderStatus,
  StockItemData,
  StockMovementData,
} from "@/types/api";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RequestJsonOptions = Omit<RequestInit, "body"> & {
  body?: string;
  auth?: boolean;
  allowAuthRetry?: boolean;
};

type JsonObject = Record<string, unknown>;

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";
}

function resolveUrl(path: string): string {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new ApiError("Defina NEXT_PUBLIC_API_BASE_URL para conectar no backend.", 0);
  }

  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}

function normalizeListPayload<T>(payload: T[] | { results?: T[] }): T[] {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (Array.isArray(payload.results)) {
    return payload.results;
  }

  return [];
}

async function parseJsonBody<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  return JSON.parse(text) as T;
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

  const parts: string[] = [];
  for (const [key, value] of Object.entries(payload)) {
    if (Array.isArray(value)) {
      parts.push(`${key}: ${value.map((item) => String(item)).join(" ")}`);
    } else if (typeof value === "string") {
      parts.push(`${key}: ${value}`);
    }
  }

  return parts.length > 0 ? parts.join(" | ") : null;
}

async function tryRefreshAccessToken(): Promise<boolean> {
  const tokens = getStoredAuthTokens();
  if (!tokens) {
    return false;
  }

  const response = await fetch(resolveUrl("/api/v1/accounts/token/refresh/"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      refresh: tokens.refresh,
    }),
  });

  if (!response.ok) {
    clearAuthTokens();
    return false;
  }

  const payload = (await parseJsonBody<Partial<AuthTokens>>(response)) ?? {};
  if (typeof payload.access !== "string" || !payload.access.trim()) {
    clearAuthTokens();
    return false;
  }

  persistAuthTokens({
    access: payload.access,
    refresh:
      typeof payload.refresh === "string" && payload.refresh.trim()
        ? payload.refresh
        : tokens.refresh,
  });

  return true;
}

async function requestJson<T>(path: string, options: RequestJsonOptions = {}): Promise<T> {
  const { auth = false, allowAuthRetry = true, body, headers, ...rest } = options;

  const requestHeaders = new Headers(headers);
  requestHeaders.set("Content-Type", "application/json");

  if (auth) {
    const accessToken = getStoredAccessToken();
    if (!accessToken) {
      throw new ApiError("Sessao nao autenticada. Faca login no Admin.", 401);
    }

    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(resolveUrl(path), {
    ...rest,
    headers: requestHeaders,
    body,
  });

  if (response.status === 401 && auth && allowAuthRetry) {
    const refreshed = await tryRefreshAccessToken();
    if (refreshed) {
      return requestJson<T>(path, {
        ...options,
        allowAuthRetry: false,
      });
    }

    throw new ApiError("Sua sessao expirou. Faca login novamente.", 401);
  }

  if (!response.ok) {
    let fallbackMessage = `Erro HTTP ${response.status} ao consultar a API.`;

    try {
      const payload = (await parseJsonBody<JsonObject>(response)) as unknown;
      const parsed = parseErrorMessage(payload);
      if (parsed) {
        fallbackMessage = parsed;
      }
    } catch {
      // Mantem mensagem padrao.
    }

    throw new ApiError(fallbackMessage, response.status);
  }

  return parseJsonBody<T>(response);
}

export async function loginAccount(username: string, password: string): Promise<AuthTokens> {
  const payload = await requestJson<AuthTokens>("/api/v1/accounts/token/", {
    method: "POST",
    body: JSON.stringify({
      username,
      password,
    }),
  });

  persistAuthTokens(payload);
  return payload;
}

export async function fetchMe(): Promise<AuthUserProfile> {
  return requestJson<AuthUserProfile>("/api/v1/accounts/me/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });
}

export async function fetchHealth(): Promise<HealthPayload> {
  return requestJson<HealthPayload>("/api/v1/health", {
    method: "GET",
    cache: "no-store",
  });
}

export async function listOrdersAdmin(): Promise<OrderData[]> {
  const payload = await requestJson<OrderData[] | { results?: OrderData[] }>(
    "/api/v1/orders/orders/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function updateOrderStatusAdmin(
  orderId: number,
  status: OrderStatus,
): Promise<OrderData> {
  return requestJson<OrderData>(`/api/v1/orders/orders/${orderId}/status/`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify({ status }),
  });
}

export async function fetchFinanceKpis(
  from: string,
  to: string,
): Promise<FinanceKpisPayload> {
  return requestJson<FinanceKpisPayload>(
    `/api/v1/finance/reports/kpis/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function fetchFinanceUnreconciled(
  from: string,
  to: string,
): Promise<FinanceUnreconciledPayload> {
  return requestJson<FinanceUnreconciledPayload>(
    `/api/v1/finance/reports/unreconciled/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function listStockItems(): Promise<StockItemData[]> {
  const payload = await requestJson<StockItemData[] | { results?: StockItemData[] }>(
    "/api/v1/inventory/stock-items/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function listStockMovements(): Promise<StockMovementData[]> {
  const payload = await requestJson<
    StockMovementData[] | { results?: StockMovementData[] }
  >("/api/v1/inventory/movements/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });

  return normalizeListPayload(payload);
}

export async function createStockMovement(
  payload: CreateStockMovementPayload,
): Promise<StockMovementData> {
  return requestJson<StockMovementData>("/api/v1/inventory/movements/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export function logoutAccount(): void {
  clearAuthTokens();
}
