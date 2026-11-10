import type { ElementType, HTMLAttributes } from "react";
import { cx } from "../../cx";

export type EyebrowProps = HTMLAttributes<HTMLElement> & {
  variant?: "eyebrow" | "frame";
  size?: 12 | 13;
  as?: ElementType;
};

export function Eyebrow({ variant = "eyebrow", size = 13, as: Tag = "p", className, children, ...rest }: EyebrowProps) {
  return (
    <Tag
      className={cx(variant === "frame" ? "eco-frame-label" : "eco-eyebrow", size === 12 && "eco-eyebrow--sm", className)}
      {...rest}
    >
      {children}
    </Tag>
  );
}
