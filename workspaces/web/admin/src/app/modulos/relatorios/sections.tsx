"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import {
  ApiError,
  exportFinanceCashflowCsv,
  exportFinanceDreCsv,
  exportOrdersCsv,
  exportProductionCsv,
  exportPurchasesCsv,
  fetchFinanceCashflow,
  listOrdersAdmin,
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
  OrderData,
  ProductionBatchData,
  PurchaseData,
} from "@/types/api";

import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";

export const RELATORIOS_BASE_PATH = "/modulos/relatorios";

export const RELATORIOS_MENU_ITEMS = [
  { key: "all", label: "Todos", href: RELATORIOS_BASE_PATH },
  { key: "fluxo-caixa", label: "Fluxo de caixa", href: `${RELATORIOS_BASE_PATH}/fluxo-caixa#fluxo-caixa` },
  { key: "compras", label: "Compras", href: `${RELATORIOS_BASE_PATH}/compras#compras` },
  { key: "producao", label: "Produção", href: `${RELATORIOS_BASE_PATH}/producao#producao` },
  { key: "pedidos", label: "Pedidos", href: `${RELATORIOS_BASE_PATH}/pedidos#pedidos` },
  { key: "exportacao", label: "Exportação", href: `${RELATORIOS_BASE_PATH}/exportacao#exportacao` },
];

export type RelatoriosSectionKey =
  | "all"
  | "fluxo-caixa"
  | "compras"
  | "producao"
  | "pedidos"
  | "exportacao";

type RelatoriosSectionsProps = {
  activeSection?: RelatoriosSectionKey;
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

  return "Falha inesperada ao carregar relatórios.";
}

function sumPlanned(batch: ProductionBatchData): number {
  return batch.production_items.reduce((accumulator, item) => {
    return accumulator + item.qty_planned;
  }, 0);
}

function sumWaste(batch: ProductionBatchData): number {
  return batch.production_items.reduce((accumulator, item) => {
    return accumulator + item.qty_waste;
  }, 0);
}

export function RelatoriosSections({ activeSection = "all" }: RelatoriosSectionsProps) {
  const range = useMemo(buildCurrentMonthRange, []);
  const [periodFrom, setPeriodFrom] = useState(range.from);
  const [periodTo, setPeriodTo] = useState(range.to);
  const [exportingKey, setExportingKey] = useState<string | null>(null);

  const [cashflow, setCashflow] = useState<FinanceCashflowPayload | null>(null);
  const [purchases, setPurchases] = useState<PurchaseData[]>([]);
  const [batches, setBatches] = useState<ProductionBatchData[]>([]);
  const [orders, setOrders] = useState<OrderData[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const isRangeValid = Boolean(periodFrom && periodTo && periodFrom <= periodTo);

  useEffect(() => {
    let mounted = true;

    async function loadRelatorios() {
      try {
        if (!isRangeValid) {
          throw new ApiError("Período inválido. Ajuste as datas inicial e final.", 400);
        }

        const [cashflowPayload, purchasesPayload, batchesPayload, ordersPayload] =
          await Promise.all([
            fetchFinanceCashflow(periodFrom, periodTo),
            listPurchasesAdmin(),
            listProductionBatchesAdmin(),
            listOrdersAdmin(),
          ]);

        if (!mounted) {
          return;
        }

        setCashflow(cashflowPayload);
        setPurchases(purchasesPayload);
        setBatches(batchesPayload);
        setOrders(ordersPayload);
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

    void loadRelatorios();

    return () => {
      mounted = false;
    };
  }, [periodFrom, periodTo, isRangeValid]);

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

  const cashflowOutByDay = useMemo(() => {
    if (!cashflow) {
      return {} as Record<string, number>;
    }

    return sumByDateKey(
      cashflow.items,
      (item) => item.date,
      (item) => Number(item.total_out) || 0,
    );
  }, [cashflow]);

  const cashflowOutSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, cashflowOutByDay);
    return values.length > 0 ? values : [0, 0, 0];
  }, [cashflowOutByDay, trendDateKeys]);

  const filteredPurchases = useMemo(() => {
    if (!isRangeValid) {
      return [];
    }

    return purchases.filter((purchase) => {
      if (!purchase.purchase_date) {
        return false;
      }
      return purchase.purchase_date >= periodFrom && purchase.purchase_date <= periodTo;
    });
  }, [isRangeValid, periodFrom, periodTo, purchases]);

  const purchaseTotalsByDay = useMemo(
    () =>
      sumByDateKey(
        filteredPurchases,
        (purchase) => purchase.purchase_date,
        (purchase) => Number(purchase.total_amount) || 0,
      ),
    [filteredPurchases],
  );

  const purchaseSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, purchaseTotalsByDay);
    return values.length > 0 ? values : [0, 0];
  }, [purchaseTotalsByDay, trendDateKeys]);

  const supplierValues = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const purchase of filteredPurchases) {
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
  }, [filteredPurchases]);

  const filteredBatches = useMemo(() => {
    if (!isRangeValid) {
      return [];
    }

    return batches.filter((batch) => {
      if (!batch.production_date) {
        return false;
      }
      return batch.production_date >= periodFrom && batch.production_date <= periodTo;
    });
  }, [batches, isRangeValid, periodFrom, periodTo]);

  const productionTotalsByDay = useMemo(
    () => sumByDateKey(filteredBatches, (batch) => batch.production_date, sumPlanned),
    [filteredBatches],
  );

  const productionSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, productionTotalsByDay);
    return values.length > 0 ? values : [0, 0];
  }, [productionTotalsByDay, trendDateKeys]);

  const productionWasteSeries = useMemo(() => {
    const values = filteredBatches
      .slice()
      .sort((a, b) => b.production_date.localeCompare(a.production_date))
      .slice(0, 5)
      .map((batch) => sumWaste(batch));

    return values.length > 0 ? values : [0, 0, 0];
  }, [filteredBatches]);

  const filteredOrders = useMemo(() => {
    if (!isRangeValid) {
      return [];
    }

    return orders.filter((order) => {
      if (!order.delivery_date) {
        return false;
      }
      return order.delivery_date >= periodFrom && order.delivery_date <= periodTo;
    });
  }, [isRangeValid, orders, periodFrom, periodTo]);

  const ordersByDay = useMemo(
    () => sumByDateKey(filteredOrders, (order) => order.delivery_date, () => 1),
    [filteredOrders],
  );

  const ordersSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, ordersByDay);
    return values.length > 0 ? values : [0, 0];
  }, [ordersByDay, trendDateKeys]);

  const paymentValues = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const order of filteredOrders) {
      for (const payment of order.payments) {
        totals[payment.method] = (totals[payment.method] ?? 0) + 1;
      }
    }

    const values = Object.values(totals)
      .sort((a, b) => b - a)
      .slice(0, 5);

    return values.length > 0 ? values : [0, 0, 0];
  }, [filteredOrders]);

  const showAll = activeSection === "all";

  const downloadCsv = async (
    key: string,
    request: () => Promise<{ blob: Blob; filename: string }>,
  ) => {
    setExportingKey(key);
    try {
      const { blob, filename } = await request();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setExportingKey(null);
    }
  };

  return (
    <>
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-text">Período de análise</h2>
        <p className="mt-1 text-sm text-muted">Defina o intervalo para os relatórios e exportações.</p>
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-2 text-sm font-medium text-text">
            Data inicial
            <input
              type="date"
              value={periodFrom}
              onChange={(event) => setPeriodFrom(event.target.value)}
              className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm font-medium text-text">
            Data final
            <input
              type="date"
              value={periodTo}
              onChange={(event) => setPeriodTo(event.target.value)}
              className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            />
          </label>
          {!isRangeValid && (
            <span className="rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700">
              Período inválido
            </span>
          )}
        </div>
      </section>

      {(showAll || activeSection === "fluxo-caixa") && (
        <section id="fluxo-caixa" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Fluxo de caixa global</h2>
              <p className="mt-1 text-sm text-muted">Entradas, saídas e saldo consolidado.</p>
            </div>
            <StatusPill tone="brand">Caixa mensal</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando fluxo de caixa...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Saldo por período</p>
                <Sparkline values={cashflowSeries} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Saídas por dia</p>
                <div className="mt-4">
                  <MiniBarChart values={cashflowOutSeries} />
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "compras") && (
        <section id="compras" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Compras integradas</h2>
              <p className="mt-1 text-sm text-muted">Impacto no caixa e itens de maior custo.</p>
            </div>
            <StatusPill tone="warning">Compras {filteredPurchases.length}</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando compras...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compras semanais</p>
                <Sparkline values={purchaseSeries} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Top fornecedores</p>
                <div className="mt-4">
                  <MiniBarChart values={supplierValues} />
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "producao") && (
        <section id="producao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Produção consolidada</h2>
              <p className="mt-1 text-sm text-muted">Planejado x produzido e perdas operacionais.</p>
            </div>
            <StatusPill tone="info">Lotes {filteredBatches.length}</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando produção...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Volume produzido</p>
                <Sparkline values={productionSeries} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Perdas por etapa</p>
                <div className="mt-4">
                  <MiniBarChart values={productionWasteSeries} />
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "pedidos") && (
        <section id="pedidos" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Pedidos consolidados</h2>
              <p className="mt-1 text-sm text-muted">Status por período e ticket médio.</p>
            </div>
            <StatusPill tone="success">Pedidos {filteredOrders.length}</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando pedidos...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos por dia</p>
                <Sparkline values={ordersSeries} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Métodos de pagamento</p>
                <div className="mt-4">
                  <MiniBarChart values={paymentValues} />
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "exportacao") && (
        <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Exportação CSV</h2>
          <p className="mt-1 text-sm text-muted">
            Exporte relatórios consolidados para auditoria e análise gerencial.
          </p>
          <div className="mt-3 text-xs text-muted">
            Período atual: {periodFrom} até {periodTo}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={!isRangeValid || exportingKey === "cashflow"}
              onClick={() =>
                downloadCsv("cashflow", () => exportFinanceCashflowCsv(periodFrom, periodTo))
              }
            >
              {exportingKey === "cashflow" ? "Exportando fluxo de caixa..." : "Exportar fluxo de caixa"}
            </button>
            <button
              type="button"
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
              disabled={!isRangeValid || exportingKey === "purchases"}
              onClick={() =>
                downloadCsv("purchases", () => exportPurchasesCsv(periodFrom, periodTo))
              }
            >
              {exportingKey === "purchases" ? "Exportando compras..." : "Exportar compras"}
            </button>
            <button
              type="button"
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
              disabled={!isRangeValid || exportingKey === "production"}
              onClick={() =>
                downloadCsv("production", () => exportProductionCsv(periodFrom, periodTo))
              }
            >
              {exportingKey === "production" ? "Exportando produção..." : "Exportar produção"}
            </button>
            <button
              type="button"
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
              disabled={!isRangeValid || exportingKey === "orders"}
              onClick={() => downloadCsv("orders", () => exportOrdersCsv(periodFrom, periodTo))}
            >
              {exportingKey === "orders" ? "Exportando pedidos..." : "Exportar pedidos"}
            </button>
            <button
              type="button"
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
              disabled={!isRangeValid || exportingKey === "dre"}
              onClick={() => downloadCsv("dre", () => exportFinanceDreCsv(periodFrom, periodTo))}
            >
              {exportingKey === "dre" ? "Exportando DRE..." : "Exportar DRE"}
            </button>
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
