import type { InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      className={[
        "w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text outline-none transition focus:border-primary",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
}
