import { cx } from "../../cx";

export type ScreenStripScreen = {
  name: string;
  image?: string;
  abandon?: number;
};

export type ScreenStripProps = {
  screens?: ScreenStripScreen[];
  selected?: number;
  onSelect?: (index: number) => void;
  unit?: string;
};

export function ScreenStrip({ screens = [], selected, onSelect, unit = "abbandoni" }: ScreenStripProps) {
  const max = Math.max(1, ...screens.map((s) => s.abandon || 0));
  const crit = screens.reduce((b, s, i) => ((s.abandon || 0) > (screens[b]?.abandon || 0) ? i : b), 0);
  return (
    <div className="eco-strip" role="group" aria-label="Schermate del flusso">
      {screens.map((s, i) => (
        <button
          key={i}
          type="button"
          className={cx("eco-shot", i === crit && !!s.abandon && "eco-shot--critical")}
          aria-pressed={selected === i}
          onClick={() => onSelect && onSelect(i)}
        >
          <div className="eco-shot__img">
            {s.image ? <img src={s.image} alt={"Schermata " + (i + 1) + ": " + s.name} /> : "Cattura " + (i + 1)}
          </div>
          <div className="eco-shot__top">
            <span className="eco-shot__n">{i + 1}</span>
            <span className="eco-shot__name">{s.name}</span>
          </div>
          <div className="eco-shot__bar" aria-hidden="true">
            <i style={{ width: ((s.abandon || 0) / max) * 100 + "%" }} />
          </div>
          <div className="eco-shot__count">
            <b>{s.abandon || 0}</b> {s.abandon === 1 ? unit.replace(/i$/, "o") : unit}
          </div>
          {i === crit && (s.abandon || 0) > 0 && <span className="eco-shot__tag">Punto critico</span>}
        </button>
      ))}
    </div>
  );
}
