"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { ApiError, listProductionBatchesAdmin } from "@/lib/api";
import {
  buildRecentDateKeys,
  buildSeriesFromTotals,
  sumByDateKey,
  normalizeDateKey,
} from "@/lib/metrics";
import type { ProductionBatchData } from "@/types/api";

import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { ProductionOpsPanel } from "@/components/modules/ProductionOpsPanel";

export const PRODUCAO_BASE_PATH = "/modulos/producao";

export const PRODUCAO_MENU_ITEMS = [
  { key: "all", label: "Todos", href: PRODUCAO_BASE_PATH },
  { key: "visao-geral", label: "Visão geral", href: `${PRODUCAO_BASE_PATH}/visao-geral#visao-geral` },
  { key: "lotes", label: "Lotes", href: `${PRODUCAO_BASE_PATH}/lotes#lotes` },
  { key: "tendencias", label: "Tendências", href: `${PRODUCAO_BASE_PATH}/tendencias#tendencias` },
  { key: "exportacao", label: "Exportação", href: `${PRODUCAO_BASE_PATH}/exportacao#exportacao` },
];

export type ProducaoSectionKey =
  | "all"
  | "visao-geral"
  | "lotes"
  | "tendencias"
  | "exportacao";

type ProducaoSectionsProps = {
  activeSection?: ProducaoSectionKey;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar dados de produção.";
}

function sumPlanned(batch: ProductionBatchData): number {
  return batch.production_items.reduce((accumulator, item) => {
    return accumulator + item.qty_planned;
  }, 0);
}

function sumProduced(batch: ProductionBatchData): number {
  return batch.production_items.reduce((accumulator, item) => {
    return accumulator + item.qty_produced;
  }, 0);
}

function sumWaste(batch: ProductionBatchData): number {
  return batch.production_items.reduce((accumulator, item) => {
    return accumulator + item.qty_waste;
  }, 0);
}

export function ProducaoSections({ activeSection = "all" }: ProducaoSectionsProps) {
  const [batches, setBatches] = useState<ProductionBatchData[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const todayKey = useMemo(() => normalizeDateKey(new Date()), []);

  useEffect(() => {
    let mounted = true;

    async function loadProducao() {
      try {
        const batchesPayload = await listProductionBatchesAdmin();

        if (!mounted) {
          return;
        }

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

    void loadProducao();

    return () => {
      mounted = false;
    };
  }, []);

  const batchesToday = useMemo(
    () => batches.filter((batch) => batch.production_date === todayKey),
    [batches, todayKey],
  );

  const lotesDoDia = batchesToday.length;
  const planejadoDia = batchesToday.reduce(
    (accumulator, batch) => accumulator + sumPlanned(batch),
    0,
  );
  const produzidoDia = batchesToday.reduce(
    (accumulator, batch) => accumulator + sumProduced(batch),
    0,
  );

  const trendDateKeys = useMemo(() => buildRecentDateKeys(7), []);
  const plannedTotalsByDay = useMemo(
    () => sumByDateKey(batches, (batch) => batch.production_date, sumPlanned),
    [batches],
  );

  const plannedSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, plannedTotalsByDay);
    return values.length > 0 ? values : [0, 0];
  }, [plannedTotalsByDay, trendDateKeys]);

  const wasteSeries = useMemo(() => {
    const values = batches
      .slice()
      .sort((a, b) => b.production_date.localeCompare(a.production_date))
      .slice(0, 5)
      .map((batch) => sumWaste(batch));

    return values.length > 0 ? values : [0, 0, 0];
  }, [batches]);

  const showAll = activeSection === "all";

  return (
    <>
      {(showAll || activeSection === "visao-geral") && (
        <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Visão geral</h2>
              <p className="mt-1 text-sm text-muted">Controle de lotes e alertas de divergência.</p>
            </div>
            <StatusPill tone="warning">{lotesDoDia} lotes hoje</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando resumo de produção...</p>}
          {!loading && (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Lotes do dia</p>
                <p className="mt-1 text-2xl font-semibold text-text">{lotesDoDia}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Planejado</p>
                <p className="mt-1 text-2xl font-semibold text-text">{planejadoDia}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Produzido</p>
                <p className="mt-1 text-2xl font-semibold text-text">{produzidoDia}</p>
              </article>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "lotes") && (
        <section id="lotes" className="scroll-mt-24">
          <ProductionOpsPanel />
        </section>
      )}

      {(showAll || activeSection === "tendencias") && (
        <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Tendências de produção</h2>
              <p className="mt-1 text-sm text-muted">Comparativo planejado x produzido por semana.</p>
            </div>
            <StatusPill tone="info">{batches.length} lotes</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando tendências...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Planejado x produzido</p>
                <Sparkline values={plannedSeries} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Perdas por lote</p>
                <div className="mt-4">
                  <MiniBarChart values={wasteSeries} />
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "exportacao") && (
        <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Exportação CSV</h2>
          <p className="mt-1 text-sm text-muted">Relatórios de produção para comparativo operacional.</p>
          <button
            type="button"
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
          >
            Exportar produção (CSV)
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
