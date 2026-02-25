"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import {
  ApiError,
  listPurchaseRequestsAdmin,
  listPurchasesAdmin,
} from "@/lib/api";
import {
  buildRecentDateKeys,
  buildSeriesFromTotals,
  sumByDateKey,
} from "@/lib/metrics";
import type {
  ProcurementRequestStatus,
  PurchaseData,
  PurchaseRequestData,
} from "@/types/api";

import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { ProcurementOpsPanel } from "@/components/modules/ProcurementOpsPanel";

export const COMPRAS_BASE_PATH = "/modulos/compras";

export const COMPRAS_MENU_ITEMS = [
  { key: "all", label: "Todos", href: COMPRAS_BASE_PATH },
  { key: "visao-geral", label: "Visão geral", href: `${COMPRAS_BASE_PATH}/visao-geral#visao-geral` },
  { key: "operacao", label: "Operação", href: `${COMPRAS_BASE_PATH}/operacao#operacao` },
  { key: "impacto", label: "Impacto", href: `${COMPRAS_BASE_PATH}/impacto#impacto` },
  { key: "exportacao", label: "Exportação", href: `${COMPRAS_BASE_PATH}/exportacao#exportacao` },
];

export type ComprasSectionKey =
  | "all"
  | "visao-geral"
  | "operacao"
  | "impacto"
  | "exportacao";

type ComprasSectionsProps = {
  activeSection?: ComprasSectionKey;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar dados de compras.";
}

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function countByStatus(
  requests: PurchaseRequestData[],
  status: ProcurementRequestStatus,
): number {
  return requests.filter((requestItem) => requestItem.status === status).length;
}

export function ComprasSections({ activeSection = "all" }: ComprasSectionsProps) {
  const [requests, setRequests] = useState<PurchaseRequestData[]>([]);
  const [purchases, setPurchases] = useState<PurchaseData[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadCompras() {
      try {
        const [requestsPayload, purchasesPayload] = await Promise.all([
          listPurchaseRequestsAdmin(),
          listPurchasesAdmin(),
        ]);

        if (!mounted) {
          return;
        }

        setRequests(requestsPayload);
        setPurchases(purchasesPayload);
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

    void loadCompras();

    return () => {
      mounted = false;
    };
  }, []);

  const openRequests = useMemo(() => countByStatus(requests, "OPEN"), [requests]);
  const approvedRequests = useMemo(
    () => countByStatus(requests, "APPROVED"),
    [requests],
  );

  const totalPurchasesValue = useMemo(() => {
    return purchases.reduce((accumulator, purchase) => {
      const amount = Number(purchase.total_amount);
      if (Number.isNaN(amount)) {
        return accumulator;
      }

      return accumulator + amount;
    }, 0);
  }, [purchases]);

  const trendDateKeys = useMemo(() => buildRecentDateKeys(7), []);
  const purchasesTotalsByDay = useMemo(
    () => sumByDateKey(purchases, (purchase) => purchase.purchase_date, (purchase) => Number(purchase.total_amount) || 0),
    [purchases],
  );
  const trendValues = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, purchasesTotalsByDay);
    return values.length > 0 ? values : [0, 0];
  }, [purchasesTotalsByDay, trendDateKeys]);

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
        <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Visão geral</h2>
              <p className="mt-1 text-sm text-muted">Acompanhe requisicoes abertas e compras do periodo.</p>
            </div>
            <StatusPill tone="warning">Pendencias {openRequests}</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando resumo de compras...</p>}
          {!loading && (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Requisicoes abertas</p>
                <p className="mt-1 text-2xl font-semibold text-text">{openRequests}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compras aprovadas</p>
                <p className="mt-1 text-2xl font-semibold text-text">{approvedRequests}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Valor comprado</p>
                <p className="mt-1 text-2xl font-semibold text-text">{formatCurrency(totalPurchasesValue)}</p>
              </article>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "operacao") && (
        <section id="operacao" className="scroll-mt-24">
          <ProcurementOpsPanel />
        </section>
      )}

      {(showAll || activeSection === "impacto") && (
        <section id="impacto" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Impacto financeiro</h2>
              <p className="mt-1 text-sm text-muted">Comparativo de fornecedores e itens criticos.</p>
            </div>
            <StatusPill tone="info">{purchases.length} compras</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando impacto...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compras por semana</p>
                <Sparkline values={trendValues} className="mt-3" />
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

      {(showAll || activeSection === "exportacao") && (
        <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Exportação CSV</h2>
          <p className="mt-1 text-sm text-muted">Gere relatorios de compras consolidados por periodo.</p>
          <button
            type="button"
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
          >
            Exportar compras (CSV)
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
