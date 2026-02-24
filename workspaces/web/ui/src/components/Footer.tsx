import type { HTMLAttributes, PropsWithChildren } from "react";

type AppFooterProps = PropsWithChildren<HTMLAttributes<HTMLElement>>;

export function AppFooter({ children, className, ...props }: AppFooterProps) {
  return (
    <footer
      className={["border-t border-border bg-surface/70", className]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </footer>
  );
}
