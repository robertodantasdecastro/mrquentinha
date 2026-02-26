import { NextResponse } from "next/server";

import { fetchPortalAppDownloads } from "@/lib/mobileRelease";

type RouteContext = {
  params: Promise<{
    target: string;
  }>;
};

export async function GET(_request: Request, context: RouteContext) {
  const { target } = await context.params;
  const downloads = await fetchPortalAppDownloads();

  if (target === "android.apk") {
    return NextResponse.redirect(downloads.androidDownloadUrl);
  }

  if (target === "ios") {
    return NextResponse.redirect(downloads.iosDownloadUrl);
  }

  return NextResponse.json(
    { detail: "Destino de download invalido." },
    { status: 404 },
  );
}
