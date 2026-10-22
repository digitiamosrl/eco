import type { ReactNode } from "react";
import { Card } from "../surfaces/Card";

export type QuotaRow = {
  label: string;
  count: number;
};

export type QuotaCardProps = {
  title?: ReactNode;
  rows?: QuotaRow[];
};

export function QuotaCard({ title, rows = [] }: QuotaCardProps) {
  const sorted = [...rows].sort((a, b) => b.count - a.count);
  const max = Math.max(1, ...rows.map((r) => r.count));
  return (
    <Card pad="none" className="eco-quota">
      <h3>{title}</h3>
      <ul className="eco-quota__rows">
        {sorted.map((r) => (
          <li key={r.label} className="eco-quota__row">
            <span className="eco-quota__lbl">{r.label}</span>
            <span className="eco-quota__n">{r.count}</span>
            <span className="eco-quota__bar" aria-hidden="true">
              <i style={{ width: (r.count / max) * 100 + "%" }} />
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
