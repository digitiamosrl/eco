import type { ReactNode } from "react";

export type ObjectionProps = {
  children?: ReactNode;
  count?: number | null;
};

export function Objection({ children, count }: ObjectionProps) {
  return (
    <div className="eco-objection">
      <span>Obiezione</span>
      {children}
      {count != null && (
        <em className="eco-objection__n" style={{ fontStyle: "normal" }}>
          · {count} {count === 1 ? "persona" : "personas"}
        </em>
      )}
    </div>
  );
}
