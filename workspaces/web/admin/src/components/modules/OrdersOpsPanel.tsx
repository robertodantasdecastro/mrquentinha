"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";
import { InlinePreloader } from "@/components/InlinePreloader";

import {
  ApiError,
  listOrdersAdmin,
  updateOrderStatusAdmin,
} from "@/lib/api";
import { formatOrderStatusLabel } from "@/lib/labels";
import type { OrderData, OrderStatus } from "@/types/api";

const STATUS_OPTIONS: OrderStatus[] = [
  "CREATED",
  "CONFIRMED",
  "IN_PROGRESS",
  "OUT_FOR_DELIVERY",
  "DELIVERED",
  "RECEIVED",
  "CANCELED",
];

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

function formatDate(dateRaw: string): string {
  const normalizedRaw = dateRaw.includes("T") ? dateRaw : `${dateRaw}T00:00:00`;
  const dateValue = new Date(normalizedRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return dateRaw;
  }

  return dateValue.toLocaleDateString("pt-BR");
}

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar pedidos.";
}

function resolveOrderStatusTone(status: OrderStatus): StatusTone {
  if (status === "CREATED" || status === "CONFIRMED") {
    return "warning";
  }

  if (status === "IN_PROGRESS") {
    return "info";
  }

  if (status === "OUT_FOR_DELIVERY") {
    return "warning";
  }

  if (status === "DELIVERED") {
    return "success";
  }

  if (status === "RECEIVED") {
    return "success";
  }

  return "danger";
}

export function OrdersOpsPanel() {
  const [orders, setOrders] = useState<OrderData[]>([]);
  const [statusDrafts, setStatusDrafts] = useState<Record<number, OrderStatus>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [updatingOrderId, setUpdatingOrderId] = useState<number | null>(null);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const pendingCount = useMemo(
    () =>
      orders.filter((order) =>
        ["CREATED", "CONFIRMED", "IN_PROGRESS", "OUT_FOR_DELIVERY"].includes(
          order.status,
        ),
      ).length,
    [orders],
  );

  const deliveredCount = useMemo(
    () =>
      orders.filter((order) =>
        ["DELIVERED", "RECEIVED"].includes(order.status),
      ).length,
    [orders],
  );

  async function loadOrders({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const payload = await listOrdersAdmin();
      setOrders(payload);
      setStatusDrafts((current) => {
        const nextDrafts: Record<number, OrderStatus> = {};
        for (const order of payload) {
          nextDrafts[order.id] = current[order.id] ?? order.status;
        }
        return nextDrafts;
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
    void loadOrders();
  }, []);

  async function handleStatusSave(orderId: number) {
    const nextStatus = statusDrafts[orderId];
    if (!nextStatus) {
      return;
    }

    setUpdatingOrderId(orderId);
    setMessage("");
    setErrorMessage("");

    try {
      const updatedOrder = await updateOrderStatusAdmin(orderId, nextStatus);
      setOrders((current) =>
        current.map((order) => (order.id === orderId ? updatedOrder : order)),
      );
      setStatusDrafts((current) => ({ ...current, [orderId]: updatedOrder.status }));
      setMessage(
        `Pedido #${orderId} atualizado para ${formatOrderStatusLabel(updatedOrder.status)}.`,
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setUpdatingOrderId(null);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Pedidos</h3>
          <p className="text-sm text-muted">
            Acompanhamento da fila de pedidos e atualização de status operacional.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadOrders({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <article className="rounded-xl border border-border bg-bg p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Total</p>
          <p className="mt-1 text-2xl font-semibold text-text">{orders.length}</p>
        </article>
        <article className="rounded-xl border border-border bg-bg p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pendentes</p>
          <p className="mt-1 text-2xl font-semibold text-text">{pendingCount}</p>
        </article>
        <article className="rounded-xl border border-border bg-bg p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Entregues</p>
          <p className="mt-1 text-2xl font-semibold text-text">{deliveredCount}</p>
        </article>
      </div>

      {loading && <InlinePreloader message="Carregando pedidos..." className="mt-4 justify-start bg-surface/70" />}

      {!loading && orders.length === 0 && (
        <p className="mt-4 rounded-xl border border-border bg-bg p-4 text-sm text-muted">
          Nenhum pedido encontrado para o escopo atual.
        </p>
      )}

      {!loading && orders.length > 0 && (
        <div className="mt-4 space-y-3">
          {orders.map((order) => (
            <article key={order.id} className="rounded-xl border border-border bg-bg p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-text">Pedido #{order.id}</p>
                  <p className="mt-1 text-xs text-muted">
                    Entrega: {formatDate(order.delivery_date)} | Itens: {order.order_items.length}
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    Total: <strong className="text-text">{formatCurrency(order.total_amount)}</strong>
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <StatusPill tone={resolveOrderStatusTone(order.status)}>
                    {formatOrderStatusLabel(order.status)}
                  </StatusPill>
                  <select
                    value={statusDrafts[order.id] ?? order.status}
                    onChange={(event) => {
                      const nextStatus = event.currentTarget.value as OrderStatus;
                      setStatusDrafts((current) => ({
                        ...current,
                        [order.id]: nextStatus,
                      }));
                    }}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  >
                    {STATUS_OPTIONS.map((statusOption) => (
                      <option key={statusOption} value={statusOption}>
                        {formatOrderStatusLabel(statusOption)}
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    onClick={() => void handleStatusSave(order.id)}
                    disabled={updatingOrderId === order.id}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {updatingOrderId === order.id ? "Salvando..." : "Salvar"}
                  </button>
                </div>
              </div>
            </article>
          ))}
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
