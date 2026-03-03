"use client";

import { type FormEvent, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";
import { InlinePreloader } from "@/components/InlinePreloader";

import {
  ApiError,
  seedParaibaCaseiraWeekAdmin,
} from "@/lib/api";
import type { SeedParaibaCaseiraWeekResultData } from "@/types/api";

type WeeklySimulationPanelProps = {
  context: "cardapio" | "compras";
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao executar simulacao semanal.";
}

function formatDate(valueRaw: string): string {
  const dateValue = new Date(`${valueRaw}T00:00:00`);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleDateString("pt-BR");
}

function buildNextMondayIso(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  const localNow = new Date(now.getTime() - offset);
  const currentWeekday = localNow.getUTCDay();

  const mondayBasedDay = currentWeekday === 0 ? 7 : currentWeekday;
  const daysUntilNextMonday = mondayBasedDay >= 1 ? 8 - mondayBasedDay : 1;

  localNow.setUTCDate(localNow.getUTCDate() + daysUntilNextMonday);
  return localNow.toISOString().slice(0, 10);
}

function formatRange(result: SeedParaibaCaseiraWeekResultData): string {
  return `${formatDate(result.start_date)} ate ${formatDate(result.end_date)}`;
}

export function WeeklySimulationPanel({ context }: WeeklySimulationPanelProps) {
  const [startDate, setStartDate] = useState<string>(buildNextMondayIso());
  const [running, setRunning] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [result, setResult] = useState<SeedParaibaCaseiraWeekResultData | null>(null);

  const statusLabel = useMemo(
    () => (context === "cardapio" ? "Fluxo Cardapio + Compras" : "Fluxo Compras + Producao"),
    [context],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setRunning(true);
    setMessage("");
    setErrorMessage("");

    try {
      const payload = await seedParaibaCaseiraWeekAdmin({
        start_date: startDate || undefined,
      });

      setResult(payload);
      setMessage(`Simulacao concluida para ${formatRange(payload)}.`);
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-text">Simulacao semanal paraibana</h2>
          <p className="mt-1 text-sm text-muted">
            Execute o ciclo completo sem terminal: cardapio, compra com OCR, producao e precificacao.
          </p>
        </div>
        <StatusPill tone="info">{statusLabel}</StatusPill>
      </div>

      <form onSubmit={handleSubmit} className="mt-4 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-2 text-sm font-medium text-text">
          Data inicial (inicio da semana)
          <input
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
            required
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          />
        </label>

        <button
          type="submit"
          disabled={running}
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {running ? "Executando..." : "Executar simulacao"}
        </button>
      </form>

      {running && (
        <InlinePreloader
          className="mt-4 justify-start bg-surface/70"
          message="Executando fluxo semanal e consolidando relatorio..."
        />
      )}

      {message && (
        <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          {message}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}

      {result && (
        <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Periodo</p>
            <p className="mt-1 text-sm font-semibold text-text">{formatRange(result)}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Cardapios</p>
            <p className="mt-1 text-2xl font-semibold text-text">{result.menu_days_processed}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Requisicoes</p>
            <p className="mt-1 text-2xl font-semibold text-text">{result.purchase_requests_created}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Lotes</p>
            <p className="mt-1 text-2xl font-semibold text-text">{result.production_batches_processed}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4 md:col-span-2 lg:col-span-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compra utilizada</p>
            <p className="mt-1 text-sm font-semibold text-text">
              {result.purchase
                ? `#${result.purchase.id} (${result.purchase.invoice_number})`
                : "Sem compra registrada no relatorio."}
            </p>
          </article>

          {result.command_log && result.command_log.length > 0 && (
            <article className="rounded-xl border border-border bg-bg p-4 md:col-span-2 lg:col-span-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Log do comando</p>
              <pre className="mt-2 max-h-64 overflow-auto rounded-md bg-surface px-3 py-2 text-xs text-text">
                {result.command_log.join("\n")}
              </pre>
            </article>
          )}
        </div>
      )}
    </section>
  );
}
