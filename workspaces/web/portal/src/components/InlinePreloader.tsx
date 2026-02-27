"use client";

import { useTemplate } from "@/components/TemplateProvider";

type InlinePreloaderProps = {
  message: string;
  className?: string;
};

export function InlinePreloader({ message, className = "" }: InlinePreloaderProps) {
  const { template } = useTemplate();
  const isLetsfit = template === "letsfit-clean";

  return (
    <div
      role="status"
      aria-live="polite"
      className={[
        "inline-flex w-full items-center justify-center gap-3 border px-4 py-4 text-sm",
        isLetsfit
          ? "rounded-xl border-primary/30 bg-white/90 text-muted shadow-sm dark:bg-surface/80"
          : "rounded-md border-border bg-bg text-muted",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span
        aria-hidden
        className={[
          "h-4 w-4 animate-spin rounded-full border-2 border-t-primary",
          isLetsfit ? "border-primary/40" : "border-primary/25",
        ]
          .filter(Boolean)
          .join(" ")}
      />
      <span>{message}</span>
    </div>
  );
}
