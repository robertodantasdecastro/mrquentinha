import type { HTMLAttributes, PropsWithChildren } from "react";

type ContainerProps = PropsWithChildren<HTMLAttributes<HTMLDivElement>>;

export function Container({ children, className, ...props }: ContainerProps) {
  return (
    <div
      className={["mx-auto w-full max-w-6xl px-4 md:px-6", className]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
