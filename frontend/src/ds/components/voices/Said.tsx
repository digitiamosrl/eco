import type { HTMLAttributes } from "react";

export type SaidProps = HTMLAttributes<HTMLParagraphElement> & {
  empty?: boolean;
};

export function Said({ children, empty, ...rest }: SaidProps) {
  if (empty || !children)
    return (
      <p className="eco-said eco-said--empty" {...rest}>
        non commenterebbe
      </p>
    );
  return (
    <p className="eco-said" {...rest}>
      {children}
    </p>
  );
}
