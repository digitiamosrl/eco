import { Button } from "../actions/Button";
import { PanelDots } from "./PanelDots";

export type LaunchBarProps = {
  personas?: number;
  description?: string;
  eta?: string;
  onStart?: () => void;
  loading?: boolean;
  disabled?: boolean;
};

export function LaunchBar({
  personas = 30,
  description = "Decision maker di PMI italiane",
  eta = "circa 3 minuti",
  onStart,
  loading,
  disabled,
}: LaunchBarProps) {
  return (
    <div className="eco-launch">
      <div className="eco-panel">
        <PanelDots total={personas} />
        <div>
          <b>{personas} personas</b>
          <span>{description}</span>
        </div>
      </div>
      <div className="eco-go">
        <Button size="big" onClick={onStart} loading={loading} disabled={disabled || loading}>
          {loading ? "Avvio…" : "Avvia test con " + personas + " personas"}
        </Button>
        <small>{eta}</small>
      </div>
    </div>
  );
}
