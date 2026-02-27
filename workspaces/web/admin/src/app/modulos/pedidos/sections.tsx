"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";
import { InlinePreloader } from "@/components/InlinePreloader";

import { ApiError, exportOrdersCsv, listOrdersAdmin } from "@/lib/api";
import {
  buildRecentDateKeys,
  buildSeriesFromTotals,
  sumByDateKey,
  normalizeDateKey,
} from "@/lib/metrics";
import type { OrderData } from "@/types/api";

import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { OrdersOpsPanel } from "@/components/modules/OrdersOpsPanel";

export const PEDIDOS_BASE_PATH = "/modulos/pedidos";

export const PEDIDOS_MENU_ITEMS = [
  { key: "all", label: "Todos", href: PEDIDOS_BASE_PATH },
  { key: "visao-geral", label: "Visão geral", href: `${PEDIDOS_BASE_PATH}/visao-geral#visao-geral` },
  { key: "operacao", label: "Operação", href: `${PEDIDOS_BASE_PATH}/operacao#operacao` },
  { key: "tendencias", label: "Tendências", href: `${PEDIDOS_BASE_PATH}/tendencias#tendencias` },
  { key: "exportacao", label: "Exportação", href: `${PEDIDOS_BASE_PATH}/exportacao#exportacao` },
];

export type PedidosSectionKey =
  | "all"
  | "visao-geral"
  | "operacao"
  | "tendencias"
  | "exportacao";

type PedidosSectionsProps = {
  activeSection?: PedidosSectionKey;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar dados de pedidos.";
}

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

export function PedidosSections({ activeSection = "all" }: PedidosSectionsProps) {
  const [orders, setOrders] = useState<OrderData[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [exporting, setExporting] = useState(false);

  const range = useMemo(buildCurrentMonthRange, []);
  const [periodFrom, setPeriodFrom] = useState(range.from);
  const [periodTo, setPeriodTo] = useState(range.to);
  const isRangeValid = Boolean(periodFrom && periodTo && periodFrom <= periodTo);

  const todayKey = useMemo(() => normalizeDateKey(new Date()), []);

  useEffect(() => {
    let mounted = true;

    async function loadPedidos() {
      try {
        const payload = await listOrdersAdmin();

        if (!mounted) {
          return;
        }

        setOrders(payload);
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

    void loadPedidos();

    return () => {
      mounted = false;
    };
  }, []);

  const ordersHoje = useMemo(
    () => orders.filter((order) => order.delivery_date === todayKey),
    [orders, todayKey],
  );

  const pedidosAtivos = ordersHoje.filter((order) =>
    ["CREATED", "CONFIRMED", "IN_PROGRESS"].includes(order.status),
  ).length;

  const emPreparo = ordersHoje.filter((order) => order.status === "IN_PROGRESS").length;
  const entregues = ordersHoje.filter((order) => order.status === "DELIVERED").length;

  const trendDateKeys = useMemo(() => buildRecentDateKeys(7), []);
  const ordersByDay = useMemo(
    () => sumByDateKey(orders, (order) => order.delivery_date, () => 1),
    [orders],
  );

  const ordersSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, ordersByDay);
    return values.length > 0 ? values : [0, 0];
  }, [trendDateKeys, ordersByDay]);

  const paymentValues = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const order of orders) {
      for (const payment of order.payments) {
        totals[payment.method] = (totals[payment.method] ?? 0) + 1;
      }
    }

    const values = Object.values(totals)
      .sort((a, b) => b - a)
      .slice(0, 5);

    return values.length > 0 ? values : [0, 0, 0];
  }, [orders]);

  const showAll = activeSection === "all";

  const downloadCsv = async () => {
    if (!isRangeValid) {
      setErrorMessage("Período inválido. Ajuste as datas inicial e final.");
      return;
    }

    setExporting(true);
    try {
      const { blob, filename } = await exportOrdersCsv(periodFrom, periodTo);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setExporting(false);
    }
  };

  return (
    <>
      {(showAll || activeSection === "visao-geral") && (
        <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Visão geral</h2>
              <p className="mt-1 text-sm text-muted">
                Fluxo operacional do dia com foco em conversão e atendimento.
              </p>
            </div>
            <StatusPill tone="info">Hoje</StatusPill>
          </div>
          {loading && <InlinePreloader message="Carregando resumo de pedidos..." className="mt-3 justify-start bg-surface/70" />}
          {!loading && (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos ativos</p>
                <p className="mt-1 text-2xl font-semibold text-text">{pedidosAtivos}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Em preparo</p>
                <p className="mt-1 text-2xl font-semibold text-text">{emPreparo}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Entregues</p>
                <p className="mt-1 text-2xl font-semibold text-text">{entregues}</p>
              </article>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "operacao") && (
        <section id="operacao" className="scroll-mt-24">
          <OrdersOpsPanel />
        </section>
      )}

      {(showAll || activeSection === "tendencias") && (
        <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Tendências de pedidos</h2>
              <p className="mt-1 text-sm text-muted">Volume por hora e conversão nos últimos dias.</p>
            </div>
            <StatusPill tone="brand">{orders.length} pedidos</StatusPill>
          </div>
          {loading && <InlinePreloader message="Carregando tendências..." className="mt-3 justify-start bg-surface/70" />}
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
            Gere arquivos CSV com filtros aplicados para reconciliação financeira.
          </p>
          <div className="mt-3 flex flex-wrap items-end gap-3">
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
          <button
            type="button"
            onClick={() => void downloadCsv()}
            disabled={!isRangeValid || exporting}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {exporting ? "Exportando pedidos..." : "Exportar pedidos (CSV)"}
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
