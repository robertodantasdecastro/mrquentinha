import "server-only";

import { cache } from "react";

export type TemplateType = "classic" | "letsfit-clean";

export type PortalSectionPayload = {
  id: number;
  template_id: string;
  page: string;
  key: string;
  title: string;
  body_json: unknown;
  sort_order: number;
  updated_at: string;
};

export type PortalConfigPayload = {
  active_template: string;
  available_templates?: unknown[];
  site_name?: string;
  site_title?: string;
  meta_description?: string;
  primary_color?: string;
  secondary_color?: string;
  dark_bg_color?: string;
  android_download_url?: string;
  ios_download_url?: string;
  qr_target_url?: string;
  is_published?: boolean;
  updated_at?: string;
  page?: string;
  sections?: PortalSectionPayload[];
};

function resolveApiBaseUrl(): string {
  const envBaseUrl =
    process.env.PORTAL_API_BASE_URL?.trim() ||
    process.env.INTERNAL_API_BASE_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ||
    "http://127.0.0.1:8000";

  return envBaseUrl.replace(/\/$/, "");
}

function normalizeTemplate(value: unknown): TemplateType {
  return value === "letsfit-clean" ? "letsfit-clean" : "classic";
}

function normalizePortalConfigPayload(payload: unknown): PortalConfigPayload {
  if (!payload || typeof payload !== "object") {
    return {
      active_template: "classic",
      sections: [],
    };
  }

  const typedPayload = payload as PortalConfigPayload;
  return {
    ...typedPayload,
    active_template: normalizeTemplate(typedPayload.active_template),
    sections: Array.isArray(typedPayload.sections) ? typedPayload.sections : [],
  };
}

const fetchPortalConfigCached = cache(
  async (page: string): Promise<PortalConfigPayload> => {
    const apiBaseUrl = resolveApiBaseUrl();
    const endpoint = `${apiBaseUrl}/api/v1/portal/config/?page=${encodeURIComponent(page)}`;

    try {
      const response = await fetch(endpoint, {
        cache: "no-store",
      });

      if (!response.ok) {
        return {
          active_template: "classic",
          sections: [],
        };
      }

      const payload = (await response.json()) as unknown;
      return normalizePortalConfigPayload(payload);
    } catch {
      return {
        active_template: "classic",
        sections: [],
      };
    }
  },
);

export async function fetchPortalConfig(
  page: string = "home",
): Promise<PortalConfigPayload> {
  return fetchPortalConfigCached(page);
}

export async function fetchPortalActiveTemplate(
  page: string = "home",
): Promise<TemplateType> {
  const config = await fetchPortalConfig(page);
  return normalizeTemplate(config.active_template);
}

export function resolveSectionByKey(
  sections: PortalSectionPayload[],
  key: string,
): PortalSectionPayload | null {
  const matched = sections.find((section) => section.key === key);
  return matched ?? null;
}
