import { PanelDots } from "./PanelDots";

export type TestProgressProps = {
  done?: number;
  total?: number;
  personas?: number;
  retried?: number;
  status?: "running" | "error";
};

export function TestProgress({ done = 0, total = 90, personas = 30, retried = 0, status = "running" }: TestProgressProps) {
  const pct = total ? Math.round((done / total) * 100) : 0;
  const perPersona = total / personas;
  const complete = Math.floor(done / perPersona);
  return (
    <div className={"eco-progress" + (status === "error" ? " eco-progress--error" : "")}>
      <div className="eco-progress__num" aria-live="polite">
        {done}
        <small>risposte su {total}</small>
      </div>
      <div
        className="eco-progress__track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={done}
        aria-label="Avanzamento del test"
      >
        <div className="eco-progress__fill" style={{ width: pct + "%" }} />
      </div>
      <PanelDots
        total={personas}
        filled={complete}
        label={complete + " personas su " + personas + " hanno risposto a tutte le varianti"}
      />
      <div className="eco-progress__meta">
        <span>
          <b>{complete}</b> personas su {personas} complete
        </span>
        {retried > 0 && (
          <span>
            <b>{retried}</b> {retried === 1 ? "risposta non valida ritentata" : "risposte non valide ritentate"}
          </span>
        )}
      </div>
    </div>
  );
}
