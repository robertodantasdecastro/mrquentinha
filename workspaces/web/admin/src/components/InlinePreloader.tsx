"use client";

import { useAdminTemplate } from "@/components/AdminTemplateProvider";

type InlinePreloaderProps = {
  message: string;
  className?: string;
};

export function InlinePreloader({ message, className = "" }: InlinePreloaderProps) {
  const { template } = useAdminTemplate();
  const isAdminKit = template === "admin-adminkit";
  const isAdminDek = template === "admin-admindek";

  return (
    <div
      role="status"
      aria-live="polite"
      className={[
        "inline-flex w-full items-center justify-center gap-3 border border-border px-4 py-4 text-sm",
        isAdminKit
          ? "rounded-lg bg-white/90 text-slate-600 shadow-sm dark:bg-slate-900/75 dark:text-slate-200"
          : isAdminDek
            ? "rounded-xl bg-white/95 text-slate-600 shadow-sm dark:bg-slate-900/80 dark:text-slate-100"
          : "rounded-md bg-bg text-muted",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span
        aria-hidden
        className={[
          "h-4 w-4 animate-spin rounded-full border-2 border-t-primary",
          isAdminKit || isAdminDek ? "border-primary/40" : "border-primary/25",
        ]
          .filter(Boolean)
          .join(" ")}
      />
      <span>{message}</span>
    </div>
  );
}
