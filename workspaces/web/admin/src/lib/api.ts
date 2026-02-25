import {
  clearAuthTokens,
  getStoredAccessToken,
  getStoredAuthTokens,
  persistAuthTokens,
} from "@/lib/storage";
import type {
  AuthTokens,
  AuthUserProfile,
  AdminUserData,
  AssignUserRolesPayload,
  AssignUserRolesResultData,
  CreateStockMovementPayload,
  CreateProductionBatchPayload,
  DishData,
  FinanceCashflowPayload,
  FinanceDrePayload,
  FinanceKpisPayload,
  FinanceUnreconciledPayload,
  HealthPayload,
  MenuDayData,
  OrderData,
  OrderStatus,
  ProductionBatchData,
  PurchaseData,
  PurchaseRequestData,
  PurchaseRequestFromMenuResultData,
  ProcurementRequestStatus,
  RoleData,
  StockItemData,
  StockMovementData,
  UpsertMenuDayPayload,
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

type RequestFileResult = {
  blob: Blob;
  filename: string;
};

type JsonObject = Record<string, unknown>;

const NETWORK_ERROR_MESSAGE =
  "Falha de conexao com a API. Verifique backend (porta 8000) e CORS do Admin (porta 3002).";

function resolveBrowserBaseUrl(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  if (!hostname) {
    return "";
  }

  return protocol + "//" + hostname + ":8000";
}

function getApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "") ?? "";
  if (fromEnv) {
    return fromEnv;
  }

  return resolveBrowserBaseUrl();
}

function resolveUrl(path: string): string {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new ApiError("Nao foi possivel identificar a URL da API do backend. Verifique a configuracao do Admin.", 0);
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

function extractFilenameFromDisposition(headerValue: string | null): string | null {
  if (!headerValue) {
    return null;
  }

  const match = headerValue.match(/filename="([^"]+)"/i);
  if (!match || !match[1]) {
    return null;
  }

  return match[1];
}

async function tryRefreshAccessToken(): Promise<boolean> {
  const tokens = getStoredAuthTokens();
  if (!tokens) {
    return false;
  }

  let response: Response;
  try {
    response = await fetch(resolveUrl("/api/v1/accounts/token/refresh/"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh: tokens.refresh,
      }),
    });
  } catch {
    return false;
  }

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

  let response: Response;
  try {
    response = await fetch(resolveUrl(path), {
      ...rest,
      headers: requestHeaders,
      body,
    });
  } catch {
    throw new ApiError(NETWORK_ERROR_MESSAGE, 0);
  }

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

async function requestFile(
  path: string,
  options: RequestJsonOptions = {},
): Promise<RequestFileResult> {
  const { auth = false, allowAuthRetry = true, body, headers, ...rest } = options;

  const requestHeaders = new Headers(headers);
  requestHeaders.set("Accept", "text/csv");

  if (auth) {
    const accessToken = getStoredAccessToken();
    if (!accessToken) {
      throw new ApiError("Sessao nao autenticada. Faca login no Admin.", 401);
    }

    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  let response: Response;
  try {
    response = await fetch(resolveUrl(path), {
      ...rest,
      headers: requestHeaders,
      body,
    });
  } catch {
    throw new ApiError(NETWORK_ERROR_MESSAGE, 0);
  }

  if (response.status === 401 && auth && allowAuthRetry) {
    const refreshed = await tryRefreshAccessToken();
    if (refreshed) {
      return requestFile(path, {
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

  const blob = await response.blob();
  const filename =
    extractFilenameFromDisposition(response.headers.get("content-disposition")) ??
    "relatorio.csv";

  return { blob, filename };
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

export async function listUsersAdmin(): Promise<AdminUserData[]> {
  const payload = await requestJson<AdminUserData[] | { results?: AdminUserData[] }>(
    "/api/v1/accounts/users/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function listRolesAdmin(): Promise<RoleData[]> {
  const payload = await requestJson<RoleData[] | { results?: RoleData[] }>(
    "/api/v1/accounts/roles/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function assignUserRolesAdmin(
  userId: number,
  payload: AssignUserRolesPayload,
): Promise<AssignUserRolesResultData> {
  return requestJson<AssignUserRolesResultData>(`/api/v1/accounts/users/${userId}/roles/`, {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
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

export async function fetchFinanceCashflow(
  from: string,
  to: string,
): Promise<FinanceCashflowPayload> {
  return requestJson<FinanceCashflowPayload>(
    `/api/v1/finance/reports/cashflow/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function fetchFinanceDre(
  from: string,
  to: string,
): Promise<FinanceDrePayload> {
  return requestJson<FinanceDrePayload>(
    `/api/v1/finance/reports/dre/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
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

export async function exportFinanceCashflowCsv(
  from: string,
  to: string,
): Promise<RequestFileResult> {
  return requestFile(
    `/api/v1/finance/reports/cashflow/export/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function exportFinanceDreCsv(
  from: string,
  to: string,
): Promise<RequestFileResult> {
  return requestFile(
    `/api/v1/finance/reports/dre/export/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function exportPurchasesCsv(
  from: string,
  to: string,
): Promise<RequestFileResult> {
  return requestFile(
    `/api/v1/procurement/reports/purchases/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function exportProductionCsv(
  from: string,
  to: string,
): Promise<RequestFileResult> {
  return requestFile(
    `/api/v1/production/reports/production/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function exportOrdersCsv(
  from: string,
  to: string,
): Promise<RequestFileResult> {
  return requestFile(
    `/api/v1/orders/reports/orders/?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
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

export async function listMenuDaysAdmin(): Promise<MenuDayData[]> {
  const payload = await requestJson<MenuDayData[] | { results?: MenuDayData[] }>(
    "/api/v1/catalog/menus/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function createMenuDayAdmin(payload: UpsertMenuDayPayload): Promise<MenuDayData> {
  return requestJson<MenuDayData>("/api/v1/catalog/menus/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function updateMenuDayAdmin(
  menuDayId: number,
  payload: UpsertMenuDayPayload,
): Promise<MenuDayData> {
  return requestJson<MenuDayData>(`/api/v1/catalog/menus/${menuDayId}/`, {
    method: "PUT",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function deleteMenuDayAdmin(menuDayId: number): Promise<void> {
  await requestJson<Record<string, never>>(`/api/v1/catalog/menus/${menuDayId}/`, {
    method: "DELETE",
    auth: true,
  });
}

export async function listDishesAdmin(): Promise<DishData[]> {
  const payload = await requestJson<DishData[] | { results?: DishData[] }>(
    "/api/v1/catalog/dishes/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function listPurchaseRequestsAdmin(): Promise<PurchaseRequestData[]> {
  const payload = await requestJson<
    PurchaseRequestData[] | { results?: PurchaseRequestData[] }
  >("/api/v1/procurement/requests/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });

  return normalizeListPayload(payload);
}

export async function updatePurchaseRequestStatusAdmin(
  requestId: number,
  status: ProcurementRequestStatus,
): Promise<PurchaseRequestData> {
  return requestJson<PurchaseRequestData>(`/api/v1/procurement/requests/${requestId}/`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify({ status }),
  });
}

export async function generatePurchaseRequestFromMenuAdmin(
  menuDayId: number,
): Promise<PurchaseRequestFromMenuResultData> {
  return requestJson<PurchaseRequestFromMenuResultData>("/api/v1/procurement/requests/from-menu/", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ menu_day_id: menuDayId }),
  });
}

export async function listPurchasesAdmin(): Promise<PurchaseData[]> {
  const payload = await requestJson<PurchaseData[] | { results?: PurchaseData[] }>(
    "/api/v1/procurement/purchases/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function listProductionBatchesAdmin(): Promise<ProductionBatchData[]> {
  const payload = await requestJson<
    ProductionBatchData[] | { results?: ProductionBatchData[] }
  >("/api/v1/production/batches/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });

  return normalizeListPayload(payload);
}

export async function createProductionBatchAdmin(
  payload: CreateProductionBatchPayload,
): Promise<ProductionBatchData> {
  return requestJson<ProductionBatchData>("/api/v1/production/batches/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function completeProductionBatchAdmin(
  batchId: number,
): Promise<ProductionBatchData> {
  return requestJson<ProductionBatchData>(`/api/v1/production/batches/${batchId}/complete/`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({}),
  });
}

export function logoutAccount(): void {
  clearAuthTokens();
}
