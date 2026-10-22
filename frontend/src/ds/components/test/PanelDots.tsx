export type PanelDotsProps = {
  total?: number;
  filled?: number;
  size?: "md" | "lg";
  label?: string;
};

export function PanelDots({ total = 30, filled, size = "md", label }: PanelDotsProps) {
  const f = filled == null ? total : filled;
  return (
    <div
      className={"eco-dots" + (size === "lg" ? " eco-dots--lg" : "")}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      {Array.from({ length: total }, (_, i) => (
        <i key={i} className={i >= f ? "eco-dots--off" : (i + 1) % 3 === 0 ? "eco-dots--a" : ""} />
      ))}
    </div>
  );
}
