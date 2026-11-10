import type { HTMLAttributes } from "react";
import { Icon } from "../icons/Icon";

export type ThoughtProps = HTMLAttributes<HTMLParagraphElement> & {
  diverge?: boolean;
};

export function Thought({ children, diverge, ...rest }: ThoughtProps) {
  return (
    <p className={"eco-thought" + (diverge ? " eco-thought--diverge" : "")} {...rest}>
      {diverge && (
        <span className="eco-gap-tag">
          <Icon name="diverge" strokeWidth={3} />
          Diverge
        </span>
      )}
      {diverge ? <span className="eco-thought__text">{children}</span> : children}
    </p>
  );
}
