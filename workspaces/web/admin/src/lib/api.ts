import {
  clearAuthTokens,
  getStoredAccessToken,
  getStoredAuthTokens,
  persistAuthTokens,
} from "@/lib/storage";
import { trackNetworkRequest } from "@/lib/networkPreloader";
import type {
  AuthTokens,
  AuthUserProfile,
  UserProfileData,
  UpdateUserProfilePayload,
  AdminUserData,
  AssignUserRolesPayload,
  AssignUserRolesResultData,
  CreateCustomerLgpdRequestPayload,
  ApplyOcrPayload,
  ApplyOcrResultData,
  CreateDishPayload,
  CreateIngredientPayload,
  OcrJobData,
  OcrKind,
  CreatePurchasePayload,
  CreateStockMovementPayload,
  CreateProductionBatchPayload,
  DishData,
  FinanceCashflowPayload,
  FinanceDrePayload,
  FinanceKpisPayload,
  FinanceUnreconciledPayload,
  HealthPayload,
  IngredientData,
  MenuDayData,
  MobileReleaseData,
  OrdersOpsDashboardData,
  OrderData,
  OrderStatus,
  ProductionBatchData,
  PortalConfigData,
  PortalConfigWritePayload,
  PortalCloudflareConfig,
  PortalCloudflarePreviewData,
  PortalCloudflareRuntimeResult,
  PortalCloudflareToggleResult,
  PortalEmailTestResult,
  PortalInstallerDraftPayload,
  PortalInstallerJobResult,
  PortalInstallerJobsListResult,
  PortalInstallerWizardValidateResult,
  PortalPaymentProviderTestResult,
  PortalSectionData,
  PortalSectionWritePayload,
  CreateMobileReleasePayload,
  EcosystemOpsRealtimeData,
  CustomerData,
  CustomerDetailData,
  CustomerGovernanceData,
  CustomerLgpdRequestData,
  CustomerOverviewData,
  PurchaseData,
  PurchaseItemData,
  PurchaseRequestData,
  PurchaseRequestFromMenuResultData,
  ProcurementRequestStatus,
  RoleData,
  StockItemData,
  StockMovementData,
  UpdateCustomerConsentsPayload,
  UpdateCustomerStatusPayload,
  UpsertMenuDayPayload,
  UpdateDishPayload,
  UpdateIngredientPayload,
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

type RequestFormDataOptions = Omit<RequestInit, "body"> & {
  body: FormData;
  auth?: boolean;
  allowAuthRetry?: boolean;
};

type JsonObject = Record<string, unknown>;

const NETWORK_ERROR_MESSAGE =
  "Falha de conexao com a API. Verifique backend (porta 8000) e CORS do Admin (porta 3002).";
const RUNTIME_API_CONFIG_ENDPOINT = "/api/runtime/config";
const RUNTIME_API_CACHE_TTL_MS = 15_000;

let runtimeApiBaseUrlCache = "";
let runtimeApiCacheExpiresAt = 0;

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

function normalizeApiBaseUrl(value: string): string {
  return value.trim().replace(/\/$/, "");
}

async function getRuntimeApiBaseUrlFromSameOrigin(): Promise<string> {
  if (typeof window === "undefined") {
    return "";
  }

  const now = Date.now();
  if (runtimeApiBaseUrlCache && now < runtimeApiCacheExpiresAt) {
    return runtimeApiBaseUrlCache;
  }

  try {
    const response = await fetch(RUNTIME_API_CONFIG_ENDPOINT, {
      cache: "no-store",
    });
    if (!response.ok) {
      return runtimeApiBaseUrlCache;
    }

    const payload = (await response.json()) as { api_base_url?: unknown };
    const resolved = normalizeApiBaseUrl(String(payload.api_base_url ?? ""));
    if (!resolved) {
      return runtimeApiBaseUrlCache;
    }

    runtimeApiBaseUrlCache = resolved;
    runtimeApiCacheExpiresAt = now + RUNTIME_API_CACHE_TTL_MS;
    return runtimeApiBaseUrlCache;
  } catch {
    return runtimeApiBaseUrlCache;
  }
}

function getStaticApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "") ?? "";
  if (fromEnv) {
    return fromEnv;
  }

  return resolveBrowserBaseUrl();
}

async function getApiBaseUrl(): Promise<string> {
  const staticUrl = getStaticApiBaseUrl();
  const runtimeUrl = await getRuntimeApiBaseUrlFromSameOrigin();
  return runtimeUrl || staticUrl;
}

async function resolveUrl(path: string): Promise<string> {
  const baseUrl = await getApiBaseUrl();
  if (!baseUrl) {
    throw new ApiError("Não foi possível identificar a URL da API do backend. Verifique a configuração do Admin.", 0);
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
    const refreshUrl = await resolveUrl("/api/v1/accounts/token/refresh/");
    response = await trackNetworkRequest(() =>
      fetch(refreshUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          refresh: tokens.refresh,
        }),
      }),
    );
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
      throw new ApiError("Sessão não autenticada. Faça login no Admin.", 401);
    }

    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  let response: Response;
  try {
    const resolvedUrl = await resolveUrl(path);
    response = await trackNetworkRequest(() =>
      fetch(resolvedUrl, {
        ...rest,
        headers: requestHeaders,
        body,
      }),
    );
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
      throw new ApiError("Sessão não autenticada. Faça login no Admin.", 401);
    }

    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  let response: Response;
  try {
    const resolvedUrl = await resolveUrl(path);
    response = await trackNetworkRequest(() =>
      fetch(resolvedUrl, {
        ...rest,
        headers: requestHeaders,
        body,
      }),
    );
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

async function requestFormData<T>(
  path: string,
  options: RequestFormDataOptions,
): Promise<T> {
  const { auth = false, allowAuthRetry = true, body, headers, ...rest } = options;

  const requestHeaders = new Headers(headers);
  if (auth) {
    const accessToken = getStoredAccessToken();
    if (!accessToken) {
      throw new ApiError("Sessão não autenticada. Faça login no Admin.", 401);
    }
    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  let response: Response;
  try {
    const resolvedUrl = await resolveUrl(path);
    response = await trackNetworkRequest(() =>
      fetch(resolvedUrl, {
        ...rest,
        headers: requestHeaders,
        body,
      }),
    );
  } catch {
    throw new ApiError(NETWORK_ERROR_MESSAGE, 0);
  }

  if (response.status === 401 && auth && allowAuthRetry) {
    const refreshed = await tryRefreshAccessToken();
    if (refreshed) {
      return requestFormData<T>(path, {
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

export async function fetchMyUserProfile(): Promise<UserProfileData> {
  return requestJson<UserProfileData>("/api/v1/accounts/me/profile/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });
}

export async function updateMyUserProfile(
  payload: UpdateUserProfilePayload,
): Promise<UserProfileData> {
  return requestJson<UserProfileData>("/api/v1/accounts/me/profile/", {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function uploadMyUserProfileFiles(body: FormData): Promise<UserProfileData> {
  return requestFormData<UserProfileData>("/api/v1/accounts/me/profile/", {
    method: "PATCH",
    auth: true,
    body,
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

export async function listCustomersAdmin(params?: {
  search?: string;
  account_status?: string;
  is_active?: "true" | "false";
  compliance?: "pending_email";
}): Promise<CustomerData[]> {
  const query = new URLSearchParams();
  if (params?.search) {
    query.set("search", params.search.trim());
  }
  if (params?.account_status) {
    query.set("account_status", params.account_status.trim());
  }
  if (params?.is_active) {
    query.set("is_active", params.is_active);
  }
  if (params?.compliance) {
    query.set("compliance", params.compliance);
  }

  const queryString = query.toString();
  const endpoint = queryString
    ? `/api/v1/accounts/customers/?${queryString}`
    : "/api/v1/accounts/customers/";
  const payload = await requestJson<CustomerData[] | { results?: CustomerData[] }>(
    endpoint,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
  return normalizeListPayload(payload);
}

export async function fetchCustomersOverviewAdmin(): Promise<CustomerOverviewData> {
  return requestJson<CustomerOverviewData>("/api/v1/accounts/customers/overview/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });
}

export async function fetchCustomerDetailAdmin(
  customerId: number,
): Promise<CustomerDetailData> {
  return requestJson<CustomerDetailData>(`/api/v1/accounts/customers/${customerId}/`, {
    method: "GET",
    auth: true,
    cache: "no-store",
  });
}

export async function updateCustomerProfileAdmin(
  customerId: number,
  payload: FormData | Record<string, unknown>,
): Promise<UserProfileData> {
  if (payload instanceof FormData) {
    return requestFormData<UserProfileData>(
      `/api/v1/accounts/customers/${customerId}/profile/`,
      {
        method: "PATCH",
        auth: true,
        body: payload,
      },
    );
  }

  return requestJson<UserProfileData>(`/api/v1/accounts/customers/${customerId}/profile/`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function updateCustomerGovernanceAdmin(
  customerId: number,
  payload: Partial<CustomerGovernanceData>,
): Promise<CustomerGovernanceData> {
  return requestJson<CustomerGovernanceData>(
    `/api/v1/accounts/customers/${customerId}/governance/`,
    {
      method: "PATCH",
      auth: true,
      body: JSON.stringify(payload),
    },
  );
}

export async function updateCustomerStatusAdmin(
  customerId: number,
  payload: UpdateCustomerStatusPayload,
): Promise<CustomerGovernanceData> {
  return requestJson<CustomerGovernanceData>(
    `/api/v1/accounts/customers/${customerId}/status/`,
    {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    },
  );
}

export async function updateCustomerConsentsAdmin(
  customerId: number,
  payload: UpdateCustomerConsentsPayload,
): Promise<CustomerGovernanceData> {
  return requestJson<CustomerGovernanceData>(
    `/api/v1/accounts/customers/${customerId}/consents/`,
    {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    },
  );
}

export async function resendCustomerEmailVerificationAdmin(
  customerId: number,
  preferredClientBaseUrl = "",
): Promise<{
  sent: boolean;
  detail: string;
  email?: string;
  client_base_url?: string;
}> {
  return requestJson(`/api/v1/accounts/customers/${customerId}/resend-email-verification/`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({
      preferred_client_base_url: preferredClientBaseUrl,
    }),
  });
}

export async function listCustomerLgpdRequestsAdmin(
  customerId: number,
): Promise<CustomerLgpdRequestData[]> {
  const payload = await requestJson<
    CustomerLgpdRequestData[] | { results?: CustomerLgpdRequestData[] }
  >(`/api/v1/accounts/customers/${customerId}/lgpd-requests/`, {
    method: "GET",
    auth: true,
    cache: "no-store",
  });
  return normalizeListPayload(payload);
}

export async function createCustomerLgpdRequestAdmin(
  customerId: number,
  payload: CreateCustomerLgpdRequestPayload,
): Promise<CustomerLgpdRequestData> {
  return requestJson<CustomerLgpdRequestData>(
    `/api/v1/accounts/customers/${customerId}/lgpd-requests/`,
    {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    },
  );
}

export async function updateCustomerLgpdRequestStatusAdmin(
  requestId: number,
  payload: {
    status: string;
    resolution_notes?: string;
  },
): Promise<CustomerLgpdRequestData> {
  return requestJson<CustomerLgpdRequestData>(
    `/api/v1/accounts/customers/lgpd-requests/${requestId}/status/`,
    {
      method: "PATCH",
      auth: true,
      body: JSON.stringify(payload),
    },
  );
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

export async function fetchOrdersOpsDashboardAdmin(): Promise<OrdersOpsDashboardData> {
  return requestJson<OrdersOpsDashboardData>("/api/v1/orders/ops/dashboard/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });
}

export async function fetchEcosystemOpsRealtimeAdmin(): Promise<EcosystemOpsRealtimeData> {
  return requestJson<EcosystemOpsRealtimeData>("/api/v1/orders/ops/realtime/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });
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

export async function createDishAdmin(payload: CreateDishPayload): Promise<DishData> {
  return requestJson<DishData>("/api/v1/catalog/dishes/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function updateDishAdmin(
  dishId: number,
  payload: UpdateDishPayload,
): Promise<DishData> {
  return requestJson<DishData>(`/api/v1/catalog/dishes/${dishId}/`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function listIngredientsAdmin(): Promise<IngredientData[]> {
  const payload = await requestJson<IngredientData[] | { results?: IngredientData[] }>(
    "/api/v1/catalog/ingredients/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function createIngredientAdmin(
  payload: CreateIngredientPayload,
): Promise<IngredientData> {
  return requestJson<IngredientData>("/api/v1/catalog/ingredients/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function updateIngredientAdmin(
  ingredientId: number,
  payload: UpdateIngredientPayload,
): Promise<IngredientData> {
  return requestJson<IngredientData>(`/api/v1/catalog/ingredients/${ingredientId}/`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function uploadIngredientImageAdmin(
  ingredientId: number,
  file: File,
): Promise<IngredientData> {
  const body = new FormData();
  body.append("image", file);

  return requestFormData<IngredientData>(`/api/v1/catalog/ingredients/${ingredientId}/image/`, {
    method: "POST",
    auth: true,
    body,
  });
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

export async function createPurchaseAdmin(
  payload: CreatePurchasePayload,
): Promise<PurchaseData> {
  return requestJson<PurchaseData>("/api/v1/procurement/purchases/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function uploadPurchaseReceiptImageAdmin(
  purchaseId: number,
  file: File,
): Promise<PurchaseData> {
  const body = new FormData();
  body.append("receipt_image", file);

  return requestFormData<PurchaseData>(
    `/api/v1/procurement/purchases/${purchaseId}/receipt-image/`,
    {
      method: "POST",
      auth: true,
      body,
    },
  );
}

export async function uploadPurchaseItemLabelImageAdmin(
  purchaseId: number,
  purchaseItemId: number,
  file: File,
  side: "front" | "back" = "front",
): Promise<PurchaseItemData> {
  const body = new FormData();
  body.append("label_image", file);
  body.append("side", side);

  return requestFormData<PurchaseItemData>(
    `/api/v1/procurement/purchases/${purchaseId}/items/${purchaseItemId}/label-image/`,
    {
      method: "POST",
      auth: true,
      body,
    },
  );
}

export async function createOcrJobAdmin(
  kind: OcrKind,
  file: File,
  rawText?: string,
): Promise<OcrJobData> {
  const body = new FormData();
  body.append("kind", kind);
  body.append("image", file);
  if (rawText && rawText.trim()) {
    body.append("raw_text", rawText.trim());
  }

  return requestFormData<OcrJobData>("/api/v1/ocr/jobs/", {
    method: "POST",
    auth: true,
    body,
  });
}

export async function applyOcrJobAdmin(
  jobId: number,
  payload: ApplyOcrPayload,
): Promise<ApplyOcrResultData> {
  return requestJson<ApplyOcrResultData>(`/api/v1/ocr/jobs/${jobId}/apply/`, {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function uploadDishImageAdmin(
  dishId: number,
  file: File,
): Promise<DishData> {
  const body = new FormData();
  body.append("image", file);

  return requestFormData<DishData>(`/api/v1/catalog/dishes/${dishId}/image/`, {
    method: "POST",
    auth: true,
    body,
  });
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

export async function listPortalConfigsAdmin(): Promise<PortalConfigData[]> {
  const payload = await requestJson<PortalConfigData[] | { results?: PortalConfigData[] }>(
    "/api/v1/portal/admin/config/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );

  return normalizeListPayload(payload);
}

export async function createPortalConfigAdmin(
  payload: PortalConfigWritePayload = {},
): Promise<PortalConfigData> {
  return requestJson<PortalConfigData>("/api/v1/portal/admin/config/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function ensurePortalConfigAdmin(): Promise<PortalConfigData> {
  const existingConfigs = await listPortalConfigsAdmin();
  if (existingConfigs.length > 0) {
    return existingConfigs[0];
  }

  return createPortalConfigAdmin({});
}

export async function updatePortalConfigAdmin(
  configId: number,
  payload: PortalConfigWritePayload,
): Promise<PortalConfigData> {
  return requestJson<PortalConfigData>(`/api/v1/portal/admin/config/${configId}/`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function publishPortalConfigAdmin(): Promise<PortalConfigData> {
  return requestJson<PortalConfigData>("/api/v1/portal/admin/config/publish/", {
    method: "POST",
    auth: true,
    body: JSON.stringify({}),
  });
}

export async function testPortalPaymentProviderAdmin(
  provider: string,
): Promise<PortalPaymentProviderTestResult> {
  return requestJson<PortalPaymentProviderTestResult>(
    "/api/v1/portal/admin/config/test-payment-provider/",
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({ provider }),
    },
  );
}

export async function testPortalEmailConfigAdmin(
  toEmail: string,
): Promise<PortalEmailTestResult> {
  return requestJson<PortalEmailTestResult>("/api/v1/portal/admin/config/test-email/", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ to_email: toEmail }),
  });
}

export async function previewPortalCloudflareAdmin(
  settings: Partial<PortalCloudflareConfig>,
): Promise<PortalCloudflarePreviewData> {
  return requestJson<PortalCloudflarePreviewData>(
    "/api/v1/portal/admin/config/cloudflare-preview/",
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({ settings }),
    },
  );
}

export async function togglePortalCloudflareAdmin(payload: {
  enabled: boolean;
  settings?: Partial<PortalCloudflareConfig>;
}): Promise<PortalCloudflareToggleResult> {
  return requestJson<PortalCloudflareToggleResult>(
    "/api/v1/portal/admin/config/cloudflare-toggle/",
    {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    },
  );
}

export async function managePortalCloudflareRuntimeAdmin(
  action: "start" | "stop" | "status" | "refresh",
): Promise<PortalCloudflareRuntimeResult> {
  return requestJson<PortalCloudflareRuntimeResult>(
    "/api/v1/portal/admin/config/cloudflare-runtime/",
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({ action }),
    },
  );
}

export async function validateInstallerWizardAdmin(
  payload: Partial<PortalInstallerDraftPayload>,
): Promise<PortalInstallerWizardValidateResult> {
  return requestJson<PortalInstallerWizardValidateResult>(
    "/api/v1/portal/admin/config/installer-wizard-validate/",
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({ payload }),
    },
  );
}

export async function saveInstallerWizardAdmin(payload: {
  payload: Partial<PortalInstallerDraftPayload>;
  completedStep: string;
}): Promise<PortalConfigData> {
  return requestJson<PortalConfigData>(
    "/api/v1/portal/admin/config/installer-wizard-save/",
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({
        payload: payload.payload,
        completed_step: payload.completedStep,
      }),
    },
  );
}

export async function startInstallerJobAdmin(
  payload: Partial<PortalInstallerDraftPayload>,
): Promise<PortalInstallerJobResult> {
  return requestJson<PortalInstallerJobResult>(
    "/api/v1/portal/admin/config/installer-jobs/start/",
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({ payload }),
    },
  );
}

export async function getInstallerJobStatusAdmin(
  jobId: string,
): Promise<PortalInstallerJobResult> {
  return requestJson<PortalInstallerJobResult>(
    `/api/v1/portal/admin/config/installer-jobs/${jobId}/status/`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function cancelInstallerJobAdmin(
  jobId: string,
): Promise<PortalInstallerJobResult> {
  return requestJson<PortalInstallerJobResult>(
    `/api/v1/portal/admin/config/installer-jobs/${jobId}/cancel/`,
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({}),
    },
  );
}

export async function listInstallerJobsAdmin(): Promise<PortalInstallerJobsListResult> {
  return requestJson<PortalInstallerJobsListResult>(
    "/api/v1/portal/admin/config/installer-jobs/",
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function listPortalSectionsAdmin(): Promise<PortalSectionData[]> {
  const payload = await requestJson<
    PortalSectionData[] | { results?: PortalSectionData[] }
  >("/api/v1/portal/admin/sections/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });

  return normalizeListPayload(payload);
}

export async function updatePortalSectionAdmin(
  sectionId: number,
  payload: PortalSectionWritePayload,
): Promise<PortalSectionData> {
  return requestJson<PortalSectionData>(`/api/v1/portal/admin/sections/${sectionId}/`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function listMobileReleasesAdmin(): Promise<MobileReleaseData[]> {
  const payload = await requestJson<
    MobileReleaseData[] | { results?: MobileReleaseData[] }
  >("/api/v1/portal/admin/mobile/releases/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });

  return normalizeListPayload(payload);
}

export async function createMobileReleaseAdmin(
  payload: CreateMobileReleasePayload,
): Promise<MobileReleaseData> {
  return requestJson<MobileReleaseData>("/api/v1/portal/admin/mobile/releases/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function publishMobileReleaseAdmin(
  releaseId: number,
): Promise<MobileReleaseData> {
  return requestJson<MobileReleaseData>(
    `/api/v1/portal/admin/mobile/releases/${releaseId}/publish/`,
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({}),
    },
  );
}

export function logoutAccount(): void {
  clearAuthTokens();
}
