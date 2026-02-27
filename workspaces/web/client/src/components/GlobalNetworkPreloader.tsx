"use client";

import { useEffect, useState } from "react";

import { useClientTemplate } from "@/components/ClientTemplateProvider";
import { subscribeNetworkPreloader } from "@/lib/networkPreloader";

export function GlobalNetworkPreloader() {
  const [pendingRequests, setPendingRequests] = useState(0);
  const { template } = useClientTemplate();
  const isQuentinhas = template === "client-quentinhas";
  const isVitrine = template === "client-vitrine-fit";

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
        isQuentinhas ? "bg-primary/15" : "bg-bg/45",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div
        className={[
          "inline-flex items-center gap-3 border px-5 py-3 shadow-lg",
          isQuentinhas
            ? "rounded-2xl border-primary/35 bg-surface/95"
            : isVitrine
              ? "rounded-xl border-border bg-white/95 dark:bg-bg/95"
              : "rounded-full border-border bg-surface/95",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <span
          aria-hidden
          className={[
            "h-5 w-5 animate-spin rounded-full border-2 border-t-primary",
            isQuentinhas ? "border-primary/45" : "border-primary/30",
          ]
            .filter(Boolean)
            .join(" ")}
        />
        <span className="text-sm font-medium text-text">
          {isVitrine ? "Atualizando vitrine de marmitas..." : "Carregando dados do cliente..."}
        </span>
      </div>
    </div>
  );
}
