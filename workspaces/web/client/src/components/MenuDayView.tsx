"use client";

import { Badge, Button, Card, Input } from "@mrquentinha/ui";
import Image from "next/image";

import { formatCurrency } from "@/lib/format";
import type { MenuDayData, MenuItemData } from "@/types/api";

export type MenuFetchState = "loading" | "empty" | "error" | "loaded";

type MenuDayViewProps = {
  selectedDate: string;
  onSelectedDateChange: (value: string) => void;
  state: MenuFetchState;
  message: string;
  menu: MenuDayData | null;
  cartQtyByItem: Record<number, number>;
  onAddItem: (item: MenuItemData) => void;
};

export function MenuDayView({
  selectedDate,
  onSelectedDateChange,
  state,
  message,
  menu,
  cartQtyByItem,
  onAddItem,
}: MenuDayViewProps) {
  return (
    <Card tone="surface" className="rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Badge>Pedido por data</Badge>
          <h1 className="mt-2 text-2xl font-bold text-text">Cardapio do dia</h1>
        </div>

        <label className="flex flex-col gap-1 text-sm font-medium text-muted">
          Selecione a data
          <Input
            type="date"
            value={selectedDate}
            onChange={(event) => onSelectedDateChange(event.target.value)}
            className="w-auto"
          />
        </label>
      </div>

      <div className="mt-5">
        {state === "loading" && (
          <div className="rounded-xl border border-border bg-bg px-4 py-10 text-center text-sm text-muted">
            {message}
          </div>
        )}

        {state === "empty" && (
          <div className="rounded-xl border border-border bg-bg px-4 py-10 text-center text-sm text-muted">
            {message}
          </div>
        )}

        {state === "error" && (
          <div className="rounded-xl border border-red-300/70 bg-red-50 px-4 py-4 text-sm text-red-700 dark:bg-red-950/25 dark:text-red-300">
            {message}
          </div>
        )}

        {state === "loaded" && menu && (
          <div className="space-y-4">
            <div className="rounded-xl border border-border bg-bg px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
                {menu.menu_date}
              </p>
              <h2 className="text-lg font-semibold text-text">{menu.title}</h2>
            </div>

            {menu.menu_items.length === 0 && (
              <div className="rounded-xl border border-border bg-bg px-4 py-7 text-sm text-muted">
                O cardapio desta data ainda nao possui itens ativos.
              </div>
            )}

            <div className="grid gap-3">
              {menu.menu_items.map((item) => {
                const currentQty = cartQtyByItem[item.id] ?? 0;
                const reachedLimit =
                  item.available_qty !== null && currentQty >= item.available_qty;
                const disabled = !item.is_active || reachedLimit;

                return (
                  <article
                    key={item.id}
                    className="rounded-xl border border-border bg-bg p-4 transition hover:border-primary/60"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h3 className="text-base font-semibold text-text">{item.dish.name}</h3>
                        <p className="mt-1 text-xs uppercase tracking-[0.12em] text-muted">
                          rendimento: {item.dish.yield_portions} porcoes
                        </p>
                      </div>

                      <p className="text-sm font-bold text-primary">
                        {formatCurrency(item.sale_price)}
                      </p>
                    </div>

                    {item.dish.image_url && (
                      <Image
                        src={item.dish.image_url}
                        alt={item.dish.name}
                        width={640}
                        height={320}
                        className="mt-3 h-32 w-full rounded-md border border-border object-cover"
                        unoptimized
                      />
                    )}

                    <div className="mt-4 flex items-center justify-between gap-2">
                      <div className="text-xs uppercase tracking-[0.12em] text-muted">
                        {item.available_qty === null
                          ? "estoque: nao informado"
                          : `disponivel: ${item.available_qty}`}
                      </div>

                      <Button
                        onClick={() => onAddItem(item)}
                        disabled={disabled}
                        size="sm"
                        className="rounded-full"
                      >
                        {!item.is_active
                          ? "Inativo"
                          : reachedLimit
                            ? "Limite"
                            : "Adicionar"}
                      </Button>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
