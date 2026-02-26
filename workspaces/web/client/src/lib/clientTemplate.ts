import "server-only";

import { cache } from "react";

import type { ClientTemplateType } from "@/types/template";

type ClientPublicConfigPayload = {
  active_template?: string;
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
  return value === "client-quentinhas" ? "client-quentinhas" : "client-classic";
}

const fetchClientActiveTemplateCached = cache(
  async (): Promise<ClientTemplateType> => {
    const apiBaseUrl = resolveApiBaseUrl();
    const endpoint = `${apiBaseUrl}/api/v1/portal/config/?channel=client&page=home`;

    try {
      const response = await fetch(endpoint, {
        cache: "no-store",
      });

      if (!response.ok) {
        return "client-classic";
      }

      const payload = (await response.json()) as ClientPublicConfigPayload;
      return normalizeTemplate(payload.active_template);
    } catch {
      return "client-classic";
    }
  },
);

export async function fetchClientActiveTemplate(): Promise<ClientTemplateType> {
  return fetchClientActiveTemplateCached();
}
