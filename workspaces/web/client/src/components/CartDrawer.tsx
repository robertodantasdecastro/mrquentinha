"use client";

import { formatCurrency } from "@/lib/format";
import type { CartItem } from "@/types/cart";

export type CheckoutState = "idle" | "submitting" | "success" | "error";

type CartDrawerProps = {
  items: CartItem[];
  totalAmount: number;
  checkoutState: CheckoutState;
  checkoutMessage: string;
  onIncrement: (menuItemId: number) => void;
  onDecrement: (menuItemId: number) => void;
  onRemove: (menuItemId: number) => void;
  onCheckout: () => void;
  isCheckoutDisabled: boolean;
};

function getMessageStyles(state: CheckoutState): string {
  if (state === "success") {
    return "border border-emerald-300/70 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-300";
  }

  if (state === "error") {
    return "border border-red-300/70 bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-300";
  }

  return "border border-border bg-bg text-muted";
}

export function CartDrawer({
  items,
  totalAmount,
  checkoutState,
  checkoutMessage,
  onIncrement,
  onDecrement,
  onRemove,
  onCheckout,
  isCheckoutDisabled,
}: CartDrawerProps) {
  return (
    <aside className="rounded-2xl border border-border bg-surface/85 p-5 shadow-sm lg:sticky lg:top-24 lg:h-fit">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-bold text-text">Carrinho</h2>
        <span className="rounded-full bg-bg px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-muted">
          {items.length} itens
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {items.length === 0 && (
          <div className="rounded-xl border border-border bg-bg px-4 py-6 text-center text-sm text-muted">
            Adicione pratos do cardapio para montar seu pedido.
          </div>
        )}

        {items.map((item) => (
          <article key={item.menuItemId} className="rounded-xl border border-border bg-bg p-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-text">{item.dishName}</h3>
                <p className="text-xs text-muted">{formatCurrency(item.unitPrice)} por unidade</p>
              </div>

              <button
                type="button"
                onClick={() => onRemove(item.menuItemId)}
                className="text-xs font-semibold uppercase tracking-[0.1em] text-muted transition hover:text-red-500"
              >
                Remover
              </button>
            </div>

            <div className="mt-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => onDecrement(item.menuItemId)}
                  className="rounded-full border border-border bg-surface px-2 py-1 text-sm font-semibold text-text transition hover:border-primary"
                  aria-label={`Diminuir quantidade de ${item.dishName}`}
                >
                  -
                </button>
                <span className="min-w-8 text-center text-sm font-semibold text-text">{item.qty}</span>
                <button
                  type="button"
                  onClick={() => onIncrement(item.menuItemId)}
                  className="rounded-full border border-border bg-surface px-2 py-1 text-sm font-semibold text-text transition hover:border-primary"
                  aria-label={`Aumentar quantidade de ${item.dishName}`}
                >
                  +
                </button>
              </div>

              <p className="text-sm font-semibold text-primary">
                {formatCurrency(Number(item.unitPrice) * item.qty)}
              </p>
            </div>
          </article>
        ))}
      </div>

      <div className="mt-4 rounded-xl border border-border bg-bg px-4 py-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted">Total estimado</span>
          <strong className="text-base text-text">{formatCurrency(totalAmount)}</strong>
        </div>
      </div>

      {checkoutMessage && (
        <div className={`mt-4 rounded-xl px-4 py-3 text-sm ${getMessageStyles(checkoutState)}`}>
          {checkoutMessage}
        </div>
      )}

      <button
        type="button"
        onClick={onCheckout}
        disabled={isCheckoutDisabled}
        className="mt-4 w-full rounded-full bg-primary px-4 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-white transition hover:bg-primary-soft disabled:cursor-not-allowed disabled:bg-border disabled:text-muted"
      >
        {checkoutState === "submitting" ? "Enviando..." : "Finalizar pedido"}
      </button>
    </aside>
  );
}
