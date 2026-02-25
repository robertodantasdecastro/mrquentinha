"use client";

import { useEffect, useMemo, useState } from "react";

import {
  ApiError,
  createOrder,
  createPaymentIntent,
  fetchMenuByDate,
  getLatestPaymentIntent,
} from "@/lib/api";
import { getTodayIsoDate } from "@/lib/format";
import { hasStoredAuthSession, rememberOrderId } from "@/lib/storage";
import {
  CartDrawer,
  type CheckoutState,
  type IntentPanelData,
} from "@/components/CartDrawer";
import { MenuDayView, type MenuFetchState } from "@/components/MenuDayView";
import type {
  CreatedOrderResponse,
  MenuDayData,
  MenuItemData,
  OnlinePaymentMethod,
  PaymentIntentData,
  PaymentSummary,
} from "@/types/api";
import type { CartItem } from "@/types/cart";

type CartState = Record<number, CartItem>;

const ONLINE_PAYMENT_LABELS: Record<OnlinePaymentMethod, string> = {
  PIX: "PIX",
  CARD: "cartao",
  VR: "VR",
};

function parseErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada. Tente novamente.";
}

function resolveCheckoutStateByIntentStatus(status: string): CheckoutState {
  if (status === "SUCCEEDED") {
    return "success";
  }

  if (status === "FAILED" || status === "CANCELED" || status === "EXPIRED") {
    return "error";
  }

  return "idle";
}

function resolveOnlinePaymentMethod(
  paymentMethod: string,
  fallback: OnlinePaymentMethod,
): OnlinePaymentMethod {
  if (paymentMethod === "PIX" || paymentMethod === "CARD" || paymentMethod === "VR") {
    return paymentMethod;
  }

  return fallback;
}

function buildIntentInstructions(intent: PaymentIntentData): string[] {
  const payload = intent.client_payload;

  if (payload.method === "PIX" && payload.pix?.copy_paste_code) {
    return [
      `Pix copia e cola: ${payload.pix.copy_paste_code}`,
      payload.pix.qr_code ? `QR mock: ${payload.pix.qr_code}` : "",
    ].filter((item) => item.length > 0);
  }

  if (payload.method === "CARD") {
    return [
      payload.card?.checkout_token
        ? `Token do checkout: ${payload.card.checkout_token}`
        : "Token de checkout indisponivel.",
      payload.card?.requires_redirect
        ? "Fluxo de redirecionamento habilitado."
        : "Fluxo sem redirecionamento.",
    ];
  }

  if (payload.method === "VR") {
    return [
      payload.vr?.authorization_token
        ? `Token VR: ${payload.vr.authorization_token}`
        : "Token VR indisponivel.",
      payload.vr?.network ? `Rede: ${payload.vr.network}` : "",
    ].filter((item) => item.length > 0);
  }

  return [];
}

function buildIntentPanel(
  orderId: number,
  paymentMethod: OnlinePaymentMethod,
  paymentId: number,
  intent: PaymentIntentData,
): IntentPanelData {
  return {
    orderId,
    paymentId,
    paymentMethod,
    status: intent.status,
    provider: intent.provider,
    providerIntentRef: intent.provider_intent_ref,
    expiresAt: intent.expires_at,
    instructions: buildIntentInstructions(intent),
  };
}

function buildIdempotencyKey(orderId: number, paymentId: number): string {
  const randomPart =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  return `client-checkout-${orderId}-${paymentId}-${randomPart}`;
}

function resolvePrimaryPayment(
  createdOrder: CreatedOrderResponse,
): PaymentSummary | null {
  if (!Array.isArray(createdOrder.payments) || createdOrder.payments.length === 0) {
    return null;
  }

  return createdOrder.payments[0];
}

export function MenuPage() {
  const [selectedDate, setSelectedDate] = useState<string>(getTodayIsoDate());
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    hasStoredAuthSession(),
  );

  const [menu, setMenu] = useState<MenuDayData | null>(null);
  const [menuState, setMenuState] = useState<MenuFetchState>("loading");
  const [menuMessage, setMenuMessage] = useState<string>("Carregando cardapio...");

  const [cart, setCart] = useState<CartState>({});
  const [selectedPaymentMethod, setSelectedPaymentMethod] =
    useState<OnlinePaymentMethod>("PIX");
  const [checkoutState, setCheckoutState] = useState<CheckoutState>("idle");
  const [checkoutMessage, setCheckoutMessage] = useState<string>("");
  const [intentPanel, setIntentPanel] = useState<IntentPanelData | null>(null);
  const [isRefreshingIntent, setIsRefreshingIntent] = useState<boolean>(false);

  useEffect(() => {
    const syncAuthState = () => {
      setIsAuthenticated(hasStoredAuthSession());
    };

    syncAuthState();

    window.addEventListener("focus", syncAuthState);
    window.addEventListener("storage", syncAuthState);

    return () => {
      window.removeEventListener("focus", syncAuthState);
      window.removeEventListener("storage", syncAuthState);
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadMenu() {
      if (!selectedDate) {
        return;
      }

      setMenuState("loading");
      setMenuMessage("Carregando cardapio...");

      try {
        const payload = await fetchMenuByDate(selectedDate);

        if (!mounted) {
          return;
        }

        setMenu(payload);
        setMenuState("loaded");
        setMenuMessage("");
      } catch (error) {
        if (!mounted) {
          return;
        }

        if (error instanceof ApiError && error.status === 404) {
          setMenu(null);
          setMenuState("empty");
          setMenuMessage(`Sem cardapio cadastrado para ${selectedDate}.`);
          return;
        }

        setMenu(null);
        setMenuState("error");
        setMenuMessage(parseErrorMessage(error));
      }
    }

    loadMenu();

    return () => {
      mounted = false;
    };
  }, [selectedDate]);

  const cartItems = useMemo(
    () =>
      Object.values(cart).sort((firstItem, secondItem) =>
        firstItem.dishName.localeCompare(secondItem.dishName),
      ),
    [cart],
  );

  const cartQtyByItem = useMemo(() => {
    const qtyByItem: Record<number, number> = {};

    for (const item of cartItems) {
      qtyByItem[item.menuItemId] = item.qty;
    }

    return qtyByItem;
  }, [cartItems]);

  const totalAmount = useMemo(
    () =>
      cartItems.reduce(
        (total, item) => total + Number(item.unitPrice) * item.qty,
        0,
      ),
    [cartItems],
  );

  const isCheckoutDisabled =
    cartItems.length === 0 || checkoutState === "submitting" || !selectedDate;

  const addToCart = (menuItem: MenuItemData) => {
    let reachedLimit = false;

    setCart((currentCart) => {
      const existingItem = currentCart[menuItem.id];
      const nextQty = (existingItem?.qty ?? 0) + 1;

      if (menuItem.available_qty !== null && nextQty > menuItem.available_qty) {
        reachedLimit = true;
        return currentCart;
      }

      return {
        ...currentCart,
        [menuItem.id]: {
          menuItemId: menuItem.id,
          dishName: menuItem.dish.name,
          unitPrice: menuItem.sale_price,
          qty: nextQty,
          availableQty: menuItem.available_qty,
        },
      };
    });

    if (reachedLimit) {
      setCheckoutState("error");
      setCheckoutMessage("Quantidade maxima disponivel para este item foi atingida.");
      return;
    }

    if (checkoutState === "error") {
      setCheckoutState("idle");
      setCheckoutMessage("");
    }
  };

  const incrementCartItem = (menuItemId: number) => {
    setCart((currentCart) => {
      const item = currentCart[menuItemId];
      if (!item) {
        return currentCart;
      }

      if (item.availableQty !== null && item.qty >= item.availableQty) {
        return currentCart;
      }

      return {
        ...currentCart,
        [menuItemId]: {
          ...item,
          qty: item.qty + 1,
        },
      };
    });
  };

  const decrementCartItem = (menuItemId: number) => {
    setCart((currentCart) => {
      const item = currentCart[menuItemId];
      if (!item) {
        return currentCart;
      }

      if (item.qty <= 1) {
        const nextCart = { ...currentCart };
        delete nextCart[menuItemId];
        return nextCart;
      }

      return {
        ...currentCart,
        [menuItemId]: {
          ...item,
          qty: item.qty - 1,
        },
      };
    });
  };

  const removeCartItem = (menuItemId: number) => {
    setCart((currentCart) => {
      const nextCart = { ...currentCart };
      delete nextCart[menuItemId];
      return nextCart;
    });
  };

  const refreshLatestIntent = async () => {
    if (!intentPanel) {
      return;
    }

    setIsRefreshingIntent(true);

    try {
      const latestIntent = await getLatestPaymentIntent(intentPanel.paymentId);
      const nextPanel = buildIntentPanel(
        intentPanel.orderId,
        intentPanel.paymentMethod,
        intentPanel.paymentId,
        latestIntent,
      );

      setIntentPanel(nextPanel);
      setCheckoutState(resolveCheckoutStateByIntentStatus(latestIntent.status));
      setCheckoutMessage(`Intent atualizado: ${latestIntent.status}.`);
    } catch (error) {
      setCheckoutState("error");
      setCheckoutMessage(parseErrorMessage(error));
    } finally {
      setIsRefreshingIntent(false);
    }
  };

  const checkout = async () => {
    if (cartItems.length === 0) {
      setCheckoutState("error");
      setCheckoutMessage("Selecione ao menos um item antes de finalizar.");
      return;
    }

    setCheckoutState("submitting");
    setCheckoutMessage("Criando pedido e preparando pagamento online...");

    try {
      const createdOrder = await createOrder(
        selectedDate,
        cartItems.map((item) => ({
          menu_item_id: item.menuItemId,
          qty: item.qty,
        })),
        selectedPaymentMethod,
      );

      rememberOrderId(createdOrder.id);

      const primaryPayment = resolvePrimaryPayment(createdOrder);
      if (!primaryPayment) {
        setCart({});
        setIntentPanel(null);
        setCheckoutState("success");
        setCheckoutMessage(
          `Pedido #${createdOrder.id} criado com sucesso. Pagamento sera configurado em seguida.`,
        );
        return;
      }

      const method = resolveOnlinePaymentMethod(
        primaryPayment.method,
        selectedPaymentMethod,
      );

      const intent = await createPaymentIntent(
        primaryPayment.id,
        buildIdempotencyKey(createdOrder.id, primaryPayment.id),
      );

      setCart({});

      const nextPanel = buildIntentPanel(
        createdOrder.id,
        method,
        primaryPayment.id,
        intent,
      );

      setIntentPanel(nextPanel);
      setCheckoutState(resolveCheckoutStateByIntentStatus(intent.status));
      setCheckoutMessage(
        `Pedido #${createdOrder.id} criado. Fluxo ${ONLINE_PAYMENT_LABELS[method]} em status ${intent.status}.`,
      );
    } catch (error) {
      setCheckoutState("error");
      if (error instanceof ApiError && error.status === 401) {
        setIsAuthenticated(false);
      }
      setCheckoutMessage(parseErrorMessage(error));
    }
  };

  return (
    <section className="space-y-4">
      <div className="rounded-2xl border border-border bg-surface/70 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          Web Cliente
        </p>
        <h1 className="mt-1 text-2xl font-bold text-text">
          Monte seu pedido e acompanhe seus status
        </h1>
        <p className="mt-2 text-sm text-muted">
          {isAuthenticated
            ? "Sessao autenticada. Seus pedidos e pagamentos seguem o escopo da conta ativa."
            : "Faca login na aba Conta para finalizar pedidos com sua conta real."}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <MenuDayView
          selectedDate={selectedDate}
          onSelectedDateChange={setSelectedDate}
          state={menuState}
          message={menuMessage}
          menu={menu}
          cartQtyByItem={cartQtyByItem}
          onAddItem={addToCart}
        />

        <CartDrawer
          items={cartItems}
          totalAmount={totalAmount}
          checkoutState={checkoutState}
          checkoutMessage={checkoutMessage}
          selectedPaymentMethod={selectedPaymentMethod}
          onPaymentMethodChange={setSelectedPaymentMethod}
          intentPanel={intentPanel}
          onRefreshIntent={refreshLatestIntent}
          isRefreshingIntent={isRefreshingIntent}
          onIncrement={incrementCartItem}
          onDecrement={decrementCartItem}
          onRemove={removeCartItem}
          onCheckout={checkout}
          isCheckoutDisabled={isCheckoutDisabled}
        />
      </div>
    </section>
  );
}
