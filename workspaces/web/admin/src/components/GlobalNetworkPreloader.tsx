"use client";

import { useEffect, useState } from "react";

import { useAdminTemplate } from "@/components/AdminTemplateProvider";
import { subscribeNetworkPreloader } from "@/lib/networkPreloader";

export function GlobalNetworkPreloader() {
  const [pendingRequests, setPendingRequests] = useState(0);
  const { template } = useAdminTemplate();
  const isAdminKit = template === "admin-adminkit";
  const isAdminDek = template === "admin-admindek";

  useEffect(() => {
    return subscribeNetworkPreloader((pending) => {
      setPendingRequests(pending);
    });
  }, []);

  if (pendingRequests <= 0) {
    return null;
  }

  return (
    <div
      className={[
        "pointer-events-none fixed inset-0 z-[120] flex items-center justify-center backdrop-blur-[2px]",
        isAdminKit || isAdminDek ? "bg-slate-950/28" : "bg-bg/45",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div
        className={[
          "inline-flex items-center gap-3 border px-5 py-3 shadow-lg",
          isAdminKit
            ? "rounded-xl border-slate-300 bg-white/95 dark:border-slate-700 dark:bg-slate-900/95"
            : isAdminDek
              ? "rounded-xl border-primary/40 bg-white/95 dark:border-primary/35 dark:bg-slate-900/95"
            : "rounded-full border-border bg-surface/95",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <span
          aria-hidden
          className={[
            "h-5 w-5 animate-spin rounded-full border-2 border-t-primary",
            isAdminKit || isAdminDek ? "border-primary/45" : "border-primary/30",
          ]
            .filter(Boolean)
            .join(" ")}
        />
        <span className="text-sm font-medium text-text">
          {isAdminKit || isAdminDek
            ? "Sincronizando operacao..."
            : "Carregando dados do Admin..."}
        </span>
      </div>
    </div>
  );
}
