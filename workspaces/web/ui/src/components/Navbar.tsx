import type { HTMLAttributes, PropsWithChildren } from "react";

type NavbarProps = PropsWithChildren<HTMLAttributes<HTMLElement>>;

export function Navbar({ children, className, ...props }: NavbarProps) {
  return (
    <header
      className={[
        "sticky top-0 z-40 border-b border-border/80 bg-bg/95 backdrop-blur",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </header>
  );
}
