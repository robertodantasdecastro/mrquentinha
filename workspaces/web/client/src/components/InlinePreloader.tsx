"use client";

import { useClientTemplate } from "@/components/ClientTemplateProvider";

type InlinePreloaderProps = {
  message: string;
  className?: string;
};

export function InlinePreloader({ message, className = "" }: InlinePreloaderProps) {
  const { template } = useClientTemplate();
  const isQuentinhas = template === "client-quentinhas";
  const isVitrine = template === "client-vitrine-fit";

  return (
    <div
      role="status"
      aria-live="polite"
      className={[
        "inline-flex w-full items-center justify-center gap-3 border px-4 py-4 text-sm",
        isQuentinhas
          ? "rounded-2xl border-primary/35 bg-surface/85 text-muted"
          : isVitrine
            ? "rounded-2xl border-border bg-white/85 text-muted shadow-sm dark:bg-bg/85"
            : "rounded-xl border-border bg-bg text-muted",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span
        aria-hidden
        className={[
          "h-4 w-4 animate-spin rounded-full border-2 border-t-primary",
          isQuentinhas ? "border-primary/40" : "border-primary/25",
        ]
          .filter(Boolean)
          .join(" ")}
      />
      <span>{message}</span>
    </div>
  );
}
