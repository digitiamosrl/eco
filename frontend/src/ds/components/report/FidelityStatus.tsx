export type FidelityStatusProps = {
  value?: number | null;
  basis?: string;
  missing?: string;
};

/** What a Kendall tau-b between panel ranking and real engagement means, in one line. */
export function fidelityMeaning(value: number): string {
  if (value >= 0.3) return "il panel ordina i post come il pubblico reale";
  if (value >= 0.1) return "il panel ordina i post in parte come il pubblico reale";
  if (value > -0.1) return "vicino a 0: il panel non prevede l’engagement reale";
  return "il panel ordina i post al contrario del pubblico reale";
}

export function FidelityStatus({ value, basis, missing = "calibrazione non ancora disponibile" }: FidelityStatusProps) {
  if (value == null) {
    return (
      <div className="eco-fid">
        <span className="eco-fid__ring" aria-hidden="true" />
        <span>
          <b>Fidelity score</b>
          <span>{missing}</span>
        </span>
      </div>
    );
  }
  return (
    <div className="eco-fid eco-fid--on">
      <span className="eco-fid__num">{value.toFixed(2).replace(".", ",")}</span>
      <span>
        <b>Fidelity score</b>
        <span>{basis || "concordanza con l’engagement reale"}</span>
        <span className="eco-fid__meaning">
          {fidelityMeaning(value)} (scala da −1 a 1)
        </span>
      </span>
    </div>
  );
}
