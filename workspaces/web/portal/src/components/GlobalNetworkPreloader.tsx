"use client";

import { useEffect, useState } from "react";

import { useTemplate } from "@/components/TemplateProvider";
import { subscribeNetworkPreloader } from "@/lib/networkPreloader";

export function GlobalNetworkPreloader() {
  const [pendingRequests, setPendingRequests] = useState(0);
  const { template } = useTemplate();
  const isLetsfit = template === "letsfit-clean";

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
        isLetsfit ? "bg-primary/12" : "bg-bg/45",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div
        className={[
          "inline-flex items-center gap-3 border px-5 py-3 shadow-lg",
          isLetsfit
            ? "rounded-xl border-primary/30 bg-white/95 dark:bg-surface/90"
            : "rounded-full border-border bg-surface/95",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <span
          aria-hidden
          className={[
            "h-5 w-5 animate-spin rounded-full border-2 border-t-primary",
            isLetsfit ? "border-primary/45" : "border-primary/30",
          ]
            .filter(Boolean)
            .join(" ")}
        />
        <span className="text-sm font-medium text-text">
          {isLetsfit ? "Atualizando vitrine institucional..." : "Carregando dados do portal..."}
        </span>
      </div>
    </div>
  );
}
