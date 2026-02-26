"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import Image from "next/image";

import {
  ApiError,
  createDishAdmin,
  createIngredientAdmin,
  listDishesAdmin,
  listIngredientsAdmin,
  uploadDishImageAdmin,
  uploadIngredientImageAdmin,
} from "@/lib/api";
import type {
  CreateDishPayload,
  DishData,
  IngredientData,
  IngredientUnit,
} from "@/types/api";

const UNIT_OPTIONS: IngredientUnit[] = ["g", "kg", "ml", "l", "unidade"];

type CompositionRowDraft = {
  ingredientId: string;
  quantity: string;
  unit: string;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar composição de pratos.";
}

function toSlugLabel(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function buildTodayDateIso(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

export function DishCompositionPanel() {
  const [ingredients, setIngredients] = useState<IngredientData[]>([]);
  const [dishes, setDishes] = useState<DishData[]>([]);

  const [ingredientName, setIngredientName] = useState("");
  const [ingredientUnit, setIngredientUnit] = useState<IngredientUnit>("kg");

  const [dishName, setDishName] = useState("");
  const [dishDescription, setDishDescription] = useState("");
  const [dishYieldPortions, setDishYieldPortions] = useState("1");
  const [compositionRows, setCompositionRows] = useState<CompositionRowDraft[]>([
    { ingredientId: "", quantity: "", unit: "kg" },
  ]);
  const [selectedIngredientImageId, setSelectedIngredientImageId] = useState("");
  const [selectedDishImageId, setSelectedDishImageId] = useState("");
  const [ingredientImageFile, setIngredientImageFile] = useState<File | null>(null);
  const [dishImageFile, setDishImageFile] = useState<File | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [savingIngredient, setSavingIngredient] = useState(false);
  const [savingDish, setSavingDish] = useState(false);
  const [uploadingIngredientImage, setUploadingIngredientImage] = useState(false);
  const [uploadingDishImage, setUploadingDishImage] = useState(false);
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function loadCompositionData({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [ingredientsPayload, dishesPayload] = await Promise.all([
        listIngredientsAdmin(),
        listDishesAdmin(),
      ]);
      const activeIngredientsPayload = ingredientsPayload.filter((item) => item.is_active);

      setIngredients(ingredientsPayload);
      setDishes(dishesPayload);
      setSelectedIngredientImageId((previous) => {
        if (
          previous &&
          ingredientsPayload.some((ingredient) => String(ingredient.id) === previous)
        ) {
          return previous;
        }

        return activeIngredientsPayload[0] ? String(activeIngredientsPayload[0].id) : "";
      });
      setSelectedDishImageId((previous) => {
        if (previous && dishesPayload.some((dish) => String(dish.id) === previous)) {
          return previous;
        }

        return dishesPayload[0] ? String(dishesPayload[0].id) : "";
      });
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadCompositionData();
  }, []);

  const activeIngredients = useMemo(
    () =>
      ingredients
        .filter((item) => item.is_active)
        .sort((left, right) => left.name.localeCompare(right.name, "pt-BR")),
    [ingredients],
  );

  const dishesWithComposition = useMemo(
    () =>
      dishes.filter((dish) => Array.isArray(dish.composition) && dish.composition.length > 0),
    [dishes],
  );
  const selectedIngredientForImage = useMemo(
    () =>
      ingredients.find(
        (ingredient) => String(ingredient.id) === selectedIngredientImageId,
      ) ?? null,
    [ingredients, selectedIngredientImageId],
  );
  const selectedDishForImage = useMemo(
    () => dishes.find((dish) => String(dish.id) === selectedDishImageId) ?? null,
    [dishes, selectedDishImageId],
  );

  function appendCompositionRow() {
    setCompositionRows((previous) => [
      ...previous,
      { ingredientId: "", quantity: "", unit: "kg" },
    ]);
  }

  function updateCompositionRow(
    index: number,
    patch: Partial<CompositionRowDraft>,
  ) {
    setCompositionRows((previous) =>
      previous.map((row, rowIndex) => {
        if (rowIndex !== index) {
          return row;
        }

        return {
          ...row,
          ...patch,
        };
      }),
    );
  }

  function removeCompositionRow(index: number) {
    setCompositionRows((previous) => previous.filter((_, rowIndex) => rowIndex !== index));
  }

  async function handleCreateIngredient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingIngredient(true);
    setMessage("");
    setErrorMessage("");

    try {
      const normalizedName = ingredientName.trim();
      if (!normalizedName) {
        throw new Error("Informe o nome do ingrediente.");
      }

      await createIngredientAdmin({
        name: normalizedName,
        unit: ingredientUnit,
        is_active: true,
      });

      setIngredientName("");
      setMessage("Ingrediente cadastrado com sucesso.");
      await loadCompositionData({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSavingIngredient(false);
    }
  }

  async function handleCreateDish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingDish(true);
    setMessage("");
    setErrorMessage("");

    try {
      const normalizedName = dishName.trim();
      if (!normalizedName) {
        throw new Error("Informe o nome do prato.");
      }

      const yieldPortions = Number.parseInt(dishYieldPortions, 10);
      if (Number.isNaN(yieldPortions) || yieldPortions <= 0) {
        throw new Error("Rendimento do prato deve ser maior que zero.");
      }

      const payloadRows = compositionRows
        .map((row) => ({
          ingredientId: Number.parseInt(row.ingredientId, 10),
          quantityValue: row.quantity.replace(",", ".").trim(),
          unitValue: row.unit.trim(),
        }))
        .filter((row) => row.ingredientId > 0 && row.quantityValue !== "");

      if (payloadRows.length === 0) {
        throw new Error("Adicione ao menos um ingrediente na composição.");
      }

      const ingredientIds = payloadRows.map((row) => row.ingredientId);
      if (ingredientIds.length !== new Set(ingredientIds).size) {
        throw new Error("Ingrediente duplicado na composição do prato.");
      }

      const payload: CreateDishPayload = {
        name: normalizedName,
        description: dishDescription.trim() || "",
        yield_portions: yieldPortions,
        ingredients: payloadRows.map((row) => ({
          ingredient: row.ingredientId,
          quantity: row.quantityValue,
          unit: row.unitValue || undefined,
        })),
      };

      await createDishAdmin(payload);

      setDishName("");
      setDishDescription("");
      setDishYieldPortions("1");
      setCompositionRows([{ ingredientId: "", quantity: "", unit: "kg" }]);
      setMessage("Prato cadastrado com composição com sucesso.");
      await loadCompositionData({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSavingDish(false);
    }
  }

  async function handleUploadIngredientImage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUploadingIngredientImage(true);
    setMessage("");
    setErrorMessage("");

    try {
      const ingredientId = Number.parseInt(selectedIngredientImageId, 10);
      if (Number.isNaN(ingredientId) || ingredientId <= 0) {
        throw new Error("Selecione um ingrediente para enviar a foto.");
      }

      if (!ingredientImageFile) {
        throw new Error("Selecione um arquivo de imagem do ingrediente.");
      }

      await uploadIngredientImageAdmin(ingredientId, ingredientImageFile);
      setIngredientImageFile(null);
      setMessage("Foto do ingrediente atualizada com sucesso.");
      await loadCompositionData({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setUploadingIngredientImage(false);
    }
  }

  async function handleUploadDishImage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUploadingDishImage(true);
    setMessage("");
    setErrorMessage("");

    try {
      const dishId = Number.parseInt(selectedDishImageId, 10);
      if (Number.isNaN(dishId) || dishId <= 0) {
        throw new Error("Selecione um prato para enviar a foto.");
      }

      if (!dishImageFile) {
        throw new Error("Selecione um arquivo de imagem do prato.");
      }

      await uploadDishImageAdmin(dishId, dishImageFile);
      setDishImageFile(null);
      setMessage("Foto do prato atualizada com sucesso.");
      await loadCompositionData({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setUploadingDishImage(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Composição de pratos</h3>
          <p className="text-sm text-muted">
            Cadastre ingredientes e pratos para alimentar o ciclo de compras e produção.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadCompositionData({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {loading && <p className="mt-4 text-sm text-muted">Carregando composição...</p>}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Ingredientes ativos
              </p>
              <p className="mt-1 text-2xl font-semibold text-text">{activeIngredients.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Pratos cadastrados
              </p>
              <p className="mt-1 text-2xl font-semibold text-text">{dishes.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Pratos com composição
              </p>
              <p className="mt-1 text-2xl font-semibold text-text">{dishesWithComposition.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Referência
              </p>
              <p className="mt-1 text-sm font-semibold text-text">{buildTodayDateIso()}</p>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <form onSubmit={(event) => void handleCreateIngredient(event)} className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Novo ingrediente</h4>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <label className="grid gap-1 text-sm text-muted">
                  Nome
                  <input
                    value={ingredientName}
                    onChange={(event) => setIngredientName(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="Ex.: Arroz integral"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Unidade
                  <select
                    value={ingredientUnit}
                    onChange={(event) =>
                      setIngredientUnit(event.currentTarget.value as IngredientUnit)
                    }
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  >
                    {UNIT_OPTIONS.map((unitOption) => (
                      <option key={unitOption} value={unitOption}>
                        {unitOption}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={savingIngredient}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {savingIngredient ? "Salvando..." : "Cadastrar ingrediente"}
                </button>
              </div>
            </form>

            <form onSubmit={(event) => void handleCreateDish(event)} className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Novo prato (quentinha)</h4>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <label className="grid gap-1 text-sm text-muted">
                  Nome do prato
                  <input
                    value={dishName}
                    onChange={(event) => setDishName(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="Ex.: Frango com arroz integral"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Rendimento (porções)
                  <input
                    type="number"
                    min={1}
                    value={dishYieldPortions}
                    onChange={(event) => setDishYieldPortions(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  />
                </label>
              </div>
              <label className="mt-3 grid gap-1 text-sm text-muted">
                Descrição
                <input
                  value={dishDescription}
                  onChange={(event) => setDishDescription(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="Ex.: Marmita de almoço com salada"
                />
              </label>

              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-text">Composição do prato</p>
                  <button
                    type="button"
                    onClick={appendCompositionRow}
                    className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                  >
                    + Ingrediente
                  </button>
                </div>
                {compositionRows.map((row, index) => (
                  <div key={`${index}-${row.ingredientId}`} className="grid gap-2 sm:grid-cols-12">
                    <select
                      value={row.ingredientId}
                      onChange={(event) =>
                        updateCompositionRow(index, { ingredientId: event.currentTarget.value })
                      }
                      className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text sm:col-span-5"
                    >
                      <option value="">Ingrediente</option>
                      {activeIngredients.map((ingredient) => (
                        <option key={ingredient.id} value={ingredient.id}>
                          {ingredient.name}
                        </option>
                      ))}
                    </select>
                    <input
                      value={row.quantity}
                      onChange={(event) =>
                        updateCompositionRow(index, { quantity: event.currentTarget.value })
                      }
                      className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text sm:col-span-3"
                      placeholder="Qtd"
                    />
                    <select
                      value={row.unit}
                      onChange={(event) =>
                        updateCompositionRow(index, { unit: event.currentTarget.value })
                      }
                      className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text sm:col-span-3"
                    >
                      {UNIT_OPTIONS.map((unitOption) => (
                        <option key={unitOption} value={unitOption}>
                          {unitOption}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => removeCompositionRow(index)}
                      disabled={compositionRows.length === 1}
                      className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60 sm:col-span-1"
                    >
                      X
                    </button>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={savingDish || activeIngredients.length === 0}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {savingDish ? "Salvando..." : "Cadastrar prato"}
                </button>
              </div>
            </form>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <form
              onSubmit={(event) => void handleUploadIngredientImage(event)}
              className="rounded-xl border border-border bg-bg p-4"
            >
              <h4 className="text-base font-semibold text-text">Foto do insumo</h4>
              <p className="mt-1 text-xs text-muted">
                Esta imagem sera usada em compras, estoque e composicao.
              </p>
              <div className="mt-3 grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Ingrediente
                  <select
                    value={selectedIngredientImageId}
                    onChange={(event) => setSelectedIngredientImageId(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  >
                    <option value="">Selecione</option>
                    {activeIngredients.map((ingredient) => (
                      <option key={ingredient.id} value={ingredient.id}>
                        {ingredient.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="grid gap-1 text-sm text-muted">
                  Arquivo de imagem
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(event) =>
                      setIngredientImageFile(event.currentTarget.files?.[0] ?? null)
                    }
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1 file:text-xs file:font-semibold file:text-white"
                  />
                </label>

                {selectedIngredientForImage?.image_url && (
                  <Image
                    src={selectedIngredientForImage.image_url}
                    alt={selectedIngredientForImage.name}
                    width={640}
                    height={320}
                    className="h-36 w-full rounded-lg border border-border object-cover"
                    unoptimized
                  />
                )}
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={
                    uploadingIngredientImage ||
                    !selectedIngredientImageId ||
                    ingredientImageFile === null
                  }
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {uploadingIngredientImage ? "Enviando..." : "Salvar foto do insumo"}
                </button>
              </div>
            </form>

            <form
              onSubmit={(event) => void handleUploadDishImage(event)}
              className="rounded-xl border border-border bg-bg p-4"
            >
              <h4 className="text-base font-semibold text-text">Foto do prato</h4>
              <p className="mt-1 text-xs text-muted">
                Esta imagem sera usada no cardapio do portal e da area do cliente.
              </p>
              <div className="mt-3 grid gap-3">
                <label className="grid gap-1 text-sm text-muted">
                  Prato
                  <select
                    value={selectedDishImageId}
                    onChange={(event) => setSelectedDishImageId(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  >
                    <option value="">Selecione</option>
                    {dishes.map((dish) => (
                      <option key={dish.id} value={dish.id}>
                        {dish.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="grid gap-1 text-sm text-muted">
                  Arquivo de imagem
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(event) =>
                      setDishImageFile(event.currentTarget.files?.[0] ?? null)
                    }
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1 file:text-xs file:font-semibold file:text-white"
                  />
                </label>

                {selectedDishForImage?.image_url && (
                  <Image
                    src={selectedDishForImage.image_url}
                    alt={selectedDishForImage.name}
                    width={640}
                    height={320}
                    className="h-36 w-full rounded-lg border border-border object-cover"
                    unoptimized
                  />
                )}
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={uploadingDishImage || !selectedDishImageId || dishImageFile === null}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {uploadingDishImage ? "Enviando..." : "Salvar foto do prato"}
                </button>
              </div>
            </form>
          </div>

          <section className="mt-4 rounded-xl border border-border bg-bg p-4">
            <h4 className="text-base font-semibold text-text">Pratos recentes com composição</h4>
            {dishesWithComposition.length === 0 && (
              <p className="mt-2 text-sm text-muted">Nenhum prato com composição cadastrado.</p>
            )}
            {dishesWithComposition.length > 0 && (
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {dishesWithComposition.slice(0, 8).map((dish) => (
                  <article key={dish.id} className="rounded-lg border border-border bg-surface px-3 py-2">
                    <p className="text-sm font-semibold text-text">{dish.name}</p>
                    <p className="text-xs text-muted">
                      Rendimento: {dish.yield_portions} porções | Composição: {dish.composition?.length ?? 0} itens
                    </p>
                    {dish.image_url && (
                      <Image
                        src={dish.image_url}
                        alt={dish.name}
                        width={640}
                        height={240}
                        className="mt-2 h-24 w-full rounded-md border border-border object-cover"
                        unoptimized
                      />
                    )}
                    <ul className="mt-1 space-y-1 text-xs text-muted">
                      {(dish.composition ?? []).slice(0, 4).map((compositionItem) => (
                        <li key={compositionItem.id}>
                          {compositionItem.ingredient.name}: {compositionItem.quantity} {toSlugLabel(compositionItem.unit)}
                        </li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {message && (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}
    </section>
  );
}
