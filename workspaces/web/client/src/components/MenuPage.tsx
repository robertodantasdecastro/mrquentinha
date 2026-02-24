"use client";

import { useEffect, useMemo, useState } from "react";

import { ApiError, createOrder, fetchMenuByDate, getDemoCustomerId } from "@/lib/api";
import { getTodayIsoDate } from "@/lib/format";
import { rememberOrderId } from "@/lib/storage";
import { CartDrawer, type CheckoutState } from "@/components/CartDrawer";
import { MenuDayView, type MenuFetchState } from "@/components/MenuDayView";
import type { MenuDayData, MenuItemData } from "@/types/api";
import type { CartItem } from "@/types/cart";

type CartState = Record<number, CartItem>;

function parseErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada. Tente novamente.";
}

export function MenuPage() {
  const [selectedDate, setSelectedDate] = useState<string>(getTodayIsoDate());

  const [menu, setMenu] = useState<MenuDayData | null>(null);
  const [menuState, setMenuState] = useState<MenuFetchState>("loading");
  const [menuMessage, setMenuMessage] = useState<string>("Carregando cardapio...");

  const [cart, setCart] = useState<CartState>({});
  const [checkoutState, setCheckoutState] = useState<CheckoutState>("idle");
  const [checkoutMessage, setCheckoutMessage] = useState<string>("");

  const demoCustomerId = getDemoCustomerId();

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

  const checkout = async () => {
    if (cartItems.length === 0) {
      setCheckoutState("error");
      setCheckoutMessage("Selecione ao menos um item antes de finalizar.");
      return;
    }

    setCheckoutState("submitting");
    setCheckoutMessage("Enviando pedido para a API...");

    try {
      const createdOrder = await createOrder(
        selectedDate,
        cartItems.map((item) => ({
          menu_item_id: item.menuItemId,
          qty: item.qty,
        })),
      );

      rememberOrderId(createdOrder.id);
      setCart({});
      setCheckoutState("success");
      setCheckoutMessage(
        `Pedido #${createdOrder.id} criado com total ${createdOrder.total_amount}.`,
      );
    } catch (error) {
      setCheckoutState("error");
      setCheckoutMessage(parseErrorMessage(error));
    }
  };

  return (
    <section className="space-y-4">
      <div className="rounded-2xl border border-border bg-surface/70 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          Web Cliente MVP
        </p>
        <h1 className="mt-1 text-2xl font-bold text-text">
          Monte seu pedido e acompanhe seus status
        </h1>
        <p className="mt-2 text-sm text-muted">
          MVP sem login real. Pedido e historico usam modo demo com integracao direta na
          API.
          {demoCustomerId ? ` Customer demo: ${demoCustomerId}.` : ""}
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
