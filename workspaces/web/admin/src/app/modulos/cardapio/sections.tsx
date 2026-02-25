"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { ApiError, listDishesAdmin, listMenuDaysAdmin } from "@/lib/api";
import {
  buildRecentDateKeys,
  buildSeriesFromTotals,
  sumByDateKey,
  normalizeDateKey,
} from "@/lib/metrics";
import type { DishData, MenuDayData } from "@/types/api";

import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { MenuOpsPanel } from "@/components/modules/MenuOpsPanel";

export const CARDAPIO_BASE_PATH = "/modulos/cardapio";

export const CARDAPIO_MENU_ITEMS = [
  { key: "all", label: "Todos", href: CARDAPIO_BASE_PATH },
  { key: "planejamento", label: "Planejamento", href: `${CARDAPIO_BASE_PATH}/planejamento#planejamento` },
  { key: "menus", label: "Menus", href: `${CARDAPIO_BASE_PATH}/menus#menus` },
  { key: "tendencias", label: "Tendencias", href: `${CARDAPIO_BASE_PATH}/tendencias#tendencias` },
];

export type CardapioSectionKey =
  | "all"
  | "planejamento"
  | "menus"
  | "tendencias";

type CardapioSectionsProps = {
  activeSection?: CardapioSectionKey;
};

function sumMenuDayQty(menuDay: MenuDayData): number {
  return menuDay.menu_items.reduce((accumulator, item) => {
    if (item.available_qty === null) {
      return accumulator;
    }

    return accumulator + item.available_qty;
  }, 0);
}

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar dados do cardapio.";
}

export function CardapioSections({ activeSection = "all" }: CardapioSectionsProps) {
  const [menuDays, setMenuDays] = useState<MenuDayData[]>([]);
  const [dishes, setDishes] = useState<DishData[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const todayKey = useMemo(() => normalizeDateKey(new Date()), []);

  useEffect(() => {
    let mounted = true;

    async function loadCardapio() {
      try {
        const [menusPayload, dishesPayload] = await Promise.all([
          listMenuDaysAdmin(),
          listDishesAdmin(),
        ]);

        if (!mounted) {
          return;
        }

        setMenuDays(menusPayload);
        setDishes(dishesPayload);
        setErrorMessage("");
      } catch (error) {
        if (mounted) {
          setErrorMessage(resolveErrorMessage(error));
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadCardapio();

    return () => {
      mounted = false;
    };
  }, []);

  const menuToday = useMemo(
    () => menuDays.find((menuDay) => menuDay.menu_date === todayKey) ?? null,
    [menuDays, todayKey],
  );

  const menusAtivos = useMemo(
    () =>
      menuDays.filter(
        (menuDay) => menuDay.menu_items.length > 0 && menuDay.menu_date >= todayKey,
      ).length,
    [menuDays, todayKey],
  );

  const pratosDoDia = menuToday?.menu_items.length ?? 0;
  const porcoesPrevistas = menuToday ? sumMenuDayQty(menuToday) : 0;

  const trendDateKeys = useMemo(() => buildRecentDateKeys(7), []);
  const menuTotalsByDay = useMemo(
    () => sumByDateKey(menuDays, (menuDay) => menuDay.menu_date, (menuDay) => sumMenuDayQty(menuDay)),
    [menuDays],
  );
  const trendValues = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, menuTotalsByDay);
    return values.length > 0 ? values : [0, 0];
  }, [menuTotalsByDay, trendDateKeys]);

  const topDishValues = useMemo(() => {
    if (dishes.length === 0) {
      return [0, 0, 0];
    }

    return dishes.slice(0, 6).map((dish) => Number(dish.yield_portions) || 0);
  }, [dishes]);

  const showAll = activeSection === "all";

  return (
    <>
      {(showAll || activeSection === "planejamento") && (
        <section id="planejamento" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Planejamento do dia</h2>
              <p className="mt-1 text-sm text-muted">Resumo do cardapio ativo e porcoes previstas.</p>
            </div>
            <StatusPill tone="brand">Menu ativo</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando resumo do cardapio...</p>}
          {!loading && (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Menus ativos</p>
                <p className="mt-1 text-2xl font-semibold text-text">{menusAtivos}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pratos do dia</p>
                <p className="mt-1 text-2xl font-semibold text-text">{pratosDoDia}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Porcoes previstas</p>
                <p className="mt-1 text-2xl font-semibold text-text">{porcoesPrevistas}</p>
              </article>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "menus") && (
        <section id="menus" className="scroll-mt-24">
          <MenuOpsPanel />
        </section>
      )}

      {(showAll || activeSection === "tendencias") && (
        <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Tendencias do cardapio</h2>
              <p className="mt-1 text-sm text-muted">Demanda e sazonalidade por prato.</p>
            </div>
            <StatusPill tone="info">{dishes.length} pratos cadastrados</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando tendencias...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Porcoes planejadas (7 dias)</p>
                <Sparkline values={trendValues} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Top pratos (ultimos dias)</p>
                <div className="mt-4">
                  <MiniBarChart values={topDishValues} />
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {errorMessage && (
        <div className="rounded-xl border border-border bg-bg px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      )}
    </>
  );
}
