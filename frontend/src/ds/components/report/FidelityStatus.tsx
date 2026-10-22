export type FidelityStatusProps = {
  value?: number | null;
  basis?: string;
};

export function FidelityStatus({ value, basis }: FidelityStatusProps) {
  if (value == null) {
    return (
      <div className="eco-fid">
        <span className="eco-fid__ring" aria-hidden="true" />
        <span>
          <b>Fidelity score</b>
          <span>calibrazione non ancora disponibile</span>
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
      </span>
    </div>
  );
}
