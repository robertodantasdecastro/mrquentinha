import "server-only";

import type { ClientTemplateType } from "@/types/template";
import type { ClientPortalSectionData } from "@/types/api";

type ClientPublicConfigPayload = {
  active_template?: string;
  page?: string;
  sections?: ClientPortalSectionData[];
};

function resolveApiBaseUrl(): string {
  const envBaseUrl =
    process.env.CLIENT_API_BASE_URL?.trim() ||
    process.env.INTERNAL_API_BASE_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ||
    "http://127.0.0.1:8000";

  return envBaseUrl.replace(/\/$/, "");
}

function normalizeTemplate(value: unknown): ClientTemplateType {
  if (value === "client-quentinhas") {
    return "client-quentinhas";
  }

  if (value === "client-vitrine-fit") {
    return "client-vitrine-fit";
  }

  if (value === "client-editorial-jp") {
    return "client-editorial-jp";
  }

  return "client-classic";
}

export async function fetchClientActiveTemplate(): Promise<ClientTemplateType> {
  const config = await fetchClientConfig("home");
  return normalizeTemplate(config.active_template);
}

export async function fetchClientConfig(
  page: string = "home",
): Promise<ClientPublicConfigPayload> {
  const apiBaseUrl = resolveApiBaseUrl();
  const endpoint = `${apiBaseUrl}/api/v1/portal/config/?channel=client&page=${encodeURIComponent(page)}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        "X-Forwarded-Proto": "https",
      },
    });

    if (!response.ok) {
      return {
        active_template: "client-classic",
        page,
        sections: [],
      };
    }

    const payload = (await response.json()) as ClientPublicConfigPayload;
    return {
      ...payload,
      active_template: normalizeTemplate(payload.active_template),
      page,
      sections: Array.isArray(payload.sections) ? payload.sections : [],
    };
  } catch {
    return {
      active_template: "client-classic",
      page,
      sections: [],
    };
  }
}
