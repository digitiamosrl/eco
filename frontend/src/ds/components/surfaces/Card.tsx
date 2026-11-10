import type { ElementType, HTMLAttributes } from "react";
import { cx } from "../../cx";

export type CardProps = HTMLAttributes<HTMLElement> & {
  variant?: "standard" | "soft" | "dashed" | "winner";
  pad?: "none" | "md" | "lg";
  as?: ElementType;
};

export function Card({ variant = "standard", pad = "md", as: Tag = "div", className, children, ...rest }: CardProps) {
  return (
    <Tag
      className={cx(
        "eco-card",
        variant !== "standard" && "eco-card--" + variant,
        pad === "md" && "eco-card--pad",
        pad === "lg" && "eco-card--pad-lg",
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}
