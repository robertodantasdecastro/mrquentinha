import "server-only";

import { cache } from "react";

import type { AdminTemplateType } from "@/types/template";

type AdminPublicConfigPayload = {
  active_template?: string;
  admin_active_template?: string;
};

function resolveApiBaseUrl(): string {
  const envBaseUrl =
    process.env.ADMIN_API_BASE_URL?.trim() ||
    process.env.INTERNAL_API_BASE_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ||
    "http://127.0.0.1:8000";

  return envBaseUrl.replace(/\/$/, "");
}

function normalizeTemplate(value: unknown): AdminTemplateType {
  if (value === "admin-admindek") {
    return "admin-admindek";
  }

  if (value === "admin-adminkit") {
    return "admin-adminkit";
  }

  return "admin-classic";
}

const fetchAdminActiveTemplateCached = cache(async (): Promise<AdminTemplateType> => {
  const apiBaseUrl = resolveApiBaseUrl();
  const endpoint = `${apiBaseUrl}/api/v1/portal/config/?channel=admin&page=home`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
    });

    if (!response.ok) {
      return "admin-classic";
    }

    const payload = (await response.json()) as AdminPublicConfigPayload;
    return normalizeTemplate(payload.admin_active_template ?? payload.active_template);
  } catch {
    return "admin-classic";
  }
});

export async function fetchAdminActiveTemplate(): Promise<AdminTemplateType> {
  return fetchAdminActiveTemplateCached();
}
