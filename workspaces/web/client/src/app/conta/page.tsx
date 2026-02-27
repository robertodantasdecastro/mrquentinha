"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { InlinePreloader } from "@/components/InlinePreloader";
import {
  ApiError,
  fetchAuthProvidersConfig,
  fetchMe,
  loginAccount,
  logoutAccount,
  registerAccount,
  resendEmailVerificationToken,
} from "@/lib/api";
import { hasStoredAuthSession } from "@/lib/storage";
import type { AuthUserProfile, PublicAuthProvidersConfig } from "@/types/api";

type AuthMode = "login" | "register";
type ViewState = "loading" | "anonymous" | "authenticated";

type LoginFormState = {
  username: string;
  password: string;
};

type RegisterFormState = {
  username: string;
  password: string;
  email: string;
  firstName: string;
  lastName: string;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada. Tente novamente.";
}

function formatRoles(user: AuthUserProfile): string {
  if (!Array.isArray(user.roles) || user.roles.length === 0) {
    return "Sem papeis definidos";
  }

  return user.roles.join(", ");
}

function sanitizeNextPath(value: string | null): string | null {
  if (!value) {
    return null;
  }

  if (!value.startsWith("/")) {
    return null;
  }

  if (value.startsWith("//")) {
    return null;
  }

  return value;
}

const INPUT_CLASS =
  "w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text outline-none transition focus:border-primary";

const DEFAULT_AUTH_PROVIDERS: PublicAuthProvidersConfig = {
  google: {
    enabled: false,
    configured: false,
    web_client_id: "",
    ios_client_id: "",
    android_client_id: "",
    auth_uri: "",
    token_uri: "",
    redirect_uri_web: "",
    redirect_uri_mobile: "",
    scope: "openid email profile",
  },
  apple: {
    enabled: false,
    configured: false,
    service_id: "",
    team_id: "",
    key_id: "",
    auth_uri: "",
    token_uri: "",
    redirect_uri_web: "",
    redirect_uri_mobile: "",
    scope: "name email",
  },
};

function buildOAuthState(provider: "google" | "apple"): string {
  const randomPart =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `mrq-${provider}-${randomPart}`;
}

function buildGoogleAuthorizeUrl(
  authConfig: PublicAuthProvidersConfig["google"],
): string | null {
  if (
    !authConfig.enabled ||
    !authConfig.configured ||
    !authConfig.auth_uri ||
    !authConfig.web_client_id ||
    !authConfig.redirect_uri_web
  ) {
    return null;
  }

  const params = new URLSearchParams({
    client_id: authConfig.web_client_id,
    redirect_uri: authConfig.redirect_uri_web,
    response_type: "code",
    scope: authConfig.scope || "openid email profile",
    access_type: "offline",
    include_granted_scopes: "true",
    prompt: "consent",
    state: buildOAuthState("google"),
  });

  return `${authConfig.auth_uri}?${params.toString()}`;
}

function buildAppleAuthorizeUrl(
  authConfig: PublicAuthProvidersConfig["apple"],
): string | null {
  if (
    !authConfig.enabled ||
    !authConfig.configured ||
    !authConfig.auth_uri ||
    !authConfig.service_id ||
    !authConfig.redirect_uri_web
  ) {
    return null;
  }

  const params = new URLSearchParams({
    client_id: authConfig.service_id,
    redirect_uri: authConfig.redirect_uri_web,
    response_type: "code",
    response_mode: "query",
    scope: authConfig.scope || "name email",
    state: buildOAuthState("apple"),
  });

  return `${authConfig.auth_uri}?${params.toString()}`;
}

export default function ContaPage() {
  const router = useRouter();
  const [nextPath, setNextPath] = useState<string | null>(null);

  const [viewState, setViewState] = useState<ViewState>("loading");
  const [mode, setMode] = useState<AuthMode>("login");
  const [busy, setBusy] = useState<boolean>(false);
  const [resendingVerification, setResendingVerification] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [authProviders, setAuthProviders] = useState<PublicAuthProvidersConfig>(
    DEFAULT_AUTH_PROVIDERS,
  );
  const [user, setUser] = useState<AuthUserProfile | null>(null);

  const [loginForm, setLoginForm] = useState<LoginFormState>({
    username: "",
    password: "",
  });

  const [registerForm, setRegisterForm] = useState<RegisterFormState>({
    username: "",
    password: "",
    email: "",
    firstName: "",
    lastName: "",
  });

  useEffect(() => {
    let mounted = true;

    async function bootstrapSession() {
      if (!hasStoredAuthSession()) {
        if (mounted) {
          setViewState("anonymous");
        }
        return;
      }

      try {
        const profile = await fetchMe();
        if (!mounted) {
          return;
        }

        setUser(profile);
        setViewState("authenticated");
      } catch {
        logoutAccount();
        if (mounted) {
          setUser(null);
          setViewState("anonymous");
        }
      }
    }

    void bootstrapSession();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadAuthProviders() {
      const payload = await fetchAuthProvidersConfig();
      if (!mounted) {
        return;
      }
      setAuthProviders(payload);
    }

    void loadAuthProviders();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const resolvedNextPath = sanitizeNextPath(
      new URLSearchParams(window.location.search).get("next"),
    );
    setNextPath(resolvedNextPath);
  }, []);

  function proceedAfterAuth() {
    if (nextPath) {
      router.push(nextPath);
      return;
    }

    router.push("/cardapio");
  }

  function handleSocialLogin(provider: "google" | "apple") {
    const url =
      provider === "google"
        ? buildGoogleAuthorizeUrl(authProviders.google)
        : buildAppleAuthorizeUrl(authProviders.apple);

    if (!url) {
      setErrorMessage(
        `Login com ${provider === "google" ? "Google" : "Apple"} ainda nao esta configurado no Portal CMS.`,
      );
      return;
    }

    window.location.href = url;
  }

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
      setMessage("Login realizado com sucesso.");
      setLoginForm({ username: "", password: "" });
      proceedAfterAuth();
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setBusy(true);
    setMessage("");
    setErrorMessage("");

    try {
      const profile = await registerAccount({
        username: registerForm.username.trim(),
        password: registerForm.password,
        email: registerForm.email.trim(),
        first_name: registerForm.firstName.trim(),
        last_name: registerForm.lastName.trim(),
      });

      setUser(profile);
      setViewState("authenticated");
      setMessage(
        "Cadastro realizado e sessao iniciada. Enviamos um e-mail para confirmacao da sua conta.",
      );
      setRegisterForm({
        username: "",
        password: "",
        email: "",
        firstName: "",
        lastName: "",
      });
      proceedAfterAuth();
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleResendVerification() {
    setResendingVerification(true);
    setMessage("");
    setErrorMessage("");

    try {
      const payload = await resendEmailVerificationToken();
      const updatedUser = await fetchMe();
      setUser(updatedUser);
      setMessage(
        payload.sent
          ? "Novo e-mail de confirmacao enviado."
          : payload.detail || "Nao foi possivel reenviar o e-mail agora.",
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setResendingVerification(false);
    }
  }

  function handleLogout() {
    logoutAccount();
    setUser(null);
    setViewState("anonymous");
    setErrorMessage("");
    setMessage("Sessao encerrada.");
  }

  return (
    <section className="space-y-4">
      <div className="rounded-2xl border border-border bg-bg/80 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
          Passo a passo
        </p>
        <div className="mt-2 grid gap-2 md:grid-cols-3">
          <div className="rounded-xl border border-border bg-surface/80 px-3 py-2 text-sm text-muted">
            1. Entre com sua conta
          </div>
          <div className="rounded-xl border border-border bg-surface/80 px-3 py-2 text-sm text-muted">
            2. Monte o pedido no cardapio
          </div>
          <div className="rounded-xl border border-border bg-surface/80 px-3 py-2 text-sm text-muted">
            3. Acompanhe e confirme em pedidos
          </div>
        </div>
      </div>

      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          Conta
        </p>
        <h1 className="mt-1 text-2xl font-bold text-text">Area do cliente</h1>

        {nextPath && (
          <p className="mt-2 text-sm text-muted">
            Apos autenticar, voce sera redirecionado para <strong>{nextPath}</strong>.
          </p>
        )}

        {viewState === "loading" && (
          <InlinePreloader
            message="Validando sessao..."
            className="mt-3 justify-start bg-surface/80"
          />
        )}

        {viewState === "authenticated" && user && (
          <div className="mt-4 space-y-4">
            <p className="text-sm text-muted">
              Sessao ativa para <strong className="text-text">{user.username}</strong>.
            </p>

            <div className="rounded-xl border border-border bg-bg p-4 text-sm text-muted">
              <p>
                <strong className="text-text">Email:</strong>{" "}
                {user.email || "nao informado"}
              </p>
              <p className="mt-1">
                <strong className="text-text">Validacao do e-mail:</strong>{" "}
                {user.email_verified ? "confirmado" : "pendente"}
              </p>
              <p className="mt-1">
                <strong className="text-text">Nome:</strong>{" "}
                {[user.first_name, user.last_name].filter(Boolean).join(" ") || "nao informado"}
              </p>
              <p className="mt-1">
                <strong className="text-text">Papeis:</strong> {formatRoles(user)}
              </p>
            </div>

            {!user.email_verified && (
              <div className="rounded-xl border border-amber-300/70 bg-amber-50 px-4 py-3 text-sm text-amber-700 dark:bg-amber-950/20 dark:text-amber-300">
                <p>Seu e-mail ainda nao foi confirmado.</p>
                <button
                  type="button"
                  onClick={() => void handleResendVerification()}
                  disabled={resendingVerification}
                  className="mt-2 rounded-md border border-amber-400/70 bg-transparent px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.08em] transition hover:bg-amber-100/70 disabled:cursor-not-allowed disabled:opacity-60 dark:hover:bg-amber-900/30"
                >
                  {resendingVerification ? "Reenviando..." : "Reenviar e-mail de confirmacao"}
                </button>
              </div>
            )}

            <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.08em]">
              <Link
                href="/cardapio"
                className="rounded-full border border-border bg-bg px-3 py-1.5 text-muted transition hover:border-primary hover:text-primary"
              >
                Ir para cardapio
              </Link>
              <Link
                href="/pedidos"
                className="rounded-full border border-border bg-bg px-3 py-1.5 text-muted transition hover:border-primary hover:text-primary"
              >
                Ir para pedidos
              </Link>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            >
              Sair
            </button>
          </div>
        )}

        {viewState === "anonymous" && (
          <div className="mt-4 space-y-4">
            <p className="text-sm text-muted">
              Entre com sua conta para visualizar apenas seus pedidos e finalizar novas compras.
            </p>

            <div className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-primary">
                Login social
              </p>
              <p className="mt-1 text-sm text-muted">
                Parametros de Google e Apple sao administrados no Portal CMS.
              </p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={() => handleSocialLogin("google")}
                  disabled={!authProviders.google.enabled}
                  className="rounded-md border border-border bg-white px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60 dark:bg-bg"
                >
                  Continuar com Google
                </button>
                <button
                  type="button"
                  onClick={() => handleSocialLogin("apple")}
                  disabled={!authProviders.apple.enabled}
                  className="rounded-md border border-border bg-text px-4 py-2 text-sm font-semibold text-bg transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Continuar com Apple
                </button>
              </div>
            </div>

            <div className="inline-flex rounded-full border border-border bg-bg p-1 text-xs font-semibold uppercase tracking-[0.08em]">
              <button
                type="button"
                onClick={() => setMode("login")}
                className={`rounded-full px-3 py-2 transition ${
                  mode === "login" ? "bg-primary text-white" : "text-muted hover:text-text"
                }`}
              >
                Login
              </button>
              <button
                type="button"
                onClick={() => setMode("register")}
                className={`rounded-full px-3 py-2 transition ${
                  mode === "register"
                    ? "bg-primary text-white"
                    : "text-muted hover:text-text"
                }`}
              >
                Cadastro
              </button>
            </div>

            {mode === "login" && (
              <form onSubmit={handleLogin} className="grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Usuario
                  <input
                    name="username"
                    required
                    autoComplete="username"
                    className={INPUT_CLASS}
                    value={loginForm.username}
                    onChange={(event) => {
                      const value = event.currentTarget.value;
                      setLoginForm((current) => ({
                        ...current,
                        username: value,
                      }));
                    }}
                  />
                </label>

                <label className="grid gap-1 text-sm text-muted">
                  Senha
                  <input
                    name="password"
                    required
                    type="password"
                    minLength={8}
                    autoComplete="current-password"
                    className={INPUT_CLASS}
                    value={loginForm.password}
                    onChange={(event) => {
                      const value = event.currentTarget.value;
                      setLoginForm((current) => ({
                        ...current,
                        password: value,
                      }));
                    }}
                  />
                </label>

                <button
                  type="submit"
                  disabled={busy}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-soft disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busy ? "Entrando..." : "Entrar"}
                </button>
              </form>
            )}

            {mode === "register" && (
              <form onSubmit={handleRegister} className="grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Usuario
                  <input
                    name="register_username"
                    required
                    autoComplete="username"
                    className={INPUT_CLASS}
                    value={registerForm.username}
                    onChange={(event) => {
                      const value = event.currentTarget.value;
                      setRegisterForm((current) => ({
                        ...current,
                        username: value,
                      }));
                    }}
                  />
                </label>

                <label className="grid gap-1 text-sm text-muted">
                  Email
                  <input
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    className={INPUT_CLASS}
                    value={registerForm.email}
                    onChange={(event) => {
                      const value = event.currentTarget.value;
                      setRegisterForm((current) => ({
                        ...current,
                        email: value,
                      }));
                    }}
                  />
                </label>

                <div className="grid gap-3 md:grid-cols-2">
                  <label className="grid gap-1 text-sm text-muted">
                    Nome
                    <input
                      name="first_name"
                      autoComplete="given-name"
                      className={INPUT_CLASS}
                      value={registerForm.firstName}
                      onChange={(event) => {
                        const value = event.currentTarget.value;
                        setRegisterForm((current) => ({
                          ...current,
                          firstName: value,
                        }));
                      }}
                    />
                  </label>

                  <label className="grid gap-1 text-sm text-muted">
                    Sobrenome
                    <input
                      name="last_name"
                      autoComplete="family-name"
                      className={INPUT_CLASS}
                      value={registerForm.lastName}
                      onChange={(event) => {
                        const value = event.currentTarget.value;
                        setRegisterForm((current) => ({
                          ...current,
                          lastName: value,
                        }));
                      }}
                    />
                  </label>
                </div>

                <label className="grid gap-1 text-sm text-muted">
                  Senha
                  <input
                    name="new_password"
                    required
                    type="password"
                    minLength={8}
                    autoComplete="new-password"
                    className={INPUT_CLASS}
                    value={registerForm.password}
                    onChange={(event) => {
                      const value = event.currentTarget.value;
                      setRegisterForm((current) => ({
                        ...current,
                        password: value,
                      }));
                    }}
                  />
                </label>

                <button
                  type="submit"
                  disabled={busy}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-soft disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busy ? "Cadastrando..." : "Criar conta"}
                </button>
              </form>
            )}
          </div>
        )}

        {message && (
          <p className="mt-4 rounded-md border border-emerald-300/70 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-300">
            {message}
          </p>
        )}

        {errorMessage && (
          <p className="mt-4 rounded-md border border-red-300/70 bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/20 dark:text-red-300">
            {errorMessage}
          </p>
        )}
      </section>
    </section>
  );
}
