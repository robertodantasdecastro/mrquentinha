import Link from "next/link";
import { ArrowRight, Info } from "lucide-react";

type HeroLetsFitProps = {
  kicker?: string;
  headline?: string;
  subheadline?: string;
  ctaPrimaryLabel?: string;
  ctaPrimaryHref?: string;
  ctaSecondaryLabel?: string;
  ctaSecondaryHref?: string;
  backgroundImageUrl?: string;
};

const HERO_DEFAULTS: Required<HeroLetsFitProps> = {
  kicker: "Comida de verdade, pronta em minutos",
  headline: "Sua rotina mais leve e saborosa",
  subheadline:
    "Marmitas saudaveis, balanceadas e feitas com ingredientes selecionados.",
  ctaPrimaryLabel: "Ver cardapio de hoje",
  ctaPrimaryHref: "/cardapio",
  ctaSecondaryLabel: "Como funciona",
  ctaSecondaryHref: "/como-funciona",
  backgroundImageUrl: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
};

export function HeroLetsFit(props: HeroLetsFitProps) {
  const data = {
    ...HERO_DEFAULTS,
    ...props,
  };
  const backgroundStyle = `url('${data.backgroundImageUrl}')`;

  return (
    <section className="relative overflow-hidden rounded-2xl bg-surface p-8 text-center md:p-16">
      <div
        className="absolute inset-0 z-0 opacity-10 bg-cover bg-center"
        style={{ backgroundImage: backgroundStyle }}
      />

      <div className="relative z-10 mx-auto flex max-w-2xl flex-col items-center gap-6">
        <span className="inline-block rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
          {data.kicker}
        </span>

        <h1 className="text-4xl font-extrabold tracking-tight text-text md:text-6xl">
          {data.headline}
        </h1>

        <p className="text-lg leading-relaxed text-muted">{data.subheadline}</p>

        <div className="flex w-full flex-col items-center justify-center gap-4 sm:w-auto sm:flex-row">
          <Link
            href={data.ctaPrimaryHref}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-primary px-8 py-4 text-base font-bold text-white transition hover:bg-primary-soft sm:w-auto"
          >
            {data.ctaPrimaryLabel}
            <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            href={data.ctaSecondaryHref}
            className="flex w-full items-center justify-center gap-2 rounded-full border-2 border-primary/20 bg-transparent px-8 py-4 text-base font-bold text-text transition hover:border-primary hover:text-primary sm:w-auto"
          >
            {data.ctaSecondaryLabel}
            <Info className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </section>
  );
}
