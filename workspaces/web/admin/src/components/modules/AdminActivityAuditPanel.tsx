"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { InlinePreloader } from "@/components/InlinePreloader";
import { ApiError, listAdminActivityLogsAdmin } from "@/lib/api";
import type { AdminActivityLogData } from "@/types/api";

const PAGE_SIZE = 40;

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada ao carregar os logs de atividade.";
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("pt-BR");
}

function resolveStatusTone(statusCode: number): "success" | "warning" | "danger" | "neutral" {
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

export function AdminActivityAuditPanel() {
  const [logs, setLogs] = useState<AdminActivityLogData[]>([]);
  const [count, setCount] = useState(0);
  const [offset, setOffset] = useState(0);
  const [nextOffset, setNextOffset] = useState<number | null>(null);

  const [searchDraft, setSearchDraft] = useState("");
  const [actorDraft, setActorDraft] = useState("");
  const [channelDraft, setChannelDraft] = useState("");
  const [methodDraft, setMethodDraft] = useState("");
  const [statusDraft, setStatusDraft] = useState("");
  const [dateFromDraft, setDateFromDraft] = useState("");
  const [dateToDraft, setDateToDraft] = useState("");

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const hasPreviousPage = offset > 0;

  const appliedFilters = useMemo(
    () => ({
      search: searchDraft.trim() || undefined,
      actor: actorDraft.trim() || undefined,
      channel: channelDraft.trim().toLowerCase() || undefined,
      method: methodDraft.trim().toUpperCase() || undefined,
      status: statusDraft.trim() || undefined,
      date_from: dateFromDraft || undefined,
      date_to: dateToDraft || undefined,
    }),
    [actorDraft, channelDraft, dateFromDraft, dateToDraft, methodDraft, searchDraft, statusDraft],
  );

  async function loadLogs(nextOffsetValue: number, options?: { silent?: boolean }) {
    const silent = options?.silent ?? false;
    if (!silent) {
      setLoading(true);
    }
    setBusy(true);

    try {
      const payload = await listAdminActivityLogsAdmin({
        ...appliedFilters,
        limit: PAGE_SIZE,
        offset: nextOffsetValue,
      });
      setLogs(payload.results);
      setCount(payload.count);
      setOffset(payload.offset);
      setNextOffset(payload.next_offset);
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
      setBusy(false);
    }
  }

  useEffect(() => {
    void loadLogs(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleApplyFilters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadLogs(0);
  }

  async function handlePreviousPage() {
    const prev = Math.max(0, offset - PAGE_SIZE);
    await loadLogs(prev, { silent: true });
  }

  async function handleNextPage() {
    if (nextOffset === null) {
      return;
    }
    await loadLogs(nextOffset, { silent: true });
  }

  async function handleRefresh() {
    await loadLogs(offset, { silent: true });
  }

  return (
    <section id="auditoria" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-text">Auditoria de atividade do Web Admin</h2>
          <p className="mt-1 text-sm text-muted">
            Historico completo de operacoes com usuario, data/hora, rota, status HTTP e metadata.
          </p>
        </div>
        <StatusPill tone="info">{count} eventos</StatusPill>
      </div>

      <form onSubmit={handleApplyFilters} className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <label className="grid gap-1 text-sm text-muted">
          Busca geral
          <input
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="rota, usuario, grupo"
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Usuario
          <input
            value={actorDraft}
            onChange={(event) => setActorDraft(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="admin_test"
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Canal
          <input
            value={channelDraft}
            onChange={(event) => setChannelDraft(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="web-admin"
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Metodo HTTP
          <select
            value={methodDraft}
            onChange={(event) => setMethodDraft(event.currentTarget.value)}
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
            value={statusDraft}
            onChange={(event) => setStatusDraft(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="200"
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Data inicial
          <input
            type="date"
            value={dateFromDraft}
            onChange={(event) => setDateFromDraft(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Data final
          <input
            type="date"
            value={dateToDraft}
            onChange={(event) => setDateToDraft(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          />
        </label>
        <div className="flex items-end justify-end gap-2 xl:col-span-1">
          <button
            type="button"
            onClick={() => {
              setSearchDraft("");
              setActorDraft("");
              setChannelDraft("");
              setMethodDraft("");
              setStatusDraft("");
              setDateFromDraft("");
              setDateToDraft("");
              void loadLogs(0);
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

      {errorMessage && (
        <div className="mt-3 rounded-lg border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {errorMessage}
        </div>
      )}

      <div className="mt-3 overflow-auto rounded-xl border border-border bg-bg">
        {loading ? (
          <div className="p-6">
            <InlinePreloader message="Carregando logs de auditoria" />
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
              </tr>
            </thead>
            <tbody>
              {logs.map((entry) => (
                <tr key={entry.id} className="border-t border-border">
                  <td className="px-3 py-2 align-top text-text">
                    {formatDateTime(entry.created_at)}
                    <p className="mt-1 text-[11px] text-muted">#{entry.request_id.slice(0, 8)}</p>
                  </td>
                  <td className="px-3 py-2 align-top text-text">
                    {entry.actor_username || "anonimo"}
                    {entry.actor_is_superuser ? (
                      <p className="mt-1 text-[11px] text-muted">superuser</p>
                    ) : entry.actor_is_staff ? (
                      <p className="mt-1 text-[11px] text-muted">staff</p>
                    ) : null}
                  </td>
                  <td className="px-3 py-2 align-top">
                    <StatusPill tone="neutral">{entry.channel || "unknown"}</StatusPill>
                  </td>
                  <td className="px-3 py-2 align-top">
                    <div className="flex flex-wrap items-center gap-1">
                      <StatusPill tone={resolveMethodTone(entry.method)}>{entry.method}</StatusPill>
                      {entry.action_group ? (
                        <StatusPill tone="info">{entry.action_group}</StatusPill>
                      ) : null}
                    </div>
                    {entry.resource ? <p className="mt-1 text-[11px] text-muted">{entry.resource}</p> : null}
                  </td>
                  <td className="px-3 py-2 align-top text-text">
                    <p className="max-w-[360px] break-all">{entry.path}</p>
                    {entry.origin ? (
                      <p className="mt-1 max-w-[360px] break-all text-[11px] text-muted">origin: {entry.origin}</p>
                    ) : null}
                    {entry.ip_address ? (
                      <p className="mt-1 text-[11px] text-muted">ip: {entry.ip_address}</p>
                    ) : null}
                  </td>
                  <td className="px-3 py-2 align-top">
                    <StatusPill tone={resolveStatusTone(entry.http_status)}>{entry.http_status}</StatusPill>
                  </td>
                  <td className="px-3 py-2 align-top text-text">{entry.duration_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
