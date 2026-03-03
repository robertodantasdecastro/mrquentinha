const PRIVATE_IPV4_PATTERN = /^(10\.|127\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)/;

export function extractHostname(hostHeader: string): string {
  const rawHost = hostHeader.split(",")[0]?.trim() ?? "";
  if (!rawHost) {
    return "";
  }

  if (rawHost.startsWith("[")) {
    const ipv6Match = rawHost.match(/^\[([^\]]+)\]/);
    if (ipv6Match?.[1]) {
      return ipv6Match[1].toLowerCase();
    }
  }

  return rawHost.replace(/:\d+$/, "").toLowerCase();
}

export function isLocalNetworkHostname(hostname: string): boolean {
  return (
    hostname === "localhost" ||
    hostname === "0.0.0.0" ||
    hostname.endsWith(".local") ||
    PRIVATE_IPV4_PATTERN.test(hostname)
  );
}

export function resolveFrontendUrl(
  hostname: string,
  port: number,
  fallback: string,
  protocol: "http" | "https" = "http",
): string {
  if (!isLocalNetworkHostname(hostname)) {
    return fallback;
  }
  return `${protocol}://${hostname}:${port}`;
}
