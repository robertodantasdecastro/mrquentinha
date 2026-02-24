import type { HTMLAttributes, PropsWithChildren } from "react";

type CardProps = PropsWithChildren<
  HTMLAttributes<HTMLDivElement> & {
    tone?: "default" | "surface";
  }
>;

const TONE_CLASS = {
  default: "bg-bg",
  surface: "bg-surface/80",
};

export function Card({
  children,
  className,
  tone = "default",
  ...props
}: CardProps) {
  return (
    <div
      className={[
        "rounded-lg border border-border p-4",
        TONE_CLASS[tone],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
