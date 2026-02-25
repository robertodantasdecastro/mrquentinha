"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import {
  ApiError,
  completeProductionBatchAdmin,
  createProductionBatchAdmin,
  listMenuDaysAdmin,
  listProductionBatchesAdmin,
} from "@/lib/api";
import type {
  CreateProductionBatchPayload,
  MenuDayData,
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

function resolveBatchStatusTone(status: ProductionBatchStatus): StatusTone {
  if (status === "PLANNED") {
    return "warning";
  }

  if (status === "IN_PROGRESS") {
    return "info";
  }

  if (status === "DONE") {
    return "success";
  }

  return "danger";
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

function buildQuantityDrafts(menuDay: MenuDayData): Record<number, string> {
  return menuDay.menu_items.reduce<Record<number, string>>((accumulator, menuItem) => {
    const defaultQty =
      menuItem.available_qty !== null && menuItem.available_qty > 0
        ? menuItem.available_qty
        : 10;
    accumulator[menuItem.id] = String(defaultQty);
    return accumulator;
  }, {});
}

export function ProductionOpsPanel() {
  const [batches, setBatches] = useState<ProductionBatchData[]>([]);
  const [menuDays, setMenuDays] = useState<MenuDayData[]>([]);
  const [selectedMenuDayId, setSelectedMenuDayId] = useState<string>("");
  const [qtyDrafts, setQtyDrafts] = useState<Record<number, string>>({});
  const [batchNote, setBatchNote] = useState<string>("");

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [creating, setCreating] = useState<boolean>(false);
  const [completingBatchId, setCompletingBatchId] = useState<number | null>(null);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  async function loadProduction({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [batchesPayload, menuDaysPayload] = await Promise.all([
        listProductionBatchesAdmin(),
        listMenuDaysAdmin(),
      ]);

      const menuCandidates = menuDaysPayload.filter(
        (menuDay) => menuDay.menu_items.length > 0,
      );

      setBatches(batchesPayload);
      setMenuDays(menuCandidates);

      if (menuCandidates.length > 0) {
        const currentSelectedId = Number.parseInt(selectedMenuDayId, 10);
        const selectedMenu =
          menuCandidates.find((menuDay) => menuDay.id === currentSelectedId) ??
          menuCandidates[0];

        setSelectedMenuDayId(String(selectedMenu.id));
        setQtyDrafts((previous) => {
          const defaults = buildQuantityDrafts(selectedMenu);
          for (const menuItem of selectedMenu.menu_items) {
            if (previous[menuItem.id]) {
              defaults[menuItem.id] = previous[menuItem.id];
            }
          }
          return defaults;
        });
      } else {
        setSelectedMenuDayId("");
        setQtyDrafts({});
      }

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedMenuDay = useMemo(() => {
    const parsedId = Number.parseInt(selectedMenuDayId, 10);
    if (Number.isNaN(parsedId)) {
      return null;
    }

    return menuDays.find((menuDay) => menuDay.id === parsedId) ?? null;
  }, [menuDays, selectedMenuDayId]);

  const plannedCount = useMemo(() => countByStatus(batches, "PLANNED"), [batches]);
  const inProgressCount = useMemo(
    () => countByStatus(batches, "IN_PROGRESS"),
    [batches],
  );
  const doneCount = useMemo(() => countByStatus(batches, "DONE"), [batches]);

  function handleSelectMenuDay(nextMenuDayId: string) {
    setSelectedMenuDayId(nextMenuDayId);

    const nextMenuDay = menuDays.find((menuDay) => String(menuDay.id) === nextMenuDayId);
    if (nextMenuDay) {
      setQtyDrafts(buildQuantityDrafts(nextMenuDay));
    } else {
      setQtyDrafts({});
    }
  }

  async function handleCreateBatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedMenuDay) {
      setErrorMessage("Selecione um cardapio com itens para criar o lote.");
      return;
    }

    setCreating(true);
    setMessage("");
    setErrorMessage("");

    try {
      const items: CreateProductionBatchPayload["items"] = selectedMenuDay.menu_items.map(
        (menuItem) => {
          const qtyValue = Number.parseInt(qtyDrafts[menuItem.id] ?? "", 10);
          if (Number.isNaN(qtyValue) || qtyValue <= 0) {
            throw new Error(`Quantidade invalida para ${menuItem.dish.name}.`);
          }

          return {
            menu_item: menuItem.id,
            qty_planned: qtyValue,
          };
        },
      );

      await createProductionBatchAdmin({
        production_date: selectedMenuDay.menu_date,
        note: batchNote.trim() ? batchNote.trim() : undefined,
        items,
      });

      setMessage("Lote criado com sucesso.");
      setBatchNote("");
      await loadProduction({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCreating(false);
    }
  }

  async function handleCompleteBatch(batch: ProductionBatchData) {
    if (batch.status === "DONE" || batch.status === "CANCELED") {
      return;
    }

    setCompletingBatchId(batch.id);
    setMessage("");
    setErrorMessage("");

    try {
      await completeProductionBatchAdmin(batch.id);
      setMessage(`Lote #${batch.id} concluido com sucesso.`);
      await loadProduction({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCompletingBatchId(null);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Produção</h3>
          <p className="text-sm text-muted">
            Fluxo operacional: criar lotes por cardapio e concluir execucao do dia.
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

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Criar lote por cardapio</h4>

              {menuDays.length === 0 && (
                <p className="mt-3 text-sm text-muted">
                  Nenhum cardapio com itens disponivel para criar lote.
                </p>
              )}

              {menuDays.length > 0 && (
                <form
                  onSubmit={(event) => void handleCreateBatch(event)}
                  className="mt-3 space-y-3"
                >
                  <label className="grid gap-1 text-sm text-muted">
                    Cardapio do dia
                    <select
                      value={selectedMenuDayId}
                      onChange={(event) => handleSelectMenuDay(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    >
                      {menuDays.map((menuDay) => (
                        <option key={menuDay.id} value={menuDay.id}>
                          {menuDay.title} ({formatDate(menuDay.menu_date)})
                        </option>
                      ))}
                    </select>
                  </label>

                  {selectedMenuDay && (
                    <div className="space-y-2">
                      {selectedMenuDay.menu_items.map((menuItem) => (
                        <article
                          key={menuItem.id}
                          className="rounded-lg border border-border bg-surface px-3 py-2"
                        >
                          <p className="text-sm font-semibold text-text">{menuItem.dish.name}</p>
                          <label className="mt-1 grid gap-1 text-xs text-muted">
                            Quantidade planejada
                            <input
                              type="number"
                              min={1}
                              value={qtyDrafts[menuItem.id] ?? ""}
                              onChange={(event) => {
                                const nextQty = event.currentTarget.value;
                                setQtyDrafts((previous) => ({
                                  ...previous,
                                  [menuItem.id]: nextQty,
                                }));
                              }}
                              className="rounded-md border border-border bg-bg px-2 py-1 text-sm text-text"
                            />
                          </label>
                        </article>
                      ))}
                    </div>
                  )}

                  <label className="grid gap-1 text-sm text-muted">
                    Observacao
                    <input
                      value={batchNote}
                      onChange={(event) => setBatchNote(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="Lote da semana"
                    />
                  </label>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={creating || !selectedMenuDay}
                      className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {creating ? "Criando..." : "Criar lote"}
                    </button>
                  </div>
                </form>
              )}
            </section>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Lotes recentes</h4>
              {batches.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhum lote de producao encontrado.</p>
              )}
              {batches.length > 0 && (
                <div className="mt-3 space-y-2">
                  {batches.slice(0, 12).map((batch) => (
                    <article
                      key={batch.id}
                      className="rounded-lg border border-border bg-surface px-3 py-2"
                    >
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-text">Lote #{batch.id}</p>
                        <StatusPill tone={resolveBatchStatusTone(batch.status)}>
                          {batch.status}
                        </StatusPill>
                      </div>
                      <p className="text-xs text-muted">
                        Data: {formatDate(batch.production_date)} | Itens: {batch.production_items.length}
                      </p>
                      <p className="text-xs text-muted">
                        Planejado: {sumPlannedByBatch(batch)} | Produzido: {sumProducedByBatch(batch)}
                      </p>

                      <div className="mt-2">
                        <button
                          type="button"
                          onClick={() => void handleCompleteBatch(batch)}
                          disabled={
                            batch.status === "DONE" ||
                            batch.status === "CANCELED" ||
                            completingBatchId === batch.id
                          }
                          className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                        >
                          {completingBatchId === batch.id
                            ? "Concluindo..."
                            : batch.status === "DONE"
                              ? "Concluido"
                              : "Concluir lote"}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </div>
        </>
      )}

      {message && (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-xl border border-border bg-bg px-4 py-3 text-sm">
          <p className="text-rose-600">{errorMessage}</p>
        </div>
      )}
    </section>
  );
}
