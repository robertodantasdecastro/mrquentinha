"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import {
  ApiError,
  fetchFinanceCashflow,
  fetchFinanceKpis,
  fetchFinanceUnreconciled,
  listProductionBatchesAdmin,
  listPurchasesAdmin,
} from "@/lib/api";
import {
  buildRecentDateKeys,
  buildSeriesFromTotals,
  sumByDateKey,
} from "@/lib/metrics";
import type {
  FinanceCashflowPayload,
  FinanceKpisPayload,
  FinanceUnreconciledPayload,
  ProductionBatchData,
  PurchaseData,
} from "@/types/api";

import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { FinanceOpsPanel } from "@/components/modules/FinanceOpsPanel";

export const FINANCEIRO_BASE_PATH = "/modulos/financeiro";

export const FINANCEIRO_MENU_ITEMS = [
  { key: "all", label: "Todos", href: FINANCEIRO_BASE_PATH },
  { key: "visao-geral", label: "Visao geral", href: `${FINANCEIRO_BASE_PATH}/visao-geral#visao-geral` },
  { key: "conciliacao", label: "Conciliacao", href: `${FINANCEIRO_BASE_PATH}/conciliacao#conciliacao` },
  { key: "tendencias", label: "Tendencias", href: `${FINANCEIRO_BASE_PATH}/tendencias#tendencias` },
  { key: "exportacao", label: "Exportacao", href: `${FINANCEIRO_BASE_PATH}/exportacao#exportacao` },
];

export type FinanceiroSectionKey =
  | "all"
  | "visao-geral"
  | "conciliacao"
  | "tendencias"
  | "exportacao";

type FinanceiroSectionsProps = {
  activeSection?: FinanceiroSectionKey;
};

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

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar financeiro.";
}

function formatCurrency(value: string | number): string {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return String(value);
  }

  return numericValue.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function formatPercent(value: string | number): string {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return String(value);
  }

  return `${numericValue.toFixed(2)}%`;
}

function sumPurchaseAmount(purchases: PurchaseData[]): number {
  return purchases.reduce((accumulator, purchase) => {
    const amount = Number(purchase.total_amount);
    if (Number.isNaN(amount)) {
      return accumulator;
    }

    return accumulator + amount;
  }, 0);
}

export function FinanceiroSections({ activeSection = "all" }: FinanceiroSectionsProps) {
  const range = useMemo(buildCurrentMonthRange, []);

  const [kpis, setKpis] = useState<FinanceKpisPayload | null>(null);
  const [unreconciled, setUnreconciled] = useState<FinanceUnreconciledPayload | null>(null);
  const [cashflow, setCashflow] = useState<FinanceCashflowPayload | null>(null);
  const [purchases, setPurchases] = useState<PurchaseData[]>([]);
  const [batches, setBatches] = useState<ProductionBatchData[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadFinanceiro() {
      try {
        const [kpisPayload, unreconciledPayload, cashflowPayload, purchasesPayload, batchesPayload] =
          await Promise.all([
            fetchFinanceKpis(range.from, range.to),
            fetchFinanceUnreconciled(range.from, range.to),
            fetchFinanceCashflow(range.from, range.to),
            listPurchasesAdmin(),
            listProductionBatchesAdmin(),
          ]);

        if (!mounted) {
          return;
        }

        setKpis(kpisPayload);
        setUnreconciled(unreconciledPayload);
        setCashflow(cashflowPayload);
        setPurchases(purchasesPayload);
        setBatches(batchesPayload);
        setErrorMessage("");
      } catch (error) {
        if (mounted) {
          setErrorMessage(resolveErrorMessage(error));
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadFinanceiro();

    return () => {
      mounted = false;
    };
  }, [range.from, range.to]);

  const pendencias = unreconciled?.items.length ?? 0;
  const receitaPedidos = kpis?.kpis.receita_total ?? "0";
  const comprasTotal = useMemo(() => sumPurchaseAmount(purchases), [purchases]);
  const lotesPeriodo = batches.length;

  const trendDateKeys = useMemo(() => buildRecentDateKeys(7), []);
  const cashflowTotalsByDay = useMemo(() => {
    if (!cashflow) {
      return {} as Record<string, number>;
    }

    return sumByDateKey(
      cashflow.items,
      (item) => item.date,
      (item) => Number(item.net) || 0,
    );
  }, [cashflow]);

  const cashflowSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, cashflowTotalsByDay);
    return values.length > 0 ? values : [0, 0];
  }, [cashflowTotalsByDay, trendDateKeys]);

  const supplierValues = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const purchase of purchases) {
      const amount = Number(purchase.total_amount);
      if (Number.isNaN(amount)) {
        continue;
      }

      totals[purchase.supplier_name] = (totals[purchase.supplier_name] ?? 0) + amount;
    }

    const values = Object.values(totals)
      .sort((a, b) => b - a)
      .slice(0, 5);

    return values.length > 0 ? values : [0, 0, 0];
  }, [purchases]);

  const showAll = activeSection === "all";

  return (
    <>
      {(showAll || activeSection === "visao-geral") && (
        <section id="visao-geral" className="scroll-mt-24">
          <FinanceOpsPanel />
        </section>
      )}

      {(showAll || activeSection === "conciliacao") && (
        <section id="conciliacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Conciliacao global</h2>
              <p className="mt-1 text-sm text-muted">Movimentos pendentes e origem financeira por modulo.</p>
            </div>
            <StatusPill tone="warning">Pendencias {pendencias}</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando conciliacao...</p>}
          {!loading && (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos</p>
                <p className="mt-1 text-xl font-semibold text-text">{formatCurrency(receitaPedidos)}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compras</p>
                <p className="mt-1 text-xl font-semibold text-text">{formatCurrency(comprasTotal)}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Producao</p>
                <p className="mt-1 text-xl font-semibold text-text">{lotesPeriodo} lotes</p>
              </article>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "tendencias") && (
        <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Tendencias financeiras</h2>
              <p className="mt-1 text-sm text-muted">Receita, despesas e margem por periodo.</p>
            </div>
            <StatusPill tone="brand">
              Margem {formatPercent(kpis?.kpis.margem_media ?? "0")}
            </StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando tendencias...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Fluxo de caixa</p>
                <Sparkline values={cashflowSeries} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Despesas por fornecedor</p>
                <div className="mt-4">
                  <MiniBarChart values={supplierValues} />
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "exportacao") && (
        <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Exportacao CSV</h2>
          <p className="mt-1 text-sm text-muted">Exporte fluxos consolidados e demonstrativos por periodo.</p>
          <button className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90" type="button">
            Exportar financeiro (CSV)
          </button>
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
