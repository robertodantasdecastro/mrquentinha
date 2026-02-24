"use client";

import { useEffect, useMemo, useState } from "react";

type DishData = {
  id: number;
  name: string;
  description?: string | null;
};

type MenuItemData = {
  id: number;
  sale_price: string;
  available_qty?: number | null;
  dish: DishData;
};

type MenuDayData = {
  id: number;
  menu_date: string;
  title: string;
  menu_items: MenuItemData[];
};

function getDefaultDate(): string {
  const now = new Date();
  const localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 10);
}

function formatCurrency(value: string): string {
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) {
    return value;
  }

  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(numberValue);
}

export function CardapioList() {
  const [selectedDate, setSelectedDate] = useState<string>(getDefaultDate());
  const [menu, setMenu] = useState<MenuDayData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "",
    [],
  );

  useEffect(() => {
    let isMounted = true;

    async function fetchMenuByDate() {
      if (!apiBaseUrl) {
        if (isMounted) {
          setMenu(null);
          setError(
            "Defina NEXT_PUBLIC_API_BASE_URL para carregar o cardapio em tempo real.",
          );
        }
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${apiBaseUrl}/api/v1/catalog/menus/by-date/${selectedDate}/`,
          {
            cache: "no-store",
          },
        );

        if (response.status === 404) {
          if (isMounted) {
            setMenu(null);
            setError(null);
          }
          return;
        }

        if (!response.ok) {
          throw new Error(`Erro ${response.status} ao consultar cardapio.`);
        }

        const payload: MenuDayData = await response.json();

        if (isMounted) {
          setMenu(payload);
        }
      } catch (fetchError) {
        if (isMounted) {
          setMenu(null);
          setError(
            fetchError instanceof Error
              ? fetchError.message
              : "Falha ao consultar o cardapio. Tente novamente.",
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchMenuByDate();

    return () => {
      isMounted = false;
    };
  }, [apiBaseUrl, selectedDate]);

  return (
    <section className="rounded-lg border border-border bg-surface/80 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
            Consulta em tempo real
          </p>
          <h2 className="mt-1 text-2xl font-bold text-text">Cardapio por data</h2>
        </div>

        <label className="flex flex-col gap-1 text-sm font-medium text-muted">
          Selecione a data
          <input
            type="date"
            value={selectedDate}
            onChange={(event) => setSelectedDate(event.target.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-text outline-none transition focus:border-primary"
          />
        </label>
      </div>

      <div className="mt-6">
        {loading && (
          <div className="rounded-md border border-border bg-bg px-4 py-8 text-center text-muted">
            Carregando cardapio...
          </div>
        )}

        {!loading && error && (
          <div className="rounded-md border border-red-400/60 bg-red-50 px-4 py-4 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </div>
        )}

        {!loading && !error && !menu && (
          <div className="rounded-md border border-border bg-bg px-4 py-8 text-center text-muted">
            Sem cardapio cadastrado para {selectedDate}.
          </div>
        )}

        {!loading && !error && menu && (
          <div className="space-y-4">
            <div className="rounded-md border border-border bg-bg px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
                {menu.menu_date}
              </p>
              <h3 className="text-lg font-semibold text-text">{menu.title}</h3>
            </div>

            {menu.menu_items.length === 0 && (
              <div className="rounded-md border border-border bg-bg px-4 py-6 text-muted">
                O cardapio desta data ainda nao possui itens ativos.
              </div>
            )}

            <div className="grid gap-3 md:grid-cols-2">
              {menu.menu_items.map((item) => (
                <article
                  key={item.id}
                  className="rounded-md border border-border bg-bg p-4 transition hover:border-primary/60"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h4 className="text-base font-semibold text-text">{item.dish.name}</h4>
                      {item.dish.description && (
                        <p className="mt-1 text-sm text-muted">{item.dish.description}</p>
                      )}
                    </div>
                    <p className="text-sm font-semibold text-primary">
                      {formatCurrency(item.sale_price)}
                    </p>
                  </div>

                  {item.available_qty !== undefined && item.available_qty !== null && (
                    <p className="mt-3 text-xs uppercase tracking-[0.14em] text-muted">
                      Disponivel: {item.available_qty}
                    </p>
                  )}
                </article>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
