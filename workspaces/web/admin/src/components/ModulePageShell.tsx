import type { ReactNode } from "react";

import { StatusPill, type StatusTone } from "@mrquentinha/ui";

export type ModuleMenuItem = {
  label: string;
  href: string;
  helper?: string;
};

type ModulePageShellProps = {
  title: string;
  description: string;
  statusLabel?: string;
  statusTone?: StatusTone;
  menuItems: ModuleMenuItem[];
  children: ReactNode;
};

export function ModulePageShell({
  title,
  description,
  statusLabel,
  statusTone = "info",
  menuItems,
  children,
}: ModulePageShellProps) {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Admin Web</p>
            <h1 className="mt-1 text-2xl font-bold text-text">{title}</h1>
            <p className="mt-2 text-sm text-muted">{description}</p>
          </div>
          {statusLabel && (
            <StatusPill tone={statusTone} className="mt-1">
              {statusLabel}
            </StatusPill>
          )}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {menuItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-full border border-border bg-bg px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-text transition hover:border-primary hover:text-primary"
            >
              {item.label}
            </a>
          ))}
        </div>
      </section>
      {children}
    </div>
  );
}
