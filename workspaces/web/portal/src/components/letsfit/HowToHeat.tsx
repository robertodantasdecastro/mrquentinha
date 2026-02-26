import { Snowflake, Zap, type LucideIcon } from "lucide-react";

export type HeatCardItem = {
  tone?: "cold" | "hot";
  title: string;
  description: string;
};

type HowToHeatProps = {
  title?: string;
  subtitle?: string;
  cards?: HeatCardItem[];
};

const HOW_TO_HEAT_DEFAULTS: Required<HowToHeatProps> = {
  title: "Facil de preparar e armazenar",
  subtitle:
    "Embalagens livres de bisfenol que vao do freezer para o micro-ondas sem perder sabor.",
  cards: [
    {
      tone: "cold",
      title: "Conservacao",
      description:
        "Geladeira por ate 3 dias ou freezer por ate 30 dias mantendo a qualidade.",
    },
    {
      tone: "hot",
      title: "Aquecimento",
      description:
        "Faca um pequeno furo na pelicula e aqueca no micro-ondas por 5 a 7 minutos.",
    },
  ],
};

function resolveCardTone(tone: string | undefined): {
  icon: LucideIcon;
  colorClassName: string;
} {
  if (tone === "cold") {
    return {
      icon: Snowflake,
      colorClassName: "bg-blue-500/10 text-blue-500",
    };
  }

  return {
    icon: Zap,
    colorClassName: "bg-primary/10 text-primary",
  };
}

export function HowToHeat(props: HowToHeatProps) {
  const data = {
    ...HOW_TO_HEAT_DEFAULTS,
    ...props,
  };

  return (
    <section className="border-y border-border bg-surface/50 py-16">
      <div className="mb-12 text-center">
        <h2 className="text-3xl font-bold text-text">{data.title}</h2>
        <p className="mx-auto mt-3 max-w-2xl text-muted">{data.subtitle}</p>
      </div>

      <div className="mx-auto grid max-w-4xl gap-8 px-4 md:grid-cols-2">
        {data.cards.map((card, index) => {
          const tone = resolveCardTone(card.tone);
          const IconComponent = tone.icon;
          return (
            <article
              key={`${card.title}-${index}`}
              className="flex flex-col items-center rounded-2xl border border-border bg-bg p-8 text-center"
            >
              <div
                className={`mb-6 flex h-16 w-16 items-center justify-center rounded-full ${tone.colorClassName}`}
              >
                <IconComponent className="h-8 w-8" />
              </div>
              <h3 className="mb-3 text-xl font-bold text-text">{card.title}</h3>
              <p className="text-sm leading-relaxed text-muted">{card.description}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
