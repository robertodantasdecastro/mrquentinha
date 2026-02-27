"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";
import { InlinePreloader } from "@/components/InlinePreloader";

import {
  ApiError,
  listStockItems,
  listStockMovements,
} from "@/lib/api";
import {
  buildRecentDateKeys,
  buildSeriesFromTotals,
  sumByDateKey,
  normalizeDateKey,
} from "@/lib/metrics";
import type { StockItemData, StockMovementData } from "@/types/api";

import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { InventoryOpsPanel } from "@/components/modules/InventoryOpsPanel";

export const ESTOQUE_BASE_PATH = "/modulos/estoque";

export const ESTOQUE_MENU_ITEMS = [
  { key: "all", label: "Todos", href: ESTOQUE_BASE_PATH },
  { key: "visao-geral", label: "Visão geral", href: `${ESTOQUE_BASE_PATH}/visao-geral#visao-geral` },
  { key: "movimentos", label: "Movimentos", href: `${ESTOQUE_BASE_PATH}/movimentos#movimentos` },
  { key: "tendencias", label: "Tendências", href: `${ESTOQUE_BASE_PATH}/tendencias#tendencias` },
];

export type EstoqueSectionKey =
  | "all"
  | "visao-geral"
  | "movimentos"
  | "tendencias";

type EstoqueSectionsProps = {
  activeSection?: EstoqueSectionKey;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar dados de estoque.";
}

function isLowStock(item: StockItemData): boolean {
  if (item.min_qty === null) {
    return false;
  }

  return Number(item.balance_qty) <= Number(item.min_qty);
}

export function EstoqueSections({ activeSection = "all" }: EstoqueSectionsProps) {
  const [stockItems, setStockItems] = useState<StockItemData[]>([]);
  const [movements, setMovements] = useState<StockMovementData[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const todayKey = useMemo(() => normalizeDateKey(new Date()), []);

  useEffect(() => {
    let mounted = true;

    async function loadEstoque() {
      try {
        const [itemsPayload, movementsPayload] = await Promise.all([
          listStockItems(),
          listStockMovements(),
        ]);

        if (!mounted) {
          return;
        }

        setStockItems(itemsPayload);
        setMovements(movementsPayload);
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

    void loadEstoque();

    return () => {
      mounted = false;
    };
  }, []);

  const alertCount = useMemo(
    () => stockItems.filter((item) => isLowStock(item)).length,
    [stockItems],
  );

  const reposicoesHoje = useMemo(
    () =>
      movements.filter(
        (movement) =>
          movement.movement_type === "IN" &&
          normalizeDateKey(movement.created_at) === todayKey,
      ).length,
    [movements, todayKey],
  );

  const trendDateKeys = useMemo(() => buildRecentDateKeys(7), []);
  const consumoTotalsByDay = useMemo(
    () =>
      sumByDateKey(
        movements.filter((movement) => movement.movement_type === "OUT"),
        (movement) => movement.created_at,
        (movement) => Number(movement.qty) || 0,
      ),
    [movements],
  );

  const reposicaoTotalsByDay = useMemo(
    () =>
      sumByDateKey(
        movements.filter((movement) => movement.movement_type === "IN"),
        (movement) => movement.created_at,
        (movement) => Number(movement.qty) || 0,
      ),
    [movements],
  );

  const consumoSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, consumoTotalsByDay);
    return values.length > 0 ? values : [0, 0];
  }, [consumoTotalsByDay, trendDateKeys]);

  const reposicaoSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys.slice(-5), reposicaoTotalsByDay);
    return values.length > 0 ? values : [0, 0, 0];
  }, [reposicaoTotalsByDay, trendDateKeys]);

  const showAll = activeSection === "all";

  return (
    <>
      {(showAll || activeSection === "visao-geral") && (
        <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Visão geral</h2>
              <p className="mt-1 text-sm text-muted">Itens críticos e reposição planejada.</p>
            </div>
            <StatusPill tone="warning">{alertCount} alertas</StatusPill>
          </div>
          {loading && <InlinePreloader message="Carregando resumo de estoque..." className="mt-3 justify-start bg-surface/70" />}
          {!loading && (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Itens em alerta</p>
                <p className="mt-1 text-2xl font-semibold text-text">{alertCount}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Reposições hoje</p>
                <p className="mt-1 text-2xl font-semibold text-text">{reposicoesHoje}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Itens cadastrados</p>
                <p className="mt-1 text-2xl font-semibold text-text">{stockItems.length}</p>
              </article>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "movimentos") && (
        <section id="movimentos" className="scroll-mt-24">
          <InventoryOpsPanel />
        </section>
      )}

      {(showAll || activeSection === "tendencias") && (
        <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Tendências de consumo</h2>
              <p className="mt-1 text-sm text-muted">Saídas diárias e reposição planejada.</p>
            </div>
            <StatusPill tone="info">{movements.length} movimentos</StatusPill>
          </div>
          {loading && <InlinePreloader message="Carregando tendências..." className="mt-3 justify-start bg-surface/70" />}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Consumo semanal</p>
                <Sparkline values={consumoSeries} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Reposições por dia</p>
                <div className="mt-4">
                  <MiniBarChart values={reposicaoSeries} />
                </div>
              </div>
            </div>
          )}
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
