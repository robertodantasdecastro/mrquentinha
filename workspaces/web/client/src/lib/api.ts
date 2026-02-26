import {
  clearAuthTokens,
  getStoredAccessToken,
  getStoredAuthTokens,
  persistAuthTokens,
} from "@/lib/storage";
import type {
  AuthTokens,
  AuthUserProfile,
  ClientPortalPublicConfig,
  CreatedOrderResponse,
  MenuDayData,
  OnlinePaymentMethod,
  OrderData,
  PaymentIntentData,
  PublicAuthProvidersConfig,
  PublicPaymentProvidersConfig,
  RegisterPayload,
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

function buildNetworkErrorMessage(): string {
  const origin =
    typeof window !== "undefined" && window.location.origin
      ? window.location.origin
      : "origem atual";

  return `Falha de conexao com a API. Verifique backend (porta 8000) e CORS para ${origin}.`;
}

function resolveBrowserBaseUrl(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  if (!hostname) {
    return "";
  }

  return `${protocol}//${hostname}:8000`;
}

function isLoopbackHost(host: string): boolean {
  return host === "localhost" || host === "127.0.0.1";
}

function shouldPreferBrowserHostBaseUrl(fromEnv: string): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const browserHost = window.location.hostname;
  if (!browserHost || isLoopbackHost(browserHost)) {
    return false;
  }

  try {
    const envUrl = new URL(fromEnv);
    return isLoopbackHost(envUrl.hostname);
  } catch {
    return false;
  }
}

function getApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "") ?? "";
  if (fromEnv) {
    if (shouldPreferBrowserHostBaseUrl(fromEnv)) {
      return resolveBrowserBaseUrl();
    }
    return fromEnv;
  }

  return resolveBrowserBaseUrl();
}

export function getResolvedApiBaseUrl(): string {
  return getApiBaseUrl();
}

function resolveUrl(path: string): string {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new ApiError(
      "Nao foi possivel identificar a URL da API do backend.",
      0,
    );
  }

  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
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

async function parseJsonBody<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  return JSON.parse(text) as T;
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

  const nextRefresh =
    typeof payload.refresh === "string" && payload.refresh.trim()
      ? payload.refresh
      : tokens.refresh;

  persistAuthTokens({
    access: payload.access,
    refresh: nextRefresh,
  });

  return true;
}

async function requestJson<T>(
  path: string,
  options: RequestJsonOptions = {},
): Promise<T> {
  const { auth = false, allowAuthRetry = true, body, headers, ...rest } = options;

  const requestHeaders = new Headers(headers);
  requestHeaders.set("Content-Type", "application/json");

  if (auth) {
    const accessToken = getStoredAccessToken();
    if (!accessToken) {
      throw new ApiError(
        "Sessao nao autenticada. Acesse a aba Conta para entrar.",
        401,
      );
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
    throw new ApiError(buildNetworkErrorMessage(), 0);
  }

  if (response.status === 401 && auth && allowAuthRetry) {
    const refreshed = await tryRefreshAccessToken();

    if (refreshed) {
      return requestJson<T>(path, {
        ...options,
        allowAuthRetry: false,
      });
    }

    throw new ApiError(
      "Sua sessao expirou. Faca login novamente na aba Conta.",
      401,
    );
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
      // Mantem mensagem de fallback sem JSON.
    }

    throw new ApiError(fallbackMessage, response.status);
  }

  return parseJsonBody<T>(response);
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

const DEFAULT_AUTH_PROVIDERS_CONFIG: PublicAuthProvidersConfig = {
  google: {
    enabled: false,
    configured: false,
    web_client_id: "",
    ios_client_id: "",
    android_client_id: "",
    auth_uri: "",
    token_uri: "",
    redirect_uri_web: "",
    redirect_uri_mobile: "",
    scope: "openid email profile",
  },
  apple: {
    enabled: false,
    configured: false,
    service_id: "",
    team_id: "",
    key_id: "",
    auth_uri: "",
    token_uri: "",
    redirect_uri_web: "",
    redirect_uri_mobile: "",
    scope: "name email",
  },
};

const DEFAULT_PAYMENT_PROVIDERS_CONFIG: PublicPaymentProvidersConfig = {
  default_provider: "mock",
  enabled_providers: ["mock"],
  frontend_provider: {
    web: "mock",
    mobile: "mock",
  },
  method_provider_order: {
    PIX: ["mock"],
    CARD: ["mock"],
    VR: ["mock"],
  },
  receiver: {
    person_type: "CNPJ",
    document: "",
    name: "",
    email: "",
  },
  mercadopago: {
    enabled: false,
    configured: false,
    api_base_url: "",
    sandbox: true,
  },
  efi: {
    enabled: false,
    configured: false,
    api_base_url: "",
    sandbox: true,
  },
  asaas: {
    enabled: false,
    configured: false,
    api_base_url: "",
    sandbox: true,
  },
};

export async function fetchMenuByDate(menuDate: string): Promise<MenuDayData> {
  return requestJson<MenuDayData>(`/api/v1/catalog/menus/by-date/${menuDate}/`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function createOrder(
  deliveryDate: string,
  items: Array<{ menu_item_id: number; qty: number }>,
  paymentMethod: OnlinePaymentMethod,
): Promise<CreatedOrderResponse> {
  return requestJson<CreatedOrderResponse>("/api/v1/orders/orders/", {
    method: "POST",
    auth: true,
    body: JSON.stringify({
      delivery_date: deliveryDate,
      payment_method: paymentMethod,
      items: items.map((item) => ({
        menu_item: item.menu_item_id,
        qty: item.qty,
      })),
    }),
  });
}

export async function createPaymentIntent(
  paymentId: number,
  idempotencyKey: string,
): Promise<PaymentIntentData> {
  return requestJson<PaymentIntentData>(`/api/v1/orders/payments/${paymentId}/intent/`, {
    method: "POST",
    auth: true,
    headers: {
      "Idempotency-Key": idempotencyKey,
      "X-Client-Channel": "WEB",
    },
    body: JSON.stringify({}),
  });
}

export async function getLatestPaymentIntent(
  paymentId: number,
): Promise<PaymentIntentData> {
  return requestJson<PaymentIntentData>(
    `/api/v1/orders/payments/${paymentId}/intent/latest/`,
    {
      method: "GET",
      auth: true,
      cache: "no-store",
    },
  );
}

export async function listOrders(): Promise<OrderData[]> {
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

export async function confirmOrderReceipt(orderId: number): Promise<OrderData> {
  return requestJson<OrderData>(`/api/v1/orders/orders/${orderId}/confirm-receipt/`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({}),
  });
}

export async function loginAccount(
  username: string,
  password: string,
): Promise<AuthTokens> {
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

export async function registerAccount(
  registration: RegisterPayload,
): Promise<AuthUserProfile> {
  await requestJson<JsonObject>("/api/v1/accounts/register/", {
    method: "POST",
    body: JSON.stringify(registration),
  });

  await loginAccount(registration.username, registration.password);
  return fetchMe();
}

export async function fetchMe(): Promise<AuthUserProfile> {
  return requestJson<AuthUserProfile>("/api/v1/accounts/me/", {
    method: "GET",
    auth: true,
    cache: "no-store",
  });
}

export async function fetchAuthProvidersConfig(): Promise<PublicAuthProvidersConfig> {
  try {
    const payload = await requestJson<ClientPortalPublicConfig>(
      "/api/v1/portal/config/?channel=client&page=home",
      {
        method: "GET",
        cache: "no-store",
      },
    );

    if (!payload.auth_providers) {
      return DEFAULT_AUTH_PROVIDERS_CONFIG;
    }

    return {
      google: {
        ...DEFAULT_AUTH_PROVIDERS_CONFIG.google,
        ...(payload.auth_providers.google ?? {}),
      },
      apple: {
        ...DEFAULT_AUTH_PROVIDERS_CONFIG.apple,
        ...(payload.auth_providers.apple ?? {}),
      },
    };
  } catch {
    return DEFAULT_AUTH_PROVIDERS_CONFIG;
  }
}

export async function fetchPaymentProvidersConfig(): Promise<PublicPaymentProvidersConfig> {
  try {
    const payload = await requestJson<ClientPortalPublicConfig>(
      "/api/v1/portal/config/?channel=client&page=home",
      {
        method: "GET",
        cache: "no-store",
      },
    );

    if (!payload.payment_providers) {
      return DEFAULT_PAYMENT_PROVIDERS_CONFIG;
    }

    return {
      ...DEFAULT_PAYMENT_PROVIDERS_CONFIG,
      ...payload.payment_providers,
      method_provider_order: {
        ...DEFAULT_PAYMENT_PROVIDERS_CONFIG.method_provider_order,
        ...(payload.payment_providers.method_provider_order ?? {}),
      },
      receiver: {
        ...DEFAULT_PAYMENT_PROVIDERS_CONFIG.receiver,
        ...(payload.payment_providers.receiver ?? {}),
      },
      mercadopago: {
        ...DEFAULT_PAYMENT_PROVIDERS_CONFIG.mercadopago,
        ...(payload.payment_providers.mercadopago ?? {}),
      },
      efi: {
        ...DEFAULT_PAYMENT_PROVIDERS_CONFIG.efi,
        ...(payload.payment_providers.efi ?? {}),
      },
      asaas: {
        ...DEFAULT_PAYMENT_PROVIDERS_CONFIG.asaas,
        ...(payload.payment_providers.asaas ?? {}),
      },
    };
  } catch {
    return DEFAULT_PAYMENT_PROVIDERS_CONFIG;
  }
}

export function logoutAccount(): void {
  clearAuthTokens();
}
