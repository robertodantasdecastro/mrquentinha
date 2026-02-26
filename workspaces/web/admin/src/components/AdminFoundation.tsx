"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import { AdminSessionGate, useAdminSession } from "@/components/AdminSessionGate";
import { ApiError, fetchOrdersOpsDashboardAdmin } from "@/lib/api";
import { ADMIN_MODULES, resolveModuleCardBorder, resolveModuleStatusTone } from "@/lib/adminModules";
import type { OpsAlertData, OpsPipelineStageData } from "@/types/api";

function resolveHealthTone(status: string): StatusTone {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus.includes("ok") || normalizedStatus.includes("online")) {
    return "success";
  }

  return "danger";
}

const Dashboard = () => {
  const { healthStatus } = useAdminSession();
  const [opsLoading, setOpsLoading] = useState<boolean>(true);
  const [opsError, setOpsError] = useState<string>("");
  const [opsPipeline, setOpsPipeline] = useState<OpsPipelineStageData[]>([]);
  const [opsAlerts, setOpsAlerts] = useState<OpsAlertData[]>([]);
  const [opsKpis, setOpsKpis] = useState<{
    pedidos_hoje: number;
    pedidos_fila: number;
    receita_hoje: string;
    requisicoes_abertas: number;
    lotes_concluidos: number;
  } | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadOpsDashboard() {
      try {
        const payload = await fetchOrdersOpsDashboardAdmin();
        if (!mounted) {
          return;
        }

        setOpsPipeline(payload.pipeline);
        setOpsAlerts(payload.alerts);
        setOpsKpis({
          pedidos_hoje: payload.kpis.pedidos_hoje,
          pedidos_fila: payload.kpis.pedidos_fila,
          receita_hoje: payload.kpis.receita_hoje,
          requisicoes_abertas: payload.kpis.requisicoes_abertas,
          lotes_concluidos: payload.kpis.lotes_concluidos,
        });
        setOpsError("");
      } catch (error) {
        if (!mounted) {
          return;
        }
        if (error instanceof ApiError) {
          setOpsError(error.message);
        } else if (error instanceof Error) {
          setOpsError(error.message);
        } else {
          setOpsError("Falha ao carregar painel operacional.");
        }
      } finally {
        if (mounted) {
          setOpsLoading(false);
        }
      }
    }

    void loadOpsDashboard();
    const intervalId = window.setInterval(() => {
      void loadOpsDashboard();
    }, 30000);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const opsPipelineCards = useMemo(
    () =>
      opsPipeline.map((stage) => {
        const tone: StatusTone =
          stage.status === "ok"
            ? "success"
            : stage.status === "warning"
              ? "warning"
              : stage.status === "info"
                ? "info"
                : "neutral";

        return (
          <Link
            key={stage.stage}
            href={stage.path}
            className="min-w-[220px] flex-1 rounded-xl border border-border bg-bg p-4 transition hover:border-primary"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              {stage.stage}
            </p>
            <p className="mt-1 text-2xl font-semibold text-text">{stage.count}</p>
            <p className="mt-1 text-xs text-muted">{stage.detail}</p>
            <StatusPill tone={tone} className="mt-2">
              {stage.status}
            </StatusPill>
          </Link>
        );
      }),
    [opsPipeline],
  );

  return (
    <div className="space-y-6">
      <section id="dashboard" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">T9.1.3-A6 concluida</p>
        <h1 className="mt-1 text-2xl font-bold text-text">Centro de Operacoes - Linha de Producao</h1>
        <p className="mt-3 text-sm text-muted">
          Fluxo continuo: Cardapio para Compras/OCR para Producao para Pedidos para Entrega para Confirmacao.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">API backend</p>
            <StatusPill tone={resolveHealthTone(healthStatus)} className="mt-2">
              {healthStatus}
            </StatusPill>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Módulos ativos</p>
            <p className="mt-2 text-lg font-semibold text-text">{ADMIN_MODULES.length}</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Foco atual</p>
            <p className="mt-2 text-lg font-semibold text-text">Ciclo operacional ponta a ponta</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos hoje</p>
            <p className="mt-2 text-lg font-semibold text-text">{opsKpis?.pedidos_hoje ?? "-"}</p>
          </article>
          <article className="rounded-xl border border-border bg-bg p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Receita hoje</p>
            <p className="mt-2 text-lg font-semibold text-text">
              {opsKpis?.receita_hoje ? `R$ ${opsKpis.receita_hoje}` : "-"}
            </p>
          </article>
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-text">Pipeline em tempo real</h2>
            <p className="mt-1 text-sm text-muted">
              Atualizacao automatica a cada 30s com indicadores do backend.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <StatusPill tone="warning">Requisicoes abertas: {opsKpis?.requisicoes_abertas ?? "-"}</StatusPill>
            <StatusPill tone="info">Fila pedidos: {opsKpis?.pedidos_fila ?? "-"}</StatusPill>
            <StatusPill tone="success">Lotes concluidos: {opsKpis?.lotes_concluidos ?? "-"}</StatusPill>
          </div>
        </div>

        {opsLoading && (
          <p className="mt-3 text-sm text-muted">Carregando pipeline operacional...</p>
        )}
        {!opsLoading && opsError && (
          <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {opsError}
          </p>
        )}
        {!opsLoading && !opsError && (
          <div className="mt-4 flex flex-wrap gap-3">{opsPipelineCards}</div>
        )}

        {opsAlerts.length > 0 && (
          <div className="mt-4 space-y-2">
            {opsAlerts.map((alert) => (
              <Link
                key={`${alert.title}-${alert.path}`}
                href={alert.path}
                className="block rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 transition hover:border-primary"
              >
                <p className="font-semibold">{alert.title}</p>
                <p>{alert.detail}</p>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-text">Módulos e status</h2>
        <p className="mt-2 text-sm text-muted">
          Acesse cada hotpage para operar o módulo com menu contextual e relatórios integrados.
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
            <h2 className="text-xl font-semibold text-text">Acesso rápido</h2>
            <p className="mt-1 text-sm text-muted">Entradas diretas para operação, relatórios e exportação.</p>
          </div>
          <Link
            href="/modulos/relatorios"
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
          >
            Abrir relatórios
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
