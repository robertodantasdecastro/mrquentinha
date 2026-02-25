"use client";

import Link from "next/link";
import { StatusPill } from "@mrquentinha/ui";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ADMIN_MODULES, resolveModuleCardBorder, resolveModuleStatusTone } from "@/lib/adminModules";

export default function ModulosPage() {
  return (
    <AdminSessionGate>
      <div className="space-y-6">
        <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-text">Modulos de gestao</h1>
          <p className="mt-2 text-sm text-muted">
            Cada modulo possui hotpage propria, menu contextual e relatorios dedicados.
          </p>
        </section>

        <section className="grid gap-3 md:grid-cols-2">
          {ADMIN_MODULES.map((moduleItem) => (
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
    </AdminSessionGate>
  );
}
