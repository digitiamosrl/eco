import type { CSSProperties, HTMLAttributes, ReactNode } from "react";
import { cx } from "../../cx";

export type ScreenProps = HTMLAttributes<HTMLDivElement> & {
  nav?: ReactNode;
  bodyStyle?: CSSProperties;
};

export function Screen({ nav, children, className, bodyStyle, ...rest }: ScreenProps) {
  return (
    <div className={cx("eco-screen", className)} {...rest}>
      {nav}
      <div className="eco-body" style={bodyStyle}>
        {children}
      </div>
    </div>
  );
}
