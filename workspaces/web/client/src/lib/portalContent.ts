import type { ClientPortalSectionData } from "@/types/api";

type JsonRecord = Record<string, unknown>;

export function asObject(value: unknown): JsonRecord {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as JsonRecord;
  }
  return {};
}

export function asString(value: unknown, fallback: string = ""): string {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

export function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function resolveSectionByKey(
  sections: ClientPortalSectionData[] | undefined,
  key: string,
): ClientPortalSectionData | null {
  if (!sections) {
    return null;
  }
  const section = sections.find((item) => item.key === key);
  return section ?? null;
}
