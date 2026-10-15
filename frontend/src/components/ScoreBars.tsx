import { toBars } from "../lib/distribution";

type Props = { distribution: Record<string, number>; mean: number };

export default function ScoreBars({ distribution, mean }: Props) {
  const bars = toBars(distribution);
  return (
    <figure className="score-bars">
      <figcaption>Distribuzione dei voti (media {mean.toLocaleString("it-IT", { minimumFractionDigits: 1, maximumFractionDigits: 1 })})</figcaption>
      <div
        className="bars"
        role="img"
        aria-label={bars.map((b) => `voto ${b.score}: ${b.count}`).join(", ")}
      >
        {bars.map((b) => (
          <div key={b.score} className="bar" style={{ height: `${b.height * 100}%` }} />
        ))}
      </div>
      <div className="bars-x" aria-hidden="true">
        {bars.map((b) => (
          <span key={b.score}>{b.score}</span>
        ))}
      </div>
    </figure>
  );
}
