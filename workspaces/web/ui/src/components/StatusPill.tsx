import type { HTMLAttributes, PropsWithChildren } from "react";

export type StatusTone =
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral"
  | "brand";

type StatusPillProps = PropsWithChildren<
  HTMLAttributes<HTMLSpanElement> & {
    tone?: StatusTone;
  }
>;

const TONE_CLASS: Record<StatusTone, string> = {
  success: "border-status-success/40 bg-status-success-soft text-status-success",
  warning: "border-status-warning/40 bg-status-warning-soft text-status-warning",
  danger: "border-status-danger/40 bg-status-danger-soft text-status-danger",
  info: "border-status-info/40 bg-status-info-soft text-status-info",
  neutral: "border-border bg-surface text-muted",
  brand: "border-primary/40 bg-primary/10 text-primary",
};

export function StatusPill({
  children,
  className,
  tone = "neutral",
  ...props
}: StatusPillProps) {
  return (
    <span
      className={[
        "inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.08em]",
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
