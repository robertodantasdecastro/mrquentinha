import Link from "next/link";
import Image from "next/image";

type IntroActionTone = "primary" | "soft" | "ghost" | "dark";

type IntroAction = {
  label: string;
  href: string;
  external?: boolean;
  tone?: IntroActionTone;
};

const ACTION_TONE_CLASS: Record<IntroActionTone, string> = {
  primary: "bg-primary text-white hover:bg-primary-soft",
  soft: "border border-primary/40 bg-primary/10 text-primary hover:bg-primary/20",
  ghost: "border border-border bg-bg text-text hover:border-primary hover:text-primary",
  dark: "bg-graphite text-white hover:bg-primary",
};

function actionClassName(tone: IntroActionTone): string {
  return `rounded-md px-4 py-2 text-sm font-semibold transition ${ACTION_TONE_CLASS[tone]}`;
}

function PortalAction({
  label,
  href,
  external = false,
  tone = "ghost",
}: IntroAction) {
  const className = actionClassName(tone);

  if (external) {
    return (
      <a className={className} href={href} target="_blank" rel="noreferrer">
        {label}
      </a>
    );
  }

  return (
    <Link className={className} href={href}>
      {label}
    </Link>
  );
}

export function PortalPageIntro({
  kicker,
  title,
  description,
  actions = [],
  imageUrl = "",
}: {
  kicker: string;
  title: string;
  description: string;
  actions?: IntroAction[];
  imageUrl?: string;
}) {
  return (
    <section className="portal-page-intro rounded-lg border border-border bg-bg p-6 md:p-8">
      {imageUrl && (
        <Image
          src={imageUrl}
          alt={title}
          width={1200}
          height={420}
          className="mb-5 h-44 w-full rounded-lg border border-border object-cover md:h-56"
          unoptimized
        />
      )}
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
        {kicker}
      </p>
      <h1 className="mt-2 text-3xl font-bold text-text md:text-4xl">{title}</h1>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-muted md:text-base">
        {description}
      </p>
      {actions.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-3">
          {actions.map((action) => (
            <PortalAction key={`${action.href}:${action.label}`} {...action} />
          ))}
        </div>
      )}
    </section>
  );
}
