"use client";

import { StatusPill, type StatusTone } from "@mrquentinha/ui";
import { formatCurrency } from "@/lib/format";
import type { CartItem } from "@/types/cart";
import type { OnlinePaymentMethod } from "@/types/api";

export type CheckoutState = "idle" | "submitting" | "success" | "error";

export type IntentPanelData = {
  orderId: number;
  paymentId: number;
  paymentMethod: OnlinePaymentMethod;
  status: string;
  provider: string;
  providerIntentRef: string | null;
  expiresAt: string | null;
  instructions: string[];
};

type CartDrawerProps = {
  items: CartItem[];
  totalAmount: number;
  checkoutState: CheckoutState;
  checkoutMessage: string;
  selectedPaymentMethod: OnlinePaymentMethod;
  onPaymentMethodChange: (method: OnlinePaymentMethod) => void;
  intentPanel: IntentPanelData | null;
  onRefreshIntent: () => void;
  isRefreshingIntent: boolean;
  onIncrement: (menuItemId: number) => void;
  onDecrement: (menuItemId: number) => void;
  onRemove: (menuItemId: number) => void;
  onCheckout: () => void;
  isCheckoutDisabled: boolean;
};

const PAYMENT_METHOD_OPTIONS: Array<{
  value: OnlinePaymentMethod;
  label: string;
  help: string;
}> = [
  {
    value: "PIX",
    label: "PIX",
    help: "Pagamento imediato com copia e cola.",
  },
  {
    value: "CARD",
    label: "Cartao",
    help: "Checkout online com token do provedor.",
  },
  {
    value: "VR",
    label: "VR",
    help: "Fluxo de autorizacao da rede de beneficios.",
  },
];

function getMessageStyles(state: CheckoutState): string {
  if (state === "success") {
    return "border border-emerald-300/70 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-300";
  }

  if (state === "error") {
    return "border border-red-300/70 bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-300";
  }

  return "border border-border bg-bg text-muted";
}

function formatDateTime(dateIso: string | null): string {
  if (!dateIso) {
    return "-";
  }

  const date = new Date(dateIso);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function resolveIntentTone(status: string): StatusTone {
  if (status === "SUCCEEDED") {
    return "success";
  }

  if (status === "REQUIRES_ACTION" || status === "PROCESSING") {
    return "warning";
  }

  if (status === "FAILED" || status === "CANCELED" || status === "EXPIRED") {
    return "danger";
  }

  return "neutral";
}

export function CartDrawer({
  items,
  totalAmount,
  checkoutState,
  checkoutMessage,
  selectedPaymentMethod,
  onPaymentMethodChange,
  intentPanel,
  onRefreshIntent,
  isRefreshingIntent,
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

      <div className="mt-4 rounded-xl border border-border bg-bg p-3">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">
          Metodo de pagamento
        </p>
        <div className="mt-2 grid gap-2">
          {PAYMENT_METHOD_OPTIONS.map((option) => {
            const isActive = selectedPaymentMethod === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => onPaymentMethodChange(option.value)}
                className={`rounded-lg border px-3 py-2 text-left transition ${
                  isActive
                    ? "border-primary bg-primary/10 text-text"
                    : "border-border bg-surface text-text hover:border-primary"
                }`}
              >
                <p className="text-sm font-semibold">{option.label}</p>
                <p className="text-xs text-muted">{option.help}</p>
              </button>
            );
          })}
        </div>
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

      {intentPanel && (
        <div className="mt-4 space-y-2 rounded-xl border border-border bg-bg p-4 text-sm text-muted">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-primary">
                Intent #{intentPanel.paymentId}
              </p>
              <p className="text-sm font-semibold text-text">
                Pedido #{intentPanel.orderId} · {intentPanel.paymentMethod}
              </p>
            </div>
            <button
              type="button"
              onClick={onRefreshIntent}
              disabled={isRefreshingIntent}
              className="rounded-full border border-border px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-text transition hover:border-primary disabled:cursor-not-allowed disabled:text-muted"
            >
              {isRefreshingIntent ? "Atualizando..." : "Atualizar"}
            </button>
          </div>

          <div className="flex items-center gap-2">
            <p>Status:</p>
            <StatusPill tone={resolveIntentTone(intentPanel.status)}>{intentPanel.status}</StatusPill>
          </div>
          <p>Provider: {intentPanel.provider}</p>
          <p>Referencia: {intentPanel.providerIntentRef ?? "-"}</p>
          <p>Expira em: {formatDateTime(intentPanel.expiresAt)}</p>

          {intentPanel.instructions.length > 0 && (
            <div className="rounded-lg border border-border bg-surface p-3">
              {intentPanel.instructions.map((instruction) => (
                <p key={instruction} className="text-xs text-text">
                  {instruction}
                </p>
              ))}
            </div>
          )}
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
