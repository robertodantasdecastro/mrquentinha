"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import { InlinePreloader } from "@/components/InlinePreloader";
import { ApiError, confirmOrderReceipt, listOrders } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { OrderData, OrderStatus } from "@/types/api";

type HistoryState = "loading" | "ready" | "unauthorized" | "error";

function formatDate(dateValue: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(`${dateValue}T12:00:00`));
}

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha ao carregar os pedidos.";
}

function resolveOrderTone(status: OrderStatus): StatusTone {
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

  if (status === "CANCELED") {
    return "danger";
  }

  return "neutral";
}

function formatOrderStatusLabel(status: OrderStatus): string {
  switch (status) {
    case "CREATED":
      return "Criado";
    case "CONFIRMED":
      return "Confirmado";
    case "IN_PROGRESS":
      return "Em preparo";
    case "OUT_FOR_DELIVERY":
      return "Saiu para entrega";
    case "DELIVERED":
      return "Entregue";
    case "RECEIVED":
      return "Recebido";
    case "CANCELED":
      return "Cancelado";
    default:
      return status;
  }
}

function resolvePaymentTone(status: string): StatusTone {
  if (status === "PAID" || status === "SUCCEEDED") {
    return "success";
  }

  if (status === "PENDING" || status === "PROCESSING") {
    return "warning";
  }

  if (status === "FAILED" || status === "CANCELED" || status === "REFUNDED") {
    return "danger";
  }

  return "neutral";
}

export function OrderHistoryList() {
  const [historyState, setHistoryState] = useState<HistoryState>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [orders, setOrders] = useState<OrderData[]>([]);
  const [confirmingOrderId, setConfirmingOrderId] = useState<number | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const loadOrders = useCallback(async () => {
    setIsRefreshing(true);

    try {
      const payload = await listOrders();
      setOrders(payload);
      setHistoryState("ready");
      setErrorMessage("");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setOrders([]);
        setHistoryState("unauthorized");
        setErrorMessage(
          "Sessao nao autenticada. Acesse a aba Conta para entrar e ver seu historico.",
        );
        return;
      }

      setOrders([]);
      setHistoryState("error");
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    setHistoryState("loading");
    void loadOrders();
  }, [loadOrders]);

  useEffect(() => {
    if (historyState !== "ready") {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadOrders();
    }, 30000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [historyState, loadOrders]);

  const sortedOrders = useMemo(
    () =>
      [...orders].sort(
        (first, second) =>
          new Date(second.created_at).getTime() - new Date(first.created_at).getTime(),
      ),
    [orders],
  );

  async function handleConfirmReceipt(orderId: number) {
    setConfirmingOrderId(orderId);
    setErrorMessage("");

    try {
      const updated = await confirmOrderReceipt(orderId);
      setOrders((current) =>
        current.map((order) => (order.id === orderId ? updated : order)),
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setConfirmingOrderId(null);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-5 shadow-sm">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-text">Historico de pedidos</h2>
          <p className="text-sm text-muted">
            Esta lista utiliza o escopo da sua conta autenticada no backend.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadOrders()}
          disabled={isRefreshing || historyState === "loading"}
          className="rounded-full border border-border bg-bg px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.08em] text-muted transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isRefreshing ? "Atualizando..." : "Atualizar lista"}
        </button>
      </div>

      {historyState === "loading" && (
        <InlinePreloader message="Carregando pedidos..." className="py-10" />
      )}

      {historyState === "unauthorized" && (
        <div className="rounded-xl border border-amber-300/70 bg-amber-50 px-4 py-4 text-sm text-amber-700 dark:bg-amber-950/20 dark:text-amber-300">
          <p>{errorMessage}</p>
          <Link
            href="/conta"
            className="mt-2 inline-flex rounded-full border border-amber-500/60 px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em]"
          >
            Ir para conta
          </Link>
        </div>
      )}

      {historyState === "error" && (
        <div className="rounded-xl border border-red-300/70 bg-red-50 px-4 py-4 text-sm text-red-700 dark:bg-red-950/20 dark:text-red-300">
          {errorMessage}
        </div>
      )}

      {historyState === "ready" && sortedOrders.length === 0 && (
        <div className="rounded-xl border border-border bg-bg px-4 py-8 text-center text-sm text-muted">
          Nenhum pedido encontrado para sua conta.
        </div>
      )}

      {historyState === "ready" && sortedOrders.length > 0 && (
        <div className="space-y-3">
          {sortedOrders.map((order) => (
            <article key={order.id} className="rounded-xl border border-border bg-bg p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-primary">
                    Pedido #{order.id}
                  </p>
                  <p className="text-sm text-muted">
                    Entrega: {formatDate(order.delivery_date)}
                  </p>
                </div>

                <div className="text-right">
                  <StatusPill tone={resolveOrderTone(order.status)}>
                    {formatOrderStatusLabel(order.status)}
                  </StatusPill>
                  <p className="mt-1 text-sm font-semibold text-text">
                    {formatCurrency(order.total_amount)}
                  </p>
                </div>
              </div>

              {order.status === "DELIVERED" && (
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() => void handleConfirmReceipt(order.id)}
                    disabled={confirmingOrderId === order.id}
                    className="rounded-md bg-primary px-3 py-2 text-xs font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {confirmingOrderId === order.id
                      ? "Confirmando..."
                      : "Confirmar recebimento"}
                  </button>
                </div>
              )}

              {order.order_items.length > 0 && (
                <ul className="mt-3 space-y-1 text-sm text-muted">
                  {order.order_items.map((item) => (
                    <li key={item.id}>
                      {item.menu_item_name} x{item.qty}
                    </li>
                  ))}
                </ul>
              )}

              {order.payments.length > 0 && (
                <div className="mt-3 rounded-lg border border-border bg-surface p-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">
                    Pagamentos
                  </p>
                  <div className="mt-2 space-y-1 text-sm text-text">
                    {order.payments.map((payment) => (
                      <div key={payment.id} className="flex flex-wrap items-center gap-2">
                        <p>
                          #{payment.id} · {payment.method} · {formatCurrency(payment.amount)}
                        </p>
                        <StatusPill tone={resolvePaymentTone(payment.status)}>
                          {payment.status}
                        </StatusPill>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      {historyState === "ready" && errorMessage && (
        <div className="mt-4 rounded-xl border border-red-300/70 bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950/20 dark:text-red-300">
          {errorMessage}
        </div>
      )}
    </section>
  );
}
