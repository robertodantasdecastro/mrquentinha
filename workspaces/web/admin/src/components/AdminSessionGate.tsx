"use client";

import { type FormEvent, createContext, useContext, useEffect, useState } from "react";

import { ApiError, fetchHealth, fetchMe, loginAccount, logoutAccount } from "@/lib/api";
import { hasStoredAuthSession } from "@/lib/storage";
import type { AuthUserProfile } from "@/types/api";

const SessionContext = createContext<SessionContextValue | null>(null);

type SessionContextValue = {
  user: AuthUserProfile;
  healthStatus: string;
  onLogout: () => void;
};

type ViewState = "loading" | "anonymous" | "authenticated";

type LoginFormState = {
  username: string;
  password: string;
};

const INPUT_CLASS =
  "w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text outline-none transition focus:border-primary";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada. Tente novamente.";
}

export function useAdminSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useAdminSession must be used inside AdminSessionGate");
  }
  return context;
}

export function AdminSessionGate({ children }: { children: React.ReactNode }) {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [loginForm, setLoginForm] = useState<LoginFormState>({ username: "", password: "" });
  const [busy, setBusy] = useState(false);
  const [user, setUser] = useState<AuthUserProfile | null>(null);
  const [healthStatus, setHealthStatus] = useState("indisponivel");
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      try {
        const health = await fetchHealth();
        if (mounted) {
          setHealthStatus(health.status || health.detail || "online");
        }
      } catch {
        if (mounted) {
          setHealthStatus("indisponivel");
        }
      }

      if (!hasStoredAuthSession()) {
        if (mounted) {
          setViewState("anonymous");
        }
        return;
      }

      try {
        const profile = await fetchMe();
        if (mounted) {
          setUser(profile);
          setViewState("authenticated");
        }
      } catch {
        logoutAccount();
        if (mounted) {
          setViewState("anonymous");
          setUser(null);
        }
      }
    }

    bootstrap();

    return () => {
      mounted = false;
    };
  }, []);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setErrorMessage("");

    try {
      await loginAccount(loginForm.username.trim(), loginForm.password);
      const profile = await fetchMe();
      setUser(profile);
      setViewState("authenticated");
      setLoginForm({ username: "", password: "" });
      setMessage("Sessao de gestao iniciada com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  function handleLogout() {
    logoutAccount();
    setUser(null);
    setViewState("anonymous");
    setMessage("Sessao encerrada.");
    setErrorMessage("");
  }

  if (viewState === "loading") {
    return (
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <p className="text-sm text-muted">Validando sessao do Admin...</p>
      </section>
    );
  }

  if (viewState === "anonymous") {
    return (
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm md:max-w-xl">
        <h2 className="text-xl font-semibold text-text">Login de gestao</h2>
        <p className="mt-2 text-sm text-muted">Use uma conta com papel administrativo.</p>
        {healthStatus === "indisponivel" && (
          <p className="mt-3 rounded-md border border-rose-400/40 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
            API indisponivel no navegador. Verifique backend ativo na porta 8000 e CORS liberado para esta origem.
          </p>
        )}
        <form onSubmit={handleLogin} className="mt-4 grid gap-3">
          <label className="grid gap-1 text-sm text-muted">
            Usuario
            <input
              required
              autoComplete="username"
              className={INPUT_CLASS}
              value={loginForm.username}
              onChange={(event) => {
                const username = event.currentTarget.value;
                setLoginForm((current) => ({ ...current, username }));
              }}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Senha
            <input
              required
              type="password"
              autoComplete="current-password"
              className={INPUT_CLASS}
              value={loginForm.password}
              onChange={(event) => {
                const password = event.currentTarget.value;
                setLoginForm((current) => ({ ...current, password }));
              }}
            />
          </label>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70">
            {busy ? "Entrando..." : "Entrar"}
          </button>
        </form>
        {(message || errorMessage) && (
          <div role="alert" className="mt-3 rounded-md border border-border bg-bg px-4 py-3 text-sm">
            {message && <p className="text-primary">{message}</p>}
            {errorMessage && <p className="text-rose-600">{errorMessage}</p>}
          </div>
        )}
      </section>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <SessionContext.Provider value={{ user, healthStatus, onLogout: handleLogout }}>
      <div className="space-y-6">
        <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-text">Sessao ativa</h2>
              <p className="mt-1 text-sm text-muted">
                Usuario <strong className="text-text">{user.username}</strong> com papeis: {user.roles?.join(", ") || "Sem papeis"}.
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary">
              Sair
            </button>
          </div>
        </section>

        {children}

        {(message || errorMessage) && (
          <section className="rounded-xl border border-border bg-bg px-4 py-3 text-sm">
            {message && <p className="text-primary">{message}</p>}
            {errorMessage && <p className="text-rose-600">{errorMessage}</p>}
          </section>
        )}
      </div>
    </SessionContext.Provider>
  );
}
