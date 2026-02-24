import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
  }
>;

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-white hover:bg-primary-soft disabled:bg-border disabled:text-muted",
  secondary:
    "border border-border bg-bg text-text hover:border-primary hover:text-primary disabled:text-muted",
  ghost: "text-muted hover:text-primary",
};

const SIZE_CLASS: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-3 text-sm",
};

export function Button({
  children,
  className,
  variant = "primary",
  size = "md",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={[
        "rounded-md font-semibold transition disabled:cursor-not-allowed",
        VARIANT_CLASS[variant],
        SIZE_CLASS[size],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
