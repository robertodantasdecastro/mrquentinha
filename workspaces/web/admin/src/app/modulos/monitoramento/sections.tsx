"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { ApiError, fetchEcosystemOpsRealtimeAdmin } from "@/lib/api";
import type { EcosystemOpsRealtimeData } from "@/types/api";
import { Sparkline } from "@/components/charts/Sparkline";
import { MiniBarChart } from "@/components/charts/MiniBarChart";

export const MONITORAMENTO_BASE_PATH = "/modulos/monitoramento";

export const MONITORAMENTO_MENU_ITEMS = [
  { key: "all", label: "Todos", href: MONITORAMENTO_BASE_PATH },
  { key: "visao-geral", label: "Visao geral", href: `${MONITORAMENTO_BASE_PATH}/visao-geral#visao-geral` },
  { key: "servicos", label: "Servicos", href: `${MONITORAMENTO_BASE_PATH}/servicos#servicos` },
  { key: "pagamentos", label: "Pagamentos", href: `${MONITORAMENTO_BASE_PATH}/pagamentos#pagamentos` },
  { key: "lifecycle", label: "Lifecycle", href: `${MONITORAMENTO_BASE_PATH}/lifecycle#lifecycle` },
];

export type MonitoramentoSectionKey =
  | "all"
  | "visao-geral"
  | "servicos"
  | "pagamentos"
  | "lifecycle";

type MonitoramentoSectionsProps = {
  activeSection?: MonitoramentoSectionKey;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha ao carregar monitoramento realtime.";
}

function formatUptime(seconds: number | null | undefined): string {
  if (!seconds || seconds <= 0) {
    return "-";
  }
  const total = Math.floor(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

export function MonitoramentoSections({ activeSection = "all" }: MonitoramentoSectionsProps) {
  const [payload, setPayload] = useState<EcosystemOpsRealtimeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadRealtime() {
      try {
        const response = await fetchEcosystemOpsRealtimeAdmin();
        if (!mounted) {
          return;
        }
        setPayload(response);
        setErrorMessage("");
      } catch (error) {
        if (!mounted) {
          return;
        }
        setErrorMessage(resolveErrorMessage(error));
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadRealtime();
    const intervalId = window.setInterval(() => void loadRealtime(), 10000);
    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const showAll = activeSection === "all";

  const serviceChartValues = useMemo(
    () => payload?.services.map((item) => (item.listener_ok ? 100 : 0)) ?? [0, 0, 0, 0],
    [payload],
  );
  const paymentSeries = useMemo(
    () =>
      payload?.payment_monitor.series_last_15_minutes.map((item) => item.webhooks_received) ??
      [0, 0],
    [payload],
  );

  return (
    <>
      {(showAll || activeSection === "visao-geral") && (
        <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Visao geral realtime</h2>
              <p className="mt-1 text-sm text-muted">
                Monitoramento central do ecossistema com atualizacao a cada 10 segundos.
              </p>
            </div>
            <StatusPill tone="info">10s</StatusPill>
          </div>

          {loading && <p className="mt-4 text-sm text-muted">Carregando dados realtime...</p>}
          {!loading && payload && (
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Load 1m</p>
                <p className="mt-1 text-2xl font-semibold text-text">{payload.server_health.load_avg_1m}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Memoria usada</p>
                <p className="mt-1 text-2xl font-semibold text-text">
                  {payload.server_health.memory.used_percent}%
                </p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Disco usado</p>
                <p className="mt-1 text-2xl font-semibold text-text">
                  {payload.server_health.disk.used_percent}%
                </p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Uptime servidor</p>
                <p className="mt-1 text-2xl font-semibold text-text">
                  {formatUptime(payload.server_health.uptime_seconds)}
                </p>
              </article>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "servicos") && payload && (
        <section id="servicos" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Servicos do ecossistema</h2>
          <p className="mt-1 text-sm text-muted">Backend, Admin, Portal e Client com listener e processo ativo.</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {payload.services.map((service) => (
              <article key={service.key} className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                  {service.name}
                </p>
                <p className="mt-1 text-base font-semibold text-text">
                  {service.status.toUpperCase()} :{service.port}
                </p>
                <p className="mt-1 text-xs text-muted">
                  PID: {service.pid ?? "-"} | RSS: {service.rss_mb ?? 0} MB
                </p>
                <p className="mt-1 text-xs text-muted">
                  Uptime processo: {formatUptime(service.uptime_seconds)}
                </p>
              </article>
            ))}
          </div>
          <div className="mt-4 rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Saude dos listeners</p>
            <div className="mt-3">
              <MiniBarChart values={serviceChartValues} />
            </div>
          </div>
        </section>
      )}

      {(showAll || activeSection === "pagamentos") && payload && (
        <section id="pagamentos" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Pagamentos em tempo real</h2>
          <p className="mt-1 text-sm text-muted">
            Canal: {payload.payment_monitor.communication_channel.transport}/
            {payload.payment_monitor.communication_channel.encryption} com{" "}
            {payload.payment_monitor.communication_channel.auth}.
          </p>
          <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Provider Web</p>
              <p className="mt-1 text-lg font-semibold text-text">
                {payload.payment_monitor.frontend_provider.web}
              </p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Provider Mobile</p>
              <p className="mt-1 text-lg font-semibold text-text">
                {payload.payment_monitor.frontend_provider.mobile}
              </p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Webhooks 15m</p>
              <p className="mt-1 text-lg font-semibold text-text">
                {payload.payment_monitor.summary.webhooks_last_15m}
              </p>
            </article>
          </div>

          <div className="mt-4 rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Comunicacao com gateways (24h)
            </p>
            <div className="mt-3 space-y-2">
              {payload.payment_monitor.providers.map((provider) => (
                <div
                  key={provider.provider}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border px-3 py-2 text-xs"
                >
                  <p className="font-semibold text-text">{provider.provider}</p>
                  <p className="text-muted">
                    sync {provider.sync_status} | webhooks {provider.webhooks_24h} | falhas{" "}
                    {provider.webhooks_failed_24h} | sucesso {provider.success_rate_24h}%
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Serie de eventos (15 minutos)
            </p>
            <Sparkline values={paymentSeries} className="mt-3" />
          </div>
        </section>
      )}

      {(showAll || activeSection === "lifecycle") && payload && (
        <section id="lifecycle" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Lifecycle do pedido</h2>
          <p className="mt-1 text-sm text-muted">
            Acompanhamento interrelacionado entre criacao, producao, entrega e confirmacao.
          </p>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Criados</p>
              <p className="mt-1 text-2xl font-semibold text-text">
                {payload.payment_monitor.order_lifecycle.created}
              </p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Em progresso</p>
              <p className="mt-1 text-2xl font-semibold text-text">
                {payload.payment_monitor.order_lifecycle.in_progress}
              </p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Entregues</p>
              <p className="mt-1 text-2xl font-semibold text-text">
                {payload.payment_monitor.order_lifecycle.delivered}
              </p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Recebidos</p>
              <p className="mt-1 text-2xl font-semibold text-text">
                {payload.payment_monitor.order_lifecycle.received}
              </p>
            </article>
          </div>
        </section>
      )}

      {errorMessage && (
        <div className="rounded-xl border border-border bg-bg px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      )}
    </>
  );
}
