import Link from "next/link";
import { Minus, Plus, ShoppingBag } from "lucide-react";

type KitSimulatorProps = {
  kicker?: string;
  headline?: string;
  description?: string;
  ctaLabel?: string;
  ctaHref?: string;
};

const KIT_DEFAULTS: Required<KitSimulatorProps> = {
  kicker: "Nao sabe o que escolher?",
  headline: "Monte seu kit para a semana!",
  description:
    "Selecione a quantidade de dias e o tipo de dieta para receber as melhores sugestoes do cardapio.",
  ctaLabel: "Simular kit personalizado",
  ctaHref: "/cardapio",
};

export function KitSimulator(props: KitSimulatorProps) {
  const data = {
    ...KIT_DEFAULTS,
    ...props,
  };

  return (
    <section className="my-16 flex flex-col items-center justify-between gap-8 rounded-3xl border border-border bg-surface p-8 md:flex-row md:p-12">
      <div className="flex-1">
        <span className="mb-2 block text-sm font-bold uppercase tracking-wider text-primary">
          {data.kicker}
        </span>
        <h2 className="mb-4 text-3xl font-extrabold text-text">{data.headline}</h2>
        <p className="mb-6 leading-relaxed text-muted">{data.description}</p>
        <Link
          href={data.ctaHref}
          className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-semibold text-white shadow-md shadow-primary/20 transition hover:bg-primary-soft"
        >
          <ShoppingBag className="h-5 w-5" />
          {data.ctaLabel}
        </Link>
      </div>

      <div className="w-full max-w-sm flex-1 rounded-2xl border border-border bg-bg p-6 shadow-sm">
        <div className="cursor-not-allowed space-y-6 opacity-70">
          <div className="pointer-events-none flex items-center justify-between">
            <span className="font-semibold text-text">Quantidade de dias</span>
            <div className="flex items-center gap-3">
              <button className="rounded-full border border-border bg-surface p-2 text-muted">
                <Minus className="h-4 w-4" />
              </button>
              <span className="w-4 text-center text-lg font-bold">5</span>
              <button className="rounded-full border border-primary/20 bg-surface p-2 text-primary">
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="pointer-events-none space-y-2">
            <span className="font-semibold text-text">Linha recomendada</span>
            <select
              className="w-full rounded-lg border border-border bg-surface px-3 py-3 text-sm text-text focus:outline-none"
              disabled
            >
              <option>Mais pedidas da semana</option>
            </select>
          </div>
        </div>
      </div>
    </section>
  );
}
