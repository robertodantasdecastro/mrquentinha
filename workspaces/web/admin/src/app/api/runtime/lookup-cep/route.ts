import { NextRequest, NextResponse } from "next/server";

const DEFAULT_INTERNAL_BACKEND_BASE_URL = "http://127.0.0.1:8000";
const PRIVATE_IPV4_PATTERN = /^(10\.|127\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)/;

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/$/, "");
}

function digitsOnly(value: string): string {
  return value.replace(/\D/g, "");
}

function resolveInternalBackendBaseUrl(): string {
  const candidates = [
    process.env.INTERNAL_API_BASE_URL,
    process.env.ADMIN_API_BASE_URL,
    process.env.NEXT_PUBLIC_API_BASE_URL,
    DEFAULT_INTERNAL_BACKEND_BASE_URL,
  ];

  for (const candidate of candidates) {
    const normalized = normalizeBaseUrl(candidate ?? "");
    if (normalized) {
      return normalized;
    }
  }

  return DEFAULT_INTERNAL_BACKEND_BASE_URL;
}

function extractRequestHostname(request: NextRequest): string {
  const forwardedHost = request.headers.get("x-forwarded-host");
  const hostHeader = request.headers.get("host");
  const rawHost = (forwardedHost || hostHeader || "").split(",")[0]?.trim() ?? "";

  if (rawHost) {
    if (rawHost.startsWith("[")) {
      const ipv6Match = rawHost.match(/^\[([^\]]+)\]/);
      if (ipv6Match?.[1]) {
        return ipv6Match[1].toLowerCase();
      }
    }
    return rawHost.replace(/:\d+$/, "").toLowerCase();
  }

  try {
    return new URL(request.url).hostname.toLowerCase();
  } catch {
    return "";
  }
}

function isLocalNetworkHostname(hostname: string): boolean {
  if (!hostname) {
    return false;
  }

  return (
    hostname === "localhost" ||
    hostname === "0.0.0.0" ||
    hostname.endsWith(".local") ||
    PRIVATE_IPV4_PATTERN.test(hostname)
  );
}

function resolveApiBaseUrlFromRequestHost(request: NextRequest): string {
  const hostname = extractRequestHostname(request);
  if (!isLocalNetworkHostname(hostname)) {
    return "";
  }

  return `http://${hostname}:8000`;
}

function resolveSameOriginApiProxyBaseUrl(request: NextRequest): string {
  const hostname = extractRequestHostname(request);
  if (!hostname || isLocalNetworkHostname(hostname)) {
    return "";
  }

  const forwardedProto = request.headers.get("x-forwarded-proto");
  const protocol = (forwardedProto || new URL(request.url).protocol).replace(/:$/, "");
  if (protocol !== "http" && protocol !== "https") {
    return "";
  }

  return `${protocol}://${hostname}`;
}

async function fetchApiBaseUrlFromBackend(): Promise<string> {
  const backendBaseUrl = resolveInternalBackendBaseUrl();
  const endpoint = `${backendBaseUrl}/api/v1/portal/config/?channel=admin&page=home`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 3500);

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      signal: controller.signal,
      headers: {
        "X-Forwarded-Proto": "https",
      },
    });
    if (!response.ok) {
      return "";
    }

    const payload = (await response.json()) as { api_base_url?: unknown };
    return normalizeBaseUrl(String(payload.api_base_url ?? ""));
  } catch {
    return "";
  } finally {
    clearTimeout(timeoutId);
  }
}

async function resolveApiBaseUrl(request: NextRequest): Promise<string> {
  const fromRequestHost = normalizeBaseUrl(resolveApiBaseUrlFromRequestHost(request));
  if (fromRequestHost) {
    return fromRequestHost;
  }

  const fromSameOriginProxy = normalizeBaseUrl(resolveSameOriginApiProxyBaseUrl(request));
  if (fromSameOriginProxy) {
    return fromSameOriginProxy;
  }

  const fromBackend = await fetchApiBaseUrlFromBackend();
  if (fromBackend) {
    return fromBackend;
  }

  return (
    normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL ?? "") ||
    DEFAULT_INTERNAL_BACKEND_BASE_URL
  );
}

export async function GET(request: NextRequest) {
  const cepRaw = request.nextUrl.searchParams.get("cep") ?? "";
  const cep = digitsOnly(cepRaw);
  if (cep.length !== 8) {
    return NextResponse.json(
      {
        detail: "CEP invalido. Informe 8 digitos.",
      },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }

  const apiBaseUrl = await resolveApiBaseUrl(request);
  const endpoint = `${apiBaseUrl}/api/v1/accounts/lookup-cep/?cep=${encodeURIComponent(cep)}`;

  try {
    const response = await fetch(endpoint, {
      method: "GET",
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    const text = await response.text();
    const body = text ? JSON.parse(text) : {};
    return NextResponse.json(body, {
      status: response.status,
      headers: {
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return NextResponse.json(
      {
        detail: "Falha ao consultar CEP no backend.",
      },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
