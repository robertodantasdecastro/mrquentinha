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
  OrdersOpsDashboardData,
  OrderData,
  OrderStatus,
  ProductionBatchData,
  PortalConfigData,
  PortalConfigWritePayload,
  PortalSectionData,
  PortalSectionWritePayload,
  PurchaseData,
  PurchaseItemData,
  PurchaseRequestData,
  PurchaseRequestFromMenuResultData,
  ProcurementRequestStatus,
  RoleData,
  StockItemData,
  StockMovementData,
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
      throw new ApiError("Sessão não autenticada. Faça login no Admin.", 401);
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
      throw new ApiError("Sessão não autenticada. Faça login no Admin.", 401);
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

export async function fetchOrdersOpsDashboardAdmin(): Promise<OrdersOpsDashboardData> {
  return requestJson<OrdersOpsDashboardData>("/api/v1/orders/ops/dashboard/", {
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

export function logoutAccount(): void {
  clearAuthTokens();
}
