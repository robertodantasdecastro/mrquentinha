"use client";

import { useEffect, useMemo, useState } from "react";

import {
  ApiError,
  listPurchaseRequestsAdmin,
  listPurchasesAdmin,
} from "@/lib/api";
import type {
  PurchaseData,
  PurchaseRequestData,
  ProcurementRequestStatus,
} from "@/types/api";

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

export function ProcurementOpsPanel() {
  const [requests, setRequests] = useState<PurchaseRequestData[]>([]);
  const [purchases, setPurchases] = useState<PurchaseData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
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

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Compras</h3>
          <p className="text-sm text-muted">
            Baseline de requisicoes e compras para controle operacional de abastecimento.
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

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Requisicoes recentes</h4>
              {requests.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhuma requisicao encontrada.</p>
              )}
              {requests.length > 0 && (
                <div className="mt-3 space-y-2">
                  {requests.slice(0, 10).map((requestItem) => (
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
                    </article>
                  ))}
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
