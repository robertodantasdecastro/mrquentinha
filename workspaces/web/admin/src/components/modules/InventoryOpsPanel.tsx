"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { InlinePreloader } from "@/components/InlinePreloader";

import {
  ApiError,
  createStockMovement,
  listStockItems,
  listStockMovements,
} from "@/lib/api";
import type {
  CreateStockMovementPayload,
  StockItemData,
  StockMovementData,
} from "@/types/api";

const MOVEMENT_TYPES: Array<CreateStockMovementPayload["movement_type"]> = [
  "IN",
  "OUT",
  "ADJUST",
];

const REFERENCE_TYPES: Array<CreateStockMovementPayload["reference_type"]> = [
  "PURCHASE",
  "CONSUMPTION",
  "ADJUSTMENT",
  "PRODUCTION",
];

const UNIT_OPTIONS: Array<CreateStockMovementPayload["unit"]> = [
  "g",
  "kg",
  "ml",
  "l",
  "unidade",
];

function formatDecimal(value: string): string {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return value;
  }

  return numericValue.toLocaleString("pt-BR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
}

function formatDateTime(valueRaw: string): string {
  const dateValue = new Date(valueRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleString("pt-BR");
}

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar estoque.";
}

export function InventoryOpsPanel() {
  const [stockItems, setStockItems] = useState<StockItemData[]>([]);
  const [movements, setMovements] = useState<StockMovementData[]>([]);
  const [ingredientId, setIngredientId] = useState<string>("");
  const [movementType, setMovementType] = useState<CreateStockMovementPayload["movement_type"]>("IN");
  const [qty, setQty] = useState<string>("1.000");
  const [unit, setUnit] = useState<CreateStockMovementPayload["unit"]>("kg");
  const [referenceType, setReferenceType] = useState<CreateStockMovementPayload["reference_type"]>("PURCHASE");
  const [referenceId, setReferenceId] = useState<string>("");
  const [note, setNote] = useState<string>("");

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const lowStockItems = useMemo(
    () =>
      stockItems.filter((item) => {
        if (item.min_qty === null) {
          return false;
        }
        return Number(item.balance_qty) <= Number(item.min_qty);
      }),
    [stockItems],
  );

  async function loadInventory({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [itemsPayload, movementsPayload] = await Promise.all([
        listStockItems(),
        listStockMovements(),
      ]);

      setStockItems(itemsPayload);
      setMovements(movementsPayload.slice(0, 15));

      if (!ingredientId && itemsPayload.length > 0) {
        const firstItem = itemsPayload[0];
        setIngredientId(String(firstItem.ingredient));
        setUnit(firstItem.unit);
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
    void loadInventory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleIngredientChange(nextIngredientId: string) {
    setIngredientId(nextIngredientId);

    const selectedItem = stockItems.find(
      (item) => String(item.ingredient) === nextIngredientId,
    );

    if (selectedItem) {
      setUnit(selectedItem.unit);
    }
  }

  async function handleCreateMovement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setErrorMessage("");

    try {
      const payload: CreateStockMovementPayload = {
        ingredient: Number(ingredientId),
        movement_type: movementType,
        qty,
        unit,
        reference_type: referenceType,
      };

      if (referenceId.trim()) {
        payload.reference_id = Number(referenceId);
      }

      if (note.trim()) {
        payload.note = note.trim();
      }

      await createStockMovement(payload);
      setMessage("Movimento registrado com sucesso.");
      setQty("1.000");
      setReferenceId("");
      setNote("");
      await loadInventory({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Estoque</h3>
          <p className="text-sm text-muted">
            Saldo por ingrediente e registro de movimentos operacionais.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadInventory({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <article className="rounded-xl border border-border bg-bg p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Itens em estoque</p>
          <p className="mt-1 text-2xl font-semibold text-text">{stockItems.length}</p>
        </article>

        <article className="rounded-xl border border-border bg-bg p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Alertas de minimo</p>
          <p className="mt-1 text-2xl font-semibold text-text">{lowStockItems.length}</p>
        </article>

        <article className="rounded-xl border border-border bg-bg p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Movimentos recentes</p>
          <p className="mt-1 text-2xl font-semibold text-text">{movements.length}</p>
        </article>
      </div>

      <form
        onSubmit={(event) => void handleCreateMovement(event)}
        className="mt-4 grid gap-3 rounded-xl border border-border bg-bg p-4 md:grid-cols-2"
      >
        <label className="grid gap-1 text-sm text-muted">
          Ingrediente
          <select
            required
            value={ingredientId}
            onChange={(event) => handleIngredientChange(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          >
            <option value="" disabled>
              Selecione...
            </option>
            {stockItems.map((item) => (
              <option key={item.id} value={item.ingredient}>
                {item.ingredient_name}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1 text-sm text-muted">
          Tipo de movimento
          <select
            value={movementType}
            onChange={(event) =>
              setMovementType(event.currentTarget.value as CreateStockMovementPayload["movement_type"])
            }
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          >
            {MOVEMENT_TYPES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1 text-sm text-muted">
          Quantidade
          <input
            required
            value={qty}
            onChange={(event) => setQty(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="1.000"
          />
        </label>

        <label className="grid gap-1 text-sm text-muted">
          Unidade
          <select
            value={unit}
            onChange={(event) =>
              setUnit(event.currentTarget.value as CreateStockMovementPayload["unit"])
            }
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          >
            {UNIT_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1 text-sm text-muted">
          Referencia
          <select
            value={referenceType}
            onChange={(event) =>
              setReferenceType(event.currentTarget.value as CreateStockMovementPayload["reference_type"])
            }
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          >
            {REFERENCE_TYPES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1 text-sm text-muted">
          ID da referencia (opcional)
          <input
            value={referenceId}
            onChange={(event) => setReferenceId(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="123"
          />
        </label>

        <label className="md:col-span-2 grid gap-1 text-sm text-muted">
          Observacao
          <input
            value={note}
            onChange={(event) => setNote(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="Entrada de compra semanal"
          />
        </label>

        <div className="md:col-span-2 flex justify-end">
          <button
            type="submit"
            disabled={saving || !ingredientId}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {saving ? "Salvando..." : "Registrar movimento"}
          </button>
        </div>
      </form>

      {loading && <InlinePreloader message="Carregando estoque..." className="mt-4 justify-start bg-surface/70" />}

      {!loading && (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <section className="rounded-xl border border-border bg-bg p-4">
            <h4 className="text-base font-semibold text-text">Saldo por ingrediente</h4>
            {stockItems.length === 0 && (
              <p className="mt-3 text-sm text-muted">Nenhum item de estoque encontrado.</p>
            )}
            {stockItems.length > 0 && (
              <div className="mt-3 space-y-2">
                {stockItems.slice(0, 12).map((item) => (
                  <article
                    key={item.id}
                    className="rounded-lg border border-border bg-surface px-3 py-2"
                  >
                    <p className="text-sm font-semibold text-text">{item.ingredient_name}</p>
                    <p className="text-xs text-muted">
                      Saldo: {formatDecimal(item.balance_qty)} {item.unit}
                    </p>
                    {item.min_qty !== null && (
                      <p className="text-xs text-muted">Minimo: {formatDecimal(item.min_qty)} {item.unit}</p>
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-xl border border-border bg-bg p-4">
            <h4 className="text-base font-semibold text-text">Movimentos recentes</h4>
            {movements.length === 0 && (
              <p className="mt-3 text-sm text-muted">Nenhum movimento registrado.</p>
            )}
            {movements.length > 0 && (
              <div className="mt-3 space-y-2">
                {movements.map((movement) => (
                  <article
                    key={movement.id}
                    className="rounded-lg border border-border bg-surface px-3 py-2"
                  >
                    <p className="text-sm font-semibold text-text">
                      {movement.movement_type} - {movement.ingredient_name}
                    </p>
                    <p className="text-xs text-muted">
                      {formatDecimal(movement.qty)} {movement.unit} | {movement.reference_type}
                    </p>
                    <p className="text-xs text-muted">Data: {formatDateTime(movement.created_at)}</p>
                  </article>
                ))}
              </div>
            )}
          </section>
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
