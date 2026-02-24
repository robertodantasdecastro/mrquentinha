import type { HTMLAttributes, PropsWithChildren } from "react";

type BadgeProps = PropsWithChildren<
  HTMLAttributes<HTMLSpanElement> & {
    tone?: "primary" | "neutral";
  }
>;

const TONE_CLASS = {
  primary: "border-primary/40 bg-primary/10 text-primary",
  neutral: "border-border bg-surface text-muted",
};

export function Badge({
  children,
  className,
  tone = "primary",
  ...props
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em]",
        TONE_CLASS[tone],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </span>
  );
}
