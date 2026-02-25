"use client";

import { type FormEvent, useEffect, useState } from "react";

import {
  ApiError,
  fetchHealth,
  fetchMe,
  loginAccount,
  logoutAccount,
} from "@/lib/api";
import { hasStoredAuthSession } from "@/lib/storage";
import type { AuthUserProfile } from "@/types/api";
import { FinanceOpsPanel } from "@/components/modules/FinanceOpsPanel";
import { InventoryOpsPanel } from "@/components/modules/InventoryOpsPanel";
import { MenuOpsPanel } from "@/components/modules/MenuOpsPanel";
import { OrdersOpsPanel } from "@/components/modules/OrdersOpsPanel";
import { ProcurementOpsPanel } from "@/components/modules/ProcurementOpsPanel";
import { ProductionOpsPanel } from "@/components/modules/ProductionOpsPanel";

type ViewState = "loading" | "anonymous" | "authenticated";

type LoginFormState = {
  username: string;
  password: string;
};

const MODULES = [
  {
    title: "Pedidos",
    description: "Fila do dia, mudanca de status e atendimento operacional.",
    stage: "T9.0.2",
    status: "ativo",
  },
  {
    title: "Financeiro",
    description: "KPIs, caixa nao conciliado e visao de risco diario.",
    stage: "T9.0.2",
    status: "ativo",
  },
  {
    title: "Estoque",
    description: "Saldo por ingrediente, alertas e registro de movimentos.",
    stage: "T9.0.2",
    status: "ativo",
  },
  {
    title: "Cardapio",
    description: "Menus e pratos com baseline de planejamento operacional.",
    stage: "T9.0.3",
    status: "ativo (baseline)",
  },
  {
    title: "Compras",
    description: "Requisicoes e compras recentes com visao de abastecimento.",
    stage: "T9.0.3",
    status: "ativo (baseline)",
  },
  {
    title: "Producao",
    description: "Lotes por data com acompanhamento de planejado x produzido.",
    stage: "T9.0.3",
    status: "ativo (baseline)",
  },
  {
    title: "Portal CMS",
    description: "Configuracao de secoes/template do portal institucional.",
    stage: "T6.3.2",
    status: "planejado",
  },
  {
    title: "Usuarios/RBAC",
    description: "Gestao de papeis, permissoes e trilha de auditoria basica.",
    stage: "T9.1.1",
    status: "planejado",
  },
];

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

function formatRoles(user: AuthUserProfile): string {
  if (!Array.isArray(user.roles) || user.roles.length === 0) {
    return "Sem papeis definidos";
  }

  return user.roles.join(", ");
}

export function AdminFoundation() {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [loginForm, setLoginForm] = useState<LoginFormState>({ username: "", password: "" });
  const [busy, setBusy] = useState<boolean>(false);
  const [user, setUser] = useState<AuthUserProfile | null>(null);
  const [healthStatus, setHealthStatus] = useState<string>("indisponivel");
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

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

  return (
    <div className="space-y-6">
      <section id="dashboard" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Etapa 9.0.3</p>
        <h1 className="mt-1 text-2xl font-bold text-text">Admin Web - Expansion</h1>
        <p className="mt-3 text-sm text-muted">
          Expansao dos modulos de gestao com baseline de Cardapio, Compras e Producao sobre a base da T9.0.2.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">API backend</p>
            <p className="mt-2 text-lg font-semibold text-text">{healthStatus}</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Sessao</p>
            <p className="mt-2 text-lg font-semibold text-text">
              {viewState === "authenticated" ? "Autenticada" : "Nao autenticada"}
            </p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Trilha atual</p>
            <p className="mt-2 text-lg font-semibold text-text">T9.0.3</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Modulos ativos</p>
            <p className="mt-2 text-lg font-semibold text-text">6</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Proxima entrega</p>
            <p className="mt-2 text-lg font-semibold text-text">T9.1.1</p>
          </article>
        </div>
      </section>

      {viewState === "loading" && (
        <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <p className="text-sm text-muted">Validando sessao do Admin...</p>
        </section>
      )}

      {viewState === "anonymous" && (
        <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm md:max-w-xl">
          <h2 className="text-xl font-semibold text-text">Login de gestao</h2>
          <p className="mt-2 text-sm text-muted">Use uma conta com papel administrativo.</p>
          <form onSubmit={handleLogin} className="mt-4 grid gap-3">
            <label className="grid gap-1 text-sm text-muted">
              Usuario
              <input
                required
                autoComplete="username"
                className={INPUT_CLASS}
                value={loginForm.username}
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, username: event.currentTarget.value }))
                }
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
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, password: event.currentTarget.value }))
                }
              />
            </label>
            <button
              type="submit"
              disabled={busy}
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {busy ? "Entrando..." : "Entrar"}
            </button>
          </form>
        </section>
      )}

      {viewState === "authenticated" && user && (
        <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-text">Sessao ativa</h2>
              <p className="mt-1 text-sm text-muted">
                Usuario <strong className="text-text">{user.username}</strong> com papeis: {formatRoles(user)}.
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            >
              Sair
            </button>
          </div>
        </section>
      )}

      <section id="modulos" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-text">Modulos e status</h2>
        <p className="mt-2 text-sm text-muted">
          Visao consolidada da trilha 9.x para operar pedidos, estoque, compras e producao.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {MODULES.map((moduleItem) => (
            <article key={moduleItem.title} className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-primary">{moduleItem.stage}</p>
              <h3 className="mt-1 text-base font-semibold text-text">{moduleItem.title}</h3>
              <p className="mt-2 text-sm text-muted">{moduleItem.description}</p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Status: {moduleItem.status}
              </p>
            </article>
          ))}
        </div>
      </section>

      {viewState === "authenticated" && user && (
        <>
          <OrdersOpsPanel />
          <FinanceOpsPanel />
          <InventoryOpsPanel />
          <MenuOpsPanel />
          <ProcurementOpsPanel />
          <ProductionOpsPanel />
        </>
      )}

      <section id="prioridades" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-text">Prioridade cronologica</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-muted">
          <li>Consolidar T9.0.3 com validacao completa no quality gate.</li>
          <li>Entrar na T9.1.1 para cobertura completa dos modulos de gestao.</li>
          <li>Integrar Portal CMS no portal (T6.3.2) sem conflito com Antigravity.</li>
        </ol>
      </section>

      {(message || errorMessage) && (
        <section className="rounded-xl border border-border bg-bg px-4 py-3 text-sm">
          {message && <p className="text-primary">{message}</p>}
          {errorMessage && <p className="text-rose-600">{errorMessage}</p>}
        </section>
      )}
    </div>
  );
}
