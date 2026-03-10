"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";
import { InlinePreloader } from "@/components/InlinePreloader";
import { DatabaseSshAccessPanel } from "@/components/modules/DatabaseSshAccessPanel";

import {
  ApiError,
  applyPortalSslCertificatesAdmin,
  createMobileReleaseAdmin,
  ensurePortalConfigAdmin,
  listMobileReleasesAdmin,
  listPortalSectionsAdmin,
  managePortalCloudflareRuntimeAdmin,
  getPortalCloudflareApiStatusAdmin,
  previewPortalCloudflareAdmin,
  publishMobileReleaseAdmin,
  publishPortalConfigAdmin,
  testPortalEmailConfigAdmin,
  testPortalPaymentProviderAdmin,
  togglePortalCloudflareAdmin,
  updatePortalConfigAdmin,
  updatePortalSectionAdmin,
} from "@/lib/api";
import type {
  PortalCloudflareConfig,
  PortalCloudflareDevUrlMode,
  PortalCloudflareMode,
  PortalCloudflarePreviewData,
  PortalCloudflareRuntimeData,
  PortalCloudflareApiStatus,
  MobileReleaseData,
  PortalAsaasConfig,
  PortalAppleAuthConfig,
  PortalAuthProvidersConfig,
  PortalConfigData,
  PortalEmailSettingsConfig,
  PortalEfiConfig,
  PortalGoogleAuthConfig,
  PortalInstallerSettingsConfig,
  PortalMercadoPagoConfig,
  PortalPaymentProviderRouting,
  PortalPaymentProvidersConfig,
  PortalPaymentReceiverConfig,
  PortalSectionData,
  PortalSslCertificatesResult,
  PortalTemplateData,
} from "@/types/api";

export const PORTAL_BASE_PATH = "/modulos/portal";
export const SERVER_ADMIN_BASE_PATH = "/modulos/administracao-servidor";

export const PORTAL_MENU_ITEMS = [
  { key: "all", label: "Todos", href: PORTAL_BASE_PATH },
  { key: "template", label: "Template ativo", href: `${PORTAL_BASE_PATH}/template#template` },
  {
    key: "autenticacao",
    label: "Autenticacao social",
    href: `${PORTAL_BASE_PATH}/autenticacao#autenticacao`,
  },
  {
    key: "pagamentos",
    label: "Pagamentos",
    href: `${PORTAL_BASE_PATH}/pagamentos#pagamentos`,
  },
  { key: "conteudo", label: "Conteudo dinamico", href: `${PORTAL_BASE_PATH}/conteudo#conteudo` },
  { key: "publicacao", label: "Publicacao", href: `${PORTAL_BASE_PATH}/publicacao#publicacao` },
];

export const SERVER_ADMIN_MENU_ITEMS = [
  { key: "all", label: "Todos", href: SERVER_ADMIN_BASE_PATH },
  { key: "email", label: "Gestao de e-mail", href: `${SERVER_ADMIN_BASE_PATH}/email#email` },
  {
    key: "conectividade",
    label: "Conectividade e dominio",
    href: `${SERVER_ADMIN_BASE_PATH}/conectividade#conectividade`,
  },
  {
    key: "mobile-build",
    label: "Build e release",
    href: `${SERVER_ADMIN_BASE_PATH}/mobile-build#mobile-build`,
  },
];

export type PortalSectionKey =
  | "all"
  | "template"
  | "autenticacao"
  | "pagamentos"
  | "conteudo"
  | "publicacao";

export type ServerAdminSectionKey =
  | "all"
  | "email"
  | "conectividade"
  | "mobile-build";

type WebAdminEnvironmentMode = "dev" | "production" | "hybrid";

type PortalSectionsMode = "portal" | "server-admin";

type PortalSectionsProps = {
  activeSection?: PortalSectionKey | ServerAdminSectionKey;
  mode?: PortalSectionsMode;
};

type TemplateOption = {
  id: string;
  label: string;
};

type PortalPageOption = {
  value: string;
  label: string;
};

const TEMPLATE_LABEL_FALLBACK: Record<string, string> = {
  classic: "Classico",
  "letsfit-clean": "LetsFit Clean",
  "editorial-jp": "Editorial JP",
  "client-classic": "Cliente Classico",
  "client-quentinhas": "Cliente Quentinhas",
  "client-vitrine-fit": "Cliente Vitrine Fit",
  "client-editorial-jp": "Cliente Editorial JP",
  "admin-classic": "Admin Classico",
  "admin-adminkit": "Admin Operations Kit",
  "admin-admindek": "Admin Dek Prime",
};

const PORTAL_PAGE_LABELS: Record<string, string> = {
  home: "Home",
  cardapio: "Cardapio",
  app: "App",
  sobre: "Sobre",
  "como-funciona": "Como funciona",
  suporte: "Suporte",
  wiki: "Wiki",
  contato: "Contato",
  pedidos: "Pedidos",
  conta: "Conta",
  privacidade: "Privacidade",
  termos: "Termos",
  lgpd: "LGPD",
};

const PAYMENT_PROVIDER_OPTIONS = [
  { value: "mock", label: "Mock (desenvolvimento)" },
  { value: "mercadopago", label: "Mercado Pago" },
  { value: "efi", label: "Efi" },
  { value: "asaas", label: "Asaas" },
];

type SetupReferenceLink = {
  label: string;
  href: string;
  description: string;
};

const GOOGLE_AUTH_REFERENCE_LINKS: SetupReferenceLink[] = [
  {
    label: "Google Cloud Console",
    href: "https://console.cloud.google.com/apis/credentials",
    description: "Criar projeto OAuth e gerar Client ID/Client Secret.",
  },
  {
    label: "Tela de consentimento OAuth",
    href: "https://console.cloud.google.com/apis/credentials/consent",
    description: "Configurar app name, escopos e usuarios de teste.",
  },
  {
    label: "Guia oficial Google OAuth",
    href: "https://developers.google.com/identity/protocols/oauth2",
    description: "Referencia oficial de fluxo e campos necessarios.",
  },
];

const APPLE_AUTH_REFERENCE_LINKS: SetupReferenceLink[] = [
  {
    label: "Apple Developer Program",
    href: "https://developer.apple.com/programs/",
    description: "Assinatura necessaria para usar Sign in with Apple.",
  },
  {
    label: "Identifiers (Service ID)",
    href: "https://developer.apple.com/account/resources/identifiers/list",
    description: "Criar Service ID, Key ID e configurar redirect URLs.",
  },
  {
    label: "Guia oficial Sign in with Apple",
    href: "https://developer.apple.com/documentation/sign_in_with_apple",
    description: "Referencia oficial para Service ID, Team ID e Private Key.",
  },
];

const MERCADOPAGO_REFERENCE_LINKS: SetupReferenceLink[] = [
  {
    label: "Criar conta Mercado Pago",
    href: "https://www.mercadopago.com.br/developers/panel",
    description: "Cadastro e acesso ao painel de desenvolvedor.",
  },
  {
    label: "Credenciais de API",
    href: "https://www.mercadopago.com.br/developers/panel/credentials",
    description: "Obter Access Token de teste/producao.",
  },
  {
    label: "Documentacao Mercado Pago",
    href: "https://www.mercadopago.com.br/developers/pt/docs",
    description: "Guia completo de integracao e webhooks.",
  },
];

const EFI_REFERENCE_LINKS: SetupReferenceLink[] = [
  {
    label: "Cadastro Efi",
    href: "https://sejaefi.com.br/",
    description: "Abrir conta e habilitar ambiente para API.",
  },
  {
    label: "Painel de aplicacoes Efi",
    href: "https://sejaefi.com.br/minha-conta/aplicacoes",
    description: "Gerar Client ID e Client Secret para integracao.",
  },
  {
    label: "Documentacao Efi API",
    href: "https://dev.sejaefi.com.br/docs/api",
    description: "Referencia oficial de endpoints e autenticacao.",
  },
];

const ASAAS_REFERENCE_LINKS: SetupReferenceLink[] = [
  {
    label: "Cadastro Asaas",
    href: "https://www.asaas.com/",
    description: "Criar conta para operar pagamentos.",
  },
  {
    label: "Gerar API Key",
    href: "https://docs.asaas.com/docs/get-started#obtendo-sua-api-key",
    description: "Passo a passo para chave de integracao.",
  },
  {
    label: "Documentacao Asaas",
    href: "https://docs.asaas.com/",
    description: "Guia oficial de cobrancas, webhooks e seguranca.",
  },
];

const DEFAULT_MOBILE_API_PUBLIC_IP_URL = "http://44.192.27.104";
const DEFAULT_MOBILE_API_AWS_DNS_URL =
  "http://ec2-44-192-27-104.compute-1.amazonaws.com";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar configuracoes do portal.";
}

function normalizeTemplateOptions(
  availableTemplates: Array<PortalTemplateData | string>,
): TemplateOption[] {
  const templateMap = new Map<string, TemplateOption>();

  for (const item of availableTemplates) {
    if (typeof item === "string") {
      const templateId = item.trim();
      if (!templateId) {
        continue;
      }

      templateMap.set(templateId, {
        id: templateId,
        label: TEMPLATE_LABEL_FALLBACK[templateId] ?? templateId,
      });
      continue;
    }

    const templateId = item.id?.trim();
    if (!templateId) {
      continue;
    }

    templateMap.set(templateId, {
      id: templateId,
      label: item.label?.trim() || TEMPLATE_LABEL_FALLBACK[templateId] || templateId,
    });
  }

  return Array.from(templateMap.values());
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "Nao publicado";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("pt-BR");
}

function formatPortalPageLabel(page: string): string {
  return PORTAL_PAGE_LABELS[page] ?? page;
}

function formatReleaseStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    QUEUED: "Na fila",
    BUILDING: "Compilando",
    TESTING: "Testando",
    SIGNED: "Assinado",
    PUBLISHED: "Publicado",
    FAILED: "Falhou",
  };
  return labels[status] ?? status;
}

function resolveReleaseStatusTone(status: string): "success" | "warning" | "danger" | "info" | "neutral" {
  if (status === "PUBLISHED") {
    return "success";
  }
  if (status === "SIGNED" || status === "BUILDING" || status === "TESTING") {
    return "info";
  }
  if (status === "FAILED") {
    return "danger";
  }
  if (status === "QUEUED") {
    return "warning";
  }
  return "neutral";
}

function resolveCloudflareConnectivityTone(
  connectivity: string | undefined,
): "success" | "warning" | "danger" | "info" | "neutral" {
  if (connectivity === "online") {
    return "success";
  }
  if (connectivity === "offline") {
    return "danger";
  }
  return "neutral";
}

function formatCloudflareConnectivityLabel(connectivity: string | undefined): string {
  if (connectivity === "online") {
    return "Online";
  }
  if (connectivity === "offline") {
    return "Offline";
  }
  return "Sem teste";
}

function stringifyBodyJson(value: unknown): string {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return "{}";
  }
}

function parseBodyJson(value: string): unknown {
  const normalized = value.trim();
  if (!normalized) {
    return {};
  }

  return JSON.parse(normalized) as unknown;
}

function stringifyOrigins(origins: string[] | undefined): string {
  if (!Array.isArray(origins) || origins.length === 0) {
    return "";
  }

  return origins.join("\n");
}

function parseOrigins(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function isHttpUrl(value: string): boolean {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function ExternalUrl({ value }: { value: string | null | undefined }) {
  const normalized = String(value ?? "").trim();
  if (!normalized || !isHttpUrl(normalized)) {
    return <code>{normalized || "-"}</code>;
  }

  return (
    <a
      href={normalized}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary underline decoration-primary/50 underline-offset-2 hover:no-underline"
    >
      <code>{normalized}</code>
    </a>
  );
}

function SetupReferenceLinks({
  title,
  links,
}: {
  title: string;
  links: SetupReferenceLink[];
}) {
  return (
    <article className="rounded-md border border-border bg-surface/70 p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.08em] text-primary">{title}</p>
      <div className="mt-2 grid gap-2">
        {links.map((link) => (
          <p key={`${title}-${link.href}`} className="text-xs text-muted">
            <a
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-primary underline decoration-primary/50 underline-offset-2 hover:no-underline"
            >
              {link.label}
            </a>
            {" - "}
            {link.description}
          </p>
        ))}
      </div>
    </article>
  );
}

function parseProviderOrder(value: string): string[] {
  const allowed = new Set(PAYMENT_PROVIDER_OPTIONS.map((option) => option.value));
  const providers = value
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter((item) => item.length > 0 && allowed.has(item));

  if (providers.length === 0) {
    return ["mock"];
  }

  return Array.from(new Set(providers));
}

function resolveHostFromApiBaseUrl(value: string): string {
  try {
    const parsed = new URL(value.trim());
    return parsed.hostname || "10.211.55.21";
  } catch {
    return "10.211.55.21";
  }
}

function getDefaultGoogleAuthConfig(): PortalGoogleAuthConfig {
  return {
    enabled: false,
    web_client_id: "",
    ios_client_id: "",
    android_client_id: "",
    client_secret: "",
    auth_uri: "https://accounts.google.com/o/oauth2/v2/auth",
    token_uri: "https://oauth2.googleapis.com/token",
    redirect_uri_web: "https://www.mrquentinha.com.br/conta/oauth/google/callback",
    redirect_uri_mobile: "mrquentinha://oauth/google/callback",
    scope: "openid email profile",
  };
}

function getDefaultAppleAuthConfig(): PortalAppleAuthConfig {
  return {
    enabled: false,
    service_id: "",
    team_id: "",
    key_id: "",
    private_key: "",
    auth_uri: "https://appleid.apple.com/auth/authorize",
    token_uri: "https://appleid.apple.com/auth/token",
    redirect_uri_web: "https://www.mrquentinha.com.br/conta/oauth/apple/callback",
    redirect_uri_mobile: "mrquentinha://oauth/apple/callback",
    scope: "name email",
  };
}

function normalizeAuthProviders(
  value: PortalAuthProvidersConfig | null | undefined,
): PortalAuthProvidersConfig {
  return {
    google: {
      ...getDefaultGoogleAuthConfig(),
      ...(value?.google ?? {}),
    },
    apple: {
      ...getDefaultAppleAuthConfig(),
      ...(value?.apple ?? {}),
    },
  };
}

function getDefaultPaymentReceiver(): PortalPaymentReceiverConfig {
  return {
    person_type: "CNPJ",
    document: "",
    name: "",
    email: "",
  };
}

function getDefaultPaymentRouting(): PortalPaymentProviderRouting {
  return {
    PIX: ["mock"],
    CARD: ["mock"],
    VR: ["mock"],
  };
}

function getDefaultPaymentFrontendProvider(): { web: string; mobile: string } {
  return {
    web: "mock",
    mobile: "mock",
  };
}

function getDefaultMercadoPagoConfig(): PortalMercadoPagoConfig {
  return {
    enabled: false,
    api_base_url: "https://api.mercadopago.com",
    access_token: "",
    webhook_secret: "",
    sandbox: true,
  };
}

function getDefaultEfiConfig(): PortalEfiConfig {
  return {
    enabled: false,
    api_base_url: "https://cobrancas-h.api.efipay.com.br",
    client_id: "",
    client_secret: "",
    webhook_secret: "",
    sandbox: true,
  };
}

function getDefaultAsaasConfig(): PortalAsaasConfig {
  return {
    enabled: false,
    api_base_url: "https://sandbox.asaas.com/api/v3",
    api_key: "",
    webhook_secret: "",
    sandbox: true,
  };
}

function normalizePaymentProviders(
  value: PortalPaymentProvidersConfig | null | undefined,
): PortalPaymentProvidersConfig {
  const defaultRouting = getDefaultPaymentRouting();
  return {
    default_provider: value?.default_provider?.trim() || "mock",
    enabled_providers:
      value?.enabled_providers
        ?.map((item) => item.trim().toLowerCase())
        .filter((item) => item.length > 0) ?? ["mock"],
    frontend_provider: {
      ...getDefaultPaymentFrontendProvider(),
      ...(value?.frontend_provider ?? {}),
    },
    method_provider_order: {
      PIX:
        value?.method_provider_order?.PIX?.map((item) => item.trim().toLowerCase()).filter(Boolean) ??
        defaultRouting.PIX,
      CARD:
        value?.method_provider_order?.CARD?.map((item) => item.trim().toLowerCase()).filter(Boolean) ??
        defaultRouting.CARD,
      VR:
        value?.method_provider_order?.VR?.map((item) => item.trim().toLowerCase()).filter(Boolean) ??
        defaultRouting.VR,
    },
    receiver: {
      ...getDefaultPaymentReceiver(),
      ...(value?.receiver ?? {}),
    },
    mercadopago: {
      ...getDefaultMercadoPagoConfig(),
      ...(value?.mercadopago ?? {}),
    },
    efi: {
      ...getDefaultEfiConfig(),
      ...(value?.efi ?? {}),
    },
    asaas: {
      ...getDefaultAsaasConfig(),
      ...(value?.asaas ?? {}),
    },
  };
}

function getDefaultEmailSettings(): PortalEmailSettingsConfig {
  return {
    enabled: false,
    backend: "django.core.mail.backends.smtp.EmailBackend",
    host: "",
    port: 587,
    username: "",
    password: "",
    use_tls: true,
    use_ssl: false,
    timeout_seconds: 15,
    from_name: "Mr Quentinha",
    from_email: "noreply@mrquentinha.local",
    reply_to_email: "",
    test_recipient: "",
  };
}

function normalizeEmailSettings(
  value: PortalEmailSettingsConfig | null | undefined,
): PortalEmailSettingsConfig {
  const defaults = getDefaultEmailSettings();
  const merged = {
    ...defaults,
    ...(value ?? {}),
  };
  const port = Number.isFinite(Number(merged.port))
    ? Number.parseInt(String(merged.port), 10)
    : defaults.port;
  const timeoutSeconds = Number.isFinite(Number(merged.timeout_seconds))
    ? Number.parseInt(String(merged.timeout_seconds), 10)
    : defaults.timeout_seconds;
  return {
    ...merged,
    port: Math.min(65535, Math.max(1, port || defaults.port)),
    timeout_seconds: Math.min(120, Math.max(1, timeoutSeconds || defaults.timeout_seconds)),
    use_ssl: merged.use_tls && merged.use_ssl ? false : merged.use_ssl,
  };
}

function getDefaultCloudflareSettings(): PortalCloudflareConfig {
  return {
    enabled: false,
    mode: "hybrid",
    dev_mode: false,
    dev_url_mode: "random",
    dev_official_domain: "dev.mrquentinha.com.br",
    scheme: "https",
    root_domain: "mrquentinha.com.br",
    subdomains: {
      portal: "www",
      client: "app",
      admin: "admin",
      api: "api",
    },
    tunnel_name: "mrquentinha",
    tunnel_id: "",
    tunnel_token: "",
    account_id: "",
    zone_id: "",
    api_token: "",
    auto_apply_routes: true,
    last_action_at: "",
    last_status_message: "Cloudflare desativado.",
    runtime: {
      state: "inactive",
      last_started_at: "",
      last_stopped_at: "",
      last_error: "",
      run_command: "",
    },
    dev_urls: {
      portal: "",
      client: "",
      admin: "",
      api: "",
    },
    dev_manual_urls: {
      portal: "https://portal-mrquentinha.trycloudflare.com",
      client: "https://cliente-mrquentinha.trycloudflare.com",
      admin: "https://admin-mrquentinha.trycloudflare.com",
      api: "https://api-mrquentinha.trycloudflare.com",
    },
    local_snapshot: {},
  };
}

function normalizeCloudflareSettings(
  value: PortalCloudflareConfig | null | undefined,
): PortalCloudflareConfig {
  const defaults = getDefaultCloudflareSettings();
  const normalizedMode =
    value?.mode === "local_only" ||
    value?.mode === "cloudflare_only" ||
    value?.mode === "hybrid"
      ? value.mode
      : defaults.mode;
  const normalizedScheme =
    value?.scheme === "http" || value?.scheme === "https" ? value.scheme : defaults.scheme;
  const normalizedDevUrlMode =
    value?.dev_url_mode === "manual" ||
    value?.dev_url_mode === "random" ||
    value?.dev_url_mode === "official"
      ? value.dev_url_mode
      : defaults.dev_url_mode;

  return {
    ...defaults,
    ...(value ?? {}),
    mode: normalizedMode,
    dev_url_mode: normalizedDevUrlMode,
    scheme: normalizedScheme,
    dev_official_domain:
      typeof value?.dev_official_domain === "string" && value.dev_official_domain.trim()
        ? value.dev_official_domain.trim()
        : defaults.dev_official_domain,
    subdomains: {
      ...defaults.subdomains,
      ...(value?.subdomains ?? {}),
    },
    runtime: {
      ...defaults.runtime,
      ...(value?.runtime ?? {}),
    },
    dev_urls: {
      ...defaults.dev_urls,
      ...(value?.dev_urls ?? {}),
    },
    dev_manual_urls: {
      ...defaults.dev_manual_urls,
      ...(value?.dev_manual_urls ?? {}),
    },
    local_snapshot: value?.local_snapshot ?? {},
  };
}

function deriveEnvironmentModeFromDraft(
  mode: PortalCloudflareMode,
  devMode: boolean,
): WebAdminEnvironmentMode {
  if (mode === "hybrid") {
    return "hybrid";
  }
  if (devMode) {
    return "dev";
  }
  return "production";
}

function normalizeOperationModeSettings(
  value: PortalInstallerSettingsConfig | null | undefined,
  cloudflareMode: PortalCloudflareMode,
  devMode: boolean,
): "dev" | "prod" | "hybrid" {
  const storedMode = value?.operation_mode;
  if (storedMode === "dev" || storedMode === "prod" || storedMode === "hybrid") {
    return storedMode;
  }

  const derivedMode = deriveEnvironmentModeFromDraft(cloudflareMode, devMode);
  if (derivedMode === "hybrid") {
    return "hybrid";
  }
  if (derivedMode === "production") {
    return "prod";
  }
  return "dev";
}

function getDefaultApiPublicAccessSettings(): PortalInstallerSettingsConfig["api_public_access"] {
  return {
    enabled: false,
    preferred_endpoint: "public_ip",
    public_ip_base_url: DEFAULT_MOBILE_API_PUBLIC_IP_URL,
    aws_dns_base_url: DEFAULT_MOBILE_API_AWS_DNS_URL,
  };
}

function normalizeApiPublicAccessSettings(
  value: PortalInstallerSettingsConfig | null | undefined,
): PortalInstallerSettingsConfig["api_public_access"] {
  const defaults = getDefaultApiPublicAccessSettings();
  const source = value?.api_public_access;
  if (!source) {
    return defaults;
  }

  const preferredEndpoint =
    source.preferred_endpoint === "aws_dns" || source.preferred_endpoint === "public_ip"
      ? source.preferred_endpoint
      : defaults.preferred_endpoint;

  return {
    enabled: Boolean(source.enabled),
    preferred_endpoint: preferredEndpoint,
    public_ip_base_url: source.public_ip_base_url?.trim() || defaults.public_ip_base_url,
    aws_dns_base_url: source.aws_dns_base_url?.trim() || defaults.aws_dns_base_url,
  };
}

export function PortalSections({
  activeSection = "all",
  mode = "portal",
}: PortalSectionsProps) {
  const [config, setConfig] = useState<PortalConfigData | null>(null);
  const [sections, setSections] = useState<PortalSectionData[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [selectedClientTemplateId, setSelectedClientTemplateId] = useState("");
  const [selectedAdminTemplateId, setSelectedAdminTemplateId] = useState("");
  const [contentTemplateId, setContentTemplateId] = useState("");
  const [contentPageFilter, setContentPageFilter] = useState("all");
  const [selectedSectionId, setSelectedSectionId] = useState("");
  const [sectionTitleDraft, setSectionTitleDraft] = useState("");
  const [sectionSortOrderDraft, setSectionSortOrderDraft] = useState("0");
  const [sectionEnabledDraft, setSectionEnabledDraft] = useState(true);
  const [sectionBodyJsonDraft, setSectionBodyJsonDraft] = useState("{}");
  const [localHostnameDraft, setLocalHostnameDraft] = useState("mrquentinha");
  const [localNetworkIpDraft, setLocalNetworkIpDraft] = useState("");
  const [operationModeDraft, setOperationModeDraft] =
    useState<WebAdminEnvironmentMode>("dev");
  const [rootDomainDraft, setRootDomainDraft] = useState("mrquentinha.local");
  const [portalDomainDraft, setPortalDomainDraft] = useState("www.mrquentinha.local");
  const [clientDomainDraft, setClientDomainDraft] = useState("app.mrquentinha.local");
  const [adminDomainDraft, setAdminDomainDraft] = useState("admin.mrquentinha.local");
  const [apiDomainDraft, setApiDomainDraft] = useState("api.mrquentinha.local");
  const [apiBaseUrlDraft, setApiBaseUrlDraft] = useState("https://10.211.55.21:8000");
  const [mobileApiPublicEnabledDraft, setMobileApiPublicEnabledDraft] = useState(false);
  const [mobileApiPreferredEndpointDraft, setMobileApiPreferredEndpointDraft] = useState<
    "public_ip" | "aws_dns"
  >("public_ip");
  const [mobileApiPublicIpUrlDraft, setMobileApiPublicIpUrlDraft] = useState(
    DEFAULT_MOBILE_API_PUBLIC_IP_URL,
  );
  const [mobileApiAwsDnsUrlDraft, setMobileApiAwsDnsUrlDraft] = useState(
    DEFAULT_MOBILE_API_AWS_DNS_URL,
  );
  const [portalBaseUrlDraft, setPortalBaseUrlDraft] = useState("https://10.211.55.21:3000");
  const [clientBaseUrlDraft, setClientBaseUrlDraft] = useState("https://10.211.55.21:3001");
  const [adminBaseUrlDraft, setAdminBaseUrlDraft] = useState("https://10.211.55.21:3002");
  const [backendBaseUrlDraft, setBackendBaseUrlDraft] = useState("https://10.211.55.21:8000");
  const [proxyBaseUrlDraft, setProxyBaseUrlDraft] = useState("https://10.211.55.21:8088");
  const [corsAllowedOriginsDraft, setCorsAllowedOriginsDraft] = useState("");
  const [cloudflareEnabledDraft, setCloudflareEnabledDraft] = useState(false);
  const [cloudflareModeDraft, setCloudflareModeDraft] = useState<PortalCloudflareMode>("hybrid");
  const [cloudflareDevModeDraft, setCloudflareDevModeDraft] = useState(false);
  const [cloudflareDevUrlModeDraft, setCloudflareDevUrlModeDraft] =
    useState<PortalCloudflareDevUrlMode>("random");
  const [cloudflareDevOfficialDomainDraft, setCloudflareDevOfficialDomainDraft] = useState(
    "dev.mrquentinha.com.br",
  );
  const [cloudflareSchemeDraft, setCloudflareSchemeDraft] = useState<"http" | "https">("https");
  const [cloudflareRootDomainDraft, setCloudflareRootDomainDraft] = useState("mrquentinha.com.br");
  const [cloudflarePortalSubdomainDraft, setCloudflarePortalSubdomainDraft] = useState("www");
  const [cloudflareClientSubdomainDraft, setCloudflareClientSubdomainDraft] = useState("app");
  const [cloudflareAdminSubdomainDraft, setCloudflareAdminSubdomainDraft] = useState("admin");
  const [cloudflareApiSubdomainDraft, setCloudflareApiSubdomainDraft] = useState("api");
  const [cloudflareTunnelNameDraft, setCloudflareTunnelNameDraft] = useState("mrquentinha");
  const [cloudflareTunnelIdDraft, setCloudflareTunnelIdDraft] = useState("");
  const [cloudflareTunnelTokenDraft, setCloudflareTunnelTokenDraft] = useState("");
  const [cloudflareAccountIdDraft, setCloudflareAccountIdDraft] = useState("");
  const [cloudflareZoneIdDraft, setCloudflareZoneIdDraft] = useState("");
  const [cloudflareApiTokenDraft, setCloudflareApiTokenDraft] = useState("");
  const [cloudflareAutoApplyRoutesDraft, setCloudflareAutoApplyRoutesDraft] = useState(true);
  const [cloudflarePortalDevUrlDraft, setCloudflarePortalDevUrlDraft] = useState("");
  const [cloudflareClientDevUrlDraft, setCloudflareClientDevUrlDraft] = useState("");
  const [cloudflareAdminDevUrlDraft, setCloudflareAdminDevUrlDraft] = useState("");
  const [cloudflareApiDevUrlDraft, setCloudflareApiDevUrlDraft] = useState("");
  const [cloudflarePreview, setCloudflarePreview] = useState<PortalCloudflarePreviewData | null>(
    null,
  );
  const [cloudflareRuntime, setCloudflareRuntime] = useState<PortalCloudflareRuntimeData | null>(
    null,
  );
  const [cloudflareApiStatus, setCloudflareApiStatus] = useState<PortalCloudflareApiStatus | null>(
    null,
  );
  const [cloudflareSaving, setCloudflareSaving] = useState(false);
  const [googleEnabledDraft, setGoogleEnabledDraft] = useState(false);
  const [googleWebClientIdDraft, setGoogleWebClientIdDraft] = useState("");
  const [googleIosClientIdDraft, setGoogleIosClientIdDraft] = useState("");
  const [googleAndroidClientIdDraft, setGoogleAndroidClientIdDraft] = useState("");
  const [googleClientSecretDraft, setGoogleClientSecretDraft] = useState("");
  const [googleAuthUriDraft, setGoogleAuthUriDraft] = useState(
    "https://accounts.google.com/o/oauth2/v2/auth",
  );
  const [googleTokenUriDraft, setGoogleTokenUriDraft] = useState(
    "https://oauth2.googleapis.com/token",
  );
  const [googleRedirectWebDraft, setGoogleRedirectWebDraft] = useState(
    "https://www.mrquentinha.com.br/conta/oauth/google/callback",
  );
  const [googleRedirectMobileDraft, setGoogleRedirectMobileDraft] = useState(
    "mrquentinha://oauth/google/callback",
  );
  const [googleScopeDraft, setGoogleScopeDraft] = useState("openid email profile");
  const [appleEnabledDraft, setAppleEnabledDraft] = useState(false);
  const [appleServiceIdDraft, setAppleServiceIdDraft] = useState("");
  const [appleTeamIdDraft, setAppleTeamIdDraft] = useState("");
  const [appleKeyIdDraft, setAppleKeyIdDraft] = useState("");
  const [applePrivateKeyDraft, setApplePrivateKeyDraft] = useState("");
  const [appleAuthUriDraft, setAppleAuthUriDraft] = useState(
    "https://appleid.apple.com/auth/authorize",
  );
  const [appleTokenUriDraft, setAppleTokenUriDraft] = useState(
    "https://appleid.apple.com/auth/token",
  );
  const [appleRedirectWebDraft, setAppleRedirectWebDraft] = useState(
    "https://www.mrquentinha.com.br/conta/oauth/apple/callback",
  );
  const [appleRedirectMobileDraft, setAppleRedirectMobileDraft] = useState(
    "mrquentinha://oauth/apple/callback",
  );
  const [appleScopeDraft, setAppleScopeDraft] = useState("name email");
  const [paymentDefaultProviderDraft, setPaymentDefaultProviderDraft] = useState("mock");
  const [paymentEnabledProvidersDraft, setPaymentEnabledProvidersDraft] = useState<string[]>([
    "mock",
  ]);
  const [paymentWebProviderDraft, setPaymentWebProviderDraft] = useState("mock");
  const [paymentMobileProviderDraft, setPaymentMobileProviderDraft] = useState("mock");
  const [paymentPixOrderDraft, setPaymentPixOrderDraft] = useState("mock");
  const [paymentCardOrderDraft, setPaymentCardOrderDraft] = useState("mock");
  const [paymentVrOrderDraft, setPaymentVrOrderDraft] = useState("mock");
  const [receiverPersonTypeDraft, setReceiverPersonTypeDraft] = useState<"CPF" | "CNPJ">(
    "CNPJ",
  );
  const [receiverDocumentDraft, setReceiverDocumentDraft] = useState("");
  const [receiverNameDraft, setReceiverNameDraft] = useState("");
  const [receiverEmailDraft, setReceiverEmailDraft] = useState("");
  const [mercadoPagoEnabledDraft, setMercadoPagoEnabledDraft] = useState(false);
  const [mercadoPagoApiBaseUrlDraft, setMercadoPagoApiBaseUrlDraft] = useState(
    "https://api.mercadopago.com",
  );
  const [mercadoPagoAccessTokenDraft, setMercadoPagoAccessTokenDraft] = useState("");
  const [mercadoPagoWebhookSecretDraft, setMercadoPagoWebhookSecretDraft] = useState("");
  const [mercadoPagoSandboxDraft, setMercadoPagoSandboxDraft] = useState(true);
  const [efiEnabledDraft, setEfiEnabledDraft] = useState(false);
  const [efiApiBaseUrlDraft, setEfiApiBaseUrlDraft] = useState(
    "https://cobrancas-h.api.efipay.com.br",
  );
  const [efiClientIdDraft, setEfiClientIdDraft] = useState("");
  const [efiClientSecretDraft, setEfiClientSecretDraft] = useState("");
  const [efiWebhookSecretDraft, setEfiWebhookSecretDraft] = useState("");
  const [efiSandboxDraft, setEfiSandboxDraft] = useState(true);
  const [asaasEnabledDraft, setAsaasEnabledDraft] = useState(false);
  const [asaasApiBaseUrlDraft, setAsaasApiBaseUrlDraft] = useState(
    "https://sandbox.asaas.com/api/v3",
  );
  const [asaasApiKeyDraft, setAsaasApiKeyDraft] = useState("");
  const [asaasWebhookSecretDraft, setAsaasWebhookSecretDraft] = useState("");
  const [asaasSandboxDraft, setAsaasSandboxDraft] = useState(true);
  const [emailEnabledDraft, setEmailEnabledDraft] = useState(false);
  const [emailBackendDraft, setEmailBackendDraft] = useState(
    "django.core.mail.backends.smtp.EmailBackend",
  );
  const [emailHostDraft, setEmailHostDraft] = useState("");
  const [emailPortDraft, setEmailPortDraft] = useState("587");
  const [emailUsernameDraft, setEmailUsernameDraft] = useState("");
  const [emailPasswordDraft, setEmailPasswordDraft] = useState("");
  const [emailUseTlsDraft, setEmailUseTlsDraft] = useState(true);
  const [emailUseSslDraft, setEmailUseSslDraft] = useState(false);
  const [emailTimeoutDraft, setEmailTimeoutDraft] = useState("15");
  const [emailFromNameDraft, setEmailFromNameDraft] = useState("Mr Quentinha");
  const [emailFromAddressDraft, setEmailFromAddressDraft] = useState(
    "noreply@mrquentinha.local",
  );
  const [emailReplyToDraft, setEmailReplyToDraft] = useState("");
  const [emailTestRecipientDraft, setEmailTestRecipientDraft] = useState("");
  const [sslEmailDraft, setSslEmailDraft] = useState("");
  const [sslDomainsDraft, setSslDomainsDraft] = useState("");
  const [sslApplying, setSslApplying] = useState(false);
  const [sslResult, setSslResult] = useState<PortalSslCertificatesResult | null>(null);
  const [testingEmail, setTestingEmail] = useState(false);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [mobileReleases, setMobileReleases] = useState<MobileReleaseData[]>([]);
  const [releaseVersionDraft, setReleaseVersionDraft] = useState("");
  const [releaseBuildNumberDraft, setReleaseBuildNumberDraft] = useState("1");
  const [releaseMinVersionDraft, setReleaseMinVersionDraft] = useState("");
  const [releaseRecommendedVersionDraft, setReleaseRecommendedVersionDraft] = useState("");
  const [releaseNotesDraft, setReleaseNotesDraft] = useState("");
  const [releaseCriticalDraft, setReleaseCriticalDraft] = useState(false);
  const [releasePolicyDraft, setReleasePolicyDraft] = useState<"OPTIONAL" | "FORCE">(
    "OPTIONAL",
  );

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [compilingRelease, setCompilingRelease] = useState(false);
  const [publishingReleaseId, setPublishingReleaseId] = useState<number | null>(null);
  const [savingSection, setSavingSection] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [refreshingSections, setRefreshingSections] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const templateOptions = useMemo(() => {
    if (!config) {
      return [] as TemplateOption[];
    }

    return normalizeTemplateOptions(config.available_templates);
  }, [config]);

  const clientTemplateOptions = useMemo(() => {
    if (!config) {
      return [] as TemplateOption[];
    }

    return normalizeTemplateOptions(config.client_available_templates);
  }, [config]);

  const adminTemplateOptions = useMemo(() => {
    if (!config) {
      return [] as TemplateOption[];
    }

    return normalizeTemplateOptions(config.admin_available_templates);
  }, [config]);

  const contentTemplateOptions = useMemo(() => {
    const optionMap = new Map<string, TemplateOption>();
    for (const option of templateOptions) {
      optionMap.set(option.id, option);
    }
    for (const option of clientTemplateOptions) {
      optionMap.set(option.id, option);
    }
    for (const option of adminTemplateOptions) {
      optionMap.set(option.id, option);
    }
    return Array.from(optionMap.values());
  }, [adminTemplateOptions, clientTemplateOptions, templateOptions]);

  const pageOptions = useMemo<PortalPageOption[]>(() => {
    const values = new Set<string>();
    for (const section of sections) {
      values.add(section.page);
    }

    const sortedValues = Array.from(values).sort((left, right) =>
      formatPortalPageLabel(left).localeCompare(formatPortalPageLabel(right), "pt-BR"),
    );

    return [
      { value: "all", label: "Todas as paginas" },
      ...sortedValues.map((value) => ({
        value,
        label: formatPortalPageLabel(value),
      })),
    ];
  }, [sections]);

  const filteredSections = useMemo(() => {
    return sections
      .filter((section) => {
        const byTemplate = contentTemplateId ? section.template_id === contentTemplateId : true;
        const byPage = contentPageFilter === "all" ? true : section.page === contentPageFilter;
        return byTemplate && byPage;
      })
      .sort((left, right) => {
        if (left.sort_order !== right.sort_order) {
          return left.sort_order - right.sort_order;
        }
        return left.id - right.id;
      });
  }, [contentPageFilter, contentTemplateId, sections]);

  const selectedSection = useMemo(
    () =>
      filteredSections.find(
        (section) => String(section.id) === selectedSectionId,
      ) ?? null,
    [filteredSections, selectedSectionId],
  );

  const activeTemplateLabel = useMemo(() => {
    if (!config) {
      return "-";
    }

    return (
      templateOptions.find((option) => option.id === config.active_template)?.label ??
      TEMPLATE_LABEL_FALLBACK[config.active_template] ??
      config.active_template
    );
  }, [config, templateOptions]);

  const activeClientTemplateLabel = useMemo(() => {
    if (!config) {
      return "-";
    }

    return (
      clientTemplateOptions.find(
        (option) => option.id === config.client_active_template,
      )?.label ??
      TEMPLATE_LABEL_FALLBACK[config.client_active_template] ??
      config.client_active_template
    );
  }, [clientTemplateOptions, config]);

  const activeAdminTemplateLabel = useMemo(() => {
    if (!config) {
      return "-";
    }

    return (
      adminTemplateOptions.find(
        (option) => option.id === config.admin_active_template,
      )?.label ??
      TEMPLATE_LABEL_FALLBACK[config.admin_active_template] ??
      config.admin_active_template
    );
  }, [adminTemplateOptions, config]);

  const derivedPublicHost = useMemo(
    () => resolveHostFromApiBaseUrl(apiBaseUrlDraft),
    [apiBaseUrlDraft],
  );
  const environmentModeDraft = operationModeDraft;
  const isHybridEnvironmentMode = environmentModeDraft === "hybrid";
  const isProductionEnvironmentMode = environmentModeDraft === "production";
  const customDevHostsEnabled = cloudflareDevUrlModeDraft === "manual";
  const officialDevHostsEnabled = cloudflareDevUrlModeDraft === "official";
  const selectedFrontendProviders = useMemo(
    () =>
      new Set(
        [paymentWebProviderDraft, paymentMobileProviderDraft]
          .map((item) => item.trim().toLowerCase())
          .filter((item) => item.length > 0),
      ),
    [paymentMobileProviderDraft, paymentWebProviderDraft],
  );
  const derivedAndroidDownloadUrl = `https://${derivedPublicHost}:3000/app/downloads/android.apk`;
  const derivedIosDownloadUrl = `https://${derivedPublicHost}:3000/app/downloads/ios`;

  function handleEnvironmentModeChange(nextMode: WebAdminEnvironmentMode) {
    setOperationModeDraft(nextMode);

    if (nextMode === "hybrid") {
      setCloudflareModeDraft("hybrid");
      setSuccessMessage(
        "Modo hibrido selecionado: rede local e Cloudflare podem coexistir.",
      );
      setErrorMessage("");
      return;
    }

    if (nextMode === "dev") {
      setCloudflareModeDraft("local_only");
      setCloudflareDevModeDraft(true);
      if (cloudflareDevUrlModeDraft === "random") {
        setCloudflareDevUrlModeDraft("manual");
      }
      setSuccessMessage(
        "Modo dev selecionado: foco em rede local e ambientes de teste controlados.",
      );
      setErrorMessage("");
      return;
    }

    setCloudflareModeDraft("local_only");
    setCloudflareDevModeDraft(false);
    if (cloudflareDevUrlModeDraft === "random") {
      setCloudflareDevUrlModeDraft("manual");
    }
    setSuccessMessage(
      "Modo producao selecionado: URLs DEV random foram desativadas por seguranca.",
    );
    setErrorMessage("");
  }

  async function handleCloudflareApiStatus() {
    setCloudflareSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const payload = await getPortalCloudflareApiStatusAdmin(
        buildCloudflareSettingsDraftPayload(),
      );
      setCloudflareApiStatus(payload);
      setSuccessMessage("Diagnostico Cloudflare API atualizado.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCloudflareSaving(false);
    }
  }

  function buildCloudflareSettingsDraftPayload(): PortalCloudflareConfig {
    const base = normalizeCloudflareSettings(config?.cloudflare_settings);
    return {
      ...base,
      enabled: cloudflareEnabledDraft,
      mode: cloudflareModeDraft,
      dev_mode: cloudflareDevModeDraft,
      dev_url_mode: cloudflareDevUrlModeDraft,
      dev_official_domain: cloudflareDevOfficialDomainDraft.trim(),
      scheme: cloudflareSchemeDraft,
      root_domain: cloudflareRootDomainDraft.trim(),
      subdomains: {
        portal: cloudflarePortalSubdomainDraft.trim(),
        client: cloudflareClientSubdomainDraft.trim(),
        admin: cloudflareAdminSubdomainDraft.trim(),
        api: cloudflareApiSubdomainDraft.trim(),
      },
      tunnel_name: cloudflareTunnelNameDraft.trim(),
      tunnel_id: cloudflareTunnelIdDraft.trim(),
      tunnel_token: cloudflareTunnelTokenDraft.trim(),
      account_id: cloudflareAccountIdDraft.trim(),
      zone_id: cloudflareZoneIdDraft.trim(),
      api_token: cloudflareApiTokenDraft.trim(),
      auto_apply_routes: cloudflareAutoApplyRoutesDraft,
      dev_manual_urls: {
        portal: cloudflarePortalDevUrlDraft.trim(),
        client: cloudflareClientDevUrlDraft.trim(),
        admin: cloudflareAdminDevUrlDraft.trim(),
        api: cloudflareApiDevUrlDraft.trim(),
      },
    };
  }

  function buildEmailSettingsDraftPayload(): PortalEmailSettingsConfig {
    const base = normalizeEmailSettings(config?.email_settings);
    return normalizeEmailSettings({
      ...base,
      enabled: emailEnabledDraft,
      backend: emailBackendDraft.trim(),
      host: emailHostDraft.trim(),
      port: Number.parseInt(emailPortDraft, 10),
      username: emailUsernameDraft.trim(),
      password: emailPasswordDraft.trim(),
      use_tls: emailUseTlsDraft,
      use_ssl: emailUseSslDraft,
      timeout_seconds: Number.parseInt(emailTimeoutDraft, 10),
      from_name: emailFromNameDraft.trim(),
      from_email: emailFromAddressDraft.trim(),
      reply_to_email: emailReplyToDraft.trim(),
      test_recipient: emailTestRecipientDraft.trim(),
    });
  }

  useEffect(() => {
    let mounted = true;

    async function loadPortalData() {
      try {
        const [configPayload, sectionsPayload, releasesPayload] = await Promise.all([
          ensurePortalConfigAdmin(),
          listPortalSectionsAdmin(),
          listMobileReleasesAdmin(),
        ]);
        if (!mounted) {
          return;
        }

        const normalizedTemplateOptions = normalizeTemplateOptions(
          configPayload.available_templates,
        );
        const normalizedClientTemplateOptions = normalizeTemplateOptions(
          configPayload.client_available_templates,
        );
        const normalizedAdminTemplateOptions = normalizeTemplateOptions(
          configPayload.admin_available_templates,
        );
        const defaultTemplateId = normalizedTemplateOptions.some(
          (option) => option.id === configPayload.active_template,
        )
          ? configPayload.active_template
          : (normalizedTemplateOptions[0]?.id ??
            normalizedClientTemplateOptions[0]?.id ??
            normalizedAdminTemplateOptions[0]?.id ??
            "");

        setConfig(configPayload);
        setSections(sectionsPayload);
        setMobileReleases(releasesPayload);
        setSelectedTemplateId(configPayload.active_template);
        setSelectedClientTemplateId(configPayload.client_active_template);
        setSelectedAdminTemplateId(configPayload.admin_active_template);
        setContentTemplateId(defaultTemplateId);
        setContentPageFilter("all");
        setLocalHostnameDraft(configPayload.local_hostname || "mrquentinha");
        setLocalNetworkIpDraft(configPayload.local_network_ip || "");
        setRootDomainDraft(configPayload.root_domain || "mrquentinha.local");
        setPortalDomainDraft(configPayload.portal_domain || "www.mrquentinha.local");
        setClientDomainDraft(configPayload.client_domain || "app.mrquentinha.local");
        setAdminDomainDraft(configPayload.admin_domain || "admin.mrquentinha.local");
        setApiDomainDraft(configPayload.api_domain || "api.mrquentinha.local");
        setApiBaseUrlDraft(configPayload.api_base_url || "https://10.211.55.21:8000");
        const mobileApiPublicAccess = normalizeApiPublicAccessSettings(
          configPayload.installer_settings,
        );
        setMobileApiPublicEnabledDraft(mobileApiPublicAccess.enabled);
        setMobileApiPreferredEndpointDraft(mobileApiPublicAccess.preferred_endpoint);
        setMobileApiPublicIpUrlDraft(mobileApiPublicAccess.public_ip_base_url);
        setMobileApiAwsDnsUrlDraft(mobileApiPublicAccess.aws_dns_base_url);
        setPortalBaseUrlDraft(configPayload.portal_base_url || "https://10.211.55.21:3000");
        setClientBaseUrlDraft(configPayload.client_base_url || "https://10.211.55.21:3001");
        setAdminBaseUrlDraft(configPayload.admin_base_url || "https://10.211.55.21:3002");
        setBackendBaseUrlDraft(configPayload.backend_base_url || "https://10.211.55.21:8000");
        setProxyBaseUrlDraft(configPayload.proxy_base_url || "https://10.211.55.21:8088");
        setCorsAllowedOriginsDraft(stringifyOrigins(configPayload.cors_allowed_origins));
        const cloudflareSettings = normalizeCloudflareSettings(
          configPayload.cloudflare_settings,
        );
        const normalizedOperationMode = normalizeOperationModeSettings(
          configPayload.installer_settings,
          cloudflareSettings.mode,
          cloudflareSettings.dev_mode,
        );
        setOperationModeDraft(
          normalizedOperationMode === "prod" ? "production" : normalizedOperationMode,
        );
        setCloudflareEnabledDraft(cloudflareSettings.enabled);
        setCloudflareModeDraft(cloudflareSettings.mode);
        setCloudflareDevModeDraft(cloudflareSettings.dev_mode);
        setCloudflareDevUrlModeDraft(cloudflareSettings.dev_url_mode);
        setCloudflareDevOfficialDomainDraft(
          cloudflareSettings.dev_official_domain || "dev.mrquentinha.com.br",
        );
        setCloudflareSchemeDraft(cloudflareSettings.scheme);
        setCloudflareRootDomainDraft(cloudflareSettings.root_domain);
        setCloudflarePortalSubdomainDraft(cloudflareSettings.subdomains.portal);
        setCloudflareClientSubdomainDraft(cloudflareSettings.subdomains.client);
        setCloudflareAdminSubdomainDraft(cloudflareSettings.subdomains.admin);
        setCloudflareApiSubdomainDraft(cloudflareSettings.subdomains.api);
        setCloudflareTunnelNameDraft(cloudflareSettings.tunnel_name);
        setCloudflareTunnelIdDraft(cloudflareSettings.tunnel_id);
        setCloudflareTunnelTokenDraft(cloudflareSettings.tunnel_token);
        setCloudflareAccountIdDraft(cloudflareSettings.account_id);
        setCloudflareZoneIdDraft(cloudflareSettings.zone_id);
        setCloudflareApiTokenDraft(cloudflareSettings.api_token);
        setCloudflareAutoApplyRoutesDraft(cloudflareSettings.auto_apply_routes);
        setCloudflarePortalDevUrlDraft(cloudflareSettings.dev_manual_urls.portal);
        setCloudflareClientDevUrlDraft(cloudflareSettings.dev_manual_urls.client);
        setCloudflareAdminDevUrlDraft(cloudflareSettings.dev_manual_urls.admin);
        setCloudflareApiDevUrlDraft(cloudflareSettings.dev_manual_urls.api);
        setCloudflareApiStatus(null);
      setCloudflareRuntime({
          state: cloudflareSettings.runtime.state,
          pid: null,
          log_file: "",
          last_started_at: cloudflareSettings.runtime.last_started_at,
          last_stopped_at: cloudflareSettings.runtime.last_stopped_at,
          last_error: cloudflareSettings.runtime.last_error,
          run_command: cloudflareSettings.runtime.run_command,
          last_log_lines: [],
          dev_mode: cloudflareSettings.dev_mode,
          dev_url_mode: cloudflareSettings.dev_url_mode,
          dev_urls: cloudflareSettings.dev_urls,
          dev_manual_urls: cloudflareSettings.dev_manual_urls,
          observed_dev_urls: cloudflareSettings.dev_urls,
          dev_services: [],
        });
        const authProviders = normalizeAuthProviders(configPayload.auth_providers);
        setGoogleEnabledDraft(authProviders.google.enabled);
        setGoogleWebClientIdDraft(authProviders.google.web_client_id);
        setGoogleIosClientIdDraft(authProviders.google.ios_client_id);
        setGoogleAndroidClientIdDraft(authProviders.google.android_client_id);
        setGoogleClientSecretDraft(authProviders.google.client_secret);
        setGoogleAuthUriDraft(authProviders.google.auth_uri);
        setGoogleTokenUriDraft(authProviders.google.token_uri);
        setGoogleRedirectWebDraft(authProviders.google.redirect_uri_web);
        setGoogleRedirectMobileDraft(authProviders.google.redirect_uri_mobile);
        setGoogleScopeDraft(authProviders.google.scope);
        setAppleEnabledDraft(authProviders.apple.enabled);
        setAppleServiceIdDraft(authProviders.apple.service_id);
        setAppleTeamIdDraft(authProviders.apple.team_id);
        setAppleKeyIdDraft(authProviders.apple.key_id);
        setApplePrivateKeyDraft(authProviders.apple.private_key);
        setAppleAuthUriDraft(authProviders.apple.auth_uri);
        setAppleTokenUriDraft(authProviders.apple.token_uri);
        setAppleRedirectWebDraft(authProviders.apple.redirect_uri_web);
        setAppleRedirectMobileDraft(authProviders.apple.redirect_uri_mobile);
        setAppleScopeDraft(authProviders.apple.scope);

        const paymentProviders = normalizePaymentProviders(
          configPayload.payment_providers,
        );
        setPaymentDefaultProviderDraft(paymentProviders.default_provider);
        setPaymentEnabledProvidersDraft(paymentProviders.enabled_providers);
        setPaymentWebProviderDraft(paymentProviders.frontend_provider.web);
        setPaymentMobileProviderDraft(paymentProviders.frontend_provider.mobile);
        setPaymentPixOrderDraft(
          paymentProviders.method_provider_order.PIX.join(", "),
        );
        setPaymentCardOrderDraft(
          paymentProviders.method_provider_order.CARD.join(", "),
        );
        setPaymentVrOrderDraft(
          paymentProviders.method_provider_order.VR.join(", "),
        );
        setReceiverPersonTypeDraft(paymentProviders.receiver.person_type);
        setReceiverDocumentDraft(paymentProviders.receiver.document);
        setReceiverNameDraft(paymentProviders.receiver.name);
        setReceiverEmailDraft(paymentProviders.receiver.email);
        setMercadoPagoEnabledDraft(paymentProviders.mercadopago.enabled);
        setMercadoPagoApiBaseUrlDraft(paymentProviders.mercadopago.api_base_url);
        setMercadoPagoAccessTokenDraft(paymentProviders.mercadopago.access_token);
        setMercadoPagoWebhookSecretDraft(
          paymentProviders.mercadopago.webhook_secret,
        );
        setMercadoPagoSandboxDraft(paymentProviders.mercadopago.sandbox);
        setEfiEnabledDraft(paymentProviders.efi.enabled);
        setEfiApiBaseUrlDraft(paymentProviders.efi.api_base_url);
        setEfiClientIdDraft(paymentProviders.efi.client_id);
        setEfiClientSecretDraft(paymentProviders.efi.client_secret);
        setEfiWebhookSecretDraft(paymentProviders.efi.webhook_secret);
        setEfiSandboxDraft(paymentProviders.efi.sandbox);
        setAsaasEnabledDraft(paymentProviders.asaas.enabled);
        setAsaasApiBaseUrlDraft(paymentProviders.asaas.api_base_url);
        setAsaasApiKeyDraft(paymentProviders.asaas.api_key);
        setAsaasWebhookSecretDraft(paymentProviders.asaas.webhook_secret);
        setAsaasSandboxDraft(paymentProviders.asaas.sandbox);
        const emailSettings = normalizeEmailSettings(configPayload.email_settings);
        setEmailEnabledDraft(emailSettings.enabled);
        setEmailBackendDraft(emailSettings.backend);
        setEmailHostDraft(emailSettings.host);
        setEmailPortDraft(String(emailSettings.port));
        setEmailUsernameDraft(emailSettings.username);
        setEmailPasswordDraft(emailSettings.password);
        setEmailUseTlsDraft(emailSettings.use_tls);
        setEmailUseSslDraft(emailSettings.use_ssl);
        setEmailTimeoutDraft(String(emailSettings.timeout_seconds));
        setEmailFromNameDraft(emailSettings.from_name);
        setEmailFromAddressDraft(emailSettings.from_email);
        setEmailReplyToDraft(emailSettings.reply_to_email);
        setEmailTestRecipientDraft(emailSettings.test_recipient);
        setSslEmailDraft(
          emailSettings.from_email ||
            emailSettings.reply_to_email ||
            "contato@mrquentinha.com.br",
        );
        setSslDomainsDraft(
          [
            configPayload.portal_domain,
            configPayload.client_domain,
            configPayload.admin_domain,
            configPayload.api_domain,
          ]
            .filter((domain) => Boolean(domain))
            .join("\n"),
        );
        setCloudflarePreview(null);
        try {
          const runtimePayload = await managePortalCloudflareRuntimeAdmin("status");
          if (mounted) {
            setCloudflareRuntime(runtimePayload.runtime);
          }
        } catch {
          // Mantem fallback de runtime local quando nao for possivel consultar status.
        }
        setErrorMessage("");
      } catch (error) {
        if (mounted) {
          setErrorMessage(resolveErrorMessage(error));
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadPortalData();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (filteredSections.length === 0) {
      setSelectedSectionId("");
      return;
    }

    setSelectedSectionId((previous) => {
      const alreadyExists = filteredSections.some(
        (section) => String(section.id) === previous,
      );
      if (alreadyExists) {
        return previous;
      }
      return String(filteredSections[0].id);
    });
  }, [filteredSections]);

  useEffect(() => {
    if (!config || !cloudflareEnabledDraft || !cloudflareDevModeDraft) {
      return;
    }

    let cancelled = false;
    const interval = window.setInterval(() => {
      if (cancelled || cloudflareSaving) {
        return;
      }

      void managePortalCloudflareRuntimeAdmin("status")
        .then((payload) => {
          if (cancelled) {
            return;
          }
          setCloudflareRuntime(payload.runtime);
        })
        .catch(() => {
          // Mantem ultimo estado exibido quando status nao responder.
        });
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [config, cloudflareDevModeDraft, cloudflareEnabledDraft, cloudflareSaving]);

  useEffect(() => {
    if (!selectedSection) {
      setSectionTitleDraft("");
      setSectionSortOrderDraft("0");
      setSectionEnabledDraft(true);
      setSectionBodyJsonDraft("{}");
      return;
    }

    setSectionTitleDraft(selectedSection.title);
    setSectionSortOrderDraft(String(selectedSection.sort_order));
    setSectionEnabledDraft(selectedSection.is_enabled);
    setSectionBodyJsonDraft(stringifyBodyJson(selectedSection.body_json));
  }, [selectedSection]);

  function shouldRenderSection(
    key: string,
    sectionMode: PortalSectionsMode,
  ): boolean {
    return (
      activeSection === key ||
      (activeSection === "all" && mode === sectionMode)
    );
  }

  async function handleRefreshSections() {
    setRefreshingSections(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const sectionsPayload = await listPortalSectionsAdmin();
      setSections(sectionsPayload);
      setSuccessMessage("Conteudo dinamico atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setRefreshingSections(false);
    }
  }

  async function handleSaveTemplate() {
    if (!config || !selectedTemplateId) {
      return;
    }

    setSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        active_template: selectedTemplateId,
      });
      setConfig(updatedConfig);
      setSelectedTemplateId(updatedConfig.active_template);
      setContentTemplateId(updatedConfig.active_template);
      setSuccessMessage("Template ativo atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveClientTemplate() {
    if (!config || !selectedClientTemplateId) {
      return;
    }

    setSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        client_active_template: selectedClientTemplateId,
      });
      setConfig(updatedConfig);
      setSelectedClientTemplateId(updatedConfig.client_active_template);
      setContentTemplateId(updatedConfig.client_active_template);
      setSuccessMessage("Template ativo do Web Cliente atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveAdminTemplate() {
    if (!config || !selectedAdminTemplateId) {
      return;
    }

    setSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        admin_active_template: selectedAdminTemplateId,
      });
      setConfig(updatedConfig);
      setSelectedAdminTemplateId(updatedConfig.admin_active_template);
      setSuccessMessage("Template ativo do Web Admin atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveAuthProviders() {
    if (!config) {
      return;
    }

    setSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        auth_providers: {
          google: {
            enabled: googleEnabledDraft,
            web_client_id: googleWebClientIdDraft.trim(),
            ios_client_id: googleIosClientIdDraft.trim(),
            android_client_id: googleAndroidClientIdDraft.trim(),
            client_secret: googleClientSecretDraft.trim(),
            auth_uri: googleAuthUriDraft.trim(),
            token_uri: googleTokenUriDraft.trim(),
            redirect_uri_web: googleRedirectWebDraft.trim(),
            redirect_uri_mobile: googleRedirectMobileDraft.trim(),
            scope: googleScopeDraft.trim(),
          },
          apple: {
            enabled: appleEnabledDraft,
            service_id: appleServiceIdDraft.trim(),
            team_id: appleTeamIdDraft.trim(),
            key_id: appleKeyIdDraft.trim(),
            private_key: applePrivateKeyDraft.trim(),
            auth_uri: appleAuthUriDraft.trim(),
            token_uri: appleTokenUriDraft.trim(),
            redirect_uri_web: appleRedirectWebDraft.trim(),
            redirect_uri_mobile: appleRedirectMobileDraft.trim(),
            scope: appleScopeDraft.trim(),
          },
        },
      });

      setConfig(updatedConfig);
      setSuccessMessage(
        "Parametros de autenticacao social (Google/Apple) atualizados com sucesso.",
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  function handleToggleEnabledPaymentProvider(provider: string) {
    setPaymentEnabledProvidersDraft((previous) => {
      const alreadyEnabled = previous.includes(provider);
      if (alreadyEnabled) {
        const next = previous.filter((item) => item !== provider);
        return next.length > 0 ? next : ["mock"];
      }
      return [...previous, provider];
    });
  }

  async function handleSavePaymentProviders() {
    if (!config) {
      return;
    }

    setSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const enabledProviders = Array.from(
        new Set(
          paymentEnabledProvidersDraft
            .map((item) => item.trim().toLowerCase())
            .filter((item) => item.length > 0),
        ),
      );
      if (enabledProviders.length === 0) {
        enabledProviders.push("mock");
      }

      const defaultProvider = paymentDefaultProviderDraft.trim().toLowerCase() || "mock";
      if (!enabledProviders.includes(defaultProvider)) {
        enabledProviders.push(defaultProvider);
      }
      const webProvider = paymentWebProviderDraft.trim().toLowerCase() || "mock";
      const mobileProvider = paymentMobileProviderDraft.trim().toLowerCase() || "mock";
      if (!enabledProviders.includes(webProvider)) {
        enabledProviders.push(webProvider);
      }
      if (!enabledProviders.includes(mobileProvider)) {
        enabledProviders.push(mobileProvider);
      }

      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        payment_providers: {
          default_provider: defaultProvider,
          enabled_providers: enabledProviders,
          frontend_provider: {
            web: webProvider,
            mobile: mobileProvider,
          },
          method_provider_order: {
            PIX: parseProviderOrder(paymentPixOrderDraft),
            CARD: parseProviderOrder(paymentCardOrderDraft),
            VR: parseProviderOrder(paymentVrOrderDraft),
          },
          receiver: {
            person_type: receiverPersonTypeDraft,
            document: receiverDocumentDraft.trim(),
            name: receiverNameDraft.trim(),
            email: receiverEmailDraft.trim(),
          },
          mercadopago: {
            enabled: mercadoPagoEnabledDraft,
            api_base_url: mercadoPagoApiBaseUrlDraft.trim(),
            access_token: mercadoPagoAccessTokenDraft.trim(),
            webhook_secret: mercadoPagoWebhookSecretDraft.trim(),
            sandbox: mercadoPagoSandboxDraft,
          },
          efi: {
            enabled: efiEnabledDraft,
            api_base_url: efiApiBaseUrlDraft.trim(),
            client_id: efiClientIdDraft.trim(),
            client_secret: efiClientSecretDraft.trim(),
            webhook_secret: efiWebhookSecretDraft.trim(),
            sandbox: efiSandboxDraft,
          },
          asaas: {
            enabled: asaasEnabledDraft,
            api_base_url: asaasApiBaseUrlDraft.trim(),
            api_key: asaasApiKeyDraft.trim(),
            webhook_secret: asaasWebhookSecretDraft.trim(),
            sandbox: asaasSandboxDraft,
          },
        },
      });

      setConfig(updatedConfig);
      setSuccessMessage("Configuracoes de pagamentos atualizadas com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveEmailSettings() {
    if (!config) {
      return;
    }

    setSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        email_settings: buildEmailSettingsDraftPayload(),
      });
      const emailSettings = normalizeEmailSettings(updatedConfig.email_settings);
      setConfig(updatedConfig);
      setEmailEnabledDraft(emailSettings.enabled);
      setEmailBackendDraft(emailSettings.backend);
      setEmailHostDraft(emailSettings.host);
      setEmailPortDraft(String(emailSettings.port));
      setEmailUsernameDraft(emailSettings.username);
      setEmailPasswordDraft(emailSettings.password);
      setEmailUseTlsDraft(emailSettings.use_tls);
      setEmailUseSslDraft(emailSettings.use_ssl);
      setEmailTimeoutDraft(String(emailSettings.timeout_seconds));
      setEmailFromNameDraft(emailSettings.from_name);
      setEmailFromAddressDraft(emailSettings.from_email);
      setEmailReplyToDraft(emailSettings.reply_to_email);
      setEmailTestRecipientDraft(emailSettings.test_recipient);
      setSslEmailDraft(
        emailSettings.from_email || emailSettings.reply_to_email || "contato@mrquentinha.com.br",
      );
      setSslDomainsDraft(
        [
          updatedConfig.portal_domain,
          updatedConfig.client_domain,
          updatedConfig.admin_domain,
          updatedConfig.api_domain,
        ]
          .filter((domain) => Boolean(domain))
          .join("\n"),
      );
      setSuccessMessage("Gestao de e-mail atualizada com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handleTestEmailSettings() {
    setTestingEmail(true);
    setSuccessMessage("");
    setErrorMessage("");
    try {
      const payload = await testPortalEmailConfigAdmin(emailTestRecipientDraft.trim());
      setSuccessMessage(payload.detail);
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setTestingEmail(false);
    }
  }

  function resolveSslDomains(): string[] {
    return sslDomainsDraft
      .split(/\s+|,/)
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }

  async function handleApplySslCertificates(dryRun = false) {
    if (!sslEmailDraft.trim()) {
      setErrorMessage("Informe o e-mail para o certificado SSL.");
      return;
    }
    const domains = resolveSslDomains();
    if (domains.length === 0) {
      setErrorMessage("Informe ao menos um dominio para SSL.");
      return;
    }

    setSslApplying(true);
    setSslResult(null);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const result = await applyPortalSslCertificatesAdmin({
        email: sslEmailDraft.trim(),
        domains,
        dry_run: dryRun,
      });
      setSslResult(result);
      setSuccessMessage(result.ok ? "Certificados aplicados com sucesso." : "Falha ao aplicar SSL.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSslApplying(false);
    }
  }

  async function handleTestPaymentProvider(provider: string) {
    setTestingProvider(provider);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const payload = await testPortalPaymentProviderAdmin(provider);
      setSuccessMessage(payload.detail);
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setTestingProvider(null);
    }
  }

  function handleApplyLocalPreset() {
    const normalizedHost = (localHostnameDraft || "mrquentinha").trim() || "mrquentinha";
    const hostFromApi = resolveHostFromApiBaseUrl(apiBaseUrlDraft);

    setLocalHostnameDraft(normalizedHost);
    setLocalNetworkIpDraft(hostFromApi);
    setRootDomainDraft(`${normalizedHost}.local`);
    setPortalDomainDraft(`www.${normalizedHost}.local`);
    setClientDomainDraft(`app.${normalizedHost}.local`);
    setAdminDomainDraft(`admin.${normalizedHost}.local`);
    setApiDomainDraft(`api.${normalizedHost}.local`);
    setPortalBaseUrlDraft(`https://${hostFromApi}:3000`);
    setClientBaseUrlDraft(`https://${hostFromApi}:3001`);
    setAdminBaseUrlDraft(`https://${hostFromApi}:3002`);
    setBackendBaseUrlDraft(`https://${hostFromApi}:8000`);
    setProxyBaseUrlDraft(`https://${hostFromApi}:8088`);
    setCorsAllowedOriginsDraft(
      [
        `https://${hostFromApi}:3000`,
        `https://${hostFromApi}:3001`,
        `https://${hostFromApi}:3002`,
      ].join("\n"),
    );
    setSuccessMessage("Preset local aplicado. Revise os campos e salve.");
    setErrorMessage("");
  }

  async function handleSaveConnectivity() {
    if (!config) {
      return;
    }

    setSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const nextInstallerSettings: PortalInstallerSettingsConfig = {
        ...(config.installer_settings ?? ({} as PortalInstallerSettingsConfig)),
        operation_mode:
          environmentModeDraft === "production" ? "prod" : environmentModeDraft,
        api_public_access: {
          enabled: mobileApiPublicEnabledDraft,
          preferred_endpoint: mobileApiPreferredEndpointDraft,
          public_ip_base_url: mobileApiPublicIpUrlDraft.trim(),
          aws_dns_base_url: mobileApiAwsDnsUrlDraft.trim(),
        },
      };
      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        api_base_url: apiBaseUrlDraft.trim(),
        local_hostname: localHostnameDraft.trim() || "mrquentinha",
        local_network_ip: localNetworkIpDraft.trim(),
        root_domain: rootDomainDraft.trim(),
        portal_domain: portalDomainDraft.trim(),
        client_domain: clientDomainDraft.trim(),
        admin_domain: adminDomainDraft.trim(),
        api_domain: apiDomainDraft.trim(),
        portal_base_url: portalBaseUrlDraft.trim(),
        client_base_url: clientBaseUrlDraft.trim(),
        admin_base_url: adminBaseUrlDraft.trim(),
        backend_base_url: backendBaseUrlDraft.trim(),
        proxy_base_url: proxyBaseUrlDraft.trim(),
        cors_allowed_origins: parseOrigins(corsAllowedOriginsDraft),
        cloudflare_settings: buildCloudflareSettingsDraftPayload(),
        installer_settings: nextInstallerSettings,
      });

      setConfig(updatedConfig);
      setLocalHostnameDraft(updatedConfig.local_hostname);
      setLocalNetworkIpDraft(updatedConfig.local_network_ip);
      setApiBaseUrlDraft(updatedConfig.api_base_url);
      setRootDomainDraft(updatedConfig.root_domain);
      setPortalDomainDraft(updatedConfig.portal_domain);
      setClientDomainDraft(updatedConfig.client_domain);
      setAdminDomainDraft(updatedConfig.admin_domain);
      setApiDomainDraft(updatedConfig.api_domain);
      setPortalBaseUrlDraft(updatedConfig.portal_base_url);
      setClientBaseUrlDraft(updatedConfig.client_base_url);
      setAdminBaseUrlDraft(updatedConfig.admin_base_url);
      setBackendBaseUrlDraft(updatedConfig.backend_base_url);
      setProxyBaseUrlDraft(updatedConfig.proxy_base_url);
      setCorsAllowedOriginsDraft(stringifyOrigins(updatedConfig.cors_allowed_origins));
      const updatedMobileApiPublicAccess = normalizeApiPublicAccessSettings(
        updatedConfig.installer_settings,
      );
      const cloudflareSettings = normalizeCloudflareSettings(
        updatedConfig.cloudflare_settings,
      );
      const updatedOperationMode = normalizeOperationModeSettings(
        updatedConfig.installer_settings,
        cloudflareSettings.mode,
        cloudflareSettings.dev_mode,
      );
      setOperationModeDraft(
        updatedOperationMode === "prod" ? "production" : updatedOperationMode,
      );
      setMobileApiPublicEnabledDraft(updatedMobileApiPublicAccess.enabled);
      setMobileApiPreferredEndpointDraft(updatedMobileApiPublicAccess.preferred_endpoint);
      setMobileApiPublicIpUrlDraft(updatedMobileApiPublicAccess.public_ip_base_url);
      setMobileApiAwsDnsUrlDraft(updatedMobileApiPublicAccess.aws_dns_base_url);
      setCloudflareEnabledDraft(cloudflareSettings.enabled);
      setCloudflareModeDraft(cloudflareSettings.mode);
      setCloudflareDevModeDraft(cloudflareSettings.dev_mode);
      setCloudflareDevUrlModeDraft(cloudflareSettings.dev_url_mode);
      setCloudflareDevOfficialDomainDraft(
        cloudflareSettings.dev_official_domain || "dev.mrquentinha.com.br",
      );
      setCloudflareSchemeDraft(cloudflareSettings.scheme);
      setCloudflareRootDomainDraft(cloudflareSettings.root_domain);
      setCloudflarePortalSubdomainDraft(cloudflareSettings.subdomains.portal);
      setCloudflareClientSubdomainDraft(cloudflareSettings.subdomains.client);
      setCloudflareAdminSubdomainDraft(cloudflareSettings.subdomains.admin);
      setCloudflareApiSubdomainDraft(cloudflareSettings.subdomains.api);
      setCloudflareTunnelNameDraft(cloudflareSettings.tunnel_name);
      setCloudflareTunnelIdDraft(cloudflareSettings.tunnel_id);
      setCloudflareTunnelTokenDraft(cloudflareSettings.tunnel_token);
      setCloudflareAccountIdDraft(cloudflareSettings.account_id);
      setCloudflareZoneIdDraft(cloudflareSettings.zone_id);
      setCloudflareApiTokenDraft(cloudflareSettings.api_token);
      setCloudflareAutoApplyRoutesDraft(cloudflareSettings.auto_apply_routes);
      setCloudflarePortalDevUrlDraft(cloudflareSettings.dev_manual_urls.portal);
      setCloudflareClientDevUrlDraft(cloudflareSettings.dev_manual_urls.client);
      setCloudflareAdminDevUrlDraft(cloudflareSettings.dev_manual_urls.admin);
      setCloudflareApiDevUrlDraft(cloudflareSettings.dev_manual_urls.api);
      setCloudflareRuntime({
        state: cloudflareSettings.runtime.state,
        pid: null,
        log_file: "",
        last_started_at: cloudflareSettings.runtime.last_started_at,
        last_stopped_at: cloudflareSettings.runtime.last_stopped_at,
        last_error: cloudflareSettings.runtime.last_error,
        run_command: cloudflareSettings.runtime.run_command,
        last_log_lines: [],
        dev_mode: cloudflareSettings.dev_mode,
        dev_url_mode: cloudflareSettings.dev_url_mode,
        dev_urls: cloudflareSettings.dev_urls,
        dev_manual_urls: cloudflareSettings.dev_manual_urls,
        observed_dev_urls: cloudflareSettings.dev_urls,
        dev_services: [],
      });
      setSuccessMessage("Conectividade entre aplicacoes atualizada com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handlePreviewCloudflare() {
    setCloudflareSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const previewPayload = await previewPortalCloudflareAdmin(
        buildCloudflareSettingsDraftPayload(),
      );
      setCloudflarePreview(previewPayload);
      setSuccessMessage("Preview Cloudflare gerado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCloudflareSaving(false);
    }
  }

  async function handleToggleCloudflare(enabled: boolean) {
    if (!config) {
      return;
    }

    setCloudflareSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const payload = await togglePortalCloudflareAdmin({
        enabled,
        settings: buildCloudflareSettingsDraftPayload(),
      });
      const updatedConfig = payload.config;
      const cloudflareSettings = normalizeCloudflareSettings(
        updatedConfig.cloudflare_settings,
      );

      setConfig(updatedConfig);
      setLocalHostnameDraft(updatedConfig.local_hostname);
      setLocalNetworkIpDraft(updatedConfig.local_network_ip);
      setApiBaseUrlDraft(updatedConfig.api_base_url);
      setRootDomainDraft(updatedConfig.root_domain);
      setPortalDomainDraft(updatedConfig.portal_domain);
      setClientDomainDraft(updatedConfig.client_domain);
      setAdminDomainDraft(updatedConfig.admin_domain);
      setApiDomainDraft(updatedConfig.api_domain);
      setPortalBaseUrlDraft(updatedConfig.portal_base_url);
      setClientBaseUrlDraft(updatedConfig.client_base_url);
      setAdminBaseUrlDraft(updatedConfig.admin_base_url);
      setBackendBaseUrlDraft(updatedConfig.backend_base_url);
      setProxyBaseUrlDraft(updatedConfig.proxy_base_url);
      setCorsAllowedOriginsDraft(stringifyOrigins(updatedConfig.cors_allowed_origins));
      setCloudflareEnabledDraft(cloudflareSettings.enabled);
      setCloudflareModeDraft(cloudflareSettings.mode);
      setCloudflareDevModeDraft(cloudflareSettings.dev_mode);
      setCloudflareDevUrlModeDraft(cloudflareSettings.dev_url_mode);
      setCloudflareDevOfficialDomainDraft(
        cloudflareSettings.dev_official_domain || "dev.mrquentinha.com.br",
      );
      setCloudflareSchemeDraft(cloudflareSettings.scheme);
      setCloudflareRootDomainDraft(cloudflareSettings.root_domain);
      setCloudflarePortalSubdomainDraft(cloudflareSettings.subdomains.portal);
      setCloudflareClientSubdomainDraft(cloudflareSettings.subdomains.client);
      setCloudflareAdminSubdomainDraft(cloudflareSettings.subdomains.admin);
      setCloudflareApiSubdomainDraft(cloudflareSettings.subdomains.api);
      setCloudflareTunnelNameDraft(cloudflareSettings.tunnel_name);
      setCloudflareTunnelIdDraft(cloudflareSettings.tunnel_id);
      setCloudflareTunnelTokenDraft(cloudflareSettings.tunnel_token);
      setCloudflareAccountIdDraft(cloudflareSettings.account_id);
      setCloudflareZoneIdDraft(cloudflareSettings.zone_id);
      setCloudflareApiTokenDraft(cloudflareSettings.api_token);
      setCloudflareAutoApplyRoutesDraft(cloudflareSettings.auto_apply_routes);
      setCloudflarePortalDevUrlDraft(cloudflareSettings.dev_manual_urls.portal);
      setCloudflareClientDevUrlDraft(cloudflareSettings.dev_manual_urls.client);
      setCloudflareAdminDevUrlDraft(cloudflareSettings.dev_manual_urls.admin);
      setCloudflareApiDevUrlDraft(cloudflareSettings.dev_manual_urls.api);
      setCloudflareRuntime({
        state: cloudflareSettings.runtime.state,
        pid: null,
        log_file: "",
        last_started_at: cloudflareSettings.runtime.last_started_at,
        last_stopped_at: cloudflareSettings.runtime.last_stopped_at,
        last_error: cloudflareSettings.runtime.last_error,
        run_command: cloudflareSettings.runtime.run_command,
        last_log_lines: [],
        dev_mode: cloudflareSettings.dev_mode,
        dev_url_mode: cloudflareSettings.dev_url_mode,
        dev_urls: cloudflareSettings.dev_urls,
        dev_manual_urls: cloudflareSettings.dev_manual_urls,
        observed_dev_urls: cloudflareSettings.dev_urls,
        dev_services: [],
      });
      setCloudflarePreview(payload.preview);
      setSuccessMessage(
        enabled
          ? "Cloudflare ativado com sucesso para exposicao online."
          : "Cloudflare desativado. Configuracao local restaurada.",
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCloudflareSaving(false);
    }
  }

  async function handleCloudflareRuntimeAction(
    action: "start" | "stop" | "status" | "refresh",
  ) {
    setCloudflareSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const payload = await managePortalCloudflareRuntimeAdmin(action);
      const updatedConfig = payload.config;
      const cloudflareSettings = normalizeCloudflareSettings(
        updatedConfig.cloudflare_settings,
      );

      setConfig(updatedConfig);
      setLocalHostnameDraft(updatedConfig.local_hostname);
      setLocalNetworkIpDraft(updatedConfig.local_network_ip);
      setApiBaseUrlDraft(updatedConfig.api_base_url);
      setRootDomainDraft(updatedConfig.root_domain);
      setPortalDomainDraft(updatedConfig.portal_domain);
      setClientDomainDraft(updatedConfig.client_domain);
      setAdminDomainDraft(updatedConfig.admin_domain);
      setApiDomainDraft(updatedConfig.api_domain);
      setPortalBaseUrlDraft(updatedConfig.portal_base_url);
      setClientBaseUrlDraft(updatedConfig.client_base_url);
      setAdminBaseUrlDraft(updatedConfig.admin_base_url);
      setBackendBaseUrlDraft(updatedConfig.backend_base_url);
      setProxyBaseUrlDraft(updatedConfig.proxy_base_url);
      setCorsAllowedOriginsDraft(stringifyOrigins(updatedConfig.cors_allowed_origins));
      setCloudflareEnabledDraft(cloudflareSettings.enabled);
      setCloudflareModeDraft(cloudflareSettings.mode);
      setCloudflareDevModeDraft(cloudflareSettings.dev_mode);
      setCloudflareDevUrlModeDraft(cloudflareSettings.dev_url_mode);
      setCloudflareDevOfficialDomainDraft(
        cloudflareSettings.dev_official_domain || "dev.mrquentinha.com.br",
      );
      setCloudflareSchemeDraft(cloudflareSettings.scheme);
      setCloudflareRootDomainDraft(cloudflareSettings.root_domain);
      setCloudflarePortalSubdomainDraft(cloudflareSettings.subdomains.portal);
      setCloudflareClientSubdomainDraft(cloudflareSettings.subdomains.client);
      setCloudflareAdminSubdomainDraft(cloudflareSettings.subdomains.admin);
      setCloudflareApiSubdomainDraft(cloudflareSettings.subdomains.api);
      setCloudflareTunnelNameDraft(cloudflareSettings.tunnel_name);
      setCloudflareTunnelIdDraft(cloudflareSettings.tunnel_id);
      setCloudflareTunnelTokenDraft(cloudflareSettings.tunnel_token);
      setCloudflareAccountIdDraft(cloudflareSettings.account_id);
      setCloudflareZoneIdDraft(cloudflareSettings.zone_id);
      setCloudflareApiTokenDraft(cloudflareSettings.api_token);
      setCloudflareAutoApplyRoutesDraft(cloudflareSettings.auto_apply_routes);
      setCloudflarePortalDevUrlDraft(cloudflareSettings.dev_manual_urls.portal);
      setCloudflareClientDevUrlDraft(cloudflareSettings.dev_manual_urls.client);
      setCloudflareAdminDevUrlDraft(cloudflareSettings.dev_manual_urls.admin);
      setCloudflareApiDevUrlDraft(cloudflareSettings.dev_manual_urls.api);
      setCloudflareRuntime(payload.runtime);
      if (action === "refresh") {
        setSuccessMessage(
          "Runtime Cloudflare DEV reiniciado e novos dominios aleatorios gerados.",
        );
      } else {
        setSuccessMessage(`Runtime Cloudflare: acao '${action}' executada com sucesso.`);
      }
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCloudflareSaving(false);
    }
  }

  async function handleCompileRelease() {
    if (!config) {
      return;
    }

    setCompilingRelease(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const buildNumber = Number.parseInt(releaseBuildNumberDraft, 10);
      if (Number.isNaN(buildNumber) || buildNumber <= 0) {
        throw new Error("Informe um build_number valido (maior que zero).");
      }

      const version = releaseVersionDraft.trim();
      if (!version) {
        throw new Error("Informe a versao da release.");
      }

      const createdRelease = await createMobileReleaseAdmin({
        config: config.id,
        release_version: version,
        build_number: buildNumber,
        update_policy: releasePolicyDraft,
        is_critical_update: releaseCriticalDraft,
        min_supported_version: releaseMinVersionDraft.trim() || version,
        recommended_version: releaseRecommendedVersionDraft.trim() || version,
        release_notes: releaseNotesDraft.trim(),
      });

      const refreshedReleases = await listMobileReleasesAdmin();
      setMobileReleases(refreshedReleases);
      setReleaseMinVersionDraft(createdRelease.min_supported_version);
      setReleaseRecommendedVersionDraft(createdRelease.recommended_version);
      setSuccessMessage(
        `Release ${createdRelease.release_version}+${createdRelease.build_number} compilada e assinada.`,
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCompilingRelease(false);
    }
  }

  async function handlePublishRelease(releaseId: number) {
    setPublishingReleaseId(releaseId);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const updatedRelease = await publishMobileReleaseAdmin(releaseId);
      setMobileReleases((previous) =>
        previous.map((item) => (item.id === updatedRelease.id ? updatedRelease : item)),
      );
      setSuccessMessage(
        `Release ${updatedRelease.release_version}+${updatedRelease.build_number} publicada.`,
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setPublishingReleaseId(null);
    }
  }

  async function handleSaveSection() {
    if (!selectedSection) {
      return;
    }

    setSavingSection(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const parsedSortOrder = Number.parseInt(sectionSortOrderDraft, 10);
      if (Number.isNaN(parsedSortOrder) || parsedSortOrder < 0) {
        throw new Error("Informe um sort_order valido (0 ou maior).");
      }

      let parsedBodyJson: unknown;
      try {
        parsedBodyJson = parseBodyJson(sectionBodyJsonDraft);
      } catch {
        throw new Error("JSON invalido no body_json da secao.");
      }

      const updatedSection = await updatePortalSectionAdmin(selectedSection.id, {
        title: sectionTitleDraft.trim(),
        sort_order: parsedSortOrder,
        is_enabled: sectionEnabledDraft,
        body_json: parsedBodyJson,
      });

      setSections((previous) =>
        previous.map((section) =>
          section.id === updatedSection.id ? updatedSection : section,
        ),
      );
      setSuccessMessage(
        `Secao ${updatedSection.key} atualizada com sucesso para o template ${updatedSection.template_id}.`,
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSavingSection(false);
    }
  }

  async function handlePublishConfig() {
    setPublishing(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const publishedConfig = await publishPortalConfigAdmin();
      setConfig(publishedConfig);
      setSelectedTemplateId(publishedConfig.active_template);
      setSelectedClientTemplateId(publishedConfig.client_active_template);
      setSelectedAdminTemplateId(publishedConfig.admin_active_template);
      setContentTemplateId(publishedConfig.active_template);
      setSuccessMessage("Configuracao do portal publicada com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setPublishing(false);
    }
  }

  return (
    <>
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-text">Resumo da configuracao</h2>
            <p className="mt-1 text-sm text-muted">
              Controle do template ativo, seções dinamicas e publicacao do portal.
            </p>
          </div>
          {config?.is_published ? (
            <StatusPill tone="success">Publicado</StatusPill>
          ) : (
            <StatusPill tone="warning">Rascunho</StatusPill>
          )}
        </div>
        {loading && <InlinePreloader message="Carregando configuracoes do portal..." className="mt-3 justify-start bg-surface/70" />}
        {!loading && config && (
          <div className="mt-4 grid gap-3 md:grid-cols-7">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Template ativo</p>
              <p className="mt-1 text-base font-semibold text-text">{activeTemplateLabel}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Template cliente</p>
              <p className="mt-1 text-base font-semibold text-text">{activeClientTemplateLabel}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Template admin</p>
              <p className="mt-1 text-base font-semibold text-text">{activeAdminTemplateLabel}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Templates disponiveis</p>
              <p className="mt-1 text-base font-semibold text-text">
                {templateOptions.length + clientTemplateOptions.length + adminTemplateOptions.length}
              </p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Secoes CMS</p>
              <p className="mt-1 text-base font-semibold text-text">{sections.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Ultima publicacao</p>
              <p className="mt-1 text-base font-semibold text-text">{formatDateTime(config.published_at)}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Cloudflare</p>
              <p className="mt-1 text-base font-semibold text-text">
                {normalizeCloudflareSettings(config.cloudflare_settings).enabled ? "Ativo" : "Inativo"}
              </p>
            </article>
          </div>
        )}
      </section>

      {shouldRenderSection("template", "portal") && (
        <section id="template" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Templates ativos por canal</h2>
          <p className="mt-1 text-sm text-muted">
            Escolha templates do Portal e do Web Cliente com publicacao unificada.
          </p>
          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <article className="rounded-xl border border-border bg-bg p-4">
              <label className="flex flex-col gap-2 text-sm font-medium text-text">
                Template do Portal
                <select
                  value={selectedTemplateId}
                  onChange={(event) => setSelectedTemplateId(event.target.value)}
                  disabled={loading || saving || templateOptions.length === 0}
                  className="rounded-xl border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  {templateOptions.length === 0 && (
                    <option value="">Nenhum template disponivel</option>
                  )}
                  {templateOptions.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <div className="mt-3">
                <button
                  type="button"
                  onClick={() => void handleSaveTemplate()}
                  disabled={
                    loading ||
                    saving ||
                    !config ||
                    !selectedTemplateId ||
                    selectedTemplateId === config.active_template
                  }
                  className="rounded-xl border border-primary bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {saving ? "Salvando..." : "Salvar template do portal"}
                </button>
              </div>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <label className="flex flex-col gap-2 text-sm font-medium text-text">
                Template do Web Cliente
                <select
                  value={selectedClientTemplateId}
                  onChange={(event) => setSelectedClientTemplateId(event.target.value)}
                  disabled={loading || saving || clientTemplateOptions.length === 0}
                  className="rounded-xl border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  {clientTemplateOptions.length === 0 && (
                    <option value="">Nenhum template de cliente disponivel</option>
                  )}
                  {clientTemplateOptions.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <div className="mt-3">
                <button
                  type="button"
                  onClick={() => void handleSaveClientTemplate()}
                  disabled={
                    loading ||
                    saving ||
                    !config ||
                    !selectedClientTemplateId ||
                    selectedClientTemplateId === config.client_active_template
                  }
                  className="rounded-xl border border-primary bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {saving ? "Salvando..." : "Salvar template do cliente"}
                </button>
              </div>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <label className="flex flex-col gap-2 text-sm font-medium text-text">
                Template do Web Admin
                <select
                  value={selectedAdminTemplateId}
                  onChange={(event) => setSelectedAdminTemplateId(event.target.value)}
                  disabled={loading || saving || adminTemplateOptions.length === 0}
                  className="rounded-xl border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  {adminTemplateOptions.length === 0 && (
                    <option value="">Nenhum template do admin disponivel</option>
                  )}
                  {adminTemplateOptions.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <p className="mt-3 text-xs text-muted">
                O template admin muda layout, navegacao e graficos do painel.
              </p>
              <div className="mt-3">
                <button
                  type="button"
                  onClick={() => void handleSaveAdminTemplate()}
                  disabled={
                    loading ||
                    saving ||
                    !config ||
                    !selectedAdminTemplateId ||
                    selectedAdminTemplateId === config.admin_active_template
                  }
                  className="rounded-xl border border-primary bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {saving ? "Salvando..." : "Salvar template do admin"}
                </button>
              </div>
            </article>
          </div>
        </section>
      )}

      {shouldRenderSection("autenticacao", "portal") && (
        <section
          id="autenticacao"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-text">Autenticacao social</h2>
          <p className="mt-1 text-sm text-muted">
            Centralize no Admin os parametros de OAuth para Web Cliente e App Mobile.
            Campos de cada box pertencem ao respectivo provider.
          </p>

          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            <SetupReferenceLinks title="Links de cadastro e setup Google" links={GOOGLE_AUTH_REFERENCE_LINKS} />
            <SetupReferenceLinks title="Links de cadastro e setup Apple" links={APPLE_AUTH_REFERENCE_LINKS} />
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <article className="rounded-xl border border-border bg-bg p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-base font-semibold text-text">Google</p>
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={googleEnabledDraft}
                    onChange={(event) => setGoogleEnabledDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Habilitado
                </label>
              </div>
              <div className="mt-3 grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Client ID (Web)
                  <input
                    value={googleWebClientIdDraft}
                    onChange={(event) => setGoogleWebClientIdDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Client ID (iOS - Google Sign-In do app)
                  <input
                    value={googleIosClientIdDraft}
                    onChange={(event) => setGoogleIosClientIdDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Client ID (Android)
                  <input
                    value={googleAndroidClientIdDraft}
                    onChange={(event) => setGoogleAndroidClientIdDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Client Secret
                  <input
                    value={googleClientSecretDraft}
                    onChange={(event) => setGoogleClientSecretDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  URL de autorizacao
                  <input
                    value={googleAuthUriDraft}
                    onChange={(event) => setGoogleAuthUriDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  URL de token
                  <input
                    value={googleTokenUriDraft}
                    onChange={(event) => setGoogleTokenUriDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Redirect URI (web)
                  <input
                    value={googleRedirectWebDraft}
                    onChange={(event) => setGoogleRedirectWebDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Redirect URI (mobile)
                  <input
                    value={googleRedirectMobileDraft}
                    onChange={(event) => setGoogleRedirectMobileDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Escopos
                  <input
                    value={googleScopeDraft}
                    onChange={(event) => setGoogleScopeDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
              </div>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-base font-semibold text-text">Apple</p>
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={appleEnabledDraft}
                    onChange={(event) => setAppleEnabledDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Habilitado
                </label>
              </div>
              <div className="mt-3 grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Service ID (Client ID Apple)
                  <input
                    value={appleServiceIdDraft}
                    onChange={(event) => setAppleServiceIdDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Team ID
                  <input
                    value={appleTeamIdDraft}
                    onChange={(event) => setAppleTeamIdDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Key ID
                  <input
                    value={appleKeyIdDraft}
                    onChange={(event) => setAppleKeyIdDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Private Key
                  <textarea
                    rows={5}
                    value={applePrivateKeyDraft}
                    onChange={(event) => setApplePrivateKeyDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  URL de autorizacao
                  <input
                    value={appleAuthUriDraft}
                    onChange={(event) => setAppleAuthUriDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  URL de token
                  <input
                    value={appleTokenUriDraft}
                    onChange={(event) => setAppleTokenUriDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Redirect URI (web)
                  <input
                    value={appleRedirectWebDraft}
                    onChange={(event) => setAppleRedirectWebDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Redirect URI (mobile)
                  <input
                    value={appleRedirectMobileDraft}
                    onChange={(event) => setAppleRedirectMobileDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Escopos
                  <input
                    value={appleScopeDraft}
                    onChange={(event) => setAppleScopeDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
              </div>
            </article>
          </div>

          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={() => void handleSaveAuthProviders()}
              disabled={loading || saving || !config}
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {saving ? "Salvando..." : "Salvar parametros de autenticacao"}
            </button>
          </div>
        </section>
      )}

      {shouldRenderSection("pagamentos", "portal") && (
        <section
          id="pagamentos"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-text">Pagamentos e gateways</h2>
          <p className="mt-1 text-sm text-muted">
            Configure Mercado Pago, Efi e Asaas, defina roteamento por metodo e valide
            conexao com botao de teste.
          </p>

          <div className="mt-4 grid gap-3 xl:grid-cols-3">
            <SetupReferenceLinks title="Cadastro e setup Mercado Pago" links={MERCADOPAGO_REFERENCE_LINKS} />
            <SetupReferenceLinks title="Cadastro e setup Efi" links={EFI_REFERENCE_LINKS} />
            <SetupReferenceLinks title="Cadastro e setup Asaas" links={ASAAS_REFERENCE_LINKS} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <article className="rounded-xl border border-border bg-bg p-4">
              <h3 className="text-base font-semibold text-text">Roteamento geral</h3>
              <div className="mt-3 grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Provider padrao
                  <select
                    value={paymentDefaultProviderDraft}
                    onChange={(event) => setPaymentDefaultProviderDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  >
                    {PAYMENT_PROVIDER_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Provider do frontend Web Cliente (um unico)
                  <select
                    value={paymentWebProviderDraft}
                    onChange={(event) => setPaymentWebProviderDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  >
                    {PAYMENT_PROVIDER_OPTIONS.map((option) => (
                      <option key={`web-${option.value}`} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Provider do App Mobile (um unico)
                  <select
                    value={paymentMobileProviderDraft}
                    onChange={(event) => setPaymentMobileProviderDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  >
                    {PAYMENT_PROVIDER_OPTIONS.map((option) => (
                      <option key={`mobile-${option.value}`} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="rounded-md border border-border bg-surface/60 px-3 py-2 text-xs text-muted">
                  Os frontends usam canal autenticado e criptografado ja padronizado. Ao ativar um
                  provider por canal, o backend passa a resolver intents por `WEB` ou `MOBILE`
                  automaticamente.
                </p>

                <fieldset className="grid gap-2">
                  <legend className="text-sm text-muted">Providers habilitados</legend>
                  {PAYMENT_PROVIDER_OPTIONS.map((option) => (
                    <label key={option.value} className="inline-flex items-center gap-2 text-sm text-text">
                      <input
                        type="checkbox"
                        checked={paymentEnabledProvidersDraft.includes(option.value)}
                        onChange={() => handleToggleEnabledPaymentProvider(option.value)}
                        className="h-4 w-4 rounded border-border text-primary"
                      />
                      {option.label}
                    </label>
                  ))}
                </fieldset>

                <label className="grid gap-1 text-sm text-muted">
                  Ordem de provider para PIX (separar por virgula)
                  <input
                    value={paymentPixOrderDraft}
                    onChange={(event) => setPaymentPixOrderDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="asaas, mercadopago, efi, mock"
                  />
                </label>

                <label className="grid gap-1 text-sm text-muted">
                  Ordem de provider para CARTAO (separar por virgula)
                  <input
                    value={paymentCardOrderDraft}
                    onChange={(event) => setPaymentCardOrderDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="mercadopago, asaas, efi, mock"
                  />
                </label>

                <label className="grid gap-1 text-sm text-muted">
                  Ordem de provider para VR (separar por virgula)
                  <input
                    value={paymentVrOrderDraft}
                    onChange={(event) => setPaymentVrOrderDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="mock"
                  />
                </label>
              </div>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <h3 className="text-base font-semibold text-text">Recebedor</h3>
              <div className="mt-3 grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Tipo de pessoa
                  <select
                    value={receiverPersonTypeDraft}
                    onChange={(event) =>
                      setReceiverPersonTypeDraft(event.currentTarget.value as "CPF" | "CNPJ")
                    }
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  >
                    <option value="CPF">CPF</option>
                    <option value="CNPJ">CNPJ</option>
                  </select>
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Documento
                  <input
                    name={receiverPersonTypeDraft === "CPF" ? "receiver_cpf" : "receiver_cnpj"}
                    value={receiverDocumentDraft}
                    onChange={(event) => setReceiverDocumentDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Nome/razao social
                  <input
                    value={receiverNameDraft}
                    onChange={(event) => setReceiverNameDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Email financeiro
                  <input
                    name="receiver_email"
                    value={receiverEmailDraft}
                    onChange={(event) => setReceiverEmailDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            {selectedFrontendProviders.has("mercadopago") && (
            <article className="rounded-xl border border-border bg-bg p-4">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-base font-semibold text-text">Mercado Pago</h3>
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={mercadoPagoEnabledDraft}
                    onChange={(event) => setMercadoPagoEnabledDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Habilitado
                </label>
              </div>
              <div className="mt-3 grid gap-2">
                <input
                  value={mercadoPagoApiBaseUrlDraft}
                  onChange={(event) => setMercadoPagoApiBaseUrlDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="API Base URL"
                />
                <input
                  value={mercadoPagoAccessTokenDraft}
                  onChange={(event) => setMercadoPagoAccessTokenDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="Access Token"
                />
                <input
                  value={mercadoPagoWebhookSecretDraft}
                  onChange={(event) => setMercadoPagoWebhookSecretDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="Webhook Secret (opcional)"
                />
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={mercadoPagoSandboxDraft}
                    onChange={(event) => setMercadoPagoSandboxDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Sandbox
                </label>
              </div>
              <button
                type="button"
                onClick={() => void handleTestPaymentProvider("mercadopago")}
                disabled={testingProvider !== null}
                className="mt-3 rounded-md border border-border px-3 py-2 text-xs font-semibold text-text transition hover:border-primary disabled:opacity-70"
              >
                {testingProvider === "mercadopago" ? "Testando..." : "Testar conexao"}
              </button>
            </article>
            )}

            {selectedFrontendProviders.has("efi") && (
            <article className="rounded-xl border border-border bg-bg p-4">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-base font-semibold text-text">Efi</h3>
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={efiEnabledDraft}
                    onChange={(event) => setEfiEnabledDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Habilitado
                </label>
              </div>
              <div className="mt-3 grid gap-2">
                <input
                  value={efiApiBaseUrlDraft}
                  onChange={(event) => setEfiApiBaseUrlDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="API Base URL"
                />
                <input
                  value={efiClientIdDraft}
                  onChange={(event) => setEfiClientIdDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="Client ID"
                />
                <input
                  value={efiClientSecretDraft}
                  onChange={(event) => setEfiClientSecretDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="Client Secret"
                />
                <input
                  value={efiWebhookSecretDraft}
                  onChange={(event) => setEfiWebhookSecretDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="Webhook Secret (opcional)"
                />
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={efiSandboxDraft}
                    onChange={(event) => setEfiSandboxDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Sandbox
                </label>
              </div>
              <button
                type="button"
                onClick={() => void handleTestPaymentProvider("efi")}
                disabled={testingProvider !== null}
                className="mt-3 rounded-md border border-border px-3 py-2 text-xs font-semibold text-text transition hover:border-primary disabled:opacity-70"
              >
                {testingProvider === "efi" ? "Testando..." : "Testar conexao"}
              </button>
            </article>
            )}

            {selectedFrontendProviders.has("asaas") && (
            <article className="rounded-xl border border-border bg-bg p-4">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-base font-semibold text-text">Asaas</h3>
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={asaasEnabledDraft}
                    onChange={(event) => setAsaasEnabledDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Habilitado
                </label>
              </div>
              <div className="mt-3 grid gap-2">
                <input
                  value={asaasApiBaseUrlDraft}
                  onChange={(event) => setAsaasApiBaseUrlDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="API Base URL"
                />
                <input
                  value={asaasApiKeyDraft}
                  onChange={(event) => setAsaasApiKeyDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="API Key"
                />
                <input
                  value={asaasWebhookSecretDraft}
                  onChange={(event) => setAsaasWebhookSecretDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="Webhook Secret (opcional)"
                />
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={asaasSandboxDraft}
                    onChange={(event) => setAsaasSandboxDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Sandbox
                </label>
              </div>
              <button
                type="button"
                onClick={() => void handleTestPaymentProvider("asaas")}
                disabled={testingProvider !== null}
                className="mt-3 rounded-md border border-border px-3 py-2 text-xs font-semibold text-text transition hover:border-primary disabled:opacity-70"
              >
                {testingProvider === "asaas" ? "Testando..." : "Testar conexao"}
              </button>
            </article>
            )}
          </div>
          {!selectedFrontendProviders.has("mercadopago") &&
            !selectedFrontendProviders.has("efi") &&
            !selectedFrontendProviders.has("asaas") && (
              <p className="mt-3 rounded-md border border-border bg-bg px-3 py-2 text-xs text-muted">
                Nenhum provider externo selecionado para WEB/MOBILE. O canal ficara em `mock`.
              </p>
            )}

          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={() => void handleSavePaymentProviders()}
              disabled={loading || saving || !config}
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {saving ? "Salvando..." : "Salvar configuracoes de pagamento"}
            </button>
          </div>
        </section>
      )}

      {shouldRenderSection("email", "server-admin") && (
        <section id="email" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Gestao de e-mail</h2>
          <p className="mt-1 text-sm text-muted">
            Configure SMTP para envio de confirmacoes e notificacoes, com teste imediato.
          </p>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <article className="rounded-xl border border-border bg-bg p-4">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-base font-semibold text-text">Servidor SMTP</h3>
                <label className="inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={emailEnabledDraft}
                    onChange={(event) => setEmailEnabledDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Habilitar SMTP customizado
                </label>
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <label className="grid gap-1 text-sm text-muted md:col-span-2">
                  Backend de e-mail
                  <input
                    value={emailBackendDraft}
                    onChange={(event) => setEmailBackendDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="django.core.mail.backends.smtp.EmailBackend"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Host SMTP
                  <input
                    value={emailHostDraft}
                    onChange={(event) => setEmailHostDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="smtp.seu-dominio.com"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Porta SMTP
                  <input
                    value={emailPortDraft}
                    onChange={(event) => setEmailPortDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="587"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Usuario SMTP
                  <input
                    value={emailUsernameDraft}
                    onChange={(event) => setEmailUsernameDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="usuario"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Senha SMTP
                  <input
                    type="password"
                    value={emailPasswordDraft}
                    onChange={(event) => setEmailPasswordDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="senha"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Timeout (s)
                  <input
                    value={emailTimeoutDraft}
                    onChange={(event) => setEmailTimeoutDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="15"
                  />
                </label>
                <div className="flex flex-wrap items-center gap-4 pt-6">
                  <label className="inline-flex items-center gap-2 text-sm text-text">
                    <input
                      type="checkbox"
                      checked={emailUseTlsDraft}
                      onChange={(event) => setEmailUseTlsDraft(event.currentTarget.checked)}
                      className="h-4 w-4 rounded border-border text-primary"
                    />
                    TLS
                  </label>
                  <label className="inline-flex items-center gap-2 text-sm text-text">
                    <input
                      type="checkbox"
                      checked={emailUseSslDraft}
                      onChange={(event) => setEmailUseSslDraft(event.currentTarget.checked)}
                      className="h-4 w-4 rounded border-border text-primary"
                    />
                    SSL
                  </label>
                </div>
              </div>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <h3 className="text-base font-semibold text-text">Identidade de envio</h3>
              <div className="mt-3 grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Nome do remetente
                  <input
                    value={emailFromNameDraft}
                    onChange={(event) => setEmailFromNameDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="Mr Quentinha"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  E-mail remetente
                  <input
                    value={emailFromAddressDraft}
                    onChange={(event) => setEmailFromAddressDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="noreply@mrquentinha.com.br"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Reply-to
                  <input
                    value={emailReplyToDraft}
                    onChange={(event) => setEmailReplyToDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="suporte@mrquentinha.com.br"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Destinatario de teste
                  <input
                    value={emailTestRecipientDraft}
                    onChange={(event) => setEmailTestRecipientDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="qa@mrquentinha.com.br"
                  />
                </label>
                <p className="rounded-md border border-border bg-surface/60 px-3 py-2 text-xs text-muted">
                  A validacao de e-mail obrigatoria permanece restrita a usuarios cliente. Perfis
                  administrativos/gestao (incluindo root/superuser) continuam com acesso ao Web Admin.
                </p>
                <div className="flex flex-wrap justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => void handleTestEmailSettings()}
                    disabled={testingEmail || loading}
                    className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {testingEmail ? "Testando..." : "Enviar e-mail de teste"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleSaveEmailSettings()}
                    disabled={loading || saving || !config}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {saving ? "Salvando..." : "Salvar configuracao de e-mail"}
                  </button>
                </div>
              </div>
            </article>
          </div>
        </section>
      )}

      {shouldRenderSection("conectividade", "server-admin") && (
        <section
          id="conectividade"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-text">Conectividade e dominios</h2>
          <p className="mt-1 text-sm text-muted">
            Configure host local, dominios/subdominios e URLs de cada aplicacao para
            desenvolvimento em rede local.
          </p>

          <div className="mt-4">
            <DatabaseSshAccessPanel compact />
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <label className="grid gap-1 text-sm text-muted">
              Host local da maquina
              <input
                value={localHostnameDraft}
                onChange={(event) => setLocalHostnameDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="mrquentinha"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              IP da rede local (opcional)
              <input
                value={localNetworkIpDraft}
                onChange={(event) => setLocalNetworkIpDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="10.211.55.21"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Endereco da API (unico)
              <input
                value={apiBaseUrlDraft}
                onChange={(event) => setApiBaseUrlDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="https://10.211.55.21:8000"
              />
            </label>
            <div className="flex items-end">
              <button
                type="button"
                onClick={handleApplyLocalPreset}
                className="w-full rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Aplicar preset local
              </button>
            </div>
          </div>

          <article className="mt-4 rounded-xl border border-border bg-bg p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-text">API publica para app mobile</h3>
                <p className="mt-1 text-xs text-muted">
                  Web client no servidor usa API local. Quando habilitar acesso externo para o app
                  mobile, utilize apenas endpoint AWS (DNS EC2 ou IP publico), sem dominio
                  `mrquentinha.com.br`.
                </p>
              </div>
              <label className="inline-flex items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={mobileApiPublicEnabledDraft}
                  onChange={(event) => setMobileApiPublicEnabledDraft(event.currentTarget.checked)}
                  className="h-4 w-4 rounded border-border text-primary"
                />
                Habilitar porta publica da API para mobile
              </label>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <label className="grid gap-1 text-sm text-muted">
                Endpoint preferencial
                <select
                  value={mobileApiPreferredEndpointDraft}
                  onChange={(event) =>
                    setMobileApiPreferredEndpointDraft(
                      event.currentTarget.value as "public_ip" | "aws_dns",
                    )
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="public_ip">IP publico (44.192.27.104)</option>
                  <option value="aws_dns">
                    DNS AWS (ec2-44-192-27-104.compute-1.amazonaws.com)
                  </option>
                </select>
              </label>

              <label className="grid gap-1 text-sm text-muted">
                API publica por IP
                <input
                  value={mobileApiPublicIpUrlDraft}
                  onChange={(event) => setMobileApiPublicIpUrlDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="http://44.192.27.104"
                />
              </label>

              <label className="grid gap-1 text-sm text-muted">
                API publica por DNS AWS
                <input
                  value={mobileApiAwsDnsUrlDraft}
                  onChange={(event) => setMobileApiAwsDnsUrlDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="http://ec2-44-192-27-104.compute-1.amazonaws.com"
                />
              </label>
            </div>
          </article>

          <article className="mt-4 rounded-xl border border-border bg-bg p-4">
            <h3 className="text-base font-semibold text-text">
              Modo de funcionamento do WebAdmin
            </h3>
            <p className="mt-1 text-xs text-muted">
              Defina o perfil operacional deste ambiente: dev, producao ou hibrido.
            </p>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <label className="grid gap-1 text-sm text-muted">
                Modo operacional
                <select
                  value={environmentModeDraft}
                  onChange={(event) =>
                    handleEnvironmentModeChange(
                      event.currentTarget.value as WebAdminEnvironmentMode,
                    )
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="dev">Ambiente DEV</option>
                  <option value="production">Ambiente Producao</option>
                  <option value="hybrid">Ambiente Hibrido</option>
                </select>
              </label>
              <div className="rounded-md border border-border bg-surface/60 px-3 py-2 text-xs text-muted">
                <p>
                  <strong className="text-text">DEV:</strong> prioriza rede local, testes e
                  ajustes rapidos.
                </p>
                <p className="mt-1">
                  <strong className="text-text">PRODUCAO:</strong> bloqueia URL random de
                  desenvolvimento e evita mudancas instaveis.
                </p>
                <p className="mt-1">
                  <strong className="text-text">HIBRIDO:</strong> permite operacao local e
                  Cloudflare em paralelo.
                </p>
              </div>
            </div>

            {isProductionEnvironmentMode && (
              <p className="mt-3 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
                Seguranca para producao: o modo DEV com dominios random fica desativado. Antes de
                publicar alteracoes, valide DNS, SSL e health checks para nao impactar uma maquina
                ja online.
              </p>
            )}
            {cloudflareApiStatus && (
              <div className="mt-4 rounded-xl border border-border bg-surface/60 p-3 text-xs text-muted">
                <p className="font-semibold text-text">Diagnostico Cloudflare API</p>
                <p className="mt-1">
                  Token: <strong className="text-text">{cloudflareApiStatus.token.valid ? "valido" : "invalido"}</strong>
                  {" "}| Zona: <strong className="text-text">{cloudflareApiStatus.zone.resolved ? "resolvida" : "nao resolvida"}</strong>
                </p>
                <p className="mt-1">
                  DNS faltando: <strong className="text-text">{cloudflareApiStatus.dns.missing.length}</strong>
                </p>
                {cloudflareApiStatus.token.errors.length > 0 && (
                  <p className="mt-2 text-amber-200">
                    Token: {cloudflareApiStatus.token.errors.join(" | ")}
                  </p>
                )}
                {cloudflareApiStatus.zone.errors.length > 0 && (
                  <p className="mt-1 text-amber-200">
                    Zona: {cloudflareApiStatus.zone.errors.join(" | ")}
                  </p>
                )}
                {cloudflareApiStatus.dns.errors.length > 0 && (
                  <p className="mt-1 text-amber-200">
                    DNS: {cloudflareApiStatus.dns.errors.join(" | ")}
                  </p>
                )}
                <div className="mt-2 rounded-md border border-border bg-bg px-2 py-2">
                  <p className="font-semibold text-text">Permissoes minimas recomendadas</p>
                  {cloudflareApiStatus.guide.required_permissions.map((item) => (
                    <p key={item} className="mt-1">- {item}</p>
                  ))}
                </div>
                <div className="mt-2 rounded-md border border-border bg-bg px-2 py-2">
                  <p className="font-semibold text-text">Guia rapido de ativacao</p>
                  {cloudflareApiStatus.guide.steps.map((item) => (
                    <p key={item} className="mt-1">{item}</p>
                  ))}
                  <div className="mt-2 grid gap-1">
                    {cloudflareApiStatus.guide.docs.map((doc) => (
                      <a
                        key={doc.url}
                        href={doc.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary underline-offset-2 hover:underline"
                      >
                        {doc.label}
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </article>

          <article className="mt-4 rounded-xl border border-border bg-bg p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-text">Cloudflare online (1 clique)</h3>
                <p className="mt-1 text-xs text-muted">
                  Configure dominio/subdominios e ative ou desative todo o roteamento externo.
                  O modo <strong>hybrid</strong> permite Cloudflare + rede local simultaneos.
                </p>
              </div>
              <StatusPill tone={cloudflareEnabledDraft ? "success" : "neutral"}>
                {cloudflareEnabledDraft ? "Ativo" : "Inativo"}
              </StatusPill>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <label className="grid gap-1 text-sm text-muted">
                Modo de exposicao
                <select
                  value={cloudflareModeDraft}
                  onChange={(event) =>
                    setCloudflareModeDraft(event.currentTarget.value as PortalCloudflareMode)
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="hybrid">Hybrid (local + cloudflare)</option>
                  <option value="cloudflare_only">Somente cloudflare</option>
                  <option value="local_only">Somente local</option>
                </select>
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Protocolo
                <select
                  value={cloudflareSchemeDraft}
                  onChange={(event) =>
                    setCloudflareSchemeDraft(event.currentTarget.value as "http" | "https")
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="https">https</option>
                  <option value="http">http</option>
                </select>
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Dominio raiz Cloudflare
                <input
                  value={cloudflareRootDomainDraft}
                  onChange={(event) => setCloudflareRootDomainDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="mrquentinha.com.br"
                />
              </label>
              <label className="mt-6 inline-flex items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={cloudflareAutoApplyRoutesDraft}
                  onChange={(event) => setCloudflareAutoApplyRoutesDraft(event.currentTarget.checked)}
                  className="h-4 w-4 rounded border-border text-primary"
                />
                Atualizar links automaticamente
              </label>
            </div>

            <div className="mt-3 rounded-lg border border-border bg-surface/60 px-3 py-2">
              <label className="inline-flex items-center gap-2 text-sm font-medium text-text">
                <input
                  type="checkbox"
                  checked={cloudflareDevModeDraft}
                  onChange={(event) => setCloudflareDevModeDraft(event.currentTarget.checked)}
                  disabled={isProductionEnvironmentMode}
                  className="h-4 w-4 rounded border-border text-primary"
                />
                Modo DEV com dominios publicos
              </label>
              <p className="mt-1 text-xs text-muted">
                Quando ativo, as URLs DEV substituem as URLs de producao (portal/client/admin/api).
                Escolha entre trycloudflare (random), manual ou dominio oficial com portas.
              </p>
              {cloudflareDevModeDraft && isHybridEnvironmentMode && (
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div className="grid gap-2 text-sm text-muted">
                    <label className="grid gap-1 text-sm text-muted">
                      Modo de URL DEV
                      <select
                        value={cloudflareDevUrlModeDraft}
                        onChange={(event) =>
                          setCloudflareDevUrlModeDraft(
                            event.currentTarget.value as PortalCloudflareDevUrlMode,
                          )
                        }
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      >
                        <option value="random" disabled={!isHybridEnvironmentMode}>
                          Random (trycloudflare)
                        </option>
                        <option value="manual">Manual (URLs estaveis)</option>
                        <option value="official">Dominio oficial + portas</option>
                      </select>
                    </label>
                    <p className="text-xs">
                      Status atual:{" "}
                      <strong className="text-text">
                        {cloudflareDevUrlModeDraft === "manual"
                          ? "manual"
                          : cloudflareDevUrlModeDraft === "official"
                            ? "dominio oficial"
                            : "random"}
                      </strong>
                    </p>
                  </div>
                  <p className="rounded-md border border-border bg-bg px-3 py-2 text-xs text-muted">
                    Em <strong>manual</strong>, as URLs abaixo viram referencia ativa para
                    roteamento/API dos frontends no modo DEV. Em <strong>random</strong>, o sistema
                    usa os dominios gerados pelo runtime (somente no modo hibrido). Em
                    <strong>oficial</strong>, usa um unico dominio (ex.: dev.mrquentinha.com.br) com
                    portas 3000/3001/3002/8000.
                  </p>
                </div>
              )}
            </div>

            {cloudflareDevModeDraft && (
              <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <label className="grid gap-1 text-sm text-muted">
                  DEV Portal URL
                  <input
                    value={cloudflarePortalDevUrlDraft}
                    onChange={(event) => setCloudflarePortalDevUrlDraft(event.currentTarget.value)}
                    disabled={!customDevHostsEnabled}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="https://portal-mrquentinha.trycloudflare.com"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  DEV Client URL
                  <input
                    value={cloudflareClientDevUrlDraft}
                    onChange={(event) => setCloudflareClientDevUrlDraft(event.currentTarget.value)}
                    disabled={!customDevHostsEnabled}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="https://cliente-mrquentinha.trycloudflare.com"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  DEV Admin URL
                  <input
                    value={cloudflareAdminDevUrlDraft}
                    onChange={(event) => setCloudflareAdminDevUrlDraft(event.currentTarget.value)}
                    disabled={!customDevHostsEnabled}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="https://admin-mrquentinha.trycloudflare.com"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  DEV API URL
                  <input
                    value={cloudflareApiDevUrlDraft}
                    onChange={(event) => setCloudflareApiDevUrlDraft(event.currentTarget.value)}
                    disabled={!customDevHostsEnabled}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="https://api-mrquentinha.trycloudflare.com"
                  />
                </label>
              </div>
            )}

            {cloudflareDevModeDraft && officialDevHostsEnabled && (
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <label className="grid gap-1 text-sm text-muted">
                  Dominio oficial DEV (porta por servico)
                  <input
                    value={cloudflareDevOfficialDomainDraft}
                    onChange={(event) =>
                      setCloudflareDevOfficialDomainDraft(event.currentTarget.value)
                    }
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="dev.mrquentinha.com.br"
                  />
                </label>
                <div className="rounded-md border border-border bg-bg px-3 py-2 text-xs text-muted">
                  Este dominio sera aplicado como:
                  <br />
                  Portal: https://dev.mrquentinha.com.br:3000
                  <br />
                  Client: https://dev.mrquentinha.com.br:3001
                  <br />
                  Admin: https://dev.mrquentinha.com.br:3002
                  <br />
                  API: https://dev.mrquentinha.com.br:8000
                </div>
              </div>
            )}

            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <label className="grid gap-1 text-sm text-muted">
                Subdominio Portal
                <input
                  value={cloudflarePortalSubdomainDraft}
                  onChange={(event) => setCloudflarePortalSubdomainDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="www"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Subdominio Cliente
                <input
                  value={cloudflareClientSubdomainDraft}
                  onChange={(event) => setCloudflareClientSubdomainDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="app"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Subdominio Admin
                <input
                  value={cloudflareAdminSubdomainDraft}
                  onChange={(event) => setCloudflareAdminSubdomainDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="admin"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Subdominio API
                <input
                  value={cloudflareApiSubdomainDraft}
                  onChange={(event) => setCloudflareApiSubdomainDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="api"
                />
              </label>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <label className="grid gap-1 text-sm text-muted">
                Tunnel name
                <input
                  value={cloudflareTunnelNameDraft}
                  onChange={(event) => setCloudflareTunnelNameDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="mrquentinha"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Tunnel ID (opcional)
                <input
                  value={cloudflareTunnelIdDraft}
                  onChange={(event) => setCloudflareTunnelIdDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Tunnel token (opcional)
                <input
                  value={cloudflareTunnelTokenDraft}
                  onChange={(event) => setCloudflareTunnelTokenDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Account ID (opcional)
                <input
                  value={cloudflareAccountIdDraft}
                  onChange={(event) => setCloudflareAccountIdDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Zone ID (opcional)
                <input
                  value={cloudflareZoneIdDraft}
                  onChange={(event) => setCloudflareZoneIdDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                API token (opcional)
                <input
                  value={cloudflareApiTokenDraft}
                  onChange={(event) => setCloudflareApiTokenDraft(event.currentTarget.value)}
                  disabled={cloudflareDevModeDraft}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void handlePreviewCloudflare()}
                disabled={cloudflareSaving}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {cloudflareSaving ? "Processando..." : "Pre-visualizar rotas"}
              </button>
              <button
                type="button"
                onClick={() => void handleToggleCloudflare(true)}
                disabled={loading || cloudflareSaving || !config}
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {cloudflareSaving ? "Ativando..." : "Ativar Cloudflare"}
              </button>
              <button
                type="button"
                onClick={() => void handleToggleCloudflare(false)}
                disabled={loading || cloudflareSaving || !config}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {cloudflareSaving ? "Desativando..." : "Desativar Cloudflare"}
              </button>
              <button
                type="button"
                onClick={() => void handleCloudflareRuntimeAction("status")}
                disabled={cloudflareSaving || !config}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {cloudflareSaving ? "Atualizando..." : "Status runtime"}
              </button>
              <button
                type="button"
                onClick={() => void handleCloudflareApiStatus()}
                disabled={cloudflareSaving || !config}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {cloudflareSaving ? "Consultando..." : "Diagnosticar Cloudflare API"}
              </button>
              <button
                type="button"
                onClick={() => void handleCloudflareRuntimeAction("start")}
                disabled={cloudflareSaving || !config}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {cloudflareSaving ? "Iniciando..." : "Iniciar tunnel"}
              </button>
              {cloudflareDevModeDraft && isHybridEnvironmentMode && (
                <button
                  type="button"
                  onClick={() => void handleCloudflareRuntimeAction("refresh")}
                  disabled={cloudflareSaving || !config}
                  className="rounded-md border border-primary/40 bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition hover:border-primary hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {cloudflareSaving ? "Gerando..." : "Gerar novos dominios DEV"}
                </button>
              )}
              <button
                type="button"
                onClick={() => void handleCloudflareRuntimeAction("stop")}
                disabled={cloudflareSaving || !config}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {cloudflareSaving ? "Parando..." : "Parar tunnel"}
              </button>
            </div>

            {cloudflarePreview && (
              <div className="mt-4 rounded-xl border border-border bg-surface/60 p-3 text-xs text-muted">
                <p className="font-semibold text-text">Preview Cloudflare</p>
                <p className="mt-1">Modo: {cloudflarePreview.mode}</p>
                {cloudflarePreview.dev_mode && (
                  <p className="mt-1">
                    Origem URLs DEV:{" "}
                    <strong className="text-text">{cloudflarePreview.dev_url_mode || "random"}</strong>
                  </p>
                )}
                <p className="mt-1">
                  Portal: <ExternalUrl value={cloudflarePreview.urls.portal_base_url} />
                </p>
                <p className="mt-1">
                  Cliente: <ExternalUrl value={cloudflarePreview.urls.client_base_url} />
                </p>
                <p className="mt-1">
                  Admin: <ExternalUrl value={cloudflarePreview.urls.admin_base_url} />
                </p>
                <p className="mt-1">
                  API: <ExternalUrl value={cloudflarePreview.urls.api_base_url} />
                </p>
                <p className="mt-2 font-semibold text-text">Ingress sugerido</p>
                {cloudflarePreview.ingress_rules.map((rule) => (
                  <p key={rule} className="mt-1">
                    {rule}
                  </p>
                ))}
                {cloudflarePreview.tunnel.run_command && (
                  <p className="mt-2">
                    Comando: <code>{cloudflarePreview.tunnel.run_command}</code>
                  </p>
                )}
                <p className="mt-2">{cloudflarePreview.coexistence_note}</p>
              </div>
            )}

            {cloudflareRuntime && (
              <div className="mt-4 rounded-xl border border-border bg-surface/60 p-3 text-xs text-muted">
                <p className="font-semibold text-text">Runtime cloudflared</p>
                <p className="mt-1">
                  Estado: <strong className="text-text">{cloudflareRuntime.state}</strong> | PID:{" "}
                  <strong className="text-text">{cloudflareRuntime.pid ?? "-"}</strong>
                </p>
                <p className="mt-1">Ultimo start: {cloudflareRuntime.last_started_at || "-"}</p>
                <p className="mt-1">Ultimo stop: {cloudflareRuntime.last_stopped_at || "-"}</p>
                {cloudflareRuntime.dev_mode && (
                  <p className="mt-1">
                    Origem URLs DEV:{" "}
                    <strong className="text-text">{cloudflareRuntime.dev_url_mode || "random"}</strong>
                  </p>
                )}
                {cloudflareRuntime.run_command && (
                  <p className="mt-1">
                    Comando ativo: <code>{cloudflareRuntime.run_command}</code>
                  </p>
                )}
                {cloudflareRuntime.dev_mode && cloudflareRuntime.dev_urls && (
                  <div className="mt-2 rounded-md border border-border bg-bg px-2 py-2">
                    <p className="font-semibold text-text">URLs DEV ativas</p>
                    <p className="mt-1">
                      Portal: <ExternalUrl value={cloudflareRuntime.dev_urls.portal} />
                    </p>
                    <p className="mt-1">
                      Client: <ExternalUrl value={cloudflareRuntime.dev_urls.client} />
                    </p>
                    <p className="mt-1">
                      Admin: <ExternalUrl value={cloudflareRuntime.dev_urls.admin} />
                    </p>
                    <p className="mt-1">
                      API: <ExternalUrl value={cloudflareRuntime.dev_urls.api} />
                    </p>
                  </div>
                )}
                {cloudflareRuntime.dev_mode && cloudflareRuntime.dev_manual_urls && (
                  <div className="mt-2 rounded-md border border-border bg-bg px-2 py-2">
                    <p className="font-semibold text-text">Padrao manual configurado</p>
                    <p className="mt-1">
                      Portal: <ExternalUrl value={cloudflareRuntime.dev_manual_urls.portal} />
                    </p>
                    <p className="mt-1">
                      Client: <ExternalUrl value={cloudflareRuntime.dev_manual_urls.client} />
                    </p>
                    <p className="mt-1">
                      Admin: <ExternalUrl value={cloudflareRuntime.dev_manual_urls.admin} />
                    </p>
                    <p className="mt-1">
                      API: <ExternalUrl value={cloudflareRuntime.dev_manual_urls.api} />
                    </p>
                  </div>
                )}
                {cloudflareRuntime.dev_mode &&
                  cloudflareRuntime.dev_services &&
                  cloudflareRuntime.dev_services.length > 0 && (
                    <div className="mt-2 rounded-md border border-border bg-bg px-2 py-2">
                      <p className="font-semibold text-text">
                        Monitoramento de conectividade (dominios DEV)
                      </p>
                      <div className="mt-2 grid gap-2">
                        {cloudflareRuntime.dev_services.map((service) => (
                          <article
                            key={service.key}
                            className="rounded-md border border-border bg-surface/70 p-2"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <p className="font-semibold text-text">
                                {service.name} ({service.key}) · porta local {service.port}
                              </p>
                              <StatusPill
                                tone={resolveCloudflareConnectivityTone(service.connectivity)}
                              >
                                {formatCloudflareConnectivityLabel(service.connectivity)}
                              </StatusPill>
                            </div>
                            <p className="mt-1">
                              URL: <ExternalUrl value={service.url} />
                            </p>
                            {service.observed_url && service.observed_url !== service.url && (
                              <p className="mt-1">
                                URL observada no runtime:{" "}
                                <ExternalUrl value={service.observed_url} />
                              </p>
                            )}
                            <p className="mt-1">
                              PID: <strong className="text-text">{service.pid ?? "-"}</strong> ·
                              HTTP:{" "}
                              <strong className="text-text">
                                {service.http_status ?? "-"}
                              </strong>{" "}
                              · Latencia:{" "}
                              <strong className="text-text">
                                {service.latency_ms ?? "-"} ms
                              </strong>
                            </p>
                            <p className="mt-1">
                              Check: <ExternalUrl value={service.checked_url} /> em{" "}
                              <strong className="text-text">
                                {service.checked_at ? formatDateTime(service.checked_at) : "-"}
                              </strong>
                            </p>
                            {service.error && (
                              <p className="mt-1 text-rose-600">Detalhe: {service.error}</p>
                            )}
                          </article>
                        ))}
                      </div>
                    </div>
                  )}
                {cloudflareRuntime.last_error && (
                  <p className="mt-1 text-rose-600">
                    Erro: {cloudflareRuntime.last_error}
                  </p>
                )}
                <p className="mt-1">Log: <code>{cloudflareRuntime.log_file || "-"}</code></p>
                {cloudflareRuntime.last_log_lines.length > 0 && (
                  <div className="mt-2 max-h-48 overflow-auto rounded-md border border-border bg-bg p-2 font-mono">
                    {cloudflareRuntime.last_log_lines.map((line, index) => (
                      <p key={`${index}-${line}`} className="whitespace-pre-wrap break-words">
                        {line}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </article>

          <article className="mt-4 rounded-xl border border-border bg-bg p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-text">SSL/TLS e certificados</h3>
                <p className="mt-1 text-xs text-muted">
                  Gera e aplica certificados HTTPS (Lets Encrypt) para Portal, Client, Admin e API.
                  Requer Nginx e certbot instalados na instancia.
                </p>
              </div>
              <StatusPill tone={sslResult?.ok ? "success" : "neutral"}>
                {sslResult?.ok ? "Aplicado" : "Aguardando"}
              </StatusPill>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <label className="grid gap-1 text-sm text-muted">
                E-mail para o certificado
                <input
                  value={sslEmailDraft}
                  onChange={(event) => setSslEmailDraft(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="contato@mrquentinha.com.br"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Dominios (um por linha)
                <textarea
                  value={sslDomainsDraft}
                  onChange={(event) => setSslDomainsDraft(event.currentTarget.value)}
                  rows={4}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder={"www.mrquentinha.com.br\napp.mrquentinha.com.br\nadmin.mrquentinha.com.br\napi.mrquentinha.com.br"}
                />
              </label>
            </div>

            {sslResult && (
              <div className="mt-3 rounded-md border border-border bg-surface/60 px-3 py-2 text-xs text-muted">
                <p className="font-semibold text-text">
                  Resultado: {sslResult.ok ? "sucesso" : "falha"} (exit {sslResult.exit_code})
                </p>
                {sslResult.stdout && (
                  <pre className="mt-2 whitespace-pre-wrap">{sslResult.stdout}</pre>
                )}
                {sslResult.stderr && (
                  <pre className="mt-2 whitespace-pre-wrap text-rose-600">{sslResult.stderr}</pre>
                )}
              </div>
            )}

            <div className="mt-3 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={() => void handleApplySslCertificates(true)}
                disabled={sslApplying || loading}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:cursor-not-allowed disabled:opacity-70"
              >
                {sslApplying ? "Processando..." : "Simular (dry-run)"}
              </button>
              <button
                type="button"
                onClick={() => void handleApplySslCertificates(false)}
                disabled={sslApplying || loading}
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {sslApplying ? "Processando..." : "Aplicar certificados"}
              </button>
            </div>
          </article>

          <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            <label className="grid gap-1 text-sm text-muted">
              Dominio raiz
              <input
                value={rootDomainDraft}
                onChange={(event) => setRootDomainDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Subdominio Portal
              <input
                value={portalDomainDraft}
                onChange={(event) => setPortalDomainDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Subdominio Cliente
              <input
                value={clientDomainDraft}
                onChange={(event) => setClientDomainDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Subdominio Admin
              <input
                value={adminDomainDraft}
                onChange={(event) => setAdminDomainDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Subdominio API
              <input
                value={apiDomainDraft}
                onChange={(event) => setApiDomainDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
          </div>

          <div className="mt-4 rounded-xl border border-border bg-bg p-3 text-xs text-muted">
            <p>
              Host publico derivado: <strong className="text-text">{derivedPublicHost}</strong>
            </p>
            <p className="mt-1">
              Android: <code>{derivedAndroidDownloadUrl}</code>
            </p>
            <p className="mt-1">
              iOS: <code>{derivedIosDownloadUrl}</code>
            </p>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            <label className="grid gap-1 text-sm text-muted">
              URL Portal
              <input
                value={portalBaseUrlDraft}
                onChange={(event) => setPortalBaseUrlDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              URL Web Cliente
              <input
                value={clientBaseUrlDraft}
                onChange={(event) => setClientBaseUrlDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              URL Web Admin
              <input
                value={adminBaseUrlDraft}
                onChange={(event) => setAdminBaseUrlDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              URL Backend API
              <input
                value={backendBaseUrlDraft}
                onChange={(event) => setBackendBaseUrlDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              URL Proxy local
              <input
                value={proxyBaseUrlDraft}
                onChange={(event) => setProxyBaseUrlDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
          </div>

          <label className="mt-4 grid gap-1 text-sm text-muted">
            CORS allowlist (uma origem por linha)
            <textarea
              rows={5}
              value={corsAllowedOriginsDraft}
              onChange={(event) => setCorsAllowedOriginsDraft(event.currentTarget.value)}
              className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              placeholder={"https://10.211.55.21:3000\nhttps://10.211.55.21:3001\nhttps://10.211.55.21:3002"}
            />
          </label>

          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={() => void handleSaveConnectivity()}
              disabled={loading || saving || !config}
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {saving ? "Salvando..." : "Salvar conectividade"}
            </button>
          </div>
        </section>
      )}

      {shouldRenderSection("mobile-build", "server-admin") && (
        <section
          id="mobile-build"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-text">Build e release mobile</h2>
          <p className="mt-1 text-sm text-muted">
            Compile Android/iOS com a mesma configuracao, gere links de download e publique no portal.
          </p>

          <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <label className="grid gap-1 text-sm text-muted">
              Versao
              <input
                value={releaseVersionDraft}
                onChange={(event) => setReleaseVersionDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="1.0.0"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Build
              <input
                type="number"
                min={1}
                value={releaseBuildNumberDraft}
                onChange={(event) => setReleaseBuildNumberDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Versao minima
              <input
                value={releaseMinVersionDraft}
                onChange={(event) => setReleaseMinVersionDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="1.0.0"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Versao recomendada
              <input
                value={releaseRecommendedVersionDraft}
                onChange={(event) => setReleaseRecommendedVersionDraft(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="1.0.0"
              />
            </label>
          </div>

          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <label className="grid gap-1 text-sm text-muted">
              Politica de atualizacao
              <select
                value={releasePolicyDraft}
                onChange={(event) =>
                  setReleasePolicyDraft(event.currentTarget.value as "OPTIONAL" | "FORCE")
                }
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              >
                <option value="OPTIONAL">Opcional</option>
                <option value="FORCE">Obrigatoria</option>
              </select>
            </label>
            <label className="mt-6 inline-flex items-center gap-2 text-sm text-text">
              <input
                type="checkbox"
                checked={releaseCriticalDraft}
                onChange={(event) => setReleaseCriticalDraft(event.currentTarget.checked)}
                className="h-4 w-4 rounded border-border text-primary"
              />
              Atualizacao critica
            </label>
          </div>

          <label className="mt-3 grid gap-1 text-sm text-muted">
            Notas da release
            <textarea
              rows={4}
              value={releaseNotesDraft}
              onChange={(event) => setReleaseNotesDraft(event.currentTarget.value)}
              className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            />
          </label>

          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={() => void handleCompileRelease()}
              disabled={compilingRelease || !config}
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {compilingRelease ? "Compilando..." : "Compilar release"}
            </button>
          </div>

          <div className="mt-5 space-y-3">
            {mobileReleases.length === 0 && (
              <p className="text-sm text-muted">Nenhuma release mobile criada.</p>
            )}
            {mobileReleases.map((release) => (
              <article
                key={release.id}
                className="rounded-xl border border-border bg-bg p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-text">
                    {release.release_version}+{release.build_number}
                  </p>
                  <StatusPill tone={resolveReleaseStatusTone(release.status)}>
                    {formatReleaseStatusLabel(release.status)}
                  </StatusPill>
                </div>
                <p className="mt-2 text-xs text-muted">
                  Android: {release.android_download_url || "-"}
                </p>
                <p className="mt-1 text-xs text-muted">
                  iOS: {release.ios_download_url || "-"}
                </p>
                {release.release_notes && (
                  <p className="mt-2 text-xs text-muted">{release.release_notes}</p>
                )}
                <div className="mt-3 flex justify-end">
                  <button
                    type="button"
                    onClick={() => void handlePublishRelease(release.id)}
                    disabled={
                      publishingReleaseId === release.id ||
                      release.status === "PUBLISHED"
                    }
                    className="rounded-md border border-primary bg-bg px-3 py-1.5 text-xs font-semibold text-primary transition hover:bg-primary hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {publishingReleaseId === release.id
                      ? "Publicando..."
                      : release.status === "PUBLISHED"
                        ? "Publicado"
                        : "Publicar"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {shouldRenderSection("conteudo", "portal") && (
        <section id="conteudo" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Conteudo dinamico</h2>
              <p className="mt-1 text-sm text-muted">
                Edite textos, links e fotos das secoes por template e pagina.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handleRefreshSections()}
              disabled={refreshingSections}
              className="rounded-xl border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {refreshingSections ? "Atualizando..." : "Atualizar secoes"}
            </button>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <label className="grid gap-1 text-sm text-muted">
              Template
              <select
                value={contentTemplateId}
                onChange={(event) => setContentTemplateId(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              >
                {contentTemplateOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-1 text-sm text-muted">
              Pagina
              <select
                value={contentPageFilter}
                onChange={(event) => setContentPageFilter(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              >
                {pageOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-1 text-sm text-muted">
              Secao
              <select
                value={selectedSectionId}
                onChange={(event) => setSelectedSectionId(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                disabled={filteredSections.length === 0}
              >
                {filteredSections.length === 0 && (
                  <option value="">Nenhuma secao encontrada</option>
                )}
                {filteredSections.map((section) => (
                  <option key={section.id} value={section.id}>
                    {section.key} | {formatPortalPageLabel(section.page)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {selectedSection && (
            <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_320px]">
              <div className="rounded-xl border border-border bg-bg p-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="grid gap-1 text-sm text-muted">
                    Titulo da secao
                    <input
                      value={sectionTitleDraft}
                      onChange={(event) => setSectionTitleDraft(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Ordenacao (sort_order)
                    <input
                      type="number"
                      min={0}
                      value={sectionSortOrderDraft}
                      onChange={(event) => setSectionSortOrderDraft(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    />
                  </label>
                </div>

                <label className="mt-3 inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={sectionEnabledDraft}
                    onChange={(event) => setSectionEnabledDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Secao habilitada
                </label>

                <label className="mt-3 grid gap-1 text-sm text-muted">
                  body_json (JSON dinamico)
                  <textarea
                    rows={18}
                    value={sectionBodyJsonDraft}
                    onChange={(event) => setSectionBodyJsonDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 font-mono text-xs text-text"
                  />
                </label>

                <div className="mt-4 flex justify-end">
                  <button
                    type="button"
                    onClick={() => void handleSaveSection()}
                    disabled={savingSection}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {savingSection ? "Salvando..." : "Salvar secao"}
                  </button>
                </div>
              </div>

              <aside className="rounded-xl border border-border bg-bg p-4 text-xs text-muted">
                <p className="font-semibold text-text">Referencia rapida (LetsFit)</p>
                <p className="mt-2">
                  <strong className="text-text">hero:</strong> kicker, headline, subheadline,
                  background_image_url, cta_primary, cta_secondary.
                </p>
                <p className="mt-2">
                  <strong className="text-text">categories:</strong> items com name,
                  description e image_url.
                </p>
                <p className="mt-2">
                  <strong className="text-text">benefits:</strong> items como texto ou objeto com
                  text e icon.
                </p>
                <p className="mt-2">
                  <strong className="text-text">kit:</strong> kicker, headline, description,
                  cta_label, cta_href.
                </p>
                <p className="mt-2">
                  <strong className="text-text">how_to_heat:</strong> title, subheadline,
                  <code> cards[&#123;title,description,tone&#125;]</code>.
                </p>
                <p className="mt-2">
                  <strong className="text-text">faq:</strong>
                  <code> items[&#123;question,answer&#125;]</code>.
                </p>
              </aside>
            </div>
          )}
        </section>
      )}

      {shouldRenderSection("publicacao", "portal") && (
        <section id="publicacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Publicacao</h2>
          <p className="mt-1 text-sm text-muted">
            Publica a configuracao atual para uso do portal publico.
          </p>
          <div className="mt-4">
            <button
              type="button"
              onClick={() => void handlePublishConfig()}
              disabled={loading || publishing || !config}
              className="rounded-xl border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {publishing ? "Publicando..." : "Publicar configuracao"}
            </button>
          </div>
        </section>
      )}

      {successMessage && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}
    </>
  );
}
