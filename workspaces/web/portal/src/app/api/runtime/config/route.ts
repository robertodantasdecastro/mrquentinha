import { NextRequest, NextResponse } from "next/server";

const DEFAULT_INTERNAL_BACKEND_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000";
const PRIVATE_IPV4_PATTERN = /^(10\.|127\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)/;

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/$/, "");
}

function resolveInternalBackendBaseUrl(): string {
  const candidates = [
    process.env.INTERNAL_API_BASE_URL,
    process.env.PORTAL_API_BASE_URL,
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

async function fetchApiBaseUrlFromBackend(): Promise<string> {
  const backendBaseUrl = resolveInternalBackendBaseUrl();
  const endpoint = `${backendBaseUrl}/api/v1/portal/config/?channel=portal&page=home`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 3500);

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      signal: controller.signal,
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

export async function GET(request: NextRequest) {
  const fromRequestHost = normalizeBaseUrl(resolveApiBaseUrlFromRequestHost(request));
  if (fromRequestHost) {
    return NextResponse.json(
      {
        api_base_url: fromRequestHost,
        source: "request_local_network",
        generated_at: new Date().toISOString(),
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      },
    );
  }

  const fromBackend = await fetchApiBaseUrlFromBackend();
  const fromEnv = normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL ?? "");
  const resolved = fromBackend || fromEnv || DEFAULT_PUBLIC_API_BASE_URL;

  return NextResponse.json(
    {
      api_base_url: resolved,
      source: fromBackend ? "backend_portal_config" : "env_fallback",
      generated_at: new Date().toISOString(),
    },
    {
      headers: {
        "Cache-Control": "no-store",
      },
    },
  );
}
