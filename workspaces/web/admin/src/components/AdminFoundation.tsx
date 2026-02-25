"use client";

import Link from "next/link";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import { AdminSessionGate, useAdminSession } from "@/components/AdminSessionGate";
import { ADMIN_MODULES, resolveModuleCardBorder, resolveModuleStatusTone } from "@/lib/adminModules";

function resolveHealthTone(status: string): StatusTone {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus.includes("ok") || normalizedStatus.includes("online")) {
    return "success";
  }

  return "danger";
}

const Dashboard = () => {
  const { healthStatus } = useAdminSession();

  return (
    <div className="space-y-6">
      <section id="dashboard" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Etapa 9.1.2</p>
        <h1 className="mt-1 text-2xl font-bold text-text">Admin Web - Relatorios e UX/IX</h1>
        <p className="mt-3 text-sm text-muted">
          Hotpages por modulo, relatorios integrados e visao de fluxo de caixa global com exportacao CSV.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">API backend</p>
            <StatusPill tone={resolveHealthTone(healthStatus)} className="mt-2">
              {healthStatus}
            </StatusPill>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Modulos ativos</p>
            <p className="mt-2 text-lg font-semibold text-text">{ADMIN_MODULES.length}</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Foco atual</p>
            <p className="mt-2 text-lg font-semibold text-text">Relatorios + UX/IX</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Exportacao</p>
            <p className="mt-2 text-lg font-semibold text-text">CSV</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Proxima entrega</p>
            <p className="mt-2 text-lg font-semibold text-text">T9.1.2</p>
          </article>
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-text">Modulos e status</h2>
        <p className="mt-2 text-sm text-muted">
          Acesse cada hotpage para operar o modulo com menu contextual e relatorios integrados.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {ADMIN_MODULES.map((moduleItem) => (
            <Link
              key={moduleItem.slug}
              href={moduleItem.path}
              className={`block rounded-xl border bg-bg p-4 transition hover:border-primary ${resolveModuleCardBorder(moduleItem.status)}`}
            >
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-primary">
                {moduleItem.stage}
              </p>
              <h3 className="mt-1 text-base font-semibold text-text">{moduleItem.title}</h3>
              <p className="mt-2 text-sm text-muted">{moduleItem.description}</p>
              <div className="mt-2">
                <StatusPill tone={resolveModuleStatusTone(moduleItem.status)}>{moduleItem.status}</StatusPill>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-text">Acesso rapido</h2>
            <p className="mt-1 text-sm text-muted">Entradas diretas para operacao, relatorios e exportacao.</p>
          </div>
          <Link
            href="/modulos/relatorios"
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
          >
            Abrir relatorios
          </Link>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {ADMIN_MODULES.map((moduleItem) => (
            <Link
              key={moduleItem.slug}
              href={moduleItem.path}
              className="rounded-full border border-border bg-bg px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-text transition hover:border-primary hover:text-primary"
            >
              {moduleItem.title}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

export function AdminFoundation() {
  return (
    <AdminSessionGate>
      <Dashboard />
    </AdminSessionGate>
  );
}
