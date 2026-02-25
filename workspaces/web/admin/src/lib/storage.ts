const AUTH_TOKENS_STORAGE_KEY = "mrq-admin-auth-tokens";

export type StoredAuthTokens = {
  access: string;
  refresh: string;
};

function hasBrowserStorage(): boolean {
  return typeof window !== "undefined";
}

export function persistAuthTokens(tokens: StoredAuthTokens): void {
  if (!hasBrowserStorage()) {
    return;
  }

  const normalizedAccess = tokens.access.trim();
  const normalizedRefresh = tokens.refresh.trim();

  if (!normalizedAccess || !normalizedRefresh) {
    return;
  }

  window.localStorage.setItem(
    AUTH_TOKENS_STORAGE_KEY,
    JSON.stringify({
      access: normalizedAccess,
      refresh: normalizedRefresh,
    }),
  );
}

export function getStoredAuthTokens(): StoredAuthTokens | null {
  if (!hasBrowserStorage()) {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_TOKENS_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<StoredAuthTokens>;
    if (typeof parsed.access !== "string" || typeof parsed.refresh !== "string") {
      return null;
    }

    const access = parsed.access.trim();
    const refresh = parsed.refresh.trim();

    if (!access || !refresh) {
      return null;
    }

    return { access, refresh };
  } catch {
    return null;
  }
}

export function getStoredAccessToken(): string | null {
  return getStoredAuthTokens()?.access ?? null;
}

export function hasStoredAuthSession(): boolean {
  return getStoredAuthTokens() !== null;
}

export function clearAuthTokens(): void {
  if (!hasBrowserStorage()) {
    return;
  }

  window.localStorage.removeItem(AUTH_TOKENS_STORAGE_KEY);
}
