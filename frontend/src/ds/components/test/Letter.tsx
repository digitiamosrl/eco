import type { HTMLAttributes } from "react";

export type LetterProps = HTMLAttributes<HTMLSpanElement> & {
  size?: "md" | "sm";
};

export function Letter({ children, size = "md", ...rest }: LetterProps) {
  return (
    <span className={"eco-letter" + (size === "sm" ? " eco-letter--sm" : "")} aria-hidden="true" {...rest}>
      {children}
    </span>
  );
}
