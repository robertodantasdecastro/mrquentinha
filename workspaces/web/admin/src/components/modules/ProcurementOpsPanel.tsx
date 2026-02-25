"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import {
  ApiError,
  generatePurchaseRequestFromMenuAdmin,
  listPurchaseRequestsAdmin,
  listPurchasesAdmin,
  updatePurchaseRequestStatusAdmin,
} from "@/lib/api";
import type {
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

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar modulo de compras.";
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

function countByStatus(
  items: PurchaseRequestData[],
  status: ProcurementRequestStatus,
): number {
  return items.filter((item) => item.status === status).length;
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

export function ProcurementOpsPanel() {
  const [requests, setRequests] = useState<PurchaseRequestData[]>([]);
  const [purchases, setPurchases] = useState<PurchaseData[]>([]);
  const [statusDrafts, setStatusDrafts] = useState<
    Record<number, ProcurementRequestStatus>
  >({});
  const [menuDayId, setMenuDayId] = useState<string>("");
  const [fromMenuResult, setFromMenuResult] =
    useState<PurchaseRequestFromMenuResultData | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [updatingRequestId, setUpdatingRequestId] = useState<number | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  async function loadProcurement({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [requestsPayload, purchasesPayload] = await Promise.all([
        listPurchaseRequestsAdmin(),
        listPurchasesAdmin(),
      ]);

      setRequests(requestsPayload);
      setPurchases(purchasesPayload);
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
      setMessage(`Requisicao #${requestItem.id} atualizada para ${nextStatus}.`);
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
      const parsedMenuDayId = Number.parseInt(menuDayId, 10);
      if (Number.isNaN(parsedMenuDayId) || parsedMenuDayId <= 0) {
        throw new Error("Informe um menu_day_id valido para gerar requisicao.");
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

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Compras</h3>
          <p className="text-sm text-muted">
            Fluxo operacional de requisicoes com geracao por menu e mudanca de status.
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

      {loading && <p className="mt-4 text-sm text-muted">Carregando modulo de compras...</p>}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Requisicoes</p>
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
              <h4 className="text-base font-semibold text-text">Gerar requisicao por menu</h4>
              <form
                onSubmit={(event) => void handleGenerateFromMenu(event)}
                className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto]"
              >
                <label className="grid gap-1 text-sm text-muted">
                  menu_day_id
                  <input
                    type="number"
                    min={1}
                    required
                    value={menuDayId}
                    onChange={(event) => setMenuDayId(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="Ex.: 12"
                  />
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

              {fromMenuResult && (
                <div className="mt-3 rounded-lg border border-border bg-surface p-3">
                  <p className="text-sm font-semibold text-text">
                    Resultado: {fromMenuResult.message}
                  </p>
                  <p className="text-xs text-muted">
                    PR: {fromMenuResult.purchase_request_id ?? "nao criada"} | Itens: {fromMenuResult.items.length}
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
          </div>

          <section className="mt-4 rounded-xl border border-border bg-bg p-4">
            <h4 className="text-base font-semibold text-text">Requisicoes recentes</h4>
            {requests.length === 0 && (
              <p className="mt-3 text-sm text-muted">Nenhuma requisicao encontrada.</p>
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
                      <p className="text-sm font-semibold text-text">
                        PR #{requestItem.id} - {requestItem.status}
                      </p>
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
                              {option}
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
