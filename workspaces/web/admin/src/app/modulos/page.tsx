"use client";

import Link from "next/link";
import { StatusPill } from "@mrquentinha/ui";

import { AdminSessionGate, useAdminSession } from "@/components/AdminSessionGate";
import { canAccessAdminModule } from "@/lib/adminAccess";
import { ADMIN_MODULES, resolveModuleCardBorder, resolveModuleStatusTone } from "@/lib/adminModules";

function ModulosContent() {
  const { user } = useAdminSession();
  const availableModules = ADMIN_MODULES.filter((moduleItem) =>
    canAccessAdminModule(user, moduleItem.slug),
  );

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-text">Módulos de gestão</h1>
        <p className="mt-2 text-sm text-muted">
          Cada módulo possui hotpage própria, menu contextual e relatórios dedicados.
        </p>
      </section>

      <section className="grid gap-3 md:grid-cols-2">
        {availableModules.map((moduleItem) => (
          <Link
            key={moduleItem.slug}
            href={moduleItem.path}
            className={`rounded-xl border bg-bg p-4 transition hover:border-primary ${resolveModuleCardBorder(moduleItem.status)}`}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-primary">
              {moduleItem.stage}
            </p>
            <h2 className="mt-1 text-base font-semibold text-text">{moduleItem.title}</h2>
            <p className="mt-2 text-sm text-muted">{moduleItem.description}</p>
            <div className="mt-3">
              <StatusPill tone={resolveModuleStatusTone(moduleItem.status)}>
                {moduleItem.status}
              </StatusPill>
            </div>
          </Link>
        ))}
      </section>
    </div>
  );
}

export default function ModulosPage() {
  return (
    <AdminSessionGate>
      <ModulosContent />
    </AdminSessionGate>
  );
}
