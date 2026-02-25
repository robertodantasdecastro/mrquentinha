"use client";

import { useEffect, useMemo, useState } from "react";

import {
  ApiError,
  fetchFinanceKpis,
  fetchFinanceUnreconciled,
} from "@/lib/api";
import type {
  CashMovementData,
  FinanceKpisPayload,
  FinanceUnreconciledPayload,
} from "@/types/api";

function buildCurrentMonthRange(): { from: string; to: string } {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  const toIsoDate = (value: Date) => value.toISOString().slice(0, 10);

  return {
    from: toIsoDate(firstDay),
    to: toIsoDate(lastDay),
  };
}

function formatCurrency(value: string): string {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return value;
  }

  return numericValue.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function formatPercent(value: string): string {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return value;
  }

  return `${numericValue.toFixed(2)}%`;
}

function formatDateTime(valueRaw: string): string {
  const dateValue = new Date(valueRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleString("pt-BR");
}

function formatDirection(direction: string): string {
  if (direction === "IN") {
    return "Entrada";
  }

  if (direction === "OUT") {
    return "Saída";
  }

  return direction;
}

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar financeiro.";
}

export function FinanceOpsPanel() {
  const initialRange = useMemo(buildCurrentMonthRange, []);

  const [fromDate, setFromDate] = useState<string>(initialRange.from);
  const [toDate, setToDate] = useState<string>(initialRange.to);
  const [kpis, setKpis] = useState<FinanceKpisPayload | null>(null);
  const [unreconciled, setUnreconciled] = useState<FinanceUnreconciledPayload | null>(
    null,
  );
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const unreconciledItems: CashMovementData[] = unreconciled?.items ?? [];

  async function loadFinance({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [kpisPayload, unreconciledPayload] = await Promise.all([
        fetchFinanceKpis(fromDate, toDate),
        fetchFinanceUnreconciled(fromDate, toDate),
      ]);

      setKpis(kpisPayload);
      setUnreconciled(unreconciledPayload);
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadFinance();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleApplyPeriod() {
    setMessage(`Período aplicado: ${fromDate} até ${toDate}.`);
    void loadFinance({ silent: true });
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Financeiro</h3>
          <p className="text-sm text-muted">
            Indicadores de receita/despesa e monitoramento de conciliação.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadFinance({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      <div className="mt-4 grid gap-3 rounded-xl border border-border bg-bg p-4 md:grid-cols-3">
        <label className="grid gap-1 text-sm text-muted">
          De
          <input
            type="date"
            value={fromDate}
            onChange={(event) => setFromDate(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          />
        </label>

        <label className="grid gap-1 text-sm text-muted">
          Até
          <input
            type="date"
            value={toDate}
            onChange={(event) => setToDate(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          />
        </label>

        <div className="flex items-end">
          <button
            type="button"
            onClick={handleApplyPeriod}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
          >
            Aplicar período
          </button>
        </div>
      </div>

      {loading && <p className="mt-4 text-sm text-muted">Carregando financeiro...</p>}

      {!loading && kpis && (
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos</p>
            <p className="mt-1 text-2xl font-semibold text-text">{kpis.kpis.pedidos}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Receita total</p>
            <p className="mt-1 text-2xl font-semibold text-text">{formatCurrency(kpis.kpis.receita_total)}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Despesas</p>
            <p className="mt-1 text-2xl font-semibold text-text">{formatCurrency(kpis.kpis.despesas_total)}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Lucro bruto</p>
            <p className="mt-1 text-2xl font-semibold text-text">{formatCurrency(kpis.kpis.lucro_bruto)}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Ticket médio</p>
            <p className="mt-1 text-2xl font-semibold text-text">{formatCurrency(kpis.kpis.ticket_medio)}</p>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Margem média</p>
            <p className="mt-1 text-2xl font-semibold text-text">{formatPercent(kpis.kpis.margem_media)}</p>
          </article>
        </div>
      )}

      {!loading && (
        <div className="mt-4 rounded-xl border border-border bg-bg p-4">
          <div className="flex items-center justify-between gap-3">
            <h4 className="text-base font-semibold text-text">Não conciliados</h4>
            <span className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              {unreconciledItems.length} registros
            </span>
          </div>

          {unreconciledItems.length === 0 && (
            <p className="mt-3 text-sm text-muted">Nenhum movimento pendente de conciliação no período.</p>
          )}

          {unreconciledItems.length > 0 && (
            <div className="mt-3 space-y-2">
              {unreconciledItems.slice(0, 12).map((item) => (
                <article
                  key={item.id}
                  className="rounded-lg border border-border bg-surface px-3 py-2"
                >
                  <p className="text-sm font-semibold text-text">
                    Movimento #{item.id} - {formatDirection(item.direction)}
                  </p>
                  <p className="text-xs text-muted">
                    Data: {formatDateTime(item.movement_date)} | Conta: {item.account}
                  </p>
                  <p className="text-xs text-muted">
                    Valor: <strong className="text-text">{formatCurrency(item.amount)}</strong>
                  </p>
                </article>
              ))}
            </div>
          )}
        </div>
      )}

      {(message || errorMessage) && (
        <div className="mt-4 rounded-xl border border-border bg-bg px-4 py-3 text-sm">
          {message && <p className="text-primary">{message}</p>}
          {errorMessage && <p className="text-rose-600">{errorMessage}</p>}
        </div>
      )}
    </section>
  );
}
