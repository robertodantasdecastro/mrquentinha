import type { HTMLAttributes, PropsWithChildren } from "react";

type SectionProps = PropsWithChildren<HTMLAttributes<HTMLElement>>;

export function Section({ children, className, ...props }: SectionProps) {
  return (
    <section className={["space-y-4", className].filter(Boolean).join(" ")} {...props}>
      {children}
    </section>
  );
}
