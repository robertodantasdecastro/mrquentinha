"use client";

import { Badge, Card, Input } from "@mrquentinha/ui";
import Image from "next/image";
import { useEffect, useMemo, useState, type ChangeEvent } from "react";

import { InlinePreloader } from "@/components/InlinePreloader";
import { trackNetworkRequest } from "@/lib/networkPreloader";

type DishData = {
  id: number;
  name: string;
  description?: string | null;
  image_url?: string | null;
  composition?: {
    id: number;
    ingredient: {
      id: number;
      name: string;
      image_url?: string | null;
    };
    quantity: string;
    unit: string;
  }[];
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

type CardapioState = "loading" | "empty" | "loaded" | "error";
const RUNTIME_API_CONFIG_ENDPOINT = "/api/runtime/config";
const RUNTIME_API_CACHE_TTL_MS = 15_000;

let runtimeApiBaseUrlCache = "";
let runtimeApiCacheExpiresAt = 0;

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

function resolveBrowserApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  if (!hostname) {
    return "";
  }

  return `${protocol}//${hostname}:8000`;
}

function resolveApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "") ?? "";
  if (envUrl) {
    return envUrl;
  }

  return resolveBrowserApiBaseUrl();
}

async function resolveRuntimeApiBaseUrl(fallback: string): Promise<string> {
  if (typeof window === "undefined") {
    return fallback;
  }

  const now = Date.now();
  if (runtimeApiBaseUrlCache && now < runtimeApiCacheExpiresAt) {
    return runtimeApiBaseUrlCache;
  }

  try {
    const response = await fetch(RUNTIME_API_CONFIG_ENDPOINT, {
      cache: "no-store",
    });
    if (!response.ok) {
      return runtimeApiBaseUrlCache || fallback;
    }

    const payload = (await response.json()) as { api_base_url?: unknown };
    const resolved = String(payload.api_base_url ?? "").trim().replace(/\/$/, "");
    if (!resolved) {
      return runtimeApiBaseUrlCache || fallback;
    }

    runtimeApiBaseUrlCache = resolved;
    runtimeApiCacheExpiresAt = now + RUNTIME_API_CACHE_TTL_MS;
    return runtimeApiBaseUrlCache;
  } catch {
    return runtimeApiBaseUrlCache || fallback;
  }
}

export function CardapioList() {
  const [selectedDate, setSelectedDate] = useState<string>(getDefaultDate());
  const [menu, setMenu] = useState<MenuDayData | null>(null);
  const [state, setState] = useState<CardapioState>("loading");
  const [message, setMessage] = useState<string>("Carregando cardapio...");

  const apiBaseUrl = useMemo(resolveApiBaseUrl, []);

  useEffect(() => {
    let isMounted = true;

    async function fetchMenuByDate() {
      const resolvedApiBaseUrl = await resolveRuntimeApiBaseUrl(apiBaseUrl);
      if (!resolvedApiBaseUrl) {
        if (isMounted) {
          setMenu(null);
          setState("error");
          setMessage(
            "Nao foi possivel identificar a API do backend para carregar o cardapio.",
          );
        }
        return;
      }

      if (isMounted) {
        setState("loading");
        setMessage("Carregando cardapio...");
      }

      try {
        const isToday = selectedDate === getDefaultDate();
        const endpoint = isToday
          ? `/api/v1/catalog/menus/today/`
          : `/api/v1/catalog/menus/by-date/${selectedDate}/`;

        const response = await trackNetworkRequest(() =>
          fetch(`${resolvedApiBaseUrl}${endpoint}`, {
            cache: "no-store",
          }),
        );

        if (response.status === 404) {
          if (isMounted) {
            setMenu(null);
            setState("empty");
            setMessage(`Sem cardapio cadastrado para ${selectedDate}.`);
          }
          return;
        }

        if (!response.ok) {
          let errorMessage = `Falha ao consultar cardapio (HTTP ${response.status}).`;

          try {
            const payload = (await response.json()) as { detail?: string };
            if (payload?.detail) {
              errorMessage = payload.detail;
            }
          } catch {
            // Mantem mensagem padrao quando resposta nao tiver JSON.
          }

          throw new Error(errorMessage);
        }

        const payload: MenuDayData = await response.json();

        if (isMounted) {
          setMenu(payload);
          setState("loaded");
          setMessage("");
        }
      } catch (fetchError) {
        if (isMounted) {
          setMenu(null);
          setState("error");
          setMessage(
            fetchError instanceof Error
              ? fetchError.message
              : "Falha ao consultar o cardapio. Tente novamente.",
          );
        }
      }
    }

    fetchMenuByDate();

    return () => {
      isMounted = false;
    };
  }, [apiBaseUrl, selectedDate]);

  return (
    <Card tone="surface" className="p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <Badge>Consulta em tempo real</Badge>
          <h2 className="mt-2 text-2xl font-bold text-text">Cardapio por data</h2>
        </div>

        <label className="flex flex-col gap-1 text-sm font-medium text-muted">
          Selecione a data
          <Input
            name="menu_date"
            type="date"
            value={selectedDate}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setSelectedDate(event.target.value)}
            className="w-auto"
          />
        </label>
      </div>

      <div className="mt-6">
        {state === "loading" && (
          <InlinePreloader message={message} className="py-8" />
        )}

        {state === "error" && (
          <div className="rounded-md border border-red-400/60 bg-red-50 px-4 py-4 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
            {message}
          </div>
        )}

        {state === "empty" && (
          <div className="rounded-md border border-border bg-bg px-4 py-8 text-center text-muted">
            {message}
          </div>
        )}

        {state === "loaded" && menu && (
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
                    <div className="min-w-0">
                      <h4 className="text-base font-semibold text-text">{item.dish.name}</h4>
                      {item.dish.description && (
                        <p className="mt-1 text-sm text-muted">{item.dish.description}</p>
                      )}
                    </div>
                    <p className="text-sm font-semibold text-primary">
                      {formatCurrency(item.sale_price)}
                    </p>
                  </div>

                  {item.dish.image_url && (
                    <Image
                      src={item.dish.image_url}
                      alt={item.dish.name}
                      width={640}
                      height={360}
                      className="mt-3 h-36 w-full rounded-md border border-border object-cover"
                      unoptimized
                    />
                  )}

                  {item.dish.composition && item.dish.composition.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {item.dish.composition.map((component) => (
                        <span
                          key={component.id}
                          className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-2 py-1 text-xs text-muted"
                        >
                          {component.ingredient.image_url && (
                            <Image
                              src={component.ingredient.image_url}
                              alt={component.ingredient.name}
                              width={20}
                              height={20}
                              className="h-5 w-5 rounded-full object-cover"
                              unoptimized
                            />
                          )}
                          {component.ingredient.name}
                        </span>
                      ))}
                    </div>
                  )}

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
    </Card>
  );
}
