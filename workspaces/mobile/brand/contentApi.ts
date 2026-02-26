/**
 * Contrato de conteudo dinamico para App Mobile.
 * Este modulo centraliza os endpoints usados para fotos e cardapio.
 */

export type MobilePortalSection = {
  id: number;
  key: string;
  title: string;
  body_json: unknown;
};

export type MobilePortalConfig = {
  active_template: string;
  auth_providers?: MobileAuthProvidersConfig;
  payment_providers?: MobilePaymentProvidersConfig;
  sections: MobilePortalSection[];
};

export type MobileGoogleAuthProvider = {
  enabled: boolean;
  configured: boolean;
  web_client_id: string;
  ios_client_id: string;
  android_client_id: string;
  auth_uri: string;
  token_uri: string;
  redirect_uri_web: string;
  redirect_uri_mobile: string;
  scope: string;
};

export type MobileAppleAuthProvider = {
  enabled: boolean;
  configured: boolean;
  service_id: string;
  team_id: string;
  key_id: string;
  auth_uri: string;
  token_uri: string;
  redirect_uri_web: string;
  redirect_uri_mobile: string;
  scope: string;
};

export type MobileAuthProvidersConfig = {
  google: MobileGoogleAuthProvider;
  apple: MobileAppleAuthProvider;
};

export type MobilePaymentProviderStatus = {
  enabled: boolean;
  configured: boolean;
  api_base_url: string;
  sandbox: boolean;
};

export type MobilePaymentProvidersConfig = {
  default_provider: string;
  enabled_providers: string[];
  method_provider_order: {
    PIX: string[];
    CARD: string[];
    VR: string[];
  };
  receiver: {
    person_type: "CPF" | "CNPJ";
    document: string;
    name: string;
    email: string;
  };
  mercadopago: MobilePaymentProviderStatus;
  efi: MobilePaymentProviderStatus;
  asaas: MobilePaymentProviderStatus;
};

export type MobileMenuDish = {
  id: number;
  name: string;
  yield_portions: number;
  image_url?: string | null;
  composition?: MobileDishCompositionItem[];
};

export type MobileDishCompositionItem = {
  id: number;
  quantity: string;
  unit: string;
  ingredient: {
    id: number;
    name: string;
    unit: string;
    image_url?: string | null;
  };
};

export type MobileMenuItem = {
  id: number;
  dish: MobileMenuDish;
  sale_price: string;
  available_qty: number | null;
  is_active: boolean;
};

export type MobileMenuDay = {
  id: number;
  menu_date: string;
  title: string;
  menu_items: MobileMenuItem[];
};

function normalizeBaseUrl(rawBaseUrl: string): string {
  const normalized = rawBaseUrl.trim();
  if (!normalized) {
    throw new Error("API base URL nao informada para o app mobile.");
  }
  return normalized.replace(/\/$/, "");
}

export async function fetchPortalHomeContent(
  apiBaseUrl: string,
): Promise<MobilePortalConfig> {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const response = await fetch(`${baseUrl}/api/v1/portal/config/?page=home`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Falha ao carregar portal mobile (HTTP ${response.status}).`);
  }

  return (await response.json()) as MobilePortalConfig;
}

export async function fetchMenuByDate(
  apiBaseUrl: string,
  menuDate: string,
): Promise<MobileMenuDay> {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const response = await fetch(
    `${baseUrl}/api/v1/catalog/menus/by-date/${encodeURIComponent(menuDate)}/`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw new Error(`Falha ao carregar cardapio mobile (HTTP ${response.status}).`);
  }

  return (await response.json()) as MobileMenuDay;
}
