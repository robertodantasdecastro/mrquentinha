"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import {
  ApiError,
  createMenuDayAdmin,
  deleteMenuDayAdmin,
  listDishesAdmin,
  listMenuDaysAdmin,
  updateMenuDayAdmin,
} from "@/lib/api";
import type {
  DishData,
  MenuDayData,
  MenuItemWritePayload,
  UpsertMenuDayPayload,
} from "@/types/api";

type MenuItemDraft = {
  selected: boolean;
  salePrice: string;
  availableQty: string;
  isActive: boolean;
};

const EMPTY_DRAFT: MenuItemDraft = {
  selected: false,
  salePrice: "0.00",
  availableQty: "",
  isActive: true,
};

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

function buildDefaultTitle(menuDate: string): string {
  return `Cardapio ${formatDate(menuDate)}`;
}

function normalizePrice(value: string): string {
  const normalized = value.replace(",", ".").trim();
  if (!normalized) {
    return "0.00";
  }

  const numeric = Number(normalized);
  if (Number.isNaN(numeric) || numeric < 0) {
    throw new Error("Preco invalido em um ou mais pratos selecionados.");
  }

  return numeric.toFixed(2);
}

function buildEmptyDrafts(dishes: DishData[]): Record<number, MenuItemDraft> {
  return dishes.reduce<Record<number, MenuItemDraft>>((accumulator, dish) => {
    accumulator[dish.id] = { ...EMPTY_DRAFT };
    return accumulator;
  }, {});
}

function mergeDraftsWithDishes(
  dishes: DishData[],
  previous: Record<number, MenuItemDraft>,
): Record<number, MenuItemDraft> {
  return dishes.reduce<Record<number, MenuItemDraft>>((accumulator, dish) => {
    accumulator[dish.id] = previous[dish.id] ? { ...previous[dish.id] } : { ...EMPTY_DRAFT };
    return accumulator;
  }, {});
}

function buildDraftsFromMenu(
  menuDay: MenuDayData,
  dishes: DishData[],
): Record<number, MenuItemDraft> {
  const drafts = buildEmptyDrafts(dishes);

  for (const menuItem of menuDay.menu_items) {
    const dishId = menuItem.dish.id;
    drafts[dishId] = {
      selected: true,
      salePrice: menuItem.sale_price,
      availableQty:
        menuItem.available_qty === null ? "" : String(menuItem.available_qty),
      isActive: menuItem.is_active,
    };
  }

  return drafts;
}

function buildMenuPayload({
  menuDate,
  title,
  dishes,
  drafts,
}: {
  menuDate: string;
  title: string;
  dishes: DishData[];
  drafts: Record<number, MenuItemDraft>;
}): UpsertMenuDayPayload {
  const items: MenuItemWritePayload[] = [];

  for (const dish of dishes) {
    const draft = drafts[dish.id];
    if (!draft || !draft.selected) {
      continue;
    }

    const payloadItem: MenuItemWritePayload = {
      dish: dish.id,
      sale_price: normalizePrice(draft.salePrice),
      is_active: draft.isActive,
    };

    const qtyRaw = draft.availableQty.trim();
    if (qtyRaw) {
      const qty = Number.parseInt(qtyRaw, 10);
      if (Number.isNaN(qty) || qty < 0) {
        throw new Error("Quantidade disponivel invalida em um ou mais pratos.");
      }
      payloadItem.available_qty = qty;
    }

    items.push(payloadItem);
  }

  if (items.length === 0) {
    throw new Error("Selecione ao menos um prato para salvar o menu.");
  }

  return {
    menu_date: menuDate,
    title: title.trim() || buildDefaultTitle(menuDate),
    items,
  };
}

export function MenuOpsPanel() {
  const [menuDays, setMenuDays] = useState<MenuDayData[]>([]);
  const [dishes, setDishes] = useState<DishData[]>([]);
  const [drafts, setDrafts] = useState<Record<number, MenuItemDraft>>({});
  const [editingMenuId, setEditingMenuId] = useState<number | null>(null);
  const [menuDate, setMenuDate] = useState<string>("");
  const [title, setTitle] = useState<string>("");

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [deletingMenuId, setDeletingMenuId] = useState<number | null>(null);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const todayIso = useMemo(buildTodayDateIso, []);
  const menuToday = menuDays.find((menuDay) => menuDay.menu_date === todayIso);
  const selectedDishesCount = useMemo(
    () => Object.values(drafts).filter((draft) => draft.selected).length,
    [drafts],
  );

  function startCreateMode(availableDishes: DishData[], options?: { keepDate?: boolean }) {
    const nextDate = options?.keepDate && menuDate ? menuDate : todayIso;
    setEditingMenuId(null);
    setMenuDate(nextDate);
    setTitle(buildDefaultTitle(nextDate));
    setDrafts(buildEmptyDrafts(availableDishes));
  }

  function startEditMode(menuDay: MenuDayData, availableDishes: DishData[]) {
    setEditingMenuId(menuDay.id);
    setMenuDate(menuDay.menu_date);
    setTitle(menuDay.title);
    setDrafts(buildDraftsFromMenu(menuDay, availableDishes));
  }

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

      if (editingMenuId !== null) {
        const currentMenu = menuDaysPayload.find((menuDay) => menuDay.id === editingMenuId);
        if (currentMenu) {
          setDrafts(buildDraftsFromMenu(currentMenu, dishesPayload));
        } else {
          startCreateMode(dishesPayload, { keepDate: true });
        }
      } else {
        setDrafts((previous) => mergeDraftsWithDishes(dishesPayload, previous));

        if (!menuDate) {
          startCreateMode(dishesPayload);
        }
      }

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateDraft(dishId: number, patch: Partial<MenuItemDraft>) {
    setDrafts((previous) => {
      const current = previous[dishId] ?? { ...EMPTY_DRAFT };
      return {
        ...previous,
        [dishId]: {
          ...current,
          ...patch,
        },
      };
    });
  }

  async function handleSubmitMenu(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setErrorMessage("");

    try {
      if (!menuDate) {
        throw new Error("Informe a data do cardapio.");
      }

      const payload = buildMenuPayload({
        menuDate,
        title,
        dishes,
        drafts,
      });

      const savedMenu =
        editingMenuId === null
          ? await createMenuDayAdmin(payload)
          : await updateMenuDayAdmin(editingMenuId, payload);

      setEditingMenuId(savedMenu.id);
      setMenuDate(savedMenu.menu_date);
      setTitle(savedMenu.title);
      setDrafts(buildDraftsFromMenu(savedMenu, dishes));
      setMessage(
        editingMenuId === null
          ? "Menu salvo com sucesso."
          : "Menu atualizado com sucesso.",
      );

      await loadMenuModule({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteMenu(menuDay: MenuDayData) {
    const confirmed = window.confirm(
      `Excluir o menu '${menuDay.title}' de ${formatDate(menuDay.menu_date)}?`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingMenuId(menuDay.id);
    setMessage("");
    setErrorMessage("");

    try {
      await deleteMenuDayAdmin(menuDay.id);

      if (editingMenuId === menuDay.id) {
        startCreateMode(dishes);
      }

      setMessage("Menu removido com sucesso.");
      await loadMenuModule({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setDeletingMenuId(null);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Cardapio</h3>
          <p className="text-sm text-muted">
            Fluxo operacional: criar, editar e publicar menu do dia com pratos e precos.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => startCreateMode(dishes)}
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
          >
            Novo menu
          </button>
          <button
            type="button"
            onClick={() => void loadMenuModule({ silent: true })}
            disabled={refreshing || loading}
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
          >
            {refreshing ? "Atualizando..." : "Atualizar"}
          </button>
        </div>
      </div>

      {loading && <p className="mt-4 text-sm text-muted">Carregando modulo de cardapio...</p>}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Menus cadastrados</p>
              <p className="mt-1 text-2xl font-semibold text-text">{menuDays.length}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pratos no menu atual</p>
              <p className="mt-1 text-2xl font-semibold text-text">{selectedDishesCount}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pratos cadastrados</p>
              <p className="mt-1 text-2xl font-semibold text-text">{dishes.length}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Menu de hoje</p>
              <p className="mt-1 text-sm font-semibold text-text">
                {menuToday ? `${menuToday.title} (${menuToday.menu_items.length} itens)` : "Nao cadastrado"}
              </p>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <form
              onSubmit={(event) => void handleSubmitMenu(event)}
              className="rounded-xl border border-border bg-bg p-4"
            >
              <h4 className="text-base font-semibold text-text">
                {editingMenuId === null ? "Novo menu do dia" : `Editando menu #${editingMenuId}`}
              </h4>

              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <label className="grid gap-1 text-sm text-muted">
                  Data
                  <input
                    type="date"
                    required
                    value={menuDate}
                    onChange={(event) => setMenuDate(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>

                <label className="grid gap-1 text-sm text-muted">
                  Titulo
                  <input
                    required
                    value={title}
                    onChange={(event) => setTitle(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="Cardapio da semana"
                  />
                </label>
              </div>

              <div className="mt-4 space-y-2">
                <p className="text-sm font-semibold text-text">Pratos no menu</p>
                {dishes.length === 0 && (
                  <p className="text-sm text-muted">Cadastre pratos para montar o cardapio.</p>
                )}

                {dishes.length > 0 && (
                  <div className="max-h-96 space-y-2 overflow-y-auto pr-1">
                    {dishes.map((dish) => {
                      const draft = drafts[dish.id] ?? EMPTY_DRAFT;

                      return (
                        <article
                          key={dish.id}
                          className="rounded-lg border border-border bg-surface p-3"
                        >
                          <label className="flex items-center gap-2 text-sm font-semibold text-text">
                            <input
                              type="checkbox"
                              checked={draft.selected}
                              onChange={(event) =>
                                updateDraft(dish.id, { selected: event.currentTarget.checked })
                              }
                              className="h-4 w-4"
                            />
                            {dish.name}
                          </label>

                          <div className="mt-2 grid gap-2 sm:grid-cols-3">
                            <label className="grid gap-1 text-xs text-muted">
                              Preco (R$)
                              <input
                                value={draft.salePrice}
                                onChange={(event) =>
                                  updateDraft(dish.id, { salePrice: event.currentTarget.value })
                                }
                                disabled={!draft.selected}
                                className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text disabled:cursor-not-allowed disabled:opacity-60"
                                placeholder="0.00"
                              />
                            </label>

                            <label className="grid gap-1 text-xs text-muted">
                              Qtd disponivel
                              <input
                                value={draft.availableQty}
                                onChange={(event) =>
                                  updateDraft(dish.id, {
                                    availableQty: event.currentTarget.value,
                                  })
                                }
                                disabled={!draft.selected}
                                className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text disabled:cursor-not-allowed disabled:opacity-60"
                                placeholder="Opcional"
                              />
                            </label>

                            <label className="flex items-center gap-2 text-xs text-muted">
                              <input
                                type="checkbox"
                                checked={draft.isActive}
                                onChange={(event) =>
                                  updateDraft(dish.id, {
                                    isActive: event.currentTarget.checked,
                                  })
                                }
                                disabled={!draft.selected}
                                className="h-4 w-4"
                              />
                              Item ativo
                            </label>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="mt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={saving || dishes.length === 0}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {saving
                    ? "Salvando..."
                    : editingMenuId === null
                      ? "Salvar menu"
                      : "Atualizar menu"}
                </button>
              </div>
            </form>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Menus recentes</h4>
              {menuDays.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhum menu cadastrado.</p>
              )}
              {menuDays.length > 0 && (
                <div className="mt-3 space-y-2">
                  {menuDays.slice(0, 12).map((menuDay) => (
                    <article
                      key={menuDay.id}
                      className="rounded-lg border border-border bg-surface px-3 py-2"
                    >
                      <p className="text-sm font-semibold text-text">{menuDay.title}</p>
                      <p className="text-xs text-muted">
                        Data: {formatDate(menuDay.menu_date)} | Itens: {menuDay.menu_items.length}
                      </p>
                      <div className="mt-2 flex gap-2">
                        <button
                          type="button"
                          onClick={() => startEditMode(menuDay, dishes)}
                          className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDeleteMenu(menuDay)}
                          disabled={deletingMenuId === menuDay.id}
                          className="rounded-md border border-rose-300 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-70"
                        >
                          {deletingMenuId === menuDay.id ? "Excluindo..." : "Excluir"}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </div>
        </>
      )}

      {message && (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-xl border border-border bg-bg px-4 py-3 text-sm">
          <p className="text-rose-600">{errorMessage}</p>
        </div>
      )}
    </section>
  );
}
