"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import {
  ApiError,
  createMobileReleaseAdmin,
  ensurePortalConfigAdmin,
  listMobileReleasesAdmin,
  listPortalSectionsAdmin,
  publishMobileReleaseAdmin,
  publishPortalConfigAdmin,
  testPortalPaymentProviderAdmin,
  updatePortalConfigAdmin,
  updatePortalSectionAdmin,
} from "@/lib/api";
import type {
  MobileReleaseData,
  PortalAsaasConfig,
  PortalAppleAuthConfig,
  PortalAuthProvidersConfig,
  PortalConfigData,
  PortalEfiConfig,
  PortalGoogleAuthConfig,
  PortalMercadoPagoConfig,
  PortalPaymentProviderRouting,
  PortalPaymentProvidersConfig,
  PortalPaymentReceiverConfig,
  PortalSectionData,
  PortalTemplateData,
} from "@/types/api";

export const PORTAL_BASE_PATH = "/modulos/portal";

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
  { key: "conectividade", label: "Conectividade", href: `${PORTAL_BASE_PATH}/conectividade#conectividade` },
  { key: "mobile-build", label: "Build mobile", href: `${PORTAL_BASE_PATH}/mobile-build#mobile-build` },
  { key: "conteudo", label: "Conteudo dinamico", href: `${PORTAL_BASE_PATH}/conteudo#conteudo` },
  { key: "publicacao", label: "Publicacao", href: `${PORTAL_BASE_PATH}/publicacao#publicacao` },
];

export type PortalSectionKey =
  | "all"
  | "template"
  | "autenticacao"
  | "pagamentos"
  | "conectividade"
  | "mobile-build"
  | "conteudo"
  | "publicacao";

type PortalSectionsProps = {
  activeSection?: PortalSectionKey;
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
  "client-classic": "Cliente Classico",
  "client-quentinhas": "Cliente Quentinhas",
  "client-vitrine-fit": "Cliente Vitrine Fit",
};

const PORTAL_PAGE_LABELS: Record<string, string> = {
  home: "Home",
  cardapio: "Cardapio",
  sobre: "Sobre",
  "como-funciona": "Como funciona",
  contato: "Contato",
};

const PAYMENT_PROVIDER_OPTIONS = [
  { value: "mock", label: "Mock (desenvolvimento)" },
  { value: "mercadopago", label: "Mercado Pago" },
  { value: "efi", label: "Efi" },
  { value: "asaas", label: "Asaas" },
];

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

export function PortalSections({ activeSection = "all" }: PortalSectionsProps) {
  const [config, setConfig] = useState<PortalConfigData | null>(null);
  const [sections, setSections] = useState<PortalSectionData[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [selectedClientTemplateId, setSelectedClientTemplateId] = useState("");
  const [contentTemplateId, setContentTemplateId] = useState("");
  const [contentPageFilter, setContentPageFilter] = useState("all");
  const [selectedSectionId, setSelectedSectionId] = useState("");
  const [sectionTitleDraft, setSectionTitleDraft] = useState("");
  const [sectionSortOrderDraft, setSectionSortOrderDraft] = useState("0");
  const [sectionEnabledDraft, setSectionEnabledDraft] = useState(true);
  const [sectionBodyJsonDraft, setSectionBodyJsonDraft] = useState("{}");
  const [localHostnameDraft, setLocalHostnameDraft] = useState("mrquentinha");
  const [localNetworkIpDraft, setLocalNetworkIpDraft] = useState("");
  const [rootDomainDraft, setRootDomainDraft] = useState("mrquentinha.local");
  const [portalDomainDraft, setPortalDomainDraft] = useState("www.mrquentinha.local");
  const [clientDomainDraft, setClientDomainDraft] = useState("app.mrquentinha.local");
  const [adminDomainDraft, setAdminDomainDraft] = useState("admin.mrquentinha.local");
  const [apiDomainDraft, setApiDomainDraft] = useState("api.mrquentinha.local");
  const [apiBaseUrlDraft, setApiBaseUrlDraft] = useState("https://10.211.55.21:8000");
  const [portalBaseUrlDraft, setPortalBaseUrlDraft] = useState("https://10.211.55.21:3000");
  const [clientBaseUrlDraft, setClientBaseUrlDraft] = useState("https://10.211.55.21:3001");
  const [adminBaseUrlDraft, setAdminBaseUrlDraft] = useState("https://10.211.55.21:3002");
  const [backendBaseUrlDraft, setBackendBaseUrlDraft] = useState("https://10.211.55.21:8000");
  const [proxyBaseUrlDraft, setProxyBaseUrlDraft] = useState("https://10.211.55.21:8088");
  const [corsAllowedOriginsDraft, setCorsAllowedOriginsDraft] = useState("");
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

  const contentTemplateOptions = useMemo(() => {
    const optionMap = new Map<string, TemplateOption>();
    for (const option of templateOptions) {
      optionMap.set(option.id, option);
    }
    for (const option of clientTemplateOptions) {
      optionMap.set(option.id, option);
    }
    return Array.from(optionMap.values());
  }, [clientTemplateOptions, templateOptions]);

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

  const derivedPublicHost = useMemo(
    () => resolveHostFromApiBaseUrl(apiBaseUrlDraft),
    [apiBaseUrlDraft],
  );
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
        const defaultTemplateId = normalizedTemplateOptions.some(
          (option) => option.id === configPayload.active_template,
        )
          ? configPayload.active_template
          : (normalizedTemplateOptions[0]?.id ??
            normalizedClientTemplateOptions[0]?.id ??
            "");

        setConfig(configPayload);
        setSections(sectionsPayload);
        setMobileReleases(releasesPayload);
        setSelectedTemplateId(configPayload.active_template);
        setSelectedClientTemplateId(configPayload.client_active_template);
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
        setPortalBaseUrlDraft(configPayload.portal_base_url || "https://10.211.55.21:3000");
        setClientBaseUrlDraft(configPayload.client_base_url || "https://10.211.55.21:3001");
        setAdminBaseUrlDraft(configPayload.admin_base_url || "https://10.211.55.21:3002");
        setBackendBaseUrlDraft(configPayload.backend_base_url || "https://10.211.55.21:8000");
        setProxyBaseUrlDraft(configPayload.proxy_base_url || "https://10.211.55.21:8088");
        setCorsAllowedOriginsDraft(stringifyOrigins(configPayload.cors_allowed_origins));
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

  const showAll = activeSection === "all";

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
      setSuccessMessage("Conectividade entre aplicacoes atualizada com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
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
        {loading && <p className="mt-3 text-sm text-muted">Carregando configuracoes do portal...</p>}
        {!loading && config && (
          <div className="mt-4 grid gap-3 md:grid-cols-5">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Template ativo</p>
              <p className="mt-1 text-base font-semibold text-text">{activeTemplateLabel}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Template cliente</p>
              <p className="mt-1 text-base font-semibold text-text">{activeClientTemplateLabel}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Templates disponiveis</p>
              <p className="mt-1 text-base font-semibold text-text">
                {templateOptions.length + clientTemplateOptions.length}
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
          </div>
        )}
      </section>

      {(showAll || activeSection === "template") && (
        <section id="template" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Templates ativos por canal</h2>
          <p className="mt-1 text-sm text-muted">
            Escolha templates do Portal e do Web Cliente com publicacao unificada.
          </p>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
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
          </div>
        </section>
      )}

      {(showAll || activeSection === "autenticacao") && (
        <section
          id="autenticacao"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-text">Autenticacao social</h2>
          <p className="mt-1 text-sm text-muted">
            Centralize no Admin os parametros de OAuth para Web Cliente e App Mobile.
            Campos de cada box pertencem ao respectivo provider.
          </p>

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

      {(showAll || activeSection === "pagamentos") && (
        <section
          id="pagamentos"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-text">Pagamentos e gateways</h2>
          <p className="mt-1 text-sm text-muted">
            Configure Mercado Pago, Efi e Asaas, defina roteamento por metodo e valide
            conexao com botao de teste.
          </p>

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

      {(showAll || activeSection === "conectividade") && (
        <section
          id="conectividade"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-text">Conectividade e dominios</h2>
          <p className="mt-1 text-sm text-muted">
            Configure host local, dominios/subdominios e URLs de cada aplicacao para
            desenvolvimento em rede local.
          </p>

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

      {(showAll || activeSection === "mobile-build") && (
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

      {(showAll || activeSection === "conteudo") && (
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

      {(showAll || activeSection === "publicacao") && (
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
