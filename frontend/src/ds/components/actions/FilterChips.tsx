import type { HTMLAttributes, ReactNode } from "react";

export type FilterChipOption = {
  value: string;
  label: ReactNode;
  dot?: boolean;
  count?: number | null;
};

export type FilterChipsProps = Omit<HTMLAttributes<HTMLDivElement>, "onChange"> & {
  options?: FilterChipOption[];
  value?: string;
  onChange?: (value: string) => void;
  label?: string;
};

export function FilterChips({ options = [], value, onChange, label = "Filtro", ...rest }: FilterChipsProps) {
  return (
    <div className="eco-chips" role="group" aria-label={label} {...rest}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          className="eco-chip"
          aria-pressed={o.value === value}
          onClick={() => onChange && onChange(o.value)}
        >
          {o.dot && <i className="eco-chip__dot" aria-hidden="true" />}
          {o.label}
          {o.count != null && <span className="eco-chip__n">{o.count}</span>}
        </button>
      ))}
    </div>
  );
}
