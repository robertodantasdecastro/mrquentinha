"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { InlinePreloader } from "@/components/InlinePreloader";
import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import {
  ApiError,
  fetchAdminActivityOverviewAdmin,
  listAdminActivityLogsAdmin,
} from "@/lib/api";
import type {
  AdminActivityLogData,
  AdminActivityOverviewData,
} from "@/types/api";

const PAGE_SIZE = 40;
const OVERVIEW_REFRESH_MS = 30000;

export const AUDITORIA_ATIVIDADE_BASE_PATH = "/modulos/auditoria-atividade";

export const AUDITORIA_ATIVIDADE_MENU_ITEMS = [
  { key: "all", label: "Todos", href: AUDITORIA_ATIVIDADE_BASE_PATH },
  {
    key: "visao-geral",
    label: "Dashboard",
    href: `${AUDITORIA_ATIVIDADE_BASE_PATH}/visao-geral#visao-geral`,
  },
  {
    key: "eventos",
    label: "Eventos",
    href: `${AUDITORIA_ATIVIDADE_BASE_PATH}/eventos#eventos`,
  },
  {
    key: "seguranca",
    label: "Seguranca",
    href: `${AUDITORIA_ATIVIDADE_BASE_PATH}/seguranca#seguranca`,
  },
  {
    key: "tendencias",
    label: "Tendencias",
    href: `${AUDITORIA_ATIVIDADE_BASE_PATH}/tendencias#tendencias`,
  },
];

export type AuditoriaAtividadeSectionKey =
  | "all"
  | "visao-geral"
  | "eventos"
  | "seguranca"
  | "tendencias";

type AuditoriaAtividadeSectionsProps = {
  activeSection?: AuditoriaAtividadeSectionKey;
};

type FiltersState = {
  search: string;
  actor: string;
  channel: string;
  method: string;
  status: string;
  dateFrom: string;
  dateTo: string;
};

const INITIAL_FILTERS: FiltersState = {
  search: "",
  actor: "",
  channel: "",
  method: "",
  status: "",
  dateFrom: "",
  dateTo: "",
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada ao carregar auditoria de atividade.";
}

function formatDateTime(valueRaw: string): string {
  const dateValue = new Date(valueRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }
  return dateValue.toLocaleString("pt-BR");
}

function resolveHttpStatusTone(statusCode: number): "success" | "warning" | "danger" | "neutral" {
  if (statusCode >= 200 && statusCode < 400) {
    return "success";
  }
  if (statusCode >= 400 && statusCode < 500) {
    return "warning";
  }
  if (statusCode >= 500) {
    return "danger";
  }
  return "neutral";
}

function resolveMethodTone(method: string): "success" | "warning" | "danger" | "info" | "neutral" {
  const normalized = method.toUpperCase();
  if (normalized === "GET") {
    return "info";
  }
  if (normalized === "POST" || normalized === "PUT" || normalized === "PATCH") {
    return "success";
  }
  if (normalized === "DELETE") {
    return "danger";
  }
  return "neutral";
}

function resolveRiskLevel(overview: AdminActivityOverviewData | null): {
  label: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
} {
  if (!overview) {
    return { label: "Sem dados", tone: "neutral" };
  }

  const errorRate = overview.totals.error_rate_percent;
  if (errorRate >= 20) {
    return { label: "Risco alto", tone: "danger" };
  }
  if (errorRate >= 10) {
    return { label: "Risco moderado", tone: "warning" };
  }
  return { label: "Risco controlado", tone: "success" };
}

function stringifyMetadata(metadata: Record<string, unknown>): string {
  try {
    return JSON.stringify(metadata, null, 2);
  } catch {
    return "{}";
  }
}

export function AuditoriaAtividadeSections({
  activeSection = "all",
}: AuditoriaAtividadeSectionsProps) {
  const [filters, setFilters] = useState<FiltersState>(INITIAL_FILTERS);
  const [logs, setLogs] = useState<AdminActivityLogData[]>([]);
  const [overview, setOverview] = useState<AdminActivityOverviewData | null>(null);
  const [count, setCount] = useState(0);
  const [offset, setOffset] = useState(0);
  const [nextOffset, setNextOffset] = useState<number | null>(null);

  const [selectedLogId, setSelectedLogId] = useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const appliedFilters = useMemo(
    () => ({
      search: filters.search.trim() || undefined,
      actor: filters.actor.trim() || undefined,
      channel: filters.channel.trim().toLowerCase() || undefined,
      method: filters.method.trim().toUpperCase() || undefined,
      status: filters.status.trim() || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
    }),
    [filters],
  );

  const selectedLog = useMemo(() => {
    if (selectedLogId === null) {
      return null;
    }
    return logs.find((item) => item.id === selectedLogId) ?? null;
  }, [logs, selectedLogId]);

  const riskLevel = useMemo(() => resolveRiskLevel(overview), [overview]);

  const hourlyEvents = useMemo(
    () => overview?.hourly_series_last_24h.map((item) => item.events) ?? [0, 0],
    [overview],
  );
  const hourlyErrors = useMemo(
    () => overview?.hourly_series_last_24h.map((item) => item.errors) ?? [0, 0],
    [overview],
  );
  const methodDistribution = useMemo(
    () => overview?.by_method.map((item) => item.count) ?? [0, 0],
    [overview],
  );
  const channelDistribution = useMemo(
    () => overview?.by_channel.map((item) => item.count) ?? [0, 0],
    [overview],
  );

  async function loadAuditData(nextOffsetValue: number, options?: { silent?: boolean }) {
    const silent = options?.silent ?? false;
    if (!silent) {
      setLoading(true);
    }
    setBusy(true);

    try {
      const [overviewPayload, logsPayload] = await Promise.all([
        fetchAdminActivityOverviewAdmin(appliedFilters),
        listAdminActivityLogsAdmin({
          ...appliedFilters,
          limit: PAGE_SIZE,
          offset: nextOffsetValue,
        }),
      ]);

      setOverview(overviewPayload);
      setLogs(logsPayload.results);
      setCount(logsPayload.count);
      setOffset(logsPayload.offset);
      setNextOffset(logsPayload.next_offset);
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
      setBusy(false);
    }
  }

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      await loadAuditData(0);
    }

    void bootstrap();

    const intervalId = window.setInterval(() => {
      if (!mounted) {
        return;
      }
      void loadAuditData(offset, { silent: true });
    }, OVERVIEW_REFRESH_MS);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const showAll = activeSection === "all";
  const hasPreviousPage = offset > 0;

  async function handleApplyFilters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSelectedLogId(null);
    await loadAuditData(0);
  }

  async function handleRefresh() {
    await loadAuditData(offset, { silent: true });
  }

  async function handlePreviousPage() {
    const prev = Math.max(0, offset - PAGE_SIZE);
    await loadAuditData(prev, { silent: true });
  }

  async function handleNextPage() {
    if (nextOffset === null) {
      return;
    }
    await loadAuditData(nextOffset, { silent: true });
  }

  return (
    <>
      {(showAll || activeSection === "visao-geral") && (
        <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Dashboard de auditoria</h2>
              <p className="mt-1 text-sm text-muted">
                Indicadores consolidados de trilha administrativa do Web Admin.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusPill tone={riskLevel.tone}>{riskLevel.label}</StatusPill>
              <StatusPill tone="info">{overview?.generated_at ? formatDateTime(overview.generated_at) : "-"}</StatusPill>
            </div>
          </div>

          {loading && <InlinePreloader message="Carregando dashboard de auditoria..." className="mt-4 justify-start bg-surface/70" />}

          {!loading && overview && (
            <>
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-6">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Eventos</p>
                  <p className="mt-1 text-2xl font-semibold text-text">{overview.totals.events}</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Taxa sucesso</p>
                  <p className="mt-1 text-2xl font-semibold text-text">{overview.totals.success_rate_percent}%</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Erros 4xx</p>
                  <p className="mt-1 text-2xl font-semibold text-text">{overview.totals.client_error_count}</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Erros 5xx</p>
                  <p className="mt-1 text-2xl font-semibold text-text">{overview.totals.server_error_count}</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Latencia media</p>
                  <p className="mt-1 text-2xl font-semibold text-text">{Math.round(overview.totals.avg_duration_ms)} ms</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Latencia p95</p>
                  <p className="mt-1 text-2xl font-semibold text-text">{overview.totals.p95_duration_ms} ms</p>
                </article>
              </div>

              <div className="mt-4 grid gap-4 xl:grid-cols-2">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Eventos por hora (24h)</p>
                  <Sparkline values={hourlyEvents} className="mt-3" />
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Erros por hora (24h)</p>
                  <Sparkline values={hourlyErrors} className="mt-3" />
                </article>
              </div>

              <div className="mt-4 grid gap-4 xl:grid-cols-2">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Distribuicao por metodo</p>
                  <div className="mt-3">
                    <MiniBarChart values={methodDistribution} />
                  </div>
                  <div className="mt-2 space-y-1 text-xs text-muted">
                    {overview.by_method.map((item) => (
                      <p key={`method-${item.key}`}>
                        {item.key}: <strong className="text-text">{item.count}</strong>
                      </p>
                    ))}
                  </div>
                </article>

                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Distribuicao por canal</p>
                  <div className="mt-3">
                    <MiniBarChart values={channelDistribution} />
                  </div>
                  <div className="mt-2 space-y-1 text-xs text-muted">
                    {overview.by_channel.map((item) => (
                      <p key={`channel-${item.key}`}>
                        {item.key}: <strong className="text-text">{item.count}</strong>
                      </p>
                    ))}
                  </div>
                </article>
              </div>
            </>
          )}
        </section>
      )}

      {(showAll || activeSection === "eventos") && (
        <section id="eventos" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Eventos e filtros operacionais</h2>
              <p className="mt-1 text-sm text-muted">
                Investigacao detalhada por usuario, rota, metodo, periodo e status.
              </p>
            </div>
            <StatusPill tone="info">{count} registros</StatusPill>
          </div>

          <form onSubmit={handleApplyFilters} className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <label className="grid gap-1 text-sm text-muted">
              Busca geral
              <input
                value={filters.search}
                onChange={(event) => setFilters((current) => ({ ...current, search: event.currentTarget.value }))}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="rota, acao, recurso, usuario"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Usuario
              <input
                value={filters.actor}
                onChange={(event) => setFilters((current) => ({ ...current, actor: event.currentTarget.value }))}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="admin_test"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Canal
              <input
                value={filters.channel}
                onChange={(event) => setFilters((current) => ({ ...current, channel: event.currentTarget.value }))}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="web-admin"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Metodo HTTP
              <select
                value={filters.method}
                onChange={(event) => setFilters((current) => ({ ...current, method: event.currentTarget.value }))}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              >
                <option value="">Todos</option>
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="PATCH">PATCH</option>
                <option value="DELETE">DELETE</option>
              </select>
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Status HTTP
              <input
                value={filters.status}
                onChange={(event) => setFilters((current) => ({ ...current, status: event.currentTarget.value }))}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="200, 403, 5xx"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Data inicial
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(event) => setFilters((current) => ({ ...current, dateFrom: event.currentTarget.value }))}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-sm text-muted">
              Data final
              <input
                type="date"
                value={filters.dateTo}
                onChange={(event) => setFilters((current) => ({ ...current, dateTo: event.currentTarget.value }))}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <div className="flex items-end justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setFilters(INITIAL_FILTERS);
                  setSelectedLogId(null);
                  void loadAuditData(0);
                }}
                disabled={busy}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                Limpar
              </button>
              <button
                type="submit"
                disabled={busy}
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Filtrar
              </button>
            </div>
          </form>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
            <p>
              Exibindo {logs.length} de {count} eventos (offset {offset}).
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void handleRefresh()}
                disabled={busy}
                className="rounded-md border border-border bg-bg px-3 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                Atualizar
              </button>
              <button
                type="button"
                onClick={() => void handlePreviousPage()}
                disabled={busy || !hasPreviousPage}
                className="rounded-md border border-border bg-bg px-3 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                Anterior
              </button>
              <button
                type="button"
                onClick={() => void handleNextPage()}
                disabled={busy || nextOffset === null}
                className="rounded-md border border-border bg-bg px-3 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                Proxima
              </button>
            </div>
          </div>

          <div className="mt-3 overflow-auto rounded-xl border border-border bg-bg">
            {loading ? (
              <div className="p-6">
                <InlinePreloader message="Carregando logs de auditoria..." />
              </div>
            ) : logs.length === 0 ? (
              <div className="p-6 text-sm text-muted">Nenhum evento encontrado com os filtros atuais.</div>
            ) : (
              <table className="min-w-full text-xs">
                <thead className="bg-surface/70 text-muted">
                  <tr>
                    <th className="px-3 py-2 text-left font-semibold">Data/hora</th>
                    <th className="px-3 py-2 text-left font-semibold">Usuario</th>
                    <th className="px-3 py-2 text-left font-semibold">Canal</th>
                    <th className="px-3 py-2 text-left font-semibold">Acao</th>
                    <th className="px-3 py-2 text-left font-semibold">Rota</th>
                    <th className="px-3 py-2 text-left font-semibold">Status</th>
                    <th className="px-3 py-2 text-left font-semibold">Tempo</th>
                    <th className="px-3 py-2 text-left font-semibold">Detalhes</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((entry) => (
                    <tr key={entry.id} className="border-t border-border">
                      <td className="px-3 py-2 align-top text-text">
                        {formatDateTime(entry.created_at)}
                        <p className="mt-1 text-[11px] text-muted">#{entry.request_id.slice(0, 8)}</p>
                      </td>
                      <td className="px-3 py-2 align-top text-text">{entry.actor_username || "anonimo"}</td>
                      <td className="px-3 py-2 align-top text-muted">{entry.channel}</td>
                      <td className="px-3 py-2 align-top">
                        <StatusPill tone={resolveMethodTone(entry.method)}>{entry.method}</StatusPill>
                      </td>
                      <td className="px-3 py-2 align-top text-text">{entry.path}</td>
                      <td className="px-3 py-2 align-top">
                        <StatusPill tone={resolveHttpStatusTone(entry.http_status)}>{entry.http_status}</StatusPill>
                      </td>
                      <td className="px-3 py-2 align-top text-muted">{entry.duration_ms} ms</td>
                      <td className="px-3 py-2 align-top">
                        <button
                          type="button"
                          onClick={() =>
                            setSelectedLogId((current) => (current === entry.id ? null : entry.id))
                          }
                          className="rounded-md border border-border bg-bg px-2 py-1 text-[11px] font-semibold text-text transition hover:border-primary hover:text-primary"
                        >
                          {selectedLogId === entry.id ? "Ocultar" : "Abrir"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {selectedLog && (
            <article className="mt-4 rounded-xl border border-border bg-bg p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold text-text">Detalhes do evento #{selectedLog.id}</h3>
                  <p className="mt-1 text-xs text-muted">
                    {selectedLog.method} {selectedLog.path} | status {selectedLog.http_status} | {selectedLog.duration_ms} ms
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedLogId(null)}
                  className="rounded-md border border-border bg-surface px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                >
                  Fechar
                </button>
              </div>

              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <div className="rounded-lg border border-border bg-surface p-3 text-xs text-muted">
                  <p>Canal: <strong className="text-text">{selectedLog.channel}</strong></p>
                  <p className="mt-1">Usuario: <strong className="text-text">{selectedLog.actor_username || "anonimo"}</strong></p>
                  <p className="mt-1">Origem: <strong className="text-text">{selectedLog.origin || "-"}</strong></p>
                  <p className="mt-1">IP: <strong className="text-text">{selectedLog.ip_address || "-"}</strong></p>
                  <p className="mt-1">Grupo: <strong className="text-text">{selectedLog.action_group || "-"}</strong></p>
                  <p className="mt-1">Recurso: <strong className="text-text">{selectedLog.resource || "-"}</strong></p>
                </div>
                <div className="rounded-lg border border-border bg-surface p-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Metadata</p>
                  <pre className="mt-2 max-h-64 overflow-auto rounded-md border border-border bg-bg p-2 text-[11px] text-text">
                    {stringifyMetadata(selectedLog.metadata)}
                  </pre>
                </div>
              </div>
            </article>
          )}
        </section>
      )}

      {(showAll || activeSection === "seguranca") && overview && (
        <section id="seguranca" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Seguranca e conformidade</h2>
          <p className="mt-1 text-sm text-muted">
            Indicadores de tentativas negadas, acesso anonimo e incidentes recentes.
          </p>

          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">401 Unauthorized</p>
              <p className="mt-1 text-2xl font-semibold text-text">{overview.security.unauthorized_count}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">403 Forbidden</p>
              <p className="mt-1 text-2xl font-semibold text-text">{overview.security.forbidden_count}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Atores unicos</p>
              <p className="mt-1 text-2xl font-semibold text-text">{overview.totals.unique_actors}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">IPs unicos</p>
              <p className="mt-1 text-2xl font-semibold text-text">{overview.totals.unique_ips}</p>
            </article>
          </div>

          <div className="mt-4 rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Ultimos eventos com falha</p>
            {overview.security.failed_events.length === 0 ? (
              <p className="mt-2 text-sm text-muted">Nenhuma falha encontrada no recorte atual.</p>
            ) : (
              <div className="mt-2 space-y-2">
                {overview.security.failed_events.map((item) => (
                  <article key={`failed-${item.id}`} className="rounded-lg border border-border bg-surface px-3 py-2">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <p className="font-semibold text-text">
                        {item.method} {item.path}
                      </p>
                      <StatusPill tone={resolveHttpStatusTone(item.http_status)}>
                        {item.http_status}
                      </StatusPill>
                    </div>
                    <p className="mt-1 text-xs text-muted">
                      {formatDateTime(item.created_at)} | usuario {item.actor_username || "anonimo"} | {item.duration_ms} ms
                    </p>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {(showAll || activeSection === "tendencias") && overview && (
        <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Tendencias e hotspots</h2>
          <p className="mt-1 text-sm text-muted">
            Principais atores, rotas e grupos de acao para analise de carga e risco.
          </p>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Top atores</p>
              <div className="mt-2 space-y-2 text-xs">
                {overview.top_actors.length === 0 && (
                  <p className="text-muted">Sem atores no recorte atual.</p>
                )}
                {overview.top_actors.map((item) => (
                  <div key={`actor-${item.key}`} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <p className="text-text">{item.key}</p>
                    <strong className="text-text">{item.count}</strong>
                  </div>
                ))}
              </div>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Top rotas</p>
              <div className="mt-2 space-y-2 text-xs">
                {overview.top_paths.length === 0 && (
                  <p className="text-muted">Sem rotas no recorte atual.</p>
                )}
                {overview.top_paths.map((item) => (
                  <div key={`path-${item.key}`} className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-2">
                    <p className="truncate text-text">{item.key}</p>
                    <strong className="text-text">{item.count}</strong>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Grupos de acao</p>
              <div className="mt-3">
                <MiniBarChart values={overview.by_action_group.map((item) => item.count)} />
              </div>
              <div className="mt-2 space-y-1 text-xs text-muted">
                {overview.by_action_group.map((item) => (
                  <p key={`action-${item.key}`}>
                    {item.key}: <strong className="text-text">{item.count}</strong>
                  </p>
                ))}
              </div>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Erros x sucesso (24h)</p>
              <Sparkline values={hourlyErrors} className="mt-3" />
              <p className="mt-2 text-xs text-muted">
                Taxa de erro atual: <strong className="text-text">{overview.totals.error_rate_percent}%</strong>
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
