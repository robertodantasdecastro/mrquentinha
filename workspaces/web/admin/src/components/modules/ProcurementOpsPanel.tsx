"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import {
  ApiError,
  createPurchaseAdmin,
  generatePurchaseRequestFromMenuAdmin,
  listIngredientsAdmin,
  listMenuDaysAdmin,
  listPurchaseRequestsAdmin,
  listPurchasesAdmin,
  updatePurchaseRequestStatusAdmin,
} from "@/lib/api";
import { formatProcurementStatusLabel } from "@/lib/labels";
import type {
  IngredientData,
  IngredientUnit,
  MenuDayData,
  ProcurementRequestStatus,
  PurchaseData,
  PurchaseRequestData,
  PurchaseRequestFromMenuResultData,
} from "@/types/api";

const REQUEST_STATUS_OPTIONS: ProcurementRequestStatus[] = [
  "OPEN",
  "APPROVED",
  "BOUGHT",
  "CANCELED",
];

const UNIT_OPTIONS: IngredientUnit[] = ["g", "kg", "ml", "l", "unidade"];

type PurchaseItemDraft = {
  ingredientId: string;
  qty: string;
  unit: IngredientUnit;
  unitPrice: string;
  taxAmount: string;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar módulo de compras.";
}

function formatDate(valueRaw: string): string {
  const dateValue = new Date(valueRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleDateString("pt-BR");
}

function formatDateTime(valueRaw: string): string {
  const dateValue = new Date(valueRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleString("pt-BR");
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

function buildTodayDateIso(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  const local = new Date(now.getTime() - offset);
  return local.toISOString().slice(0, 10);
}

function countByStatus(
  items: PurchaseRequestData[],
  status: ProcurementRequestStatus,
): number {
  return items.filter((item) => item.status === status).length;
}

function resolveRequestStatusTone(status: ProcurementRequestStatus): StatusTone {
  if (status === "OPEN") {
    return "warning";
  }

  if (status === "APPROVED") {
    return "info";
  }

  if (status === "BOUGHT") {
    return "success";
  }

  return "danger";
}

function buildStatusDrafts(
  requests: PurchaseRequestData[],
): Record<number, ProcurementRequestStatus> {
  return requests.reduce<Record<number, ProcurementRequestStatus>>(
    (accumulator, requestItem) => {
      accumulator[requestItem.id] = requestItem.status;
      return accumulator;
    },
    {},
  );
}

function buildDefaultPurchaseItem(
  ingredients: IngredientData[],
): PurchaseItemDraft {
  const firstIngredient = ingredients[0];
  const defaultUnit = firstIngredient?.unit ?? "kg";

  return {
    ingredientId: firstIngredient ? String(firstIngredient.id) : "",
    qty: "",
    unit: defaultUnit,
    unitPrice: "",
    taxAmount: "",
  };
}

export function ProcurementOpsPanel() {
  const [requests, setRequests] = useState<PurchaseRequestData[]>([]);
  const [purchases, setPurchases] = useState<PurchaseData[]>([]);
  const [menuDays, setMenuDays] = useState<MenuDayData[]>([]);
  const [ingredients, setIngredients] = useState<IngredientData[]>([]);
  const [statusDrafts, setStatusDrafts] = useState<
    Record<number, ProcurementRequestStatus>
  >({});
  const [selectedMenuDayId, setSelectedMenuDayId] = useState<string>("");
  const [fromMenuResult, setFromMenuResult] =
    useState<PurchaseRequestFromMenuResultData | null>(null);

  const [supplierName, setSupplierName] = useState("");
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [purchaseDate, setPurchaseDate] = useState(buildTodayDateIso());
  const [purchaseItems, setPurchaseItems] = useState<PurchaseItemDraft[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [updatingRequestId, setUpdatingRequestId] = useState<number | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [creatingPurchase, setCreatingPurchase] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  async function loadProcurement({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [requestsPayload, purchasesPayload, menuDaysPayload, ingredientsPayload] =
        await Promise.all([
          listPurchaseRequestsAdmin(),
          listPurchasesAdmin(),
          listMenuDaysAdmin(),
          listIngredientsAdmin(),
        ]);

      const menuCandidates = menuDaysPayload.filter(
        (menuDay) => menuDay.menu_items.length > 0,
      );
      const activeIngredients = ingredientsPayload
        .filter((ingredient) => ingredient.is_active)
        .sort((left, right) => left.name.localeCompare(right.name, "pt-BR"));

      setRequests(requestsPayload);
      setPurchases(purchasesPayload);
      setMenuDays(menuCandidates);
      setIngredients(activeIngredients);

      setStatusDrafts((previous) => {
        const next = buildStatusDrafts(requestsPayload);
        for (const [requestIdRaw, status] of Object.entries(previous)) {
          const requestId = Number(requestIdRaw);
          if (next[requestId]) {
            next[requestId] = status;
          }
        }
        return next;
      });

      if (menuCandidates.length > 0) {
        const hasSelected = menuCandidates.some(
          (menuDay) => String(menuDay.id) === selectedMenuDayId,
        );
        if (!hasSelected) {
          setSelectedMenuDayId(String(menuCandidates[0].id));
        }
      } else {
        setSelectedMenuDayId("");
      }

      if (purchaseItems.length === 0) {
        setPurchaseItems([buildDefaultPurchaseItem(activeIngredients)]);
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
    void loadProcurement();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  function addPurchaseItemDraft() {
    setPurchaseItems((previous) => [
      ...previous,
      buildDefaultPurchaseItem(ingredients),
    ]);
  }

  function removePurchaseItemDraft(index: number) {
    setPurchaseItems((previous) => previous.filter((_, rowIndex) => rowIndex !== index));
  }

  function updatePurchaseItemDraft(
    index: number,
    patch: Partial<PurchaseItemDraft>,
  ) {
    setPurchaseItems((previous) =>
      previous.map((item, rowIndex) => {
        if (rowIndex !== index) {
          return item;
        }

        return {
          ...item,
          ...patch,
        };
      }),
    );
  }

  async function handleUpdateRequestStatus(requestItem: PurchaseRequestData) {
    const nextStatus = statusDrafts[requestItem.id] ?? requestItem.status;
    if (nextStatus === requestItem.status) {
      return;
    }

    setUpdatingRequestId(requestItem.id);
    setMessage("");
    setErrorMessage("");

    try {
      await updatePurchaseRequestStatusAdmin(requestItem.id, nextStatus);
      setMessage(
        `Requisição #${requestItem.id} atualizada para ${formatProcurementStatusLabel(nextStatus)}.`,
      );
      await loadProcurement({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setUpdatingRequestId(null);
    }
  }

  async function handleGenerateFromMenu(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setGenerating(true);
    setMessage("");
    setErrorMessage("");

    try {
      const parsedMenuDayId = Number.parseInt(selectedMenuDayId, 10);
      if (Number.isNaN(parsedMenuDayId) || parsedMenuDayId <= 0) {
        throw new Error("Selecione um cardápio válido para gerar a requisição.");
      }

      const result = await generatePurchaseRequestFromMenuAdmin(parsedMenuDayId);
      setFromMenuResult(result);
      setMessage(result.message);
      await loadProcurement({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setGenerating(false);
    }
  }

  async function handleCreatePurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreatingPurchase(true);
    setMessage("");
    setErrorMessage("");

    try {
      if (!supplierName.trim()) {
        throw new Error("Informe o fornecedor da compra.");
      }

      const payloadItems = purchaseItems
        .map((item) => ({
          ingredientId: Number.parseInt(item.ingredientId, 10),
          qty: item.qty.replace(",", ".").trim(),
          unit: item.unit,
          unitPrice: item.unitPrice.replace(",", ".").trim(),
          taxAmount: item.taxAmount.replace(",", ".").trim(),
        }))
        .filter(
          (item) =>
            item.ingredientId > 0 && item.qty !== "" && item.unitPrice !== "",
        );

      if (payloadItems.length === 0) {
        throw new Error("Adicione ao menos um item válido na compra.");
      }

      const ingredientIds = payloadItems.map((item) => item.ingredientId);
      if (ingredientIds.length !== new Set(ingredientIds).size) {
        throw new Error("Ingrediente duplicado na compra.");
      }

      await createPurchaseAdmin({
        supplier_name: supplierName.trim(),
        invoice_number: invoiceNumber.trim() || undefined,
        purchase_date: purchaseDate,
        items: payloadItems.map((item) => ({
          ingredient: item.ingredientId,
          qty: item.qty,
          unit: item.unit,
          unit_price: item.unitPrice,
          tax_amount: item.taxAmount || undefined,
        })),
      });

      setSupplierName("");
      setInvoiceNumber("");
      setPurchaseDate(buildTodayDateIso());
      setPurchaseItems([buildDefaultPurchaseItem(ingredients)]);
      setMessage("Compra registrada com sucesso e estoque atualizado.");
      await loadProcurement({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCreatingPurchase(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Compras</h3>
          <p className="text-sm text-muted">
            Gere requisições por cardápio e registre compras para alimentar estoque e produção.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadProcurement({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {loading && <p className="mt-4 text-sm text-muted">Carregando módulo de compras...</p>}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Requisições</p>
              <p className="mt-1 text-2xl font-semibold text-text">{requests.length}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Abertas</p>
              <p className="mt-1 text-2xl font-semibold text-text">{openRequests}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Aprovadas</p>
              <p className="mt-1 text-2xl font-semibold text-text">{approvedRequests}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Valor comprado</p>
              <p className="mt-1 text-sm font-semibold text-text">
                {totalPurchasesValue.toLocaleString("pt-BR", {
                  style: "currency",
                  currency: "BRL",
                })}
              </p>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Gerar requisição por cardápio</h4>
              {menuDays.length === 0 && (
                <p className="mt-3 text-sm text-muted">
                  Nenhum cardápio com itens disponível para gerar requisição.
                </p>
              )}

              {menuDays.length > 0 && (
                <form
                  onSubmit={(event) => void handleGenerateFromMenu(event)}
                  className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto]"
                >
                  <label className="grid gap-1 text-sm text-muted">
                    Cardápio do dia
                    <select
                      required
                      value={selectedMenuDayId}
                      onChange={(event) => setSelectedMenuDayId(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    >
                      {menuDays.map((menuDay) => (
                        <option key={menuDay.id} value={menuDay.id}>
                          {menuDay.title} ({formatDate(menuDay.menu_date)})
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="self-end">
                    <button
                      type="submit"
                      disabled={generating}
                      className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {generating ? "Gerando..." : "Gerar"}
                    </button>
                  </div>
                </form>
              )}

              {fromMenuResult && (
                <div className="mt-3 rounded-lg border border-border bg-surface p-3">
                  <p className="text-sm font-semibold text-text">
                    Resultado: {fromMenuResult.message}
                  </p>
                  <p className="text-xs text-muted">
                    PR: {fromMenuResult.purchase_request_id ?? "não criada"} | Itens: {fromMenuResult.items.length}
                  </p>
                  {fromMenuResult.items.length > 0 && (
                    <ul className="mt-2 space-y-1 text-xs text-muted">
                      {fromMenuResult.items.slice(0, 8).map((item) => (
                        <li key={item.ingredient_id}>
                          {item.ingredient_name}: {item.required_qty} {item.unit}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Registrar compra</h4>
              <p className="mt-1 text-xs text-muted">
                O fluxo OCR continua disponível no backend; este formulário acelera o ciclo operacional.
              </p>
              <form onSubmit={(event) => void handleCreatePurchase(event)} className="mt-3 space-y-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="grid gap-1 text-sm text-muted">
                    Fornecedor
                    <input
                      required
                      value={supplierName}
                      onChange={(event) => setSupplierName(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="Ex.: Distribuidora Central"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Data da compra
                    <input
                      type="date"
                      required
                      value={purchaseDate}
                      onChange={(event) => setPurchaseDate(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    />
                  </label>
                </div>
                <label className="grid gap-1 text-sm text-muted">
                  Nota fiscal (opcional)
                  <input
                    value={invoiceNumber}
                    onChange={(event) => setInvoiceNumber(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="NF-000123"
                  />
                </label>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-text">Itens da compra</p>
                    <button
                      type="button"
                      onClick={addPurchaseItemDraft}
                      className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                    >
                      + Item
                    </button>
                  </div>
                  {purchaseItems.map((item, index) => (
                    <div key={`${index}-${item.ingredientId}`} className="grid gap-2 md:grid-cols-12">
                      <select
                        value={item.ingredientId}
                        onChange={(event) => {
                          const nextIngredientId = event.currentTarget.value;
                          const ingredient = ingredients.find(
                            (candidate) => String(candidate.id) === nextIngredientId,
                          );
                          updatePurchaseItemDraft(index, {
                            ingredientId: nextIngredientId,
                            unit: ingredient?.unit ?? item.unit,
                          });
                        }}
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-4"
                      >
                        <option value="">Ingrediente</option>
                        {ingredients.map((ingredient) => (
                          <option key={ingredient.id} value={ingredient.id}>
                            {ingredient.name}
                          </option>
                        ))}
                      </select>
                      <input
                        value={item.qty}
                        onChange={(event) =>
                          updatePurchaseItemDraft(index, { qty: event.currentTarget.value })
                        }
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-2"
                        placeholder="Qtd"
                      />
                      <select
                        value={item.unit}
                        onChange={(event) =>
                          updatePurchaseItemDraft(index, {
                            unit: event.currentTarget.value as IngredientUnit,
                          })
                        }
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-2"
                      >
                        {UNIT_OPTIONS.map((unitOption) => (
                          <option key={unitOption} value={unitOption}>
                            {unitOption}
                          </option>
                        ))}
                      </select>
                      <input
                        value={item.unitPrice}
                        onChange={(event) =>
                          updatePurchaseItemDraft(index, { unitPrice: event.currentTarget.value })
                        }
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-2"
                        placeholder="Preço"
                      />
                      <input
                        value={item.taxAmount}
                        onChange={(event) =>
                          updatePurchaseItemDraft(index, { taxAmount: event.currentTarget.value })
                        }
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-1"
                        placeholder="Imp."
                      />
                      <button
                        type="button"
                        onClick={() => removePurchaseItemDraft(index)}
                        disabled={purchaseItems.length === 1}
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60 md:col-span-1"
                      >
                        X
                      </button>
                    </div>
                  ))}
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={creatingPurchase || ingredients.length === 0}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {creatingPurchase ? "Registrando..." : "Registrar compra"}
                  </button>
                </div>
              </form>
            </section>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Compras recentes</h4>
              {purchases.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhuma compra encontrada.</p>
              )}
              {purchases.length > 0 && (
                <div className="mt-3 space-y-2">
                  {purchases.slice(0, 10).map((purchase) => (
                    <article
                      key={purchase.id}
                      className="rounded-lg border border-border bg-surface px-3 py-2"
                    >
                      <p className="text-sm font-semibold text-text">{purchase.supplier_name}</p>
                      <p className="text-xs text-muted">
                        Data: {formatDate(purchase.purchase_date)} | Itens: {purchase.purchase_items.length}
                      </p>
                      <p className="text-xs text-muted">
                        Total: <strong className="text-text">{formatCurrency(purchase.total_amount)}</strong>
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Requisições recentes</h4>
              {requests.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhuma requisição encontrada.</p>
              )}
              {requests.length > 0 && (
                <div className="mt-3 space-y-2">
                  {requests.slice(0, 12).map((requestItem) => {
                    const selectedStatus = statusDrafts[requestItem.id] ?? requestItem.status;
                    const isDirty = selectedStatus !== requestItem.status;

                    return (
                      <article
                        key={requestItem.id}
                        className="rounded-lg border border-border bg-surface px-3 py-2"
                      >
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-text">PR #{requestItem.id}</p>
                          <StatusPill tone={resolveRequestStatusTone(requestItem.status)}>
                            {formatProcurementStatusLabel(requestItem.status)}
                          </StatusPill>
                        </div>
                        <p className="text-xs text-muted">
                          Itens: {requestItem.request_items.length} | Data: {formatDateTime(requestItem.requested_at)}
                        </p>

                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <select
                            value={selectedStatus}
                            onChange={(event) => {
                              const nextStatus =
                                event.currentTarget.value as ProcurementRequestStatus;
                              setStatusDrafts((previous) => ({
                                ...previous,
                                [requestItem.id]: nextStatus,
                              }));
                            }}
                            className="rounded-md border border-border bg-bg px-2 py-1 text-xs text-text"
                          >
                            {REQUEST_STATUS_OPTIONS.map((option) => (
                              <option key={option} value={option}>
                                {formatProcurementStatusLabel(option)}
                              </option>
                            ))}
                          </select>

                          <button
                            type="button"
                            onClick={() => void handleUpdateRequestStatus(requestItem)}
                            disabled={!isDirty || updatingRequestId === requestItem.id}
                            className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                          >
                            {updatingRequestId === requestItem.id ? "Salvando..." : "Salvar status"}
                          </button>
                        </div>
                      </article>
                    );
                  })}
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
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}
    </section>
  );
}
