import "server-only";

import { cache } from "react";

type MobileReleaseLatestPayload = {
  release_version?: string;
  published_at?: string | null;
  android_download_url?: string;
  ios_download_url?: string;
};

export type PortalAppDownloadsData = {
  appUrl: string;
  androidDownloadUrl: string;
  iosDownloadUrl: string;
  releaseVersion: string;
  publishedAt: string | null;
};

function resolveApiBaseUrl(): string {
  const envBaseUrl =
    process.env.PORTAL_API_BASE_URL?.trim() ||
    process.env.INTERNAL_API_BASE_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ||
    "http://127.0.0.1:8000";

  return envBaseUrl.replace(/\/$/, "");
}

function buildPortalAppUrlFromApiBase(apiBaseUrl: string): string {
  try {
    const parsed = new URL(apiBaseUrl);
    const scheme = parsed.protocol.replace(":", "") || "https";
    const host = parsed.hostname || "10.211.55.21";
    return `${scheme}://${host}:3000/app`;
  } catch {
    return "https://10.211.55.21:3000/app";
  }
}

const fetchPortalAppDownloadsCached = cache(async (): Promise<PortalAppDownloadsData> => {
  const apiBaseUrl = resolveApiBaseUrl();
  const endpoint = `${apiBaseUrl}/api/v1/portal/mobile/releases/latest/`;
  const fallbackAppUrl = buildPortalAppUrlFromApiBase(apiBaseUrl);

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
    });
    if (!response.ok) {
      return {
        appUrl: fallbackAppUrl,
        androidDownloadUrl: `${fallbackAppUrl}/downloads/android.apk`,
        iosDownloadUrl: `${fallbackAppUrl}/downloads/ios`,
        releaseVersion: "",
        publishedAt: null,
      };
    }

    const payload = (await response.json()) as MobileReleaseLatestPayload;
    const androidDownloadUrl =
      payload.android_download_url || `${fallbackAppUrl}/downloads/android.apk`;
    const iosDownloadUrl = payload.ios_download_url || `${fallbackAppUrl}/downloads/ios`;

    return {
      appUrl: fallbackAppUrl,
      androidDownloadUrl,
      iosDownloadUrl,
      releaseVersion: payload.release_version || "",
      publishedAt: payload.published_at || null,
    };
  } catch {
    return {
      appUrl: fallbackAppUrl,
      androidDownloadUrl: `${fallbackAppUrl}/downloads/android.apk`,
      iosDownloadUrl: `${fallbackAppUrl}/downloads/ios`,
      releaseVersion: "",
      publishedAt: null,
    };
  }
});

export async function fetchPortalAppDownloads(): Promise<PortalAppDownloadsData> {
  return fetchPortalAppDownloadsCached();
}
