import { cx } from "../../cx";

const fmt = (n: number) => n.toFixed(1).replace(".", ",");
const WORDS = ["zero", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove", "dieci"];

export type ScoreBlockProps = {
  mean?: number | null;
  /** Numero di voti per ciascun valore da 1 a 5. */
  distribution?: Partial<Record<1 | 2 | 3 | 4 | 5, number>>;
  tone?: "primary" | "secondary";
  maxBar?: number;
};

export function ScoreBlock({ mean, distribution = {}, tone = "primary", maxBar = 76 }: ScoreBlockProps) {
  const counts = ([1, 2, 3, 4, 5] as const).map((k) => distribution[k] || 0);
  const n = counts.reduce((a, b) => a + b, 0);
  const max = Math.max(1, ...counts);
  const label = "Voti: " + counts.map((c, i) => i + 1 + " " + (WORDS[c] || c)).join(", ");
  return (
    <div className={cx("eco-score", tone === "secondary" && "eco-score--secondary")}>
      <div className="eco-mean">
        {mean == null ? "–" : fmt(mean)}
        <small>
          media · {n} {n === 1 ? "risposta" : "risposte"}
        </small>
      </div>
      <div className="eco-dist" role="img" aria-label={label}>
        {counts.map((c, i) => (
          <div key={i} className="eco-dist__col">
            <b>{c}</b>
            <i
              className={c === 0 ? "eco-dist__zero" : ""}
              style={c ? { height: Math.round((c / max) * maxBar) } : undefined}
            />
          </div>
        ))}
      </div>
      <div className="eco-axis" aria-hidden="true">
        <span>1</span>
        <span>2</span>
        <span>3</span>
        <span>4</span>
        <span>5</span>
      </div>
      <div className="eco-axis-label" aria-hidden="true">
        voto
      </div>
    </div>
  );
}
