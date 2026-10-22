import type { HTMLAttributes, ReactNode } from "react";

export type SegmentedOption = {
  value: string;
  label: ReactNode;
  icon?: ReactNode;
};

export type SegmentedProps = Omit<HTMLAttributes<HTMLDivElement>, "onChange"> & {
  options?: SegmentedOption[];
  value?: string;
  onChange?: (value: string) => void;
  label?: string;
};

export function Segmented({ options = [], value, onChange, label = "Modalità", ...rest }: SegmentedProps) {
  return (
    <div className="eco-seg" role="tablist" aria-label={label} {...rest}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="tab"
          className="eco-seg__opt"
          aria-selected={o.value === value}
          onClick={() => onChange && onChange(o.value)}
        >
          {o.icon}
          {o.label}
        </button>
      ))}
    </div>
  );
}
