import {
  CheckCircle2,
  Clock,
  CreditCard,
  Package,
  Truck,
  type LucideIcon,
} from "lucide-react";

export type BenefitItem = {
  text: string;
  icon?: string;
};

type BenefitsBarProps = {
  items?: BenefitItem[];
};

const ICON_BY_KEY: Record<string, LucideIcon> = {
  clock: Clock,
  truck: Truck,
  check: CheckCircle2,
  card: CreditCard,
};

const BENEFITS_DEFAULTS: BenefitItem[] = [
  { text: "Pronto em 5 min", icon: "clock" },
  { text: "Entrega agendada", icon: "truck" },
  { text: "Ingredientes selecionados", icon: "check" },
  { text: "Pagamento no app", icon: "card" },
];

function resolveIcon(iconKey?: string): LucideIcon {
  if (iconKey && ICON_BY_KEY[iconKey]) {
    return ICON_BY_KEY[iconKey];
  }
  return Package;
}

export function BenefitsBar({ items = BENEFITS_DEFAULTS }: BenefitsBarProps) {
  return (
    <section className="flex flex-wrap justify-center gap-6 border-y border-border bg-surface px-4 py-6 md:gap-12 md:px-8">
      {items.map((benefit, index) => {
        const IconComponent = resolveIcon(benefit.icon);
        return (
          <div key={`${benefit.text}-${index}`} className="flex items-center gap-3">
            <IconComponent className="h-6 w-6 text-primary" />
            <span className="text-sm font-medium text-text">{benefit.text}</span>
          </div>
        );
      })}
    </section>
  );
}
