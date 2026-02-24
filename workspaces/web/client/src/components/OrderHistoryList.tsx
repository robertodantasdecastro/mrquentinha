"use client";

import { useEffect, useMemo, useState } from "react";

import { ApiError, getDemoCustomerId, listOrders } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { getRememberedOrderIds } from "@/lib/storage";
import type { OrderData } from "@/types/api";

type HistoryState = "loading" | "ready" | "error";
type FilterMode = "customer" | "remembered" | "all";

type FilterResult = {
  orders: OrderData[];
  mode: FilterMode;
};

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

function applyDemoFilter(orders: OrderData[]): FilterResult {
  const demoCustomerId = getDemoCustomerId();
  const rememberedIds = getRememberedOrderIds();

  if (demoCustomerId !== null) {
    const customerOrders = orders.filter(
      (order) => order.customer === demoCustomerId,
    );
    if (customerOrders.length > 0) {
      return { orders: customerOrders, mode: "customer" };
    }
  }

  if (rememberedIds.length > 0) {
    const rememberedOrders = orders.filter((order) =>
      rememberedIds.includes(order.id),
    );

    if (rememberedOrders.length > 0) {
      return { orders: rememberedOrders, mode: "remembered" };
    }
  }

  return { orders, mode: "all" };
}

export function OrderHistoryList() {
  const [historyState, setHistoryState] = useState<HistoryState>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [orders, setOrders] = useState<OrderData[]>([]);
  const [filterMode, setFilterMode] = useState<FilterMode>("all");

  useEffect(() => {
    let mounted = true;

    async function loadOrders() {
      setHistoryState("loading");
      setErrorMessage("");

      try {
        const payload = await listOrders();
        if (!mounted) {
          return;
        }

        const filtered = applyDemoFilter(payload);

        setOrders(filtered.orders);
        setFilterMode(filtered.mode);
        setHistoryState("ready");
      } catch (error) {
        if (!mounted) {
          return;
        }

        setOrders([]);
        setHistoryState("error");
        setErrorMessage(resolveErrorMessage(error));
      }
    }

    loadOrders();

    return () => {
      mounted = false;
    };
  }, []);

  const sortedOrders = useMemo(
    () =>
      [...orders].sort(
        (first, second) =>
          new Date(second.created_at).getTime() - new Date(first.created_at).getTime(),
      ),
    [orders],
  );

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-5 shadow-sm">
      <div className="mb-4 flex flex-col gap-2">
        <h2 className="text-xl font-bold text-text">Historico de pedidos</h2>
        <p className="text-sm text-muted">
          {filterMode === "customer" &&
            "Filtro aplicado por customer demo via NEXT_PUBLIC_DEMO_CUSTOMER_ID."}
          {filterMode === "remembered" &&
            "Filtro aplicado pelos pedidos criados neste navegador (modo demo)."}
          {filterMode === "all" &&
            "MVP sem auth: exibindo pedidos retornados pela API sem filtro seguro."}
        </p>
      </div>

      {historyState === "loading" && (
        <div className="rounded-xl border border-border bg-bg px-4 py-10 text-center text-sm text-muted">
          Carregando pedidos...
        </div>
      )}

      {historyState === "error" && (
        <div className="rounded-xl border border-red-300/70 bg-red-50 px-4 py-4 text-sm text-red-700 dark:bg-red-950/20 dark:text-red-300">
          {errorMessage}
        </div>
      )}

      {historyState === "ready" && sortedOrders.length === 0 && (
        <div className="rounded-xl border border-border bg-bg px-4 py-8 text-center text-sm text-muted">
          Nenhum pedido encontrado para o modo demo.
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
                  <p className="rounded-full border border-border bg-surface px-3 py-1 text-xs font-semibold uppercase tracking-[0.1em] text-muted">
                    {order.status}
                  </p>
                  <p className="mt-1 text-sm font-semibold text-text">
                    {formatCurrency(order.total_amount)}
                  </p>
                </div>
              </div>

              {order.order_items.length > 0 && (
                <ul className="mt-3 space-y-1 text-sm text-muted">
                  {order.order_items.map((item) => (
                    <li key={item.id}>
                      {item.menu_item_name} x{item.qty}
                    </li>
                  ))}
                </ul>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
