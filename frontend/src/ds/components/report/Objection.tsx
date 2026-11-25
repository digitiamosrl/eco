import type { ReactNode } from "react";

export type ObjectionProps = {
  children?: ReactNode;
  count?: number | null;
  label?: string;
};

export function Objection({ children, count, label = "Obiezione" }: ObjectionProps) {
  return (
    <div className="eco-objection">
      <span>{label}</span>
      {children}
      {count != null && (
        <em className="eco-objection__n" style={{ fontStyle: "normal" }}>
          · {count} {count === 1 ? "persona" : "personas"}
        </em>
      )}
    </div>
  );
}
