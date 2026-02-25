"use client";

import { useEffect, useMemo, useState } from "react";

import {
  ApiError,
  listDishesAdmin,
  listMenuDaysAdmin,
} from "@/lib/api";
import type { DishData, MenuDayData } from "@/types/api";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar modulo de cardapio.";
}

function formatDate(valueRaw: string): string {
  const dateValue = new Date(`${valueRaw}T00:00:00`);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleDateString("pt-BR");
}

function buildTodayDateIso(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  const local = new Date(now.getTime() - offset);
  return local.toISOString().slice(0, 10);
}

export function MenuOpsPanel() {
  const [menuDays, setMenuDays] = useState<MenuDayData[]>([]);
  const [dishes, setDishes] = useState<DishData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  async function loadMenuModule({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [menuDaysPayload, dishesPayload] = await Promise.all([
        listMenuDaysAdmin(),
        listDishesAdmin(),
      ]);

      setMenuDays(menuDaysPayload);
      setDishes(dishesPayload);
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadMenuModule();
  }, []);

  const todayIso = useMemo(buildTodayDateIso, []);
  const menuToday = menuDays.find((menuDay) => menuDay.menu_date === todayIso);
  const activeMenus = menuDays.filter((menuDay) => menuDay.menu_items.length > 0);
  const activeDishes = dishes.filter((dish) => Boolean(dish.name));

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Cardapio</h3>
          <p className="text-sm text-muted">
            Baseline do modulo de planejamento de menus e pratos para operacao diaria.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadMenuModule({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {loading && <p className="mt-4 text-sm text-muted">Carregando modulo de cardapio...</p>}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Menus carregados</p>
              <p className="mt-1 text-2xl font-semibold text-text">{menuDays.length}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Menus ativos</p>
              <p className="mt-1 text-2xl font-semibold text-text">{activeMenus.length}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pratos cadastrados</p>
              <p className="mt-1 text-2xl font-semibold text-text">{activeDishes.length}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Menu de hoje</p>
              <p className="mt-1 text-sm font-semibold text-text">
                {menuToday ? `${menuToday.title} (${menuToday.menu_items.length} itens)` : "Nao cadastrado"}
              </p>
            </article>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Menus recentes</h4>
              {menuDays.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhum menu cadastrado.</p>
              )}
              {menuDays.length > 0 && (
                <div className="mt-3 space-y-2">
                  {menuDays.slice(0, 8).map((menuDay) => (
                    <article
                      key={menuDay.id}
                      className="rounded-lg border border-border bg-surface px-3 py-2"
                    >
                      <p className="text-sm font-semibold text-text">{menuDay.title}</p>
                      <p className="text-xs text-muted">
                        Data: {formatDate(menuDay.menu_date)} | Itens: {menuDay.menu_items.length}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Pratos recentes</h4>
              {dishes.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhum prato encontrado.</p>
              )}
              {dishes.length > 0 && (
                <div className="mt-3 space-y-2">
                  {dishes.slice(0, 10).map((dish) => (
                    <article
                      key={dish.id}
                      className="rounded-lg border border-border bg-surface px-3 py-2"
                    >
                      <p className="text-sm font-semibold text-text">{dish.name}</p>
                      <p className="text-xs text-muted">
                        Rendimento: {dish.yield_portions} porcoes
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
