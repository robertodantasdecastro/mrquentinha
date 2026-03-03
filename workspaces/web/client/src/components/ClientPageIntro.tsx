import Link from "next/link";
import Image from "next/image";

type IntroActionTone = "primary" | "soft" | "ghost";

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
};

function actionClassName(tone: IntroActionTone): string {
  return `rounded-md px-4 py-2 text-sm font-semibold transition ${ACTION_TONE_CLASS[tone]}`;
}

function IntroActionLink({
  label,
  href,
  external = false,
  tone = "ghost",
}: IntroAction) {
  if (external) {
    return (
      <a className={actionClassName(tone)} href={href} target="_blank" rel="noreferrer">
        {label}
      </a>
    );
  }

  return (
    <Link className={actionClassName(tone)} href={href}>
      {label}
    </Link>
  );
}

export function ClientPageIntro({
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
    <section className="client-page-intro rounded-2xl border border-border bg-surface/70 p-5 md:p-6">
      {imageUrl && (
        <Image
          src={imageUrl}
          alt={title}
          width={1200}
          height={360}
          className="mb-4 h-40 w-full rounded-lg border border-border object-cover md:h-52"
          unoptimized
        />
      )}
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
        {kicker}
      </p>
      <h1 className="mt-2 text-2xl font-bold text-text md:text-3xl">{title}</h1>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-muted md:text-base">
        {description}
      </p>
      {actions.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-3">
          {actions.map((action) => (
            <IntroActionLink key={`${action.href}:${action.label}`} {...action} />
          ))}
        </div>
      )}
    </section>
  );
}
