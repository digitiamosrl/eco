import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "../../cx";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "light";
  size?: "md" | "big";
  block?: boolean;
  loading?: boolean;
  icon?: ReactNode;
};

export function Button({
  variant = "primary",
  size = "md",
  block,
  loading,
  icon,
  className,
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cx(
        "eco-btn",
        variant === "light" && "eco-btn--light",
        size === "big" && "eco-btn--big",
        block && "eco-btn--block",
        className,
      )}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <span className="eco-btn__spin" aria-hidden="true" /> : icon}
      {children}
    </button>
  );
}
