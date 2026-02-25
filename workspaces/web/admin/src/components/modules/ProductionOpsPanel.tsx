"use client";

import { useEffect, useMemo, useState } from "react";

import { ApiError, listProductionBatchesAdmin } from "@/lib/api";
import type {
  ProductionBatchData,
  ProductionBatchStatus,
} from "@/types/api";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar modulo de producao.";
}

function formatDate(valueRaw: string): string {
  const dateValue = new Date(`${valueRaw}T00:00:00`);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleDateString("pt-BR");
}

function countByStatus(
  batches: ProductionBatchData[],
  status: ProductionBatchStatus,
): number {
  return batches.filter((batch) => batch.status === status).length;
}

function sumPlannedByBatch(batch: ProductionBatchData): number {
  return batch.production_items.reduce((accumulator, item) => {
    return accumulator + item.qty_planned;
  }, 0);
}

function sumProducedByBatch(batch: ProductionBatchData): number {
  return batch.production_items.reduce((accumulator, item) => {
    return accumulator + item.qty_produced;
  }, 0);
}

export function ProductionOpsPanel() {
  const [batches, setBatches] = useState<ProductionBatchData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  async function loadProduction({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const payload = await listProductionBatchesAdmin();
      setBatches(payload);
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadProduction();
  }, []);

  const plannedCount = useMemo(() => countByStatus(batches, "PLANNED"), [batches]);
  const inProgressCount = useMemo(
    () => countByStatus(batches, "IN_PROGRESS"),
    [batches],
  );
  const doneCount = useMemo(() => countByStatus(batches, "DONE"), [batches]);

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Producao</h3>
          <p className="text-sm text-muted">
            Baseline de lotes por dia para acompanhamento de planejamento e execucao.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadProduction({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {loading && <p className="mt-4 text-sm text-muted">Carregando modulo de producao...</p>}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Lotes</p>
              <p className="mt-1 text-2xl font-semibold text-text">{batches.length}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Planejados</p>
              <p className="mt-1 text-2xl font-semibold text-text">{plannedCount}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Em progresso</p>
              <p className="mt-1 text-2xl font-semibold text-text">{inProgressCount}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Concluidos</p>
              <p className="mt-1 text-2xl font-semibold text-text">{doneCount}</p>
            </article>
          </div>

          <section className="mt-4 rounded-xl border border-border bg-bg p-4">
            <h4 className="text-base font-semibold text-text">Lotes recentes</h4>
            {batches.length === 0 && (
              <p className="mt-3 text-sm text-muted">Nenhum lote de producao encontrado.</p>
            )}
            {batches.length > 0 && (
              <div className="mt-3 space-y-2">
                {batches.slice(0, 10).map((batch) => (
                  <article
                    key={batch.id}
                    className="rounded-lg border border-border bg-surface px-3 py-2"
                  >
                    <p className="text-sm font-semibold text-text">
                      Lote #{batch.id} - {batch.status}
                    </p>
                    <p className="text-xs text-muted">
                      Data: {formatDate(batch.production_date)} | Itens: {batch.production_items.length}
                    </p>
                    <p className="text-xs text-muted">
                      Planejado: {sumPlannedByBatch(batch)} | Produzido: {sumProducedByBatch(batch)}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-xl border border-border bg-bg px-4 py-3 text-sm">
          <p className="text-rose-600">{errorMessage}</p>
        </div>
      )}
    </section>
  );
}
