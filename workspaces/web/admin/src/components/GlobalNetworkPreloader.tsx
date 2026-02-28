"use client";

import { useEffect, useState } from "react";

import { useAdminTemplate } from "@/components/AdminTemplateProvider";
import { subscribeNetworkPreloader } from "@/lib/networkPreloader";

export function GlobalNetworkPreloader() {
  const [pendingRequests, setPendingRequests] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const { template } = useAdminTemplate();
  const isAdminKit = template === "admin-adminkit";
  const isAdminDek = template === "admin-admindek";

  useEffect(() => {
    return subscribeNetworkPreloader((pending) => {
      setPendingRequests(pending);
    });
  }, []);

  useEffect(() => {
    let timerId: ReturnType<typeof setTimeout> | null = null;

    if (pendingRequests > 0) {
      // Evita flicker em requests curtos e reduz impacto visual no operador.
      timerId = setTimeout(() => setIsVisible(true), 450);
    } else {
      // Mantem a troca de estado assíncrona para evitar render cascata no efeito.
      timerId = setTimeout(() => setIsVisible(false), 80);
    }

    return () => {
      if (timerId) {
        clearTimeout(timerId);
      }
    };
  }, [pendingRequests]);

  const hasPendingRequests = pendingRequests > 0;

  if (!hasPendingRequests && !isVisible) {
    return null;
  }

  return (
    <>
      {hasPendingRequests && (
        <div
          aria-hidden
          className={[
            "pointer-events-none fixed inset-x-0 top-0 z-[119] h-1",
            isAdminKit || isAdminDek
              ? "bg-gradient-to-r from-transparent via-primary/70 to-transparent"
              : "bg-gradient-to-r from-transparent via-primary/50 to-transparent",
          ]
            .filter(Boolean)
            .join(" ")}
        />
      )}
      {isVisible && hasPendingRequests && (
        <div
          aria-live="polite"
          className="pointer-events-none fixed right-3 top-3 z-[120]"
        >
          <div
            className={[
              "inline-flex items-center gap-2 border px-3 py-1.5 shadow-sm",
              isAdminKit
                ? "rounded-lg border-slate-200 bg-white/90 dark:border-slate-700 dark:bg-slate-900/90"
                : isAdminDek
                  ? "rounded-lg border-primary/35 bg-white/90 dark:border-primary/30 dark:bg-slate-900/90"
                  : "rounded-full border-border bg-surface/92",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <span
              aria-hidden
              className={[
                "h-3.5 w-3.5 animate-spin rounded-full border-2 border-t-primary",
                isAdminKit || isAdminDek ? "border-primary/45" : "border-primary/30",
              ]
                .filter(Boolean)
                .join(" ")}
            />
            <span className="text-xs font-medium text-text">
              {isAdminKit || isAdminDek
                ? "Sincronizando em segundo plano..."
                : "Atualizando dados..."}
            </span>
          </div>
        </div>
      )}
    </>
  );
}
