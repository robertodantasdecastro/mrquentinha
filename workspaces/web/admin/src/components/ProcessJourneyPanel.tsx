"use client";

import Link from "next/link";

import { useAdminTemplate } from "@/components/AdminTemplateProvider";
import { PROCESS_JOURNEY_STEPS } from "@/lib/processJourney";

export function ProcessJourneyPanel() {
  const { template } = useAdminTemplate();
  const isAdminDek = template === "admin-admindek";

  return (
    <section
      className={[
        "rounded-2xl border border-border bg-surface/80 p-6 shadow-sm",
        isAdminDek ? "bg-white/90 dark:bg-surface/85" : "",
      ].join(" ")}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Passo a passo operacional
          </p>
          <h2 className="mt-1 text-xl font-semibold text-text">
            Jornada guiada da operacao diaria
          </h2>
          <p className="mt-1 text-sm text-muted">
            Siga da primeira etapa ate o fechamento de relatorios com navegacao assistida.
          </p>
        </div>
        <Link
          href="/modulos/fluxo-operacional"
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
        >
          Abrir modo guiado
        </Link>
      </div>

      <ol
        className={[
          "mt-4 grid gap-3 lg:grid-cols-3",
          isAdminDek ? "relative lg:gap-4" : "",
        ].join(" ")}
      >
        {PROCESS_JOURNEY_STEPS.map((step, index) => (
          <li
            key={step.slug}
            className={[
              "rounded-xl border border-border bg-bg p-4",
              isAdminDek ? "relative overflow-hidden" : "",
            ].join(" ")}
          >
            {isAdminDek && (
              <span className="mb-2 inline-flex rounded-full border border-primary/35 bg-primary/10 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-primary">
                etapa {index + 1}
              </span>
            )}
            <h3 className="text-sm font-semibold text-text">{step.title}</h3>
            <p className="mt-2 text-sm text-muted">{step.description}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link
                href={`/modulos/fluxo-operacional/${step.slug}`}
                className="rounded-full border border-primary px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-primary transition hover:bg-primary/10"
              >
                Etapa guiada
              </Link>
              <Link
                href={step.moduleHref}
                className="rounded-full border border-border px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-muted transition hover:border-primary hover:text-primary"
              >
                {step.moduleLabel}
              </Link>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
