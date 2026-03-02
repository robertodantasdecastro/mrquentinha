"use client";

type ModuleGuideStep = {
  title: string;
  description: string;
};

type ModuleGuideProps = {
  title: string;
  summary: string;
  steps: ModuleGuideStep[];
  note?: string;
};

export function ModuleGuide({ title, summary, steps, note }: ModuleGuideProps) {
  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-primary">
            Guia do modulo
          </p>
          <h2 className="mt-1 text-lg font-semibold text-text">{title}</h2>
          <p className="mt-1 text-sm text-muted">{summary}</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {steps.map((step, index) => (
          <article key={`${step.title}-${index}`} className="rounded-xl border border-border bg-bg p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Passo {index + 1}
            </p>
            <p className="mt-2 text-sm font-semibold text-text">{step.title}</p>
            <p className="mt-1 text-xs text-muted">{step.description}</p>
          </article>
        ))}
      </div>

      {note && (
        <p className="mt-4 rounded-lg border border-border bg-bg px-3 py-2 text-xs text-muted">
          {note}
        </p>
      )}
    </section>
  );
}
