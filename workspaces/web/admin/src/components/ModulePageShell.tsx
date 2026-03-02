import type { ReactNode } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import { useAdminSession } from "@/components/AdminSessionGate";
import { useAdminTemplate } from "@/components/AdminTemplateProvider";
import { canAccessAdminModule } from "@/lib/adminAccess";

export type ModuleMenuItem = {
  key: string;
  label: string;
  href: string;
  helper?: string;
};

type ModulePageShellProps = {
  moduleSlug?: string;
  moduleLabel?: string;
  requiredAccess?: "read" | "write";
  title: string;
  description: string;
  statusLabel?: string;
  statusTone?: StatusTone;
  menuItems: ModuleMenuItem[];
  activeKey?: string | null;
  children: ReactNode;
};

export function ModulePageShell({
  moduleSlug,
  moduleLabel,
  requiredAccess = "read",
  title,
  description,
  statusLabel,
  statusTone = "info",
  menuItems,
  activeKey,
  children,
}: ModulePageShellProps) {
  const { template } = useAdminTemplate();
  const { user } = useAdminSession();
  const pathname = usePathname();
  const isAdminKit = template === "admin-adminkit";
  const isAdminDek = template === "admin-admindek";
  const resolvedModuleSlug =
    moduleSlug || pathname.split("/").filter(Boolean).slice(1, 2).join("");
  const resolvedModuleLabel = moduleLabel || title;
  const hasModuleAccess = resolvedModuleSlug
    ? canAccessAdminModule(user, resolvedModuleSlug, requiredAccess)
    : true;

  if (!hasModuleAccess) {
    return (
      <section className="rounded-2xl border border-amber-300 bg-amber-50 p-6 text-amber-900 shadow-sm">
        <h2 className="text-lg font-semibold">Acesso restrito</h2>
        <p className="mt-2 text-sm">
          O módulo <strong>{resolvedModuleLabel}</strong> exige permissão de leitura.
        </p>
        <p className="mt-1 text-sm">
          Solicite ao administrador o acesso do módulo com nível de leitura ou leitura e escrita.
        </p>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section
        className={[
          "rounded-2xl border border-border bg-surface/80 p-6 shadow-sm",
          isAdminKit || isAdminDek ? "bg-white/90 dark:bg-surface/90" : "",
        ].join(" ")}
      >
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
        <div
          className={[
            "mt-4 flex flex-wrap gap-2",
            isAdminKit || isAdminDek ? "rounded-xl border border-border bg-bg p-2" : "",
          ].join(" ")}
        >
          {menuItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "border px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] transition",
                isAdminKit || isAdminDek ? "rounded-lg" : "rounded-full",
                activeKey === item.key
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border bg-bg text-text hover:border-primary hover:text-primary",
              ].join(" ")}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </section>
      {children}
    </div>
  );
}
